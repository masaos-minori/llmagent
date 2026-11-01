#!/usr/bin/env python3
"""scripts/agent/workflow/task_ops.py — Task CRUD operations for workflow.sqlite."""

import sqlite3
import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.models import TaskRecord


def create_task(
    db: SQLiteHelper,
    session_id: str | None,
    turn_number: int | None,
    workflow_version: str,
    workflow_id: str,
) -> TaskRecord:
    """Create a new task record.

    The `task_nonce` is a globally unique opaque identifier (UUID4) generated here
    for this task row; it is never derived from caller-supplied fields. `session_id` and
    `turn_number` are recorded metadata only; `turn_number` is a process-local counter
    (`agent/conversation_state_manager.py`, incremented in `append_user_message`) and is
    not part of task identity. Task identity is `task_id`: two `create_task` calls with
    identical arguments create two tasks (no request-level deduplication). The
    `tasks.task_nonce` UNIQUE constraint therefore stays inert (a backstop against a
    future key-derivation regression), and resume across a retained `workflow.sqlite`
    uses `task_id`, not this nonce.
    """
    task_nonce = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """

        INSERT INTO tasks
            (task_id, session_id, workflow_id, turn_number, workflow_version,
             status, task_nonce, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """,
        (
            task_id,
            session_id,
            workflow_id,
            turn_number,
            workflow_version,
            task_nonce,
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
        task_nonce=task_nonce,
        created_at=now,
        updated_at=now,
        workflow_id=workflow_id,
    )


def update_task_status(db: SQLiteHelper, task_id: str, status: str) -> None:
    """Update the status of a task record in the database."""
    db.execute(
        "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
        (status, _now(), task_id),
    )
    db.commit()


def _row_to_task(r: sqlite3.Row) -> TaskRecord:
    """Convert a database row into a TaskRecord dataclass instance."""
    row = dict(r)
    return TaskRecord(
        task_id=row["task_id"],
        session_id=row["session_id"],
        turn_number=row["turn_number"],
        workflow_version=row["workflow_version"],
        status=row["status"],
        task_nonce=row["task_nonce"],
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


def _scalar_count(db: SQLiteHelper, sql: str, params: tuple[object, ...]) -> int:
    """Run a `COUNT(*) as cnt`-style query and return the scalar result."""
    rows = db.fetchall(sql, params)
    return int(rows[0]["cnt"]) if rows else 0


def get_task_count(db: SQLiteHelper, session_id: str) -> int:
    """Return the number of tasks associated with a session."""
    return _scalar_count(
        db,
        "SELECT COUNT(*) as cnt FROM tasks WHERE session_id=?",
        (session_id,),
    )


def get_workflow_count(db: SQLiteHelper, session_id: str) -> int:
    """Return the number of distinct workflows for a session."""
    return _scalar_count(
        db,
        "SELECT COUNT(DISTINCT workflow_id) as cnt"
        " FROM tasks WHERE session_id=? AND workflow_id IS NOT NULL",
        (session_id,),
    )
