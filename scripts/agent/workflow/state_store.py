#!/usr/bin/env python3
"""agent/workflow/state_store.py
CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from db.helper import SQLiteHelper

from agent.workflow.models import AttemptRecord, TaskRecord

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class StateStore:
    """CRUD facade over workflow.sqlite. One instance per workflow engine lifecycle."""

    def __init__(self) -> None:
        self._db = SQLiteHelper(target="workflow")
        self._db.open(write_mode=True, row_factory=True)

    def close(self) -> None:
        self._db.close()

    # ── Task ─────────────────────────────────────────────────────────────────

    def create_task(
        self,
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
        self._db.execute(
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
        self._db.commit()
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

    def update_task_status(self, task_id: str, status: str) -> None:
        self._db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
            (status, _now(), task_id),
        )
        self._db.commit()

    def _row_to_task(self, r: Any) -> TaskRecord:
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

    def get_task_by_id(self, task_id: str) -> TaskRecord | None:
        """Return the task record for the given task_id, or None if absent."""
        rows = self._db.fetchall("SELECT * FROM tasks WHERE task_id=?", (task_id,))
        if not rows:
            return None
        return self._row_to_task(rows[0])

    def get_task_by_idempotency_key(self, key: str) -> TaskRecord | None:
        rows = self._db.fetchall("SELECT * FROM tasks WHERE idempotency_key=?", (key,))
        if not rows:
            return None
        return self._row_to_task(rows[0])

    def get_task_by_session(self, session_id: str) -> list[TaskRecord]:
        """Return all tasks for a session ordered by created_at ascending."""
        rows = self._db.fetchall(
            "SELECT * FROM tasks WHERE session_id=? ORDER BY created_at ASC",
            (session_id,),
        )
        return [self._row_to_task(r) for r in rows]

    def get_latest_task(self, session_id: str) -> TaskRecord | None:
        """Return the most recently created task for a session."""
        rows = self._db.fetchall(
            "SELECT * FROM tasks WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        if not rows:
            return None
        return self._row_to_task(rows[0])

    def list_tasks(self, limit: int = 50) -> list[TaskRecord]:
        """Return up to `limit` tasks ordered by created_at descending."""
        rows = self._db.fetchall(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_task(r) for r in rows]

    # ── Attempt ───────────────────────────────────────────────────────────────

    def start_attempt(self, task_id: str, stage_id: str) -> AttemptRecord:
        attempt_id = str(uuid.uuid4())
        now = _now()
        self._db.execute(
            """
            INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at)
            VALUES (?, ?, ?, 'running', ?)
            """,
            (attempt_id, task_id, stage_id, now),
        )
        self._db.commit()
        return AttemptRecord(
            attempt_id=attempt_id,
            task_id=task_id,
            stage_id=stage_id,
            status="running",
            started_at=now,
        )

    def finish_attempt(
        self,
        attempt_id: str,
        status: str,
        error_msg: str | None = None,
        error_kind: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        self._db.execute(
            "UPDATE attempts SET status=?, ended_at=?, error_msg=?, error_kind=?, error_detail=? WHERE attempt_id=?",
            (status, _now(), error_msg, error_kind, error_detail, attempt_id),
        )
        self._db.commit()

    def count_attempts(self, task_id: str, stage_id: str) -> int:
        rows = self._db.fetchall(
            "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
            (task_id, stage_id),
        )
        return int(rows[0][0])
