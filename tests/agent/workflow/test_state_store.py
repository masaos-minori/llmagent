#!/usr/bin/env python3
"""tests/agent/workflow/test_state_store.py

Tests for StateStore.recover_stale_attempts() against a real fixture DB.

The mock-based seeds this file used to carry hid the production timestamp
parse defect (wflease001 Background); every scenario now seeds real rows
with production-format timestamps and explicit lease values (REQ-009).
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from agent.workflow.state_store import StateStore
from db.config import DbConfig
from db.create_schema import create_workflow_schema


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


def _iso(seconds_ago: float) -> str:
    """Production-format Z timestamp (REQ-009)."""
    dt = datetime.now(UTC) - timedelta(seconds=seconds_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_ahead(seconds: float) -> str:
    dt = datetime.now(UTC) + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
    from unittest.mock import patch

    db_path = tmp_path / "workflow.sqlite"
    with patch(
        "db.helper.build_db_config",
        return_value=DbConfig(
            rag_db_path=str(tmp_path / "rag.sqlite"),
            session_db_path=str(tmp_path / "session.sqlite"),
            workflow_db_path=str(db_path),
        ),
    ):
        create_workflow_schema()
    return db_path


@pytest.fixture()
def store(workflow_db: Path):
    from unittest.mock import patch

    with patch("db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))):
        s = StateStore()
    yield s
    s.close()


def _seed_attempt(
    db_path: Path,
    attempt_id: str,
    *,
    started_at: str,
    status: str = "running",
    owner_id: str | None = None,
    lease_expires_at: str | None = None,
) -> None:
    """Insert one attempt row via a real task (attempts has a task FK)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO tasks (task_id, session_id, workflow_id, workflow_version, "
            "status, created_at, task_nonce) VALUES (?, 'sess1', 'wf-test', '1.0.0', 'running', ?, ?)",
            (f"task-{attempt_id}", _iso(7200), str(uuid.uuid4())),
        )
        conn.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at, "
            "owner_id, lease_expires_at) VALUES (?, ?, 's1', ?, ?, ?, ?)",
            (
                attempt_id,
                f"task-{attempt_id}",
                status,
                started_at,
                owner_id,
                lease_expires_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _attempt_row(db_path: Path, attempt_id: str) -> dict:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT status, ended_at, error_msg FROM attempts WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
    finally:
        conn.close()
    return {"status": row[0], "ended_at": row[1], "error_msg": row[2]}


class TestRecoverStaleAttemptsOptimisticLocking:
    """Real-DB behavior of the lease-based takeover in recover_stale_attempts()."""

    def test_recover_single_stale_attempt(self, store, workflow_db: Path) -> None:
        _seed_attempt(workflow_db, "att-1", started_at=_iso(7200))
        result = store.recover_stale_attempts()
        assert result == 1
        row = _attempt_row(workflow_db, "att-1")
        assert row["status"] == "failed"
        assert row["ended_at"] is not None
        assert "legacy" in (row["error_msg"] or "")
        report = store.last_recovery_report
        assert (report.recovered, report.legacy_recovered) == (1, 1)
        assert (report.still_live, report.unparseable) == (0, 0)

    def test_recover_non_stale_attempt_not_changed(
        self, store, workflow_db: Path
    ) -> None:
        _seed_attempt(workflow_db, "att-1", started_at=_iso(60))
        result = store.recover_stale_attempts()
        assert result == 0
        assert _attempt_row(workflow_db, "att-1")["status"] == "running"
        assert store.last_recovery_report.still_live == 1

    def test_live_lease_is_never_recovered(self, store, workflow_db: Path) -> None:
        # AC-4 core rule: an unexpired lease is live even when the row is old.
        _seed_attempt(
            workflow_db,
            "att-1",
            started_at=_iso(7200),
            owner_id="host-a",
            lease_expires_at=_iso_ahead(300),
        )
        result = store.recover_stale_attempts()
        assert result == 0
        assert _attempt_row(workflow_db, "att-1")["status"] == "running"
        assert store.last_recovery_report.still_live == 1

    def test_expired_lease_recovered_even_when_row_is_young(
        self, store, workflow_db: Path
    ) -> None:
        # Lease expiry, not age, decides staleness (REQ-006): a young row with
        # an expired lease is stale; legacy age would call it live.
        _seed_attempt(
            workflow_db,
            "att-1",
            started_at=_iso(60),
            owner_id="host-a",
            lease_expires_at=_iso(10),
        )
        result = store.recover_stale_attempts()
        assert result == 1
        row = _attempt_row(workflow_db, "att-1")
        assert row["status"] == "failed"
        assert "lease expired" in (row["error_msg"] or "")
        report = store.last_recovery_report
        assert (report.recovered, report.legacy_recovered) == (1, 0)

    def test_recover_concurrent_calls_only_one_succeeds(
        self, store, workflow_db: Path
    ) -> None:
        # Conditional update: the second pass sees the row already failed and
        # claims nothing (rowcount 0 path).
        _seed_attempt(workflow_db, "att-1", started_at=_iso(7200))
        first = store.recover_stale_attempts()
        second = store.recover_stale_attempts()
        assert first == 1
        assert second == 0
        assert store.last_recovery_report.recovered == 0

    def test_recover_multiple_stale_attempts_all_claimed(
        self, store, workflow_db: Path
    ) -> None:
        _seed_attempt(workflow_db, "att-1", started_at=_iso(7200))
        _seed_attempt(workflow_db, "att-2", started_at=_iso(7300))
        result = store.recover_stale_attempts()
        assert result == 2
        assert _attempt_row(workflow_db, "att-1")["status"] == "failed"
        assert _attempt_row(workflow_db, "att-2")["status"] == "failed"
        assert store.last_recovery_report.recovered == 2

    def test_recover_mixed_stale_and_non_stale(self, store, workflow_db: Path) -> None:
        _seed_attempt(workflow_db, "att-1", started_at=_iso(7200))
        _seed_attempt(workflow_db, "att-2", started_at=_iso(30))
        result = store.recover_stale_attempts()
        assert result == 1
        assert _attempt_row(workflow_db, "att-2")["status"] == "running"
        report = store.last_recovery_report
        assert (report.recovered, report.still_live) == (1, 1)

    def test_recover_no_running_attempts(self, store, workflow_db: Path) -> None:
        result = store.recover_stale_attempts()
        assert result == 0
        report = store.last_recovery_report
        assert (report.recovered, report.still_live) == (0, 0)

    def test_recover_already_failed_attempt_not_double_recovered(
        self, store, workflow_db: Path
    ) -> None:
        _seed_attempt(workflow_db, "att-1", started_at=_iso(7200), status="failed")
        result = store.recover_stale_attempts()
        assert result == 0

    def test_recover_unparseable_started_at_is_reported_not_skipped(
        self, store, workflow_db: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # AC-3: the row is neither recovered nor silently skipped — it is
        # logged with the raw value and counted in the report.
        _seed_attempt(workflow_db, "att-1", started_at="not-a-date")
        with caplog.at_level(logging.WARNING, logger="agent.workflow.state_store"):
            result = store.recover_stale_attempts()
        assert result == 0
        assert _attempt_row(workflow_db, "att-1")["status"] == "running"
        assert store.last_recovery_report.unparseable == 1
        messages = [rec.getMessage() for rec in caplog.records]
        assert any(
            "unparseable workflow attempt timestamp" in m
            and "att-1" in m
            and "not-a-date" in m
            for m in messages
        )

    def test_recover_unparseable_lease_is_reported_not_skipped(
        self, store, workflow_db: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _seed_attempt(
            workflow_db,
            "att-1",
            started_at=_iso(7200),
            owner_id="host-a",
            lease_expires_at="garbage",
        )
        with caplog.at_level(logging.WARNING, logger="agent.workflow.state_store"):
            result = store.recover_stale_attempts()
        assert result == 0
        assert _attempt_row(workflow_db, "att-1")["status"] == "running"
        assert store.last_recovery_report.unparseable == 1
        assert any("garbage" in rec.getMessage() for rec in caplog.records)

    def test_recover_stale_lease_expired_row(self, store, workflow_db: Path) -> None:
        lease = _iso(10)
        _seed_attempt(
            workflow_db,
            "att-1",
            started_at=_iso(7200),
            owner_id="host-a",
            lease_expires_at=lease,
        )
        result = store.recover_stale_attempts()
        assert result == 1
        row = _attempt_row(workflow_db, "att-1")
        assert row["status"] == "failed"
        assert "lease expired" in row["error_msg"]
        assert store.last_recovery_report.recovered == 1


class TestDoubleClose:
    """REQ-005: StateStore.close() is idempotent-safe through SQLiteHelper.close (early
    return when conn is None); a second close neither raises nor re-opens the connection.
    """

    def test_double_close_is_noop(self, store) -> None:
        conn = store.get_connection()
        assert conn.conn is not None
        store.close()
        assert conn.conn is None
        # Second close is a no-op: no raise, conn stays None.
        store.close()
        assert conn.conn is None
