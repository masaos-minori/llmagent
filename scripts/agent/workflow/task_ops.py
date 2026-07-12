#!/usr/bin/env python3
"""agent/workflow/task_ops — Task CRUD operations for workflow.sqlite."""

import uuid
from typing import Any

from agent.workflow.models import TaskRecord
from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now


def create_task(
    db: SQLiteHelper,
    session_id: str | None,
    turn_number: int | None,
    workflow_version: str,
    workflow_id: str,
) -> TaskRecord:
    """Create a new task record."""
    if session_id is not None and turn_number is not None:
        idempotency_key = f"{session_id}:{turn_number}"
    else:
        idempotency_key = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """
        INSERT INTO tasks
            (task_id, session_id, workflow_id, turn_number, workflow_version,
             status, idempotency_key, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        (
            task_id,
            session_id,
            workflow_id,
            turn_number,
            workflow_version,
            idempotency_key,
            now,
            now,
        ),
    )
    db.commit()
    return TaskRecord(
        task_id=task_id,
        session_id=session_id,
        turn_number=turn_number,
        workflow_version=workflow_version,
        status="pending",
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
        workflow_id=workflow_id,
    )


def update_task_status(db: SQLiteHelper, task_id: str, status: str) -> None:
    db.execute(
        "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
        (status, _now(), task_id),
    )
    db.commit()


def _row_to_task(r: Any) -> TaskRecord:
    row = dict(r)
    return TaskRecord(
        task_id=row["task_id"],
        session_id=row["session_id"],
        turn_number=row["turn_number"],
        workflow_version=row["workflow_version"],
        status=row["status"],
        idempotency_key=row["idempotency_key"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        workflow_id=row.get("workflow_id") or "",
    )


def get_task_by_id(db: SQLiteHelper, task_id: str) -> TaskRecord | None:
    """Return the task record for the given task_id, or None if absent."""
    rows = db.fetchall("SELECT * FROM tasks WHERE task_id=?", (task_id,))
    if not rows:
        return None
    return _row_to_task(rows[0])


def get_task_by_idempotency_key(db: SQLiteHelper, key: str) -> TaskRecord | None:
    rows = db.fetchall("SELECT * FROM tasks WHERE idempotency_key=?", (key,))
    if not rows:
        return None
    return _row_to_task(rows[0])


def get_task_by_session(db: SQLiteHelper, session_id: str) -> list[TaskRecord]:
    """Return all tasks for a session ordered by created_at ascending."""
    rows = db.fetchall(
        "SELECT * FROM tasks WHERE session_id=? ORDER BY created_at ASC",
        (session_id,),
    )
    return [_row_to_task(r) for r in rows]


def get_latest_task(db: SQLiteHelper, session_id: str) -> TaskRecord | None:
    """Return the most recently created task for a session."""
    rows = db.fetchall(
        "SELECT * FROM tasks WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
        (session_id,),
    )
    if not rows:
        return None
    return _row_to_task(rows[0])


def list_tasks(db: SQLiteHelper, limit: int = 50) -> list[TaskRecord]:
    """Return up to `limit` tasks ordered by created_at descending."""
    rows = db.fetchall(
        "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return [_row_to_task(r) for r in rows]
