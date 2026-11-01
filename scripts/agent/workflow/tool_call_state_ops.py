#!/usr/bin/env python3
"""scripts/agent/workflow/tool_call_state_ops.py — Tool-call state operations for workflow.sqlite.

Task-scoped read/write helpers over the ``tool_call_state`` table (toolexec001
REQ-007/REQ-008). The agent's view of a tool call lives here, written by the executor
path; the durable dedup store stays behind the dispatcher boundary (ADR-008), so these
helpers never touch ``mcp_dedup.sqlite``.

``created_at``/``updated_at`` are REAL epoch seconds, matching the row-06 DDL of the
table (unlike the ISO-8601 TEXT columns of the older workflow tables).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from db.helper import SQLiteHelper


@dataclass
class ToolCallState:
    """Database record for one tool-call lifecycle row."""

    idempotency_key: str
    task_id: str
    tool: str
    state: str  # pending | completed | failed | interrupted
    retry_class: str
    snapshot_id: str | None
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
        snapshot_id=row["snapshot_id"],
        created_at=float(row["created_at"]),
        updated_at=float(row["updated_at"]),
    )


def record_tool_call(
    db: SQLiteHelper,
    task_id: str,
    idempotency_key: str,
    tool: str,
    retry_class: str,
    snapshot_id: str | None = None,
) -> None:
    """Insert a tool-call row in state 'pending'.

    Re-recording a key that already exists is a no-op re-finalize candidate, not a
    second row: the primary key rejects the insert and the caller's dispatch flow
    reaches this only for new calls, so INSERT OR IGNORE keeps the helper safe under
    a racing writer.
    """
    now = time.time()
    db.execute(
        "INSERT OR IGNORE INTO tool_call_state"
        " (idempotency_key, task_id, tool, state, retry_class, snapshot_id, created_at, updated_at)"
        " VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)",
        (idempotency_key, task_id, tool, retry_class, snapshot_id, now, now),
    )
    db.commit()


def finalize_tool_call(db: SQLiteHelper, idempotency_key: str, state: str) -> None:
    """Move a tool-call row to its final state, bumping updated_at."""
    db.execute(
        "UPDATE tool_call_state SET state=?, updated_at=? WHERE idempotency_key=?",
        (state, time.time(), idempotency_key),
    )
    db.commit()


def pending_tool_calls(db: SQLiteHelper, task_id: str) -> list[ToolCallState]:
    """Return the task's pending tool-call rows, oldest first.

    The only method the turn-entry detection path (workflow_engine) calls; kept cheap
    via the ``idx_tool_call_state_task_state`` index.
    """
    rows = db.fetchall(
        "SELECT * FROM tool_call_state WHERE task_id=? AND state='pending'"
        " ORDER BY created_at ASC",
        (task_id,),
    )
    return [_row_to_state(r) for r in rows]


def classify_stale_pending(
    db: SQLiteHelper, task_id: str, timeout_seconds: float
) -> list[ToolCallState]:
    """Mark this task's pending rows older than `timeout_seconds` as 'interrupted'.

    Idempotent on re-run: only rows still in state 'pending' are transitioned, and
    the transition happens inside the WHERE-guarded UPDATE (optimistic-lock style,
    same discipline as ``recover_stale_attempts``). Returns the rows this call
    transitioned. The timeout value comes from the caller (the dispatcher-side
    ``pending_timeout_minutes`` config), not read here — this module stays
    config-free.
    """
    cutoff = time.time() - timeout_seconds
    keys = [
        str(row["idempotency_key"])
        for row in db.fetchall(
            "SELECT idempotency_key FROM tool_call_state"
            " WHERE task_id=? AND state='pending' AND created_at < ?",
            (task_id, cutoff),
        )
    ]
    if not keys:
        return []
    stale: list[ToolCallState] = []
    now = time.time()
    for key in keys:
        cursor = db.execute(
            "UPDATE tool_call_state SET state='interrupted', updated_at=?"
            " WHERE idempotency_key=? AND state='pending'",
            (now, key),
        )
        if cursor.rowcount == 1:
            row = get_tool_call_state(db, key)
            if row is not None:
                stale.append(row)
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
