#!/usr/bin/env python3
"""agent/workflow/state_store.py
CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from db.helper import SQLiteHelper

from agent.workflow.models import ArtifactRef, AttemptRecord, TaskRecord

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


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
        session_id: str,
        turn_number: int,
        workflow_version: str,
    ) -> TaskRecord:
        """Create a new task record; idempotency_key is session_id:turn_number."""
        idempotency_key = f"{session_id}:{turn_number}"
        task_id = str(uuid.uuid4())
        now = _now()
        self._db.execute(
            """
            INSERT INTO tasks
                (task_id, session_id, turn_number, workflow_version,
                 status, idempotency_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                task_id,
                session_id,
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
        )

    def update_task_status(self, task_id: str, status: str) -> None:
        self._db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
            (status, _now(), task_id),
        )
        self._db.commit()

    def get_task_by_idempotency_key(self, key: str) -> TaskRecord | None:
        rows = self._db.fetchall("SELECT * FROM tasks WHERE idempotency_key=?", (key,))
        if not rows:
            return None
        r = rows[0]
        return TaskRecord(
            task_id=r["task_id"],
            session_id=r["session_id"],
            turn_number=r["turn_number"],
            workflow_version=r["workflow_version"],
            status=r["status"],
            idempotency_key=r["idempotency_key"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )

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
        self, attempt_id: str, status: str, error_msg: str | None = None
    ) -> None:
        self._db.execute(
            "UPDATE attempts SET status=?, ended_at=?, error_msg=? WHERE attempt_id=?",
            (status, _now(), error_msg, attempt_id),
        )
        self._db.commit()

    def count_attempts(self, task_id: str, stage_id: str) -> int:
        rows = self._db.fetchall(
            "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
            (task_id, stage_id),
        )
        return int(rows[0][0])

    # ── Idempotency ───────────────────────────────────────────────────────────

    def is_event_processed(self, event_id: str) -> bool:
        rows = self._db.fetchall(
            "SELECT 1 FROM processed_events WHERE event_id=?", (event_id,)
        )
        return len(rows) > 0

    def begin_stage_if_new(
        self, event_id: str, task_id: str, stage_id: str
    ) -> AttemptRecord | None:
        """Atomically check event_id and start attempt if new.

        Uses begin_immediate to hold the write lock across the check-then-insert.
        Returns AttemptRecord if the stage should run, None if already processed.
        No explicit commit() is called — begin_immediate handles the transaction.
        """
        attempt_id = str(uuid.uuid4())
        now = _now()
        with self._db.begin_immediate():
            if self.is_event_processed(event_id):
                return None
            self._db.execute(
                """
                INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at)
                VALUES (?, ?, ?, 'running', ?)
                """,
                (attempt_id, task_id, stage_id, now),
            )
            self._db.execute(
                """
                INSERT INTO processed_events (event_id, task_id, stage_id, recorded_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, task_id, stage_id, now),
            )
        return AttemptRecord(
            attempt_id=attempt_id,
            task_id=task_id,
            stage_id=stage_id,
            status="running",
            started_at=now,
        )

    # ── Artifact ──────────────────────────────────────────────────────────────

    def record_artifact(self, task_id: str, stage_id: str, uri: str) -> ArtifactRef:
        artifact_id = str(uuid.uuid4())
        now = _now()
        self._db.execute(
            """
            INSERT INTO artifacts (artifact_id, task_id, stage_id, uri, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (artifact_id, task_id, stage_id, uri, now),
        )
        self._db.commit()
        return ArtifactRef(
            artifact_id=artifact_id,
            task_id=task_id,
            stage_id=stage_id,
            uri=uri,
            created_at=now,
        )
