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

import time
from dataclasses import dataclass

from db.helper import SQLiteHelper

from agent.workflow.models import TOOL_CALL_STATES


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
    created_at: float  # epoch seconds
    updated_at: float  # epoch seconds


def _row_to_state(r: object) -> ToolCallState:
    row = dict(r)  # type: ignore[call-overload]  # — r is a sqlite3.Row at runtime; the parameter is typed object
    return ToolCallState(
        idempotency_key=row["idempotency_key"],
        task_id=row["task_id"],
        tool=row["tool"],
        state=row["state"],
        retry_class=row["retry_class"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def record_tool_call(
    db: SQLiteHelper,
    task_id: str,
    idempotency_key: str,
    tool: str,
    retry_class: str,
) -> None:
    """Insert a tool-call row in state 'pending'.

    `idempotency_key` is the opaque uuid7 logical call id from the call's
    execution context — unique by construction, so distinct calls can never
    merge into one row. Re-recording a key that already exists is a no-op
    re-finalize candidate, not a second row: the primary key rejects the insert
    and the caller's dispatch flow reaches this only for new calls, so INSERT
    OR IGNORE keeps the helper safe under a racing writer.
    """
    now = time.time()
    db.execute(
        "INSERT OR IGNORE INTO tool_call_state"
        " (idempotency_key, task_id, tool, state, retry_class, created_at, updated_at)"
        " VALUES (?, ?, ?, 'pending', ?, ?, ?)",
        (idempotency_key, task_id, tool, retry_class, now, now),
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
    "SELECT idempotency_key, state FROM tool_call_state"
    " WHERE task_id=? AND state IN ("
    + ", ".join("?" for _ in _STALE_SCAN_STATES)
    + ") AND created_at < ?"
)


def classify_stale_pending(
    db: SQLiteHelper, task_id: str, timeout_seconds: float
) -> list[ToolCallState]:
    """Transition this task's timed-out tool-call rows by dispatch stage.

    Rows still at ``pending``/``dispatch_starting`` (never dispatched) become
    ``interrupted`` — the replayable outcome callers have always seen. Rows at
    ``dispatched``/``response_received`` become ``outcome_unknown``: the request
    may have executed server-side, so automatic replay is forbidden (AC-6).

    Idempotent on re-run: only rows still in the source state listed beside
    them are transitioned, and the transition happens inside the WHERE-guarded
    UPDATE (optimistic-lock style, same discipline as ``recover_stale_attempts``).
    Returns the rows this call transitioned. The timeout value comes from the
    caller (the dispatcher-side ``pending_timeout_minutes`` config), not read
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
        target_state = (
            "interrupted"
            if source_state in _STALE_REPLAYABLE_STATES
            else "outcome_unknown"
        )
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


def get_tool_call_state(db: SQLiteHelper, idempotency_key: str) -> ToolCallState | None:
    """Return one tool-call row by key, or None if absent."""
    row = db.fetchall(
        "SELECT * FROM tool_call_state WHERE idempotency_key=?", (idempotency_key,)
    )
    if not row:
        return None
    return _row_to_state(row[0])
