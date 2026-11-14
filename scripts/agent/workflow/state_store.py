#!/usr/bin/env python3
"""scripts/agent/workflow/state_store.py

CRUD operations and idempotency enforcement for workflow.sqlite.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now
from shared.json_utils import parse_iso_utc

from agent.workflow import (
    artifact_ops,
    attempt_ops,
    idempotency_ops,
    tool_call_state_ops,
)
from agent.workflow.models import ArtifactRef, AttemptRecord, TaskRecord
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
    get_task_count,
    get_workflow_count,
    update_task_status,
)
from agent.workflow.tool_call_state_ops import ToolCallState

logger = logging.getLogger(__name__)

# Retention horizon for processed_events rows of terminal tasks (wfaudit001
# the 30-day value is the plan UNK-01 choice, not the dedup default).
_EVENT_RETENTION_SEC = 30 * 24 * 3600
# Terminal subset of TASK_STATUSES whose processed_events rows are purged;
# keep in sync with agent.workflow.models.TASK_STATUSES.
_TERMINAL_TASK_STATUSES = ("completed", "failed", "halted")


@dataclass(frozen=True)
class RecoveryReport:
    """Classification counts from the last ``recover_stale_attempts()`` run."""

    recovered: int = 0
    still_live: int = 0
    unparseable: int = 0
    tasks_reconciled: int = 0


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

    def begin_stage_if_new(
        self,
        event_id: str,
        task_id: str,
        stage_id: str,
        workflow_id: str | None = None,
        lease_duration_sec: int | None = None,
    ) -> AttemptRecord | None:
        """Start an attempt for the event if it has not been processed yet.

        Delegates to idempotency_ops.begin_stage_if_new with the store's own
        connection. Returns AttemptRecord if the stage should run, None if the
        event was already processed. begin_immediate handles the transaction;
        no explicit commit here.
        """
        return idempotency_ops.begin_stage_if_new(
            self._db,
            event_id,
            task_id,
            stage_id,
            workflow_id=workflow_id,
            lease_duration_sec=lease_duration_sec,
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

    # ── Artifact ─────────────────────────────────────────────────────────────

    def record_artifact(
        self,
        task_id: str,
        stage_id: str,
        uri: str,
        workflow_id: str | None = None,
        attempt_number: int | None = None,
    ) -> ArtifactRef:
        """Insert an artifact reference using the store's own connection.

        Delegates to artifact_ops.record_artifact; that function commits.
        """
        return artifact_ops.record_artifact(
            self._db,
            task_id,
            stage_id,
            uri,
            workflow_id=workflow_id,
            attempt_number=attempt_number,
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

    def recover_stale_attempts(self) -> int:
        """Mark lease-expired running attempts as failed.

        Always operates on the store's own connection; callers pass no arguments.

        An attempt is stale when its ``lease_expires_at`` is in the past. The
        lease-less legacy age rule was removed (adrrev005): the sole
        attempts writer always stamps a lease, so a lease-less row has no
        expiry evidence and stays live, and legacy databases that carry such
        rows are refused earlier by the workflow fingerprint gate. A live lease
        is never recovered, including by another process (AC-4). This
        method is called once during process initialization before any turn
        processing begins.

        Takeover is a conditional compare-and-swap UPDATE pinned to the exact
        ``owner_id``/``lease_expires_at`` values seen by the classify pass: ``rowcount == 0`` means another recoverer won the race and
        the row is skipped. Every claimed attempt also deletes the
        ``processed_events`` rows of its (``task_id``, ``stage_id``) pair in the
        same transaction, so a resumed stage re-executes instead of being
        permanently skipped. After the loop, every claimed task with
        no remaining live attempt is reconciled from ``running`` to ``failed``
        through the validated ops helper (still one transaction); tasks that
        keep a live-leased or terminal-status attempt are never touched. The classification and reconciliation counts land in
        ``last_recovery_report``; the return value stays the recovered count.
        """
        db = self._db
        classified = _classify_running_attempts(db)
        unparseable = sum(1 for r in classified if r["classification"] == "unparseable")
        still_live = sum(1 for r in classified if r["classification"] == "live")
        stale = [r for r in classified if r["classification"] == "stale"]
        recovered = 0
        reconciled_candidates: set[str] = set()
        for item in stale:
            attempt_id = item["attempt_id"]
            logger.warning(
                "Attempting recovery of stale attempt %s (started_at=%s, elapsed=%.1fs)",
                attempt_id,
                item["started_at"],
                item["elapsed_sec"],
            )
            cursor = db.execute(
                "UPDATE attempts SET status='failed', ended_at=?, error_msg=? "
                "WHERE attempt_id=? AND status='running' AND owner_id IS ? "
                "AND lease_expires_at IS ?",
                (
                    _now(),
                    "recovered at startup: lease expired",
                    attempt_id,
                    item["owner_id"],
                    item["lease_expires_at"],
                ),
            )
            if cursor.rowcount == 1:
                recovered += 1
                reconciled_candidates.add(item["task_id"])
                # A claimed (orphaned) attempt's stage must be re-executable on
                # resume: clear the whole (task_id, stage_id) event pair in the
                # same transaction as the attempt failover.
                db.execute(
                    "DELETE FROM processed_events WHERE task_id=? AND stage_id=?",
                    (item["task_id"], item["stage_id"]),
                )
                logger.info("Successfully marked attempt %s as failed", attempt_id)
            else:
                logger.info(
                    "Failed to mark attempt %s as failed (already claimed or changed state)",
                    attempt_id,
                )

        tasks_reconciled = 0
        if stale:
            # Parent-task reconciliation (wfaudit007): a claimed task
            # whose attempts are now all terminal moves running -> failed in
            # this same transaction. The status check mirrors a guarded UPDATE
            # (only a still-running task is written); tasks with a live
            # attempt are skipped outright.
            for task_id in reconciled_candidates:
                live = db.fetchall(
                    "SELECT 1 FROM attempts WHERE task_id=? AND status='running' LIMIT 1",
                    (task_id,),
                )
                if live:
                    continue
                current = db.fetchall(
                    "SELECT status FROM tasks WHERE task_id=?", (task_id,)
                )
                if not current or current[0]["status"] != "running":
                    continue
                update_task_status(db, task_id, "failed", commit=False)
                tasks_reconciled += 1
            logger.info(
                "startup recovery: recovered=%s still_live=%s "
                "unparseable=%s tasks_reconciled=%s",
                recovered,
                still_live,
                unparseable,
                tasks_reconciled,
            )
            db.commit()
        self.last_recovery_report = RecoveryReport(
            recovered=recovered,
            still_live=still_live,
            unparseable=unparseable,
            tasks_reconciled=tasks_reconciled,
        )
        return recovered

    def purge_finished_workflow_events(self) -> int:
        """Delete ``processed_events`` rows of terminal tasks past the retention horizon.

        Always operates on the store's own connection; callers pass no arguments.

        Startup-only retention purge: tasks whose status is terminal
        (``_TERMINAL_TASK_STATUSES``) with ``updated_at`` older than
        ``_EVENT_RETENTION_SEC`` lose their event rows; running/pending tasks
        and the ``tasks``/``attempts`` rows themselves are never touched. The
        cutoff is computed in the same UTC ISO Z form the tasks table stores,
        so the ``updated_at <`` comparison is same-format lexicographic.
        Returns the number of deleted rows.
        """
        db = self._db
        cutoff = (datetime.now(UTC) - timedelta(seconds=_EVENT_RETENTION_SEC)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        cursor = db.execute(
            "DELETE FROM processed_events WHERE task_id IN "
            "(SELECT task_id FROM tasks WHERE status IN (?, ?, ?) AND updated_at < ?)",
            (*_TERMINAL_TASK_STATUSES, cutoff),
        )
        db.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info(
                "purge_finished_workflow_events: deleted %s processed_events rows (cutoff=%s)",
                deleted,
                cutoff,
            )
        return deleted


def _classify_running_attempts(db: SQLiteHelper) -> list[dict]:
    """Classify every running attempt row as stale, live, or unparseable.

    Staleness is decided from ``lease_expires_at`` when present (expired =
    stale). Lease-less rows stay live: the lease-less legacy age rule was
    removed (adrrev005) and the sole attempts writer always stamps a
    lease. All comparisons use aware UTC datetimes via ``parse_iso_utc`` — no
    host-local time anywhere (AC-2). Unparseable ``started_at`` or
    ``lease_expires_at`` values are logged with the attempt id and raw value
    and classified ``unparseable`` — the row is neither recovered nor silently
    skipped (AC-3).
    """
    rows = db.fetchall(
        "SELECT attempt_id, task_id, stage_id, started_at, owner_id, lease_expires_at "
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
            "task_id": row["task_id"],
            "stage_id": row["stage_id"],
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
            # adrrev005 no lease means no expiry evidence; the row
            # stays live instead of falling back to a legacy age threshold.
            stale = False
        classified.append({**entry, "classification": "stale" if stale else "live"})
    return classified
