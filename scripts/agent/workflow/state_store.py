#!/usr/bin/env python3
"""scripts/agent/workflow/state_store.py

CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
import time

from db.helper import SQLiteHelper

from agent.workflow.attempt_ops import finish_attempt, mark_attempt_finished
from agent.workflow.errors import AttemptTransitionError
from agent.workflow.models import AttemptStatus, TaskRecord, TaskStatus
from agent.workflow.task_ops import (
    claim_task,
    create_task,
    get_task_count,
    get_workflow_count,
    transition_task_in_txn,
    update_task_status,
)

logger = logging.getLogger(__name__)

# Grace period in seconds — attempts younger than this are NOT considered stale.
_STALE_GRACE_SEC = 30

_ERROR_KIND_STALE_RECOVERED = "stale_recovered"


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
        return create_task(
            self._db, session_id, turn_number, workflow_version, workflow_id
        )

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update the task's status and set updated_at timestamp."""
        update_task_status(self._db, task_id, status)

    # ── Attempt ───────────────────────────────────────────────────────────────

    def finish_attempt(
        self,
        attempt_id: str,
        status: str,
        error_msg: str | None = None,
        error_kind: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        """Move a running attempt to `completed` or `failed` (terminal-only, conditional)."""
        finish_attempt(
            self._db, attempt_id, status, error_msg, error_kind, error_detail
        )

    def claim_task(self, task_id: str) -> None:
        """Move a `pending` or `failed` task to `running`; reject every other status."""
        claim_task(self._db, task_id)

    def count_attempts(self, task_id: str, stage_id: str) -> int:
        """Return the number of attempts recorded for a task-stage pair."""
        rows = self._db.fetchall(
            "SELECT COUNT(*) FROM attempts WHERE task_id=? AND stage_id=?",
            (task_id, stage_id),
        )
        return int(rows[0][0])

    # ── Diagnostic Queries ───────────────────────────────────────────────

    def _scalar_count(self, sql: str, params: tuple[object, ...]) -> int:
        """Run a `COUNT(*) as cnt`-style query and return the scalar result."""
        rows = self._db.fetchall(sql, params)
        return int(rows[0]["cnt"]) if rows else 0

    def get_task_count(self, session_id: str) -> int:
        """Return the number of tasks associated with a session."""
        return get_task_count(self._db, session_id)

    def get_workflow_count(self, session_id: str) -> int:
        """Return the number of distinct workflows for a session."""
        return get_workflow_count(self._db, session_id)

    def get_execute_attempt_count(self, session_id: str) -> int:
        """Return the number of execute-stage attempts for tasks in a session.

        Returns:
            Non-negative integer. Always returns a valid int even if no matching
            rows exist (defaults to 0 via _scalar_count). Never returns None.
        """
        return self._scalar_count(
            "SELECT COUNT(*) as cnt FROM attempts"
            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)"
            " AND stage_id='execute'",
            (session_id,),
        )

    def get_artifact_uris(self, session_id: str) -> list[str]:
        """Return artifact URIs for tasks in a session."""
        rows = self._db.fetchall(
            "SELECT uri FROM artifacts WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)",
            (session_id,),
        )
        uris = (dict(r) for r in rows)
        return [str(d["uri"]) for d in uris if d.get("uri")]

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
        """Mark stale running attempts failed and fail their running tasks.

        An attempt is stale when it has been running longer than the grace period
        (_STALE_GRACE_SEC). Called once during process initialization before any turn
        processing begins. Each stale attempt is recovered in its own write
        transaction: the attempt moves `running -> failed` (conditional, so a lost
        race is skipped), then its task moves `running -> failed` when no other
        attempt of the task is still `running`. A repeated call finds no `running`
        stale attempt and changes nothing.

        Returns the number of attempts actually transitioned.
        """
        recovered_count = 0
        for item in self.find_stale_running_attempts(db):
            attempt_id = item["attempt_id"]
            logger.warning(
                "Attempting recovery of stale attempt %s (started_at=%s, elapsed=%.1fs)",
                attempt_id,
                item["started_at"],
                item["elapsed_sec"],
            )
            try:
                with db.begin_immediate():
                    mark_attempt_finished(
                        db,
                        attempt_id,
                        AttemptStatus.FAILED.value,
                        error_msg="stale running attempt recovered at startup",
                        error_kind=_ERROR_KIND_STALE_RECOVERED,
                    )
                    self._fail_task_without_running_attempts(db, attempt_id)
            except AttemptTransitionError:
                logger.info(
                    "Attempt %s was already finished or claimed; skipped", attempt_id
                )
                continue
            recovered_count += 1
            logger.info("Successfully marked attempt %s as failed", attempt_id)
        return recovered_count

    @staticmethod
    def _fail_task_without_running_attempts(db: SQLiteHelper, attempt_id: str) -> None:
        """Move the attempt's task `running -> failed` when no attempt of it still runs."""
        rows = db.fetchall(
            "SELECT t.task_id, t.status FROM attempts a JOIN tasks t"
            " ON t.task_id = a.task_id WHERE a.attempt_id=?",
            (attempt_id,),
        )
        if not rows or rows[0]["status"] != TaskStatus.RUNNING.value:
            return
        task_id = rows[0]["task_id"]
        other = db.fetchall(
            "SELECT 1 FROM attempts WHERE task_id=? AND status=? LIMIT 1",
            (task_id, AttemptStatus.RUNNING.value),
        )
        if not other:
            transition_task_in_txn(
                db,
                task_id,
                TaskStatus.FAILED.value,
                expected=TaskStatus.RUNNING.value,
            )
