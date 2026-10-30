#!/usr/bin/env python3
"""scripts/agent/workflow/attempt_ops.py — Attempt operations for workflow.sqlite."""

import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.errors import AttemptTransitionError
from agent.workflow.models import (
    ATTEMPT_TERMINAL_STATUSES,
    AttemptRecord,
    AttemptStatus,
)


def max_attempt_number(db: SQLiteHelper, task_id: str, stage_id: str) -> int:
    """Return the largest persisted attempt number of a task-stage pair, or 0."""
    rows = db.fetchall(
        "SELECT COALESCE(MAX(attempt_number), 0) FROM attempts"
        " WHERE task_id=? AND stage_id=?",
        (task_id, stage_id),
    )
    return int(rows[0][0])


def insert_attempt(db: SQLiteHelper, task_id: str, stage_id: str) -> AttemptRecord:
    """Insert a running attempt with the next persisted number.

    Runs inside the caller's write transaction (`begin_immediate()`), so the number
    allocation and the insert are one serialized step; the unique index on
    (task_id, stage_id, attempt_number) is the backstop. Never commits.
    """
    attempt_id = str(uuid.uuid4())
    now = _now()
    number = max_attempt_number(db, task_id, stage_id) + 1
    db.execute(
        """

        INSERT INTO attempts
            (attempt_id, task_id, stage_id, status, started_at, attempt_number)
        VALUES (?, ?, ?, 'running', ?, ?)
        """,
        (attempt_id, task_id, stage_id, now, number),
    )
    return AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        stage_id=stage_id,
        status=AttemptStatus.RUNNING.value,
        started_at=now,
        attempt_number=number,
    )


def mark_attempt_finished(
    db: SQLiteHelper,
    attempt_id: str,
    status: str,
    error_msg: str | None = None,
    error_kind: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Move a `running` attempt to a terminal status inside the caller's transaction.

    Raises AttemptTransitionError for a non-terminal status or when the attempt is
    not `running` (already finished, recovered, or unknown). Never commits.
    """
    try:
        terminal = AttemptStatus(status) in ATTEMPT_TERMINAL_STATUSES
    except ValueError:
        terminal = False
    if not terminal:
        raise AttemptTransitionError(attempt_id, "unknown", status)
    cursor = db.execute(
        "UPDATE attempts SET status=?, ended_at=?, error_msg=?, error_kind=?,"
        " error_detail=? WHERE attempt_id=? AND status='running'",
        (status, _now(), error_msg, error_kind, error_detail, attempt_id),
    )
    if cursor.rowcount != 1:
        rows = db.fetchall(
            "SELECT status FROM attempts WHERE attempt_id=?", (attempt_id,)
        )
        found = str(rows[0]["status"]) if rows else "missing"
        raise AttemptTransitionError(attempt_id, found, status)


def finish_attempt(
    db: SQLiteHelper,
    attempt_id: str,
    status: str,
    error_msg: str | None = None,
    error_kind: str | None = None,
    error_detail: str | None = None,
) -> None:
    """Move a running attempt to `completed` or `failed` in its own transaction."""
    with db.begin_immediate():
        mark_attempt_finished(
            db, attempt_id, status, error_msg, error_kind, error_detail
        )


def count_attempts(db: SQLiteHelper, task_id: str, stage_id: str) -> int:
    """Count the number of attempts for a specific task and stage combination."""
    rows = db.fetchall(
        "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
        (task_id, stage_id),
    )
    return int(rows[0][0])
