#!/usr/bin/env python3
"""tests/agent/workflow/test_stale_recovery_lease.py

Lease-based stale-attempt recovery scenario matrix (wflease001, AC-2/AC-4/AC-5/AC-7).

Companion to test_state_store.py (single-attempt unit coverage). This file covers
the multi-attempt and multi-worker scenarios the plan's acceptance criteria name
directly: live leases protected under wall-clock staleness, expired leases won by
exactly one worker, the legacy no-lease fallback boundary, and the AC-7 fencing
gate deferred to the wfrecovery001 plan.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from agent.workflow.state_store import StateStore
from db.config import DbConfig
from db.create_schema import create_workflow_schema

# Mirrors the private constants in scripts/agent/workflow/state_store.py and
# scripts/agent/workflow/workflow_engine.py. Tests assert the documented
# behavior (live/expired/legacy thresholds, lease margin), so silently changing
# a constant must fail here rather than pass vacuously.
_LEGACY_STALE_AGE_SEC = 3600  # state_store._LEGACY_STALE_AGE_SEC
_LEASE_MARGIN_SEC = 30  # workflow_engine._LEASE_MARGIN_SEC


def _iso(seconds_ago: float) -> str:
    """Production-format Z timestamp (REQ-009)."""
    dt = datetime.now(UTC) - timedelta(seconds=seconds_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_ahead(seconds: float) -> str:
    dt = datetime.now(UTC) + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


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
            "SELECT status, error_msg FROM attempts WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
    finally:
        conn.close()
    return {"status": row[0], "error_msg": row[1]}


class TestLiveLeaseIsProtected:
    """AC-2/AC-4: wall-clock staleness must not recover an attempt with a live lease."""

    def test_stale_by_age_but_lease_live_is_not_recovered(
        self, store, workflow_db: Path
    ) -> None:
        """started_at is far past the legacy threshold, but the lease is in the
        future: a legitimately long-running attempt must keep status='running'.
        The old 3600s wall-clock rule always made such attempts recoverable."""
        _seed_attempt(
            workflow_db,
            "att-live",
            started_at=_iso(7200),
            owner_id="owner-a",
            lease_expires_at=_iso_ahead(600),
        )

        result = store.recover_stale_attempts(store.get_connection())

        assert result == 0
        report = store.last_recovery_report
        assert (report.recovered, report.legacy_recovered) == (0, 0)
        assert report.still_live == 1
        assert _attempt_row(workflow_db, "att-live")["status"] == "running"


class TestExpiredLeaseIsRecovered:
    """AC-2: an expired lease is recovered regardless of how recent started_at looks."""

    def test_expired_lease_recovered_once_and_idempotent(
        self, store, workflow_db: Path
    ) -> None:
        """The compare-and-swap UPDATE fires on the first pass; the second pass sees
        no running row and must report zero recoveries (not repeated per poll)."""
        _seed_attempt(
            workflow_db,
            "att-exp",
            started_at=_iso(10),
            owner_id="owner-a",
            lease_expires_at=_iso(1),
        )

        first = store.recover_stale_attempts(store.get_connection())
        second = store.recover_stale_attempts(store.get_connection())

        assert first == 1
        assert second == 0
        row = _attempt_row(workflow_db, "att-exp")
        assert row["status"] == "failed"
        assert "lease expired" in (row["error_msg"] or "")

    def test_mixed_leases_only_expired_recovered(
        self, store, workflow_db: Path
    ) -> None:
        """Two running attempts: only the expired-lease row is recovered."""
        _seed_attempt(
            workflow_db,
            "att-exp",
            started_at=_iso(10),
            owner_id="owner-a",
            lease_expires_at=_iso(1),
        )
        _seed_attempt(
            workflow_db,
            "att-live",
            started_at=_iso(10),
            owner_id="owner-b",
            lease_expires_at=_iso_ahead(300),
        )

        result = store.recover_stale_attempts(store.get_connection())

        assert result == 1
        assert store.last_recovery_report.still_live == 1
        assert _attempt_row(workflow_db, "att-exp")["status"] == "failed"
        assert _attempt_row(workflow_db, "att-live")["status"] == "running"


class TestConcurrentRecoverSingleWinner:
    """AC-5: concurrent recoverers race the same expired lease; exactly one wins."""

    def test_concurrent_recover_single_winner(self, workflow_db: Path) -> None:
        """N workers each build their own StateStore/connection and call
        recover_stale_attempts at the same time. The takeover UPDATE pins
        owner_id/lease_expires_at AND status='running', so only one worker's
        UPDATE matches; every other worker must see rowcount==0 and report 0.
        SQLite connections are thread-bound, so each StateStore is created
        inside its worker thread."""
        from unittest.mock import patch

        _seed_attempt(
            workflow_db,
            "att-race",
            started_at=_iso(10),
            owner_id="dead-owner",
            lease_expires_at=_iso(1),
        )

        results: list[int] = []
        lock = threading.Lock()

        def worker() -> None:
            with patch(
                "db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))
            ):
                s = StateStore()
            try:
                count = s.recover_stale_attempts(s.get_connection())
            finally:
                s.close()
            with lock:
                results.append(count)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sorted(results) == [0, 0, 0, 1]
        assert _attempt_row(workflow_db, "att-race")["status"] == "failed"


class TestLegacyFallback:
    """AC-3: lease-less attempts (pre-migration rows) fall back to the age rule."""

    def test_legacy_attempt_past_threshold_is_recovered(
        self, store, workflow_db: Path
    ) -> None:
        """started_at older than _LEGACY_STALE_AGE_SEC, owner_id/lease_expires_at NULL."""
        _seed_attempt(
            workflow_db, "att-old", started_at=_iso(_LEGACY_STALE_AGE_SEC + 60)
        )

        result = store.recover_stale_attempts(store.get_connection())

        assert result == 1
        report = store.last_recovery_report
        assert (report.recovered, report.legacy_recovered) == (1, 1)
        row = _attempt_row(workflow_db, "att-old")
        assert row["status"] == "failed"
        assert f"legacy attempt older than {_LEGACY_STALE_AGE_SEC}s" in (
            row["error_msg"] or ""
        )

    def test_legacy_attempt_within_threshold_is_not_recovered(
        self, store, workflow_db: Path
    ) -> None:
        """A recent lease-less attempt stays running: the fallback must not widen."""
        _seed_attempt(
            workflow_db, "att-young", started_at=_iso(_LEGACY_STALE_AGE_SEC - 600)
        )

        result = store.recover_stale_attempts(store.get_connection())

        assert result == 0
        assert store.last_recovery_report.legacy_recovered == 0
        assert _attempt_row(workflow_db, "att-young")["status"] == "running"

    def test_unparseable_timestamp_is_reported_not_recovered(
        self, store, workflow_db: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """REQ-003/AC-3: a malformed lease timestamp is neither recovered nor
        silently skipped — it is counted and logged with the attempt id."""
        _seed_attempt(
            workflow_db,
            "att-bad",
            started_at=_iso(10),
            owner_id="owner-a",
            lease_expires_at="not-a-timestamp",
        )

        with caplog.at_level("WARNING"):
            result = store.recover_stale_attempts(store.get_connection())

        assert result == 0
        report = store.last_recovery_report
        assert (report.recovered, report.legacy_recovered) == (0, 0)
        assert report.unparseable == 1
        assert _attempt_row(workflow_db, "att-bad")["status"] == "running"
        messages = [str(r.message) for r in caplog.records]
        assert any("att-bad" in msg for msg in messages)


class TestFencingGateAC7:
    """AC-7 fencing tokens: the fence is not yet implemented and is specified by
    the wfrecovery001 Plan.

    `AttemptFencedError` and the finish_attempt fence do not exist until that plan
    lands, so this gate asserts their current absence. The moment the fence appears
    this test fails and forces this file to be flipped into a passing enforcement
    gate. See:
    - issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
    - plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
    - implementations/done/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md
    - implementations/done/20261101-163219_12_tests_agent_workflow_test_stale_recovery_lease.py.md
    """

    def test_finish_attempt_fence_not_yet_implemented(self) -> None:
        with pytest.raises(ImportError):
            from agent.workflow.attempt_ops import (
                AttemptFencedError,  # noqa: F401 — the import itself is the assertion
            )

    def test_engine_lease_margin_constant(self) -> None:
        """AC-7 lease-margin invariant: a lease outlives its own stage timeout,
        so a running attempt is never recoverable while its stage is executing.
        Mirrors workflow_engine._run_stage: lease_duration_sec = timeout + margin."""
        from agent.workflow.workflow_engine import _LEASE_MARGIN_SEC

        assert _LEASE_MARGIN_SEC == 30
        assert _LEASE_MARGIN_SEC > 0
