#!/usr/bin/env python3
"""agent/workflow/attempt_ops.py — Attempt operations for workflow.sqlite."""

import uuid
from datetime import UTC, datetime

from db.helper import SQLiteHelper

from agent.workflow.models import AttemptRecord


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def start_attempt(db: SQLiteHelper, task_id: str, stage_id: str) -> AttemptRecord:
    attempt_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """
        INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at)
        VALUES (?, ?, ?, 'running', ?)
        """,
        (attempt_id, task_id, stage_id, now),
    )
    db.commit()
    return AttemptRecord(
        attempt_id=attempt_id,
        task_id=task_id,
        stage_id=stage_id,
        status="running",
        started_at=now,
    )


def finish_attempt(db: SQLiteHelper, attempt_id: str, status: str, error_msg: str | None = None) -> None:
    db.execute(
        "UPDATE attempts SET status=?, ended_at=?, error_msg=? WHERE attempt_id=?",
        (status, _now(), error_msg, attempt_id),
    )
    db.commit()


def count_attempts(db: SQLiteHelper, task_id: str, stage_id: str) -> int:
    rows = db.fetchall(
        "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
        (task_id, stage_id),
    )
    return int(rows[0][0])
