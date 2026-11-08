#!/usr/bin/env python3
"""scripts/agent/workflow/state_store.py

CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now
from shared.json_utils import parse_iso_utc

from agent.workflow import attempt_ops, tool_call_state_ops
from agent.workflow.models import TaskRecord
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
    get_task_count,
    get_workflow_count,
    update_task_status,
)
from agent.workflow.tool_call_state_ops import ToolCallState

logger = logging.getLogger(__name__)

# Attempts created before the lease migration carry no lease; they are stale
# once older than this many seconds (Plan REQ-008 interim safety net).
_LEGACY_STALE_AGE_SEC = 3600


@dataclass(frozen=True)
class RecoveryReport:
    """Classification counts from the last ``recover_stale_attempts()`` run."""

    recovered: int = 0
    still_live: int = 0
    legacy_recovered: int = 0
    unparseable: int = 0


class StateStore:
    """CRUD facade over workflow.sqlite. One instance per workflow engine lifecycle."""

    def __init__(self) -> None:
        """Initialize the state store by opening the workflow SQLite database in write mode."""
        self._db = SQLiteHelper(target="workflow")
        self._db.open(write_mode=True, row_factory=True)
        self.last_recovery_report = RecoveryReport()

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

    def get_task_by_id(self, task_id: str) -> TaskRecord | None:
        """Return the task record for the given task_id, or None if absent."""
        return get_task_by_id(self._db, task_id)

    # ── Attempt ───────────────────────────────────────────────────────────────

    def finish_attempt(
        self,
        attempt_id: str,
        status: str,
        error_msg: str | None = None,
        error_kind: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        """Mark an attempt as completed with its final status and optional error details."""
        attempt_ops.finish_attempt(
            self._db, attempt_id, status, error_msg, error_kind, error_detail
        )

    # ── Tool-call state (workflow.sqlite tool_call_state table) ──────────────

    def record_tool_call(
        self,
        task_id: str,
        idempotency_key: str,
        tool: str,
        retry_class: str,
    ) -> None:
        """Insert a tool-call row in state 'pending' for the task."""
        tool_call_state_ops.record_tool_call(
            self._db, task_id, idempotency_key, tool, retry_class
        )

    def finalize_tool_call(self, idempotency_key: str, state: str) -> None:
        """Move a tool-call row to its final state, bumping updated_at."""
        tool_call_state_ops.finalize_tool_call(self._db, idempotency_key, state)

    def classify_stale_pending(
        self, task_id: str, timeout_seconds: float
    ) -> list[ToolCallState]:
        """Mark this task's timed-out pending tool-call rows as 'interrupted'."""
        return tool_call_state_ops.classify_stale_pending(
            self._db, task_id, timeout_seconds
        )

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

    def recover_stale_attempts(self, db: SQLiteHelper) -> int:
        """Mark lease-expired (or lease-less and old) running attempts as failed.

        An attempt is stale when its ``lease_expires_at`` is in the past, or —
        for rows that predate the lease migration and have no lease — when
        ``started_at`` is older than ``_LEGACY_STALE_AGE_SEC``. A live lease is
        never recovered, including by another process (REQ-006 / AC-4). This
        method is called once during process initialization before any turn
        processing begins.

        Takeover is a conditional compare-and-swap UPDATE pinned to the exact
        ``owner_id``/``lease_expires_at`` values seen by the classify pass
        (REQ-007): ``rowcount == 0`` means another recoverer won the race and
        the row is skipped. The four-way classification counts land in
        ``last_recovery_report``; the return value stays the recovered count.
        """
        classified = _classify_running_attempts(db)
        unparseable = sum(1 for r in classified if r["classification"] == "unparseable")
        still_live = sum(1 for r in classified if r["classification"] == "live")
        stale = [r for r in classified if r["classification"] == "stale"]
        recovered = 0
        legacy_recovered = 0
        for item in stale:
            attempt_id = item["attempt_id"]
            logger.warning(
                "Attempting recovery of stale attempt %s (started_at=%s, elapsed=%.1fs)",
                attempt_id,
                item["started_at"],
                item["elapsed_sec"],
            )
            if item["lease_expires_at"] is None:
                reason = f"legacy attempt older than {_LEGACY_STALE_AGE_SEC}s"
            else:
                reason = "lease expired"
            cursor = db.execute(
                "UPDATE attempts SET status='failed', ended_at=?, error_msg=? "
                "WHERE attempt_id=? AND status='running' AND owner_id IS ? "
                "AND lease_expires_at IS ?",
                (
                    _now(),
                    f"recovered at startup: {reason}",
                    attempt_id,
                    item["owner_id"],
                    item["lease_expires_at"],
                ),
            )
            if cursor.rowcount == 1:
                recovered += 1
                if item["lease_expires_at"] is None:
                    legacy_recovered += 1
                logger.info("Successfully marked attempt %s as failed", attempt_id)
            else:
                logger.info(
                    "Failed to mark attempt %s as failed (already claimed or changed state)",
                    attempt_id,
                )

        if stale:
            db.commit()
        self.last_recovery_report = RecoveryReport(
            recovered=recovered,
            still_live=still_live,
            legacy_recovered=legacy_recovered,
            unparseable=unparseable,
        )
        return recovered


def _classify_running_attempts(db: SQLiteHelper) -> list[dict]:
    """Classify every running attempt row as stale, live, or unparseable.

    Staleness is decided from ``lease_expires_at`` when present (expired =
    stale); lease-less rows fall back to the legacy age rule (REQ-008). All
    comparisons use aware UTC datetimes via ``parse_iso_utc`` — no host-local
    time anywhere (REQ-002 / AC-2). Unparseable ``started_at`` or
    ``lease_expires_at`` values are logged with the attempt id and raw value
    and classified ``unparseable`` — the row is neither recovered nor silently
    skipped (REQ-003 / AC-3).
    """
    rows = db.fetchall(
        "SELECT attempt_id, started_at, owner_id, lease_expires_at "
        "FROM attempts WHERE status='running'"
    )
    now_utc = datetime.now(UTC)
    classified: list[dict] = []
    for row in rows:
        attempt_id = row["attempt_id"]
        started_at = row["started_at"]
        lease_expires_at = row["lease_expires_at"]
        entry = {
            "attempt_id": attempt_id,
            "started_at": started_at,
            "owner_id": row["owner_id"],
            "lease_expires_at": lease_expires_at,
        }
        try:
            started_dt = parse_iso_utc(started_at)
        except ValueError:
            logger.warning(
                "unparseable workflow attempt timestamp: attempt_id=%s value=%s",
                attempt_id,
                started_at,
            )
            classified.append({**entry, "classification": "unparseable"})
            continue
        entry["elapsed_sec"] = (now_utc - started_dt).total_seconds()
        if lease_expires_at is not None:
            try:
                lease_dt = parse_iso_utc(lease_expires_at)
            except ValueError:
                logger.warning(
                    "unparseable workflow attempt timestamp: attempt_id=%s value=%s",
                    attempt_id,
                    lease_expires_at,
                )
                classified.append({**entry, "classification": "unparseable"})
                continue
            stale = lease_dt < now_utc
        else:
            stale = entry["elapsed_sec"] > _LEGACY_STALE_AGE_SEC
        classified.append({**entry, "classification": "stale" if stale else "live"})
    return classified
