#!/usr/bin/env python3
"""agent/workflow/state_store.py

CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.models import AttemptRecord, TaskRecord

logger = logging.getLogger(__name__)

# Grace period in seconds — attempts younger than this are NOT considered stale.
_STALE_GRACE_SEC = 30


class StateStore:
    """CRUD facade over workflow.sqlite. One instance per workflow engine lifecycle."""

    def __init__(self) -> None:
        """Initialize the state store by opening the workflow SQLite database in write mode."""
        self._db = SQLiteHelper(target="workflow")
        self._db.open(write_mode=True, row_factory=True)

    def close(self) -> None:
        """Close the underlying database connection."""
        self._db.close()

    def get_connection(self) -> SQLiteHelper:
        """Return the underlying SQLiteHelper connection.

        Used by external callers that need direct DB access for queries
        not covered by the StateStore CRUD API. Prefer using StateStore
        methods when possible; use this only when necessary.
        """
        return self._db

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
        """Update the task's status and set updated_at timestamp."""
        self._db.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
            (status, _now(), task_id),
        )
        self._db.commit()

    def _row_to_task(self, r: Any) -> TaskRecord:
        """Convert a database row dict into a TaskRecord."""
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
        """Return the task record matching the given idempotency key, or None if absent."""
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
        """Create a new attempt record with status 'running'."""
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
        """Mark an attempt as completed with its final status and optional error details."""
        self._db.execute(
            "UPDATE attempts SET status=?, ended_at=?, error_msg=?, error_kind=?, error_detail=? WHERE attempt_id=?",
            (status, _now(), error_msg, error_kind, error_detail, attempt_id),
        )
        self._db.commit()

    def count_attempts(self, task_id: str, stage_id: str) -> int:
        """Return the number of attempts recorded for a task-stage pair."""
        rows = self._db.fetchall(
            "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
            (task_id, stage_id),
        )
        return int(rows[0][0])

    # ── Diagnostic Queries ───────────────────────────────────────────────

    def get_task_count(self, session_id: str) -> int:
        """Return the number of tasks associated with a session."""
        rows = self._db.fetchall(
            "SELECT COUNT(*) as cnt FROM tasks WHERE session_id=?",
            (session_id,),
        )
        return int(rows[0]["cnt"]) if rows else 0

    def get_workflow_count(self, session_id: str) -> int:
        """Return the number of distinct workflows for a session."""
        rows = self._db.fetchall(
            "SELECT COUNT(DISTINCT workflow_id) as cnt"
            " FROM tasks WHERE session_id=? AND workflow_id IS NOT NULL",
            (session_id,),
        )
        return int(rows[0]["cnt"]) if rows else 0

    def get_approval_count(self, session_id: str) -> int:
        """Return the number of approval events for tasks in a session."""
        rows = self._db.fetchall(
            "SELECT COUNT(*) as cnt FROM approvals"
            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)",
            (session_id,),
        )
        return int(rows[0]["cnt"]) if rows else 0

    def get_execute_attempt_count(self, session_id: str) -> int:
        """Return the number of execute-stage attempts for tasks in a session."""
        rows = self._db.fetchall(
            "SELECT COUNT(*) as cnt FROM attempts"
            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)"
            " AND stage_id='execute'",
            (session_id,),
        )
        return int(rows[0]["cnt"]) if rows else 0

    def get_artifact_uris(self, session_id: str) -> list[str]:
        """Return artifact URIs for tasks in a session."""
        rows = self._db.fetchall(
            "SELECT uri FROM artifacts WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)",
            (session_id,),
        )
        return [str(dict(r)["uri"]) for r in rows if dict(r).get("uri")]

    # ── Startup Recovery ─────────────────────────────────────────────────────

    def find_stale_running_attempts(self, db: SQLiteHelper) -> list[dict]:
        """Find running attempts that exceed the configured grace period.

        Returns a list of dicts with keys: attempt_id, started_at, elapsed_sec.
        Only returns attempts older than _STALE_GRACE_SEC seconds.
        """
        rows = db.fetchall(
            "SELECT attempt_id, started_at FROM attempts WHERE status='running'",
        )
        stale = []
        now_ts = time.time()
        for row in rows:
            attempt_id = row["attempt_id"]
            started_at = row["started_at"]
            try:
                started_ts = time.mktime(time.strptime(started_at, "%Y-%m-%dT%H:%M:%S"))
            except ValueError:
                continue
            elapsed = now_ts - started_ts
            if elapsed > _STALE_GRACE_SEC:
                stale.append(
                    {
                        "attempt_id": attempt_id,
                        "started_at": started_at,
                        "elapsed_sec": elapsed,
                    }
                )
        return stale

    def recover_stale_attempts(self, db: SQLiteHelper) -> int:
        """Mark stale running attempts as failed using optimistic locking.

        An attempt is considered stale if it has been running longer than the
        configured grace period (_STALE_GRACE_SEC). This method is called once
        during process initialization before any turn processing begins.

        Returns the number of successfully transitioned attempts.
        """
        stale = self.find_stale_running_attempts(db)
        recovered_count = 0
        for item in stale:
            attempt_id = item["attempt_id"]
            started_at = item["started_at"]
            elapsed = item["elapsed_sec"]
            logger.warning(
                "Attempting recovery of stale attempt %s (started_at=%s, elapsed=%.1fs)",
                attempt_id,
                started_at,
                elapsed,
            )
            # Optimistic lock: only update if status is still 'running'
            cursor = db.execute(
                "UPDATE attempts SET status='failed', ended_at=? WHERE attempt_id=? AND status='running'",
                (_now(), attempt_id),
            )
            if cursor.rowcount == 1:
                recovered_count += 1
                logger.info("Successfully marked attempt %s as failed", attempt_id)
            else:
                logger.info(
                    "Failed to mark attempt %s as failed (already claimed or changed state)",
                    attempt_id,
                )

        if stale:
            db.commit()
        return recovered_count
