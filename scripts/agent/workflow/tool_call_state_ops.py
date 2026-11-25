#!/usr/bin/env python3
"""scripts/agent/workflow/tool_call_state_ops.py — Tool-call state operations for workflow.sqlite.

Task-scoped read/write helpers over the ``tool_call_state`` table (toolexec001
). The agent's view of a tool call lives here, written by the executor
path; the durable dedup store stays behind the dispatcher boundary (ADR-008), so these
helpers never touch ``mcp_dedup.sqlite``.

``created_at``/``updated_at`` are REAL epoch seconds, matching the row-06 DDL of the
table (unlike the ISO-8601 TEXT columns of the older workflow tables).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

from db.helper import SQLiteHelper

from agent.workflow.models import TOOL_CALL_STATES

logger = logging.getLogger(__name__)


@dataclass
class ToolCallState:
    """Database record for one tool-call lifecycle row."""

    idempotency_key: str
    task_id: str
    tool: str
    # intent vocabulary: pending | dispatch_starting | dispatched | response_received
    # | completed | failed | interrupted | outcome_unknown | reconciliation_required
    state: str
    retry_class: str
    args_hash: str  # canonical argument hash read by replay-directive reconstruction
    created_at: float  # epoch seconds
    updated_at: float  # epoch seconds


class CallStateResolver(Protocol):
    """The seam stale classification consults for an already-dispatched row.

    Implementations read evidence and return a state from the shared mapping table, or
    None when nothing can be established. They never write a tool_call_state row: the
    guarded UPDATE below is the only writer, so a resolver cannot race it.
    """

    def resolve_state(self, row: ToolCallState) -> str | None: ...


def _row_to_state(r: object) -> ToolCallState:
    row = dict(r)  # type: ignore[call-overload]  # — r is a sqlite3.Row at runtime; the parameter is typed object
    return ToolCallState(
        idempotency_key=row["idempotency_key"],
        task_id=row["task_id"],
        tool=row["tool"],
        state=row["state"],
        retry_class=row["retry_class"],
        args_hash=row["args_hash"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def record_tool_call(
    db: SQLiteHelper,
    task_id: str,
    idempotency_key: str,
    tool: str,
    retry_class: str,
    args_hash: str,
) -> None:
    """Insert a tool-call row in state 'pending'.

    `args_hash` is the canonical argument hash computed at preparation; the column is
    `NOT NULL` with no default, so this writer is the place it is populated. It is the
    field replay-directive reconstruction matches a reissued call against.

    `idempotency_key` is the opaque uuid7 logical call id from the call's
    execution context — unique by construction, so distinct calls can never
    merge into one row. Re-recording a key that already exists is a no-op
    re-finalize candidate, not a second row: the primary key rejects the insert
    and the caller's dispatch flow reaches this only for new calls, so INSERT
    OR IGNORE keeps the helper safe under a racing writer, and the stored hash
    stays the one written by the first insert.
    """
    now = time.time()
    db.execute(
        "INSERT OR IGNORE INTO tool_call_state"
        " (idempotency_key, task_id, tool, state, retry_class, args_hash,"
        " created_at, updated_at)"
        " VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)",
        (idempotency_key, task_id, tool, retry_class, args_hash, now, now),
    )
    db.commit()


def finalize_tool_call(db: SQLiteHelper, idempotency_key: str, state: str) -> None:
    """Move a tool-call row to another state in the intent vocabulary, bumping
    updated_at.

    Accepts the intermediate dispatch-stage states (`dispatch_starting`,
    `dispatched`, `response_received`) exactly like the terminal ones — the
    vocabulary check is the only gate.

    Raises:
        ValueError: if `state` is not in the `tool_call_state.state` vocabulary.
    """
    if state not in TOOL_CALL_STATES:
        raise ValueError(
            f"invalid tool_call_state.state {state!r} (allowed: {sorted(TOOL_CALL_STATES)})"
        )
    db.execute(
        "UPDATE tool_call_state SET state=?, updated_at=? WHERE idempotency_key=?",
        (state, time.time(), idempotency_key),
    )
    db.commit()


def pending_tool_calls(db: SQLiteHelper, task_id: str) -> list[ToolCallState]:
    """Return the task's pending tool-call rows, oldest first.

    Test-only helper: exercised by the workflow state-store tests. Kept cheap via
    the ``idx_tool_call_state_task_state`` index. The turn-entry stale-detection
    entry point is ``classify_stale_pending`` (``workflow_engine.py:180``).
    """
    rows = db.fetchall(
        "SELECT * FROM tool_call_state WHERE task_id=? AND state='pending'"
        " ORDER BY created_at ASC",
        (task_id,),
    )
    return [_row_to_state(r) for r in rows]


# Stale-scan source-state groups (REQ-009, AC-6): rows that never reached the
# wire replay safely as 'interrupted'; rows already dispatched get
# 'outcome_unknown' because their server-side outcome is unknowable.
_STALE_REPLAYABLE_STATES = ("pending", "dispatch_starting")
_STALE_OUTCOME_UNKNOWN_STATES = ("dispatched", "response_received")
_STALE_SCAN_STATES = _STALE_REPLAYABLE_STATES + _STALE_OUTCOME_UNKNOWN_STATES
_STALE_SCAN_SQL = (
    "SELECT idempotency_key, state FROM tool_call_state"  # nosec B608 — the concatenation only emits literal ? placeholders from a module-constant tuple; all values bind through the placeholders
    " WHERE task_id=? AND state IN ("
    + ", ".join("?" for _ in _STALE_SCAN_STATES)
    + ") AND created_at < ?"
)


def _resolved_target(
    resolver: CallStateResolver, row: ToolCallState | None
) -> str | None:
    """Target state for a dispatched row, or None when the row must be left alone.

    A resolver that establishes nothing, or returns a value outside this vocabulary,
    leaves the row at the outcome it would have had without a resolver. `in_progress` is
    a recovery outcome only (mcpdl004 REQ-005): it is not a tool_call_state state, so
    the row stays as it is and is not listed to turn control.
    """
    if row is None:
        return "outcome_unknown"
    try:
        value = resolver.resolve_state(row)
    except Exception as exc:  # noqa: BLE001 — a resolver is optional evidence; its failure must not change a row that was already going to be classified
        logger.warning(
            "event=call_state_resolver label=resolver_failed call=%s error=%s",
            row.idempotency_key[:8],
            type(exc).__name__,
        )
        return "outcome_unknown"
    if value is None:
        return "outcome_unknown"
    if value == "in_progress":
        return None
    if value not in TOOL_CALL_STATES:
        return "outcome_unknown"
    return value


def classify_stale_pending(
    db: SQLiteHelper,
    task_id: str,
    timeout_seconds: float,
    resolver: CallStateResolver | None = None,
) -> list[ToolCallState]:
    """Transition this task's timed-out tool-call rows by dispatch stage.

    Rows still at ``pending``/``dispatch_starting`` (never dispatched) become
    ``interrupted`` — the replayable outcome callers have always seen. Rows at
    ``dispatched``/``response_received`` become ``outcome_unknown``: the request
    may have executed server-side, so automatic replay is forbidden (AC-6).

    With a ``resolver`` (mcpdl004 REQ-005), a dispatched row is asked before the
    decision is made, and the answer it gives replaces ``outcome_unknown`` when
    that answer is a state this vocabulary can store. ``in_progress`` is not a
    stored state, so such a row is left untouched and not listed. Without a
    resolver the behavior is byte-identical to before, and a resolver failure
    never changes a row that would otherwise have become ``outcome_unknown``. No
    resolver re-executes a handler here: it reports what it read.

    Idempotent on re-run: only rows still in the source state listed beside
    them are transitioned, and the transition happens inside the WHERE-guarded
    UPDATE (optimistic-lock style, same discipline as ``recover_stale_attempts``).
    Returns the rows this call transitioned. The timeout value comes from the
    caller (the Agent-side ``AgentConfig.pending_timeout_minutes``), not read
    here — this module stays config-free.
    """
    cutoff = time.time() - timeout_seconds
    rows = db.fetchall(_STALE_SCAN_SQL, (task_id, *_STALE_SCAN_STATES, cutoff))
    if not rows:
        return []
    stale: list[ToolCallState] = []
    now = time.time()
    for row in rows:
        source_state = str(row["state"])
        target_state: str | None = (
            "interrupted"
            if source_state in _STALE_REPLAYABLE_STATES
            else "outcome_unknown"
        )
        if resolver is not None and source_state in _STALE_OUTCOME_UNKNOWN_STATES:
            # The scan selects key and state only, so the resolver is given the full
            # tool-call record through the existing helper.
            target_state = _resolved_target(
                resolver, get_tool_call_state(db, str(row["idempotency_key"]))
            )
        if target_state is None:
            continue
        cursor = db.execute(
            "UPDATE tool_call_state SET state=?, updated_at=?"
            " WHERE idempotency_key=? AND state=?",
            (target_state, now, str(row["idempotency_key"]), source_state),
        )
        if cursor.rowcount == 1:
            state_row = get_tool_call_state(db, str(row["idempotency_key"]))
            if state_row is not None:
                stale.append(state_row)
    db.commit()
    return stale


def reconstruct_replay_directives(
    db: SQLiteHelper, task_id: str
) -> list[ToolCallState]:
    """Return this task's `interrupted` replayable rows, oldest first.

    These are the rows a replay directive is built from (REQ-004): `interrupted` with
    `retry_class` 'retryable'. Consumption is recorded by the row leaving the
    replayable states, so a restarted process sees no directive for a row the replay
    completed (REQ-006). A row the replay left at `dispatch_starting` is still
    replayable — `classify_stale_pending` re-transitions a stale row in that state to
    `interrupted` (mcpdl001 REQ-009), so it produces a directive again.

    Reads only: `classify_stale_pending` is the only writer of `interrupted`, so this
    query cannot race its guarded UPDATE. It runs at turn entry after that call, so the
    rows it lists are the rows classification just transitioned.
    """
    rows = db.fetchall(
        "SELECT * FROM tool_call_state WHERE task_id=? AND state='interrupted'"
        " AND retry_class='retryable' ORDER BY created_at ASC",
        (task_id,),
    )
    return [_row_to_state(r) for r in rows]


def get_tool_call_state(db: SQLiteHelper, idempotency_key: str) -> ToolCallState | None:
    """Return one tool-call row by key, or None if absent."""
    row = db.fetchall(
        "SELECT * FROM tool_call_state WHERE idempotency_key=?", (idempotency_key,)
    )
    if not row:
        return None
    return _row_to_state(row[0])
