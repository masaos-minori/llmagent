"""Tests for shared.mcp_dedup: lease/identity store contract (mcpdl002).

Single-process state machine and config coverage for the rewritten store:
acquisition vocabulary, owner-conditional finalization, attempt history,
stamped identity (`_USER_VERSION` + store_meta + installation marker),
retention-scoped purge, and lease-expiry reconciliation.
Result metadata and result-class classification (mcpdl004 REQ-003) is covered
in TestResultMetadata and TestCallStateView.
Multi-caller concurrency lives in test_mcp_dedup_concurrency.py; the
identity/loss matrix lives in test_mcp_dedup_identity.py.

All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
from shared.config_errors import ConfigMissingError, ConfigParseError
from shared.mcp_dedup import (
    _USER_VERSION,
    DEFAULT_DB_PATH,
    DedupLeaseConflict,
    DedupStore,
    DedupStoreConfig,
    DedupStoreError,
    classify_interrupted,
    load_dedup_section,
    open_dedup_store,
    read_store_identity,
)
from shared.mcp_dedup_config import dedup_db_dir

# Component-keyed snapshot (execution_snapshot.COMPONENT_KEYS shape).
_SNAP = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "dedup": "gen=1;schema=deadbeef",
}


@pytest.fixture()
def store(tmp_path):
    s = DedupStore(str(tmp_path / "mcp_dedup.sqlite"), lease_seconds=30)
    yield s
    s.close()


def _history(store: DedupStore) -> list[tuple[int, str, str | None]]:
    """(attempt_number, outcome, detail) rows from call_attempt_history."""
    conn = sqlite3.connect(store.db_path)
    try:
        return [
            (int(r[0]), str(r[1]), None if r[2] is None else str(r[2]))
            for r in conn.execute(
                "SELECT attempt_number, outcome, detail FROM call_attempt_history"
                " ORDER BY recorded_epoch, rowid"
            )
        ]
    finally:
        conn.close()


def _raw_connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


class TestAcquisitionStateMachine:
    def test_acquire_creates_owned_pending_row(self, store):
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        assert res.status == "acquired"
        assert res.attempt_number == 1
        assert res.owner_id == "owner-a"
        assert res.lease_expires_epoch is not None
        row = store.get_execution("k1")
        assert row is not None
        assert row.status == "pending"
        assert row.owner_id == "owner-a"

    def test_owner_finalizes_completed_and_replay(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, {"ok": True}, "owner-a")
        row = store.get_execution("k1")
        assert row is not None and row.status == "completed"
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        assert res.status == "replay_completed"
        assert res.result == {"ok": True}
        assert res.owner_id is None
        assert res.lease_expires_epoch is None

    def test_second_caller_gets_in_progress(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        assert res.status == "in_progress"
        assert res.owner_id == "owner-a"
        row = store.get_execution("k1")
        assert row is not None and row.status == "pending" and row.attempt_number == 1

    def test_contract_mismatch_on_args_hash_or_tool(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        res = store.try_acquire_execution("k1", "web_search", "h2", _SNAP, "owner-a")
        assert res.status == "contract_mismatch"
        res2 = store.try_acquire_execution("k1", "write_file", "h1", _SNAP, "owner-a")
        assert res2.status == "contract_mismatch"

    def test_completed_snapshot_mismatch_is_replay_unavailable(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "done", "owner-a")
        moved = dict(_SNAP, git_sha="other1")
        res = store.try_acquire_execution("k1", "web_search", "h1", moved, "owner-b")
        assert res.status == "replay_unavailable"

    def test_truncated_completed_is_replay_unavailable(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "x" * 9000, "owner-a")
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        assert res.status == "replay_unavailable"

    def test_failed_terminal_is_replay_unavailable(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_failed("k1", "timeout", "owner-a")
        row = store.get_execution("k1")
        assert row is not None and row.status == "failed"
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        assert res.status == "replay_unavailable"
        assert res.attempt_number == 1

    def test_terminal_rows_are_immutable(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "done", "owner-a")
        # The same owner cannot re-finalize or heartbeat a terminal row.
        with pytest.raises(DedupLeaseConflict):
            store.record_failed("k1", "timeout", "owner-a")
        with pytest.raises(DedupLeaseConflict):
            store.record_completed("k1", _SNAP, "late", "owner-a")
        with pytest.raises(DedupLeaseConflict):
            store.renew_lease("k1", "owner-a")
        row = store.get_execution("k1")
        assert row is not None and row.status == "completed"
        assert row.result == "done"
        # A terminal row never re-opens through acquisition either.
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-c")
        assert res.status == "replay_completed"

    def test_non_owner_finalization_raises(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        with pytest.raises(DedupLeaseConflict):
            store.record_completed("k1", _SNAP, "done", "owner-b")
        row = store.get_execution("k1")
        assert row is not None and row.status == "pending"

    def test_expired_pending_yields_reconciliation_required(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        res = store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-b", now_epoch=now + 3600
        )
        assert res.status == "reconciliation_required"
        assert res.attempt_number == 1
        # Classification only: no new owner, no attempt advance (AC-3).
        row = store.get_execution("k1")
        assert row is not None
        assert row.status == "pending"
        assert row.attempt_number == 1
        assert row.owner_id == "owner-a"

    def test_reconcile_then_reacquire_advances_attempt(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        reconciled = store.reconcile_execution("k1", now_epoch=now + 3600)
        assert reconciled.status == "interrupted"
        res = store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-b", now_epoch=now + 3601
        )
        assert res.status == "acquired"
        assert res.attempt_number == 2
        assert res.owner_id == "owner-b"
        row = store.get_execution("k1")
        # REQ-004: the stored snapshot is not rewritten by the recovery.
        assert row is not None and dict(row.snapshot) == _SNAP

    def test_reconcile_refuses_live_lease(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        with pytest.raises(DedupLeaseConflict, match="live lease"):
            store.reconcile_execution("k1")
        with pytest.raises(DedupLeaseConflict):
            store.reconcile_execution("absent")

    def test_max_attempts_gate_reaches_outcome_unknown(self, store):
        now = time.time()
        attempts = store._max_attempts
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        t = now
        for attempt in range(2, attempts + 1):
            t += 3600
            res = store.try_acquire_execution(
                "k1", "web_search", "h1", _SNAP, "owner-x", now_epoch=t
            )
            assert res.status == "reconciliation_required"
            store.reconcile_execution("k1", now_epoch=t)
            res = store.try_acquire_execution(
                "k1", "web_search", "h1", _SNAP, f"owner-{attempt}", now_epoch=t + 1
            )
            assert res.status == "acquired"
            assert res.attempt_number == attempt
        t += 3600
        res = store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-z", now_epoch=t
        )
        assert res.status == "outcome_unknown"
        assert res.attempt_number == attempts
        with pytest.raises(DedupLeaseConflict, match="exhausted attempts"):
            store.reconcile_execution("k1", now_epoch=t)

    def test_attempt_history_records_each_decision(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "done", "owner-a")
        store.try_acquire_execution("k2", "web_search", "h2", _SNAP, "owner-a")
        store.reconcile_execution("k2", now_epoch=now + 3600)
        store.try_acquire_execution(
            "k2", "web_search", "h2", _SNAP, "owner-b", now_epoch=now + 3601
        )
        store.record_failed("k2", "timeout", "owner-b", now_epoch=now + 3601)
        assert _history(store) == [
            (1, "attempt", None),
            (1, "completed", None),
            (1, "attempt", None),
            (1, "reconciled", "lease_expired"),
            (2, "attempt", "post-recovery"),
            (2, "failed", "timeout"),
        ]

    def test_result_truncation(self, store):
        big = "x" * 9000
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, big, "owner-a")
        result = store.get_execution("k1").result
        assert result["truncated"] is True
        assert len(result["preview"]) < len(big)
        assert result["sha256"]

    def test_unknown_key_lookup_returns_none(self, store):
        assert store.get_execution("absent") is None

    def test_clear_removes_row(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.clear("k1")
        assert store.get_execution("k1") is None
        # A cleared key acquires again as a fresh first attempt.
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        assert res.status == "acquired" and res.attempt_number == 1


class TestLeaseOwnership:
    def test_owner_heartbeat_extends_lease(self, store):
        now = time.time()
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        expiry = store.renew_lease("k1", "owner-a", now_epoch=now + 10)
        assert expiry == pytest.approx(now + 10 + 30)
        assert res.lease_expires_epoch is not None
        assert res.lease_expires_epoch < expiry
        row = store.get_execution("k1")
        assert row is not None and row.lease_expires_epoch == pytest.approx(expiry)
        # The live lease now blocks reconcile.
        with pytest.raises(DedupLeaseConflict, match="live lease"):
            store.reconcile_execution("k1", now_epoch=now + 10)

    def test_non_owner_renew_raises(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        with pytest.raises(DedupLeaseConflict):
            store.renew_lease("k1", "owner-b")

    def test_expired_owner_renew_raises(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        with pytest.raises(DedupLeaseConflict, match="live lease"):
            store.renew_lease("k1", "owner-a", now_epoch=now + 3600)


class TestFingerprintGate:
    """Stamped identity: first open writes user_version=1 + store_meta + marker."""

    def test_first_initialization_stamps_identity(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        s = DedupStore(str(path))
        assert s.start_state == "first_initialization"
        s.close()
        conn = _raw_connect(path)
        try:
            assert (
                int(conn.execute("PRAGMA user_version").fetchone()[0]) == _USER_VERSION
            )
            tables = {
                str(r[0])
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert tables == {"dedup_call_state", "store_meta", "call_attempt_history"}
            assert (
                conn.execute("SELECT store_uuid FROM store_meta").fetchone() is not None
            )
        finally:
            conn.close()
        assert (path.parent / ".mcp_dedup_installed").is_file()

    def test_reopen_of_stamped_store_is_healthy(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        DedupStore(path).close()
        s = DedupStore(path)
        assert s.start_state == "healthy"
        s.close()

    def test_old_shape_refused(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        conn = _raw_connect(path)
        conn.execute(
            "CREATE TABLE tool_call_state ("
            "key TEXT PRIMARY KEY, tool_name TEXT NOT NULL, args_hash TEXT NOT NULL,"
            " status TEXT NOT NULL, snapshot_json TEXT NOT NULL,"
            " created_epoch REAL NOT NULL, updated_epoch REAL NOT NULL)"
        )
        conn.commit()
        conn.close()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(path)
        assert excinfo.value.state == "legacy_or_unverified"

    def test_extra_table_refused(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        DedupStore(str(path)).close()
        conn = _raw_connect(path)
        conn.execute("CREATE TABLE legacy_dedup_cache (k TEXT)")
        conn.commit()
        conn.close()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(str(path))
        assert excinfo.value.state == "schema_mismatch"
        assert "unexpected table 'legacy_dedup_cache'" in str(excinfo.value)

    def test_missing_index_refused(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        DedupStore(str(path)).close()
        conn = _raw_connect(path)
        conn.execute("DROP INDEX idx_dcs_updated")
        conn.commit()
        conn.close()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(str(path))
        assert excinfo.value.state == "schema_mismatch"
        assert "mcp_dedup.sqlite" in str(excinfo.value)

    def test_version_stamp_drift_refused(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        DedupStore(str(path)).close()
        conn = _raw_connect(path)
        conn.execute(f"PRAGMA user_version = {_USER_VERSION + 1}")
        conn.commit()
        conn.close()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(str(path))
        assert excinfo.value.state == "schema_mismatch"
        assert "identity stamp" in str(excinfo.value)

    def test_missing_identity_row_refused(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        DedupStore(str(path)).close()
        conn = _raw_connect(path)
        conn.execute("DELETE FROM store_meta")
        conn.commit()
        conn.close()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(str(path))
        assert excinfo.value.state == "legacy_or_unverified"
        assert "no identity row" in str(excinfo.value)


class TestReopenDurability:
    def test_completed_row_survives_reopen(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        s = DedupStore(path)
        s.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        s.record_completed("k1", _SNAP, "done", "owner-a")
        s.close()

        s2 = DedupStore(path)
        assert s2.start_state == "healthy"
        row = s2.get_execution("k1")
        s2.close()
        assert row is not None and row.status == "completed"
        assert row.result == "done"
        assert dict(row.snapshot)["deployed_rev"] == "deadbeef"

    def test_interrupted_row_survives_reopen(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        s = DedupStore(path)
        s.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        s.mark_interrupted("k1", "owner-a")
        s.close()

        s2 = DedupStore(path)
        row = s2.get_execution("k1")
        assert row is not None and row.status == "interrupted"
        res = s2.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-b")
        s2.close()
        assert res.status == "acquired" and res.attempt_number == 2

    def test_identity_stable_across_reopen(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        s = DedupStore(str(path))
        identity_before = read_store_identity(path)
        s.close()
        s2 = DedupStore(str(path))
        identity_after = read_store_identity(path)
        s2.close()
        assert identity_before is not None
        assert identity_before == identity_after
        assert identity_before[0] == 1


class TestCrossProcessSharing:
    def _child(self, path: str, code: str) -> None:
        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; sys.path.insert(0, " + repr(scripts_dir) + ");" + code,
            ],
            check=True,
            timeout=30,
        )

    def test_second_process_replays_first_completed(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        s = DedupStore(path)
        s.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        s.record_completed("k1", _SNAP, "done", "owner-a")
        s.close()
        code = (
            "from shared.mcp_dedup import DedupStore;"
            "s = DedupStore(" + repr(path) + ");"
            "res = s.try_acquire_execution('k1', 'web_search', 'h1', "
            + repr(_SNAP)
            + ", 'child');"
            "assert res.status == 'replay_completed' and res.result == 'done';"
            "s.close()"
        )
        self._child(path, code)

    def test_child_terminal_write_visible_to_parent(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        s = DedupStore(path)
        s.try_acquire_execution("k2", "web_search", "h2", _SNAP, "owner-a")
        code = (
            "from shared.mcp_dedup import DedupStore;"
            "s = DedupStore(" + repr(path) + ");"
            "s.renew_lease('k2', 'owner-a');"
            "s.record_completed('k2', " + repr(_SNAP) + ", 'done', 'owner-a');"
            "s.close()"
        )
        self._child(path, code)
        row = s.get_execution("k2")
        s.close()
        assert row is not None and row.status == "completed"
        assert row.result == "done"


class TestTtlPurge:
    def test_expired_terminal_rows_and_history_purged(self, store):
        now = time.time()
        old = now - 15 * 86400
        store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-a", now_epoch=old
        )
        store.record_completed("k1", _SNAP, "done", "owner-a", now_epoch=old)
        store.try_acquire_execution(
            "k2", "web_search", "h2", _SNAP, "owner-a", now_epoch=now
        )
        store.record_completed("k2", _SNAP, "fresh", "owner-a", now_epoch=now)
        assert store.purge_expired(retention_days=14, now_epoch=now) == 1
        assert store.get_execution("k1") is None
        assert store.get_execution("k2") is not None
        # Only k2's history survives the cutoff.
        assert _history(store) == [(1, "attempt", None), (1, "completed", None)]

    def test_expired_terminal_states_all_purged(self, store):
        now = time.time()
        old = now - 15 * 86400
        store.try_acquire_execution("kc", "web_search", "h1", _SNAP, "o", now_epoch=old)
        store.record_completed("kc", _SNAP, "done", "o", now_epoch=old)
        store.try_acquire_execution("kf", "web_search", "h2", _SNAP, "o", now_epoch=old)
        store.record_failed("kf", "timeout", "o", now_epoch=old)
        store.try_acquire_execution("ki", "web_search", "h3", _SNAP, "o", now_epoch=old)
        store.mark_interrupted("ki", "o", now_epoch=old)
        assert store.purge_expired(retention_days=14, now_epoch=now) == 3
        for key in ("kc", "kf", "ki"):
            assert store.get_execution(key) is None

    def test_pending_rows_never_purged(self, store):
        now = time.time()
        old = now - 30 * 86400
        store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-a", now_epoch=old
        )
        assert store.purge_expired(retention_days=14, now_epoch=now) == 0
        row = store.get_execution("k1")
        assert row is not None and row.status == "pending"

    def test_overdue_pending_never_purged(self, store):
        # REQ-002: an expired lease is reported as overdue by the read path, but the
        # sweep still leaves the pending row outside its scope.
        now = time.time()
        old = now - 30 * 86400
        store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-a", now_epoch=old
        )
        row = store.get_execution("k1")
        assert row is not None and row.lease_expires_epoch < now
        assert store.get_dedup_metrics_view().pending_overdue(now) == 1
        assert store.purge_expired(retention_days=14, now_epoch=now) == 0
        assert store.get_execution("k1") is not None

    def test_reconciled_row_becomes_sweepable(self, store):
        # A stale pending row is outside the sweep until reconciliation moves it to a
        # terminal state; the row's own updated_epoch then decides the cutoff.
        now = time.time()
        old = now - 30 * 86400
        store.try_acquire_execution(
            "k1", "web_search", "h1", _SNAP, "owner-a", now_epoch=old
        )
        assert store.purge_expired(retention_days=14, now_epoch=now) == 0
        store.reconcile_execution("k1", now_epoch=now)
        assert store.get_execution("k1").status == "interrupted"
        later = now + 15 * 86400
        assert store.purge_expired(retention_days=14, now_epoch=later) == 1
        assert store.get_execution("k1") is None

    def test_held_terminal_row_not_purged(self, tmp_path):
        # REQ-003: the same age means different actions per state. The held state is
        # skipped by the sweep and stays visible as held rather than as retained at large.
        now = time.time()
        old = now - 15 * 86400
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "held.sqlite"), legal_hold_states=("completed",)
        )
        store = DedupStore(str(cfg.db_path), lease_seconds=30, config=cfg)
        try:
            store.try_acquire_execution(
                "kc", "web_search", "h1", _SNAP, "o", now_epoch=old
            )
            store.record_completed("kc", _SNAP, "done", "o", now_epoch=old)
            store.try_acquire_execution(
                "kf", "web_search", "h2", _SNAP, "o", now_epoch=old
            )
            store.record_failed("kf", "timeout", "o", now_epoch=old)
            assert store.purge_expired(retention_days=14, now_epoch=now) == 1
            assert store.get_execution("kc") is not None
            assert store.get_execution("kf") is None
            view = store.get_dedup_metrics_view()
            assert view.row_states() == {"completed": 1}
            assert view.held_past_retention(now, retention_days=14) == 1
        finally:
            store.close()

    def test_no_hold_purge_behaviour_unchanged(self, store):
        # Without a configured hold the sweep is what it was before this row: every
        # terminal state past the cutoff is deleted, and nothing is reported as held.
        now = time.time()
        old = now - 15 * 86400
        assert store._legal_hold_states() == ()
        store.try_acquire_execution("kc", "web_search", "h1", _SNAP, "o", now_epoch=old)
        store.record_completed("kc", _SNAP, "done", "o", now_epoch=old)
        store.try_acquire_execution("kf", "web_search", "h2", _SNAP, "o", now_epoch=old)
        store.record_failed("kf", "timeout", "o", now_epoch=old)
        store.try_acquire_execution("ki", "web_search", "h3", _SNAP, "o", now_epoch=old)
        store.mark_interrupted("ki", "o", now_epoch=old)
        assert store.purge_expired(retention_days=14, now_epoch=now) == 3
        for key in ("kc", "kf", "ki"):
            assert store.get_execution(key) is None
        assert store.get_dedup_metrics_view().held_past_retention(now, 14) == 0


class TestDedupMetricsView:
    def test_view_reports_counts_and_boundaries(self, tmp_path):
        now = time.time()
        old = now - 30 * 86400
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "view.sqlite"),
            retention_days=14,
            max_dedup_rows=3000,
            max_dedup_growth_per_hour=500,
            max_dedup_wal_mb=64,
            legal_hold_states=("completed",),
        )
        store = DedupStore(str(cfg.db_path), lease_seconds=30, config=cfg)
        try:
            store.try_acquire_execution(
                "kc", "web_search", "h1", _SNAP, "o", now_epoch=old
            )
            store.record_completed("kc", _SNAP, "done", "o", now_epoch=old)
            store.try_acquire_execution(
                "kp", "web_search", "h2", _SNAP, "o", now_epoch=old
            )
            view = store.get_dedup_metrics_view()
            assert view.db_path == str(cfg.db_path)
            assert view.row_states() == {"completed": 1, "pending": 1}
            # `pending_overdue` counts only rows whose lease is past the clock it is given.
            assert view.pending_overdue(now) == 1
            assert view.pending_overdue(old) == 0
            assert view.created_since(now - 3600) == 0
            assert view.created_since(old) == 2
            # REQ-003: the held row is counted as held, not as retained at large (AC-3).
            assert view.held_past_retention(now, cfg.retention_days) == 1
            assert view.wal_size_bytes() >= 0
            assert view.lock_wait_ms() >= 0
        finally:
            store.close()

    def test_read_pass_leaves_the_ledger_unchanged(self, tmp_path):
        # AC-8: the view issues reads only, so a metrics pass cannot mutate the ledger.
        now = time.time()
        old = now - 30 * 86400
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "readonly.sqlite"), legal_hold_states=("completed",)
        )
        store = DedupStore(str(cfg.db_path), lease_seconds=30, config=cfg)
        try:
            store.try_acquire_execution(
                "kc", "web_search", "h1", _SNAP, "o", now_epoch=old
            )
            store.record_completed("kc", _SNAP, "done", "o", now_epoch=old)
            view = store.get_dedup_metrics_view()
            before_count = store._conn.execute(
                "SELECT COUNT(*) FROM dedup_call_state"
            ).fetchone()[0]
            before_row = store.get_execution("kc")
            before_history = _history(store)
            before_changes = store._conn.total_changes

            for value in (
                view.row_states(),
                view.pending_overdue(now),
                view.created_since(now - 3600),
                view.held_past_retention(now, cfg.retention_days),
                view.wal_size_bytes(),
            ):
                assert value is not None

            after_count = store._conn.execute(
                "SELECT COUNT(*) FROM dedup_call_state"
            ).fetchone()[0]
            assert after_count == before_count
            assert store.get_execution("kc") == before_row
            assert _history(store) == before_history
            # No write happened on the connection during the pass.
            assert store._conn.total_changes == before_changes
            assert view.lock_wait_ms() >= 0
        finally:
            store.close()


class TestLeaseClassification:
    def test_expired_lease_classifies_interrupted_without_mutation(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        row = store.get_execution("k1")
        assert classify_interrupted(row, 30, now_epoch=now + 3600) == "interrupted"
        # Classification must not write: the stored row is still 'pending'.
        assert store.get_execution("k1").status == "pending"

    def test_live_lease_stays_pending(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        row = store.get_execution("k1")
        assert classify_interrupted(row, 30, now_epoch=now + 10) == "pending"

    def test_terminal_rows_are_not_reclassified(self, store):
        now = time.time()
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "done", "owner-a")
        row = store.get_execution("k1")
        assert classify_interrupted(row, 30, now_epoch=now + 3600) == "completed"

    def test_explicit_mark_interrupted(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.mark_interrupted("k1", "owner-a")
        assert store.get_execution("k1").status == "interrupted"


class TestStartStateClassification:
    """Start-state gate replacing the removed lost_or_recreated sentinel path."""

    def test_genuine_first_run_is_first_initialization(self, tmp_path):
        store = DedupStore(str(tmp_path / "mcp_dedup.sqlite"))
        assert store.start_state == "first_initialization"
        store.close()

    def test_healthy_store_reopens_healthy(self, tmp_path):
        path = str(tmp_path / "mcp_dedup.sqlite")
        store = DedupStore(path)
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.close()
        reopened = DedupStore(path)
        assert reopened.start_state == "healthy"
        reopened.close()

    def test_deleted_db_with_marker_is_lost(self, tmp_path):
        path = tmp_path / "mcp_dedup.sqlite"
        store = DedupStore(str(path))
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, "done", "owner-a")
        store.close()
        path.unlink()
        with pytest.raises(DedupStoreError) as excinfo:
            DedupStore(str(path))
        assert excinfo.value.state == "lost"


class TestDedupSectionValidation:
    def test_missing_table_raises_typed_error(self):
        with pytest.raises(ConfigMissingError):
            load_dedup_section(None, "cicd_mcp_server.toml")

    def test_non_table_section_raises_parse_error(self):
        with pytest.raises(ConfigParseError):
            load_dedup_section("not a table", "cicd_mcp_server.toml")

    def test_wrong_value_type_raises_parse_error(self):
        with pytest.raises(ConfigParseError):
            load_dedup_section({"retention_days": "fourteen"}, "x_mcp_server.toml")

    def test_empty_db_path_rejected(self):
        with pytest.raises(ConfigParseError, match="db_path"):
            load_dedup_section({"db_path": ""}, "x_mcp_server.toml")

    def test_lease_seconds_out_of_range_rejected(self):
        with pytest.raises(ConfigParseError, match="lease_seconds"):
            load_dedup_section({"lease_seconds": 0}, "x_mcp_server.toml")

    def test_max_attempts_out_of_range_rejected(self):
        with pytest.raises(ConfigParseError, match="max_attempts"):
            load_dedup_section({"max_attempts": 11}, "x_mcp_server.toml")

    def test_retention_days_out_of_range_rejected(self):
        with pytest.raises(ConfigParseError, match="retention_days"):
            load_dedup_section({"retention_days": 0}, "x_mcp_server.toml")

    def test_unknown_dedup_key_rejected(self):
        with pytest.raises(ConfigParseError, match="unknown dedup keys"):
            load_dedup_section({"sentinel_mode": 1}, "x_mcp_server.toml")

    def test_partial_section_gets_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LLMAGENT_DB_DIR", str(tmp_path))
        cfg = load_dedup_section(
            {"db_path": str(tmp_path / "mcp_dedup.sqlite")}, "x_mcp_server.toml"
        )
        assert cfg.retention_days == 14
        assert cfg.pending_timeout_minutes == 10
        assert cfg.lease_seconds == 30
        assert cfg.max_attempts == 3

    def test_db_path_outside_contract_dir_rejected(self, tmp_path):
        with pytest.raises(ConfigParseError, match="canonical dedup store path"):
            load_dedup_section(
                {"db_path": str(tmp_path / "outside.sqlite")}, "x_mcp_server.toml"
            )

    def test_relative_db_path_rejected(self):
        with pytest.raises(ConfigParseError, match="absolute path"):
            load_dedup_section({"db_path": "relative.sqlite"}, "x_mcp_server.toml")

    def test_store_opens_from_injected_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LLMAGENT_DB_DIR", str(tmp_path))
        cfg = load_dedup_section(
            {"db_path": str(tmp_path / "mcp_dedup.sqlite")}, "x_mcp_server.toml"
        )
        store = open_dedup_store(cfg)
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        assert res.status == "acquired"
        store.close()
        assert (tmp_path / "mcp_dedup.sqlite").exists()

    def test_lease_and_attempt_knobs_flow_to_store(self, tmp_path):
        # DedupStoreConfig is the single source for the lease/attempt knobs.
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "x.sqlite"), lease_seconds=45, max_attempts=2
        )
        store = open_dedup_store(cfg)
        assert store._lease_seconds == 45
        assert store._max_attempts == 2
        store.close()


class TestDedupDbDirContract:
    def test_default_dir_is_db_path_parent(self, monkeypatch):
        monkeypatch.delenv("LLMAGENT_DB_DIR", raising=False)
        assert dedup_db_dir() == Path(DEFAULT_DB_PATH).parent

    def test_env_override_relocates_contract_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LLMAGENT_DB_DIR", str(tmp_path))
        assert dedup_db_dir() == tmp_path


class TestResultMetadata:
    """mcpdl004 REQ-003: classification and metadata at store time."""

    def test_small_result_stores_complete_with_hash_and_size(self, store):
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, {"ok": True}, "owner-a")
        row = store.get_execution("k1")
        assert row is not None
        serialized = json.dumps({"ok": True}, ensure_ascii=False)
        assert row.result_class == "complete"
        assert (
            row.result_sha256 == hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        )
        assert row.result_size_bytes == len(serialized.encode("utf-8"))
        assert row.result_code is None
        assert row.external_ref is None

    def test_oversized_result_stores_redacted_preview(self, store):
        payload = "x" * 9000
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, payload, "owner-a")
        row = store.get_execution("k1")
        assert row is not None and row.result_class == "redacted_preview"
        stored = row.result
        assert stored["truncated"] is True
        assert stored["sha256"] == row.result_sha256
        serialized = json.dumps(payload, ensure_ascii=False)
        assert row.result_size_bytes == len(serialized.encode("utf-8"))
        assert len(stored["preview"]) <= 1000

    def test_redaction_precedes_preview_slicing(self, store):
        payload = (
            "Bearer dummy-secret ?sig=dummy ?token=dummy /home/user/private "
            + "y" * 9000
        )
        store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, payload, "owner-a")
        row = store.get_execution("k1")
        assert row is not None and row.result_class == "redacted_preview"
        preview = row.result["preview"]
        assert "<redacted>" in preview
        assert "dummy-secret" not in preview
        assert "/home/user" not in preview
        # A complete result is stored unredacted: redaction is preview-only.
        store.try_acquire_execution("k2", "web_search", "h2", _SNAP, "owner-a")
        store.record_completed("k2", _SNAP, "Bearer dummy-secret", "owner-a")
        row2 = store.get_execution("k2")
        assert row2 is not None and row2.result_class == "complete"
        assert "dummy-secret" in row2.result

    def test_record_failed_stores_replay_unavailable(self, store):
        store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
        store.record_failed("k1", "timeout", "owner-a")
        row = store.get_execution("k1")
        assert row is not None
        assert row.result_class == "replay_unavailable"
        assert row.result_code == "timeout"

    def test_external_ref_stores_secure_reference(self, store):
        store.try_acquire_execution("k1", "github", "h1", _SNAP, "owner-a")
        store.record_completed(
            "k1", _SNAP, {"ok": True}, "owner-a", external_ref="obj-42"
        )
        row = store.get_execution("k1")
        assert row is not None
        assert row.result_class == "secure_reference"
        assert row.external_ref == "obj-42"


class TestCallStateView:
    """mcpdl004 REQ-001/REQ-005: the read-only control-API projection."""

    def test_pending_with_live_lease_maps_to_in_progress(self, store):
        store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
        view = store.call_state_view("k1")
        assert view is not None
        assert view.lease_live is True
        assert view.agent_state == "in_progress"
        assert view.reconciliation_required is False
        assert view.error_code == "none"
        assert view.attempts_exhausted is False

    def test_pending_with_expired_lease_maps_to_reconciliation_required(self, store):
        store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
        view = store.call_state_view("k1", now_epoch=time.time() + 600)
        assert view is not None
        assert view.lease_live is False
        assert view.agent_state == "reconciliation_required"
        assert view.reconciliation_required is True

    def test_completed_and_failed_rows_map_through_the_table(self, store):
        store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
        store.record_completed("k1", _SNAP, {"ok": True}, "owner-a")
        view = store.call_state_view("k1")
        assert view is not None and view.agent_state == "completed"
        assert view.result_class == "complete"
        store.try_acquire_execution("k2", "git", "h2", _SNAP, "owner-a")
        store.record_failed("k2", "timeout", "owner-a")
        view = store.call_state_view("k2")
        assert view is not None and view.agent_state == "failed"
        assert view.error_code == "handler_failed"
        assert view.result_class == "replay_unavailable"

    def test_unknown_key_returns_none(self, store):
        assert store.call_state_view("missing-key") is None

    def test_attempts_exhausted_reflects_max_attempts(self, tmp_path):
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "x.sqlite"), lease_seconds=30, max_attempts=2
        )
        store = open_dedup_store(cfg)
        try:
            store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
            assert store.call_state_view("k1").attempts_exhausted is False
            store._conn.execute(
                "UPDATE dedup_call_state SET attempt_number = 2 WHERE key = 'k1'"
            )
            assert store.call_state_view("k1").attempts_exhausted is True
        finally:
            store.close()

    def test_append_reconcile_evidence_records_history_and_leaves_row(self, store):
        store.try_acquire_execution("k1", "git", "h1", _SNAP, "owner-a")
        before = store.get_execution("k1")
        store.append_reconcile_evidence("k1", "ambiguous", "deadbeef")
        hist = _history(store)
        assert hist[-1][1] == "reconcile_decision"
        assert hist[-1][2] == "ambiguous:deadbeef"
        after = store.get_execution("k1")
        assert after == before
        with pytest.raises(ValueError, match="not in RECONCILE_OUTCOMES"):
            store.append_reconcile_evidence("k1", "found", "deadbeef")
