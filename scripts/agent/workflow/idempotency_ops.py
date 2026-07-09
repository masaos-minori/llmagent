#!/usr/bin/env python3
"""agent/workflow/idempotency_ops.py — Idempotency operations for workflow.sqlite."""

import uuid
from datetime import UTC, datetime

from agent.workflow.models import AttemptRecord
from db.helper import SQLiteHelper


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_event_processed(db: SQLiteHelper, event_id: str) -> bool:
    rows = db.fetchall("SELECT 1 FROM processed_events WHERE event_id=?", (event_id,))
    return len(rows) > 0


def begin_stage_if_new(
    db: SQLiteHelper,
    event_id: str,
    task_id: str,
    stage_id: str,
    workflow_id: str | None = None,
) -> AttemptRecord | None:
    """Atomically check event_id and start attempt if new.

    Uses begin_immediate to hold the write lock across the check-then-insert.
    Returns AttemptRecord if the stage should run, None if already processed.
    No explicit commit() is called — begin_immediate handles the transaction.
    """
    attempt_id = str(uuid.uuid4())
    now = _now()
    with db.begin_immediate():
        if is_event_processed(db, event_id):
            return None
        db.execute(
            """
            INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at)
            VALUES (?, ?, ?, 'running', ?)
            """,
            (attempt_id, task_id, stage_id, now),
        )
        db.execute(
            """
            INSERT INTO processed_events (event_id, task_id, stage_id, recorded_at, workflow_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, task_id, stage_id, now, workflow_id),
        )
    return AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        stage_id=stage_id,
        status="running",
        started_at=now,
    )
