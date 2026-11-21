"""Tests for shared.mcp_dedup: lease/identity store contract (mcpdl002).

Single-process state machine and config coverage for the rewritten store:
acquisition vocabulary, owner-conditional finalization, attempt history,
stamped identity (PRAGMA user_version = 1 + store_meta + installation
marker), retention-scoped purge, and lease-expiry reconciliation.
Multi-caller concurrency lives in test_mcp_dedup_concurrency.py; the
identity/loss matrix lives in test_mcp_dedup_identity.py.

All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.
"""

from __future__ import annotations

import logging
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest
from shared.config_errors import ConfigMissingError, ConfigParseError
from shared.mcp_dedup import (
    DEFAULT_DB_PATH,
    DedupConfig,
    DedupLeaseConflict,
    DedupStore,
    DedupStoreError,
    classify_interrupted,
    clear_dedup_config_cache,
    load_dedup_config,
    open_dedup_store,
    read_store_identity,
    retry_class,
)

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
            assert int(conn.execute("PRAGMA user_version").fetchone()[0]) == 1
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
        conn.execute("PRAGMA user_version = 2")
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


class TestConfigValidation:
    def test_missing_file_raises_typed_error(self, tmp_path):
        with pytest.raises(ConfigMissingError):
            load_dedup_config(tmp_path / "absent.toml")

    def test_malformed_toml_raises_parse_error(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text("[[ broken toml", encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad)

    def test_wrong_type_raises_parse_error(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text('[dedup]\nretention_days = "fourteen"\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad)

    def test_bad_section_types_raise_parse_error(self, tmp_path):
        bad1 = tmp_path / "mcp_dedup.toml"
        bad1.write_text('dedup = "not a table"\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad1)
        bad2 = tmp_path / "mcp_dedup.toml"
        bad2.write_text('[dedup]\ndb_path = ""\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad2)
        bad3 = tmp_path / "mcp_dedup.toml"
        bad3.write_text("[dedup]\n[retry_class]\nwrite_file = 5\n", encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad3)

    def test_partial_config_gets_defaults(self, tmp_path):
        partial = tmp_path / "mcp_dedup.toml"
        partial.write_text('[dedup]\ndb_path = "/tmp/x.sqlite"\n', encoding="utf-8")
        cfg = load_dedup_config(partial)
        assert cfg.retention_days == 14
        assert cfg.pending_timeout_minutes == 10
        assert cfg.lease_seconds == 30
        assert cfg.max_attempts == 3
        assert cfg.retry_class == {}

    def test_lease_seconds_out_of_range_rejected(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text("[dedup]\nlease_seconds = 0\n", encoding="utf-8")
        with pytest.raises(ConfigParseError, match="lease_seconds"):
            load_dedup_config(bad)

    def test_max_attempts_out_of_range_rejected(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text("[dedup]\nmax_attempts = 11\n", encoding="utf-8")
        with pytest.raises(ConfigParseError, match="max_attempts"):
            load_dedup_config(bad)

    def test_unknown_dedup_key_rejected(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text("[dedup]\nsentinel_mode = 1\n", encoding="utf-8")
        with pytest.raises(ConfigParseError, match="unknown dedup keys"):
            load_dedup_config(bad)

    def test_retry_class_lookup(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text(
            '[dedup]\n[retry_class]\nwrite_file = "retryable"\nshell_run = "non_retryable"\n',
            encoding="utf-8",
        )
        cfg = load_dedup_config(cfg_file)
        assert retry_class("write_file", cfg) == "retryable"
        assert retry_class("shell_run", cfg) == "non_retryable"
        # Unknown tools are never retried blindly.
        assert retry_class("some_new_tool", cfg) == "non_retryable"

    def test_retry_class_unknown_tool_name_rejected(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text(
            '[dedup]\n[retry_class]\nnot_a_tool = "retryable"\n', encoding="utf-8"
        )
        with pytest.raises(ConfigParseError, match="not_a_tool"):
            load_dedup_config(bad)

    def test_retry_class_disallowed_value_rejected(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text(
            '[dedup]\n[retry_class]\nwrite_file = "sometimes"\n', encoding="utf-8"
        )
        with pytest.raises(ConfigParseError, match="write_file"):
            load_dedup_config(bad)

    def test_retry_class_reference_drift_is_reported_not_fatal(self, tmp_path, caplog):
        # agentcfg003: the declared retry_policy is the authority; a mirror entry
        # disagreeing with the RETRYABLE_TOOLS reference set is a drift finding,
        # not a load failure, and the loaded classification stands.
        drift = tmp_path / "mcp_dedup.toml"
        drift.write_text(
            '[dedup]\n[retry_class]\nwrite_file = "non_retryable"\n', encoding="utf-8"
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_dedup_config(drift)
        assert cfg.retry_class["write_file"] == "non_retryable"
        assert retry_class("write_file", cfg) == "non_retryable"
        assert any("drift finding" in record.message for record in caplog.records)

    def test_retry_class_membership_contradiction_reports_drift(self, tmp_path, caplog):
        # agentcfg003 replaced the fail-closed gate: a mirror entry contradicting
        # the RETRYABLE_TOOLS reference set loads with a drift finding.
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text(
            '[dedup]\n[retry_class]\nsearch_web = "retryable"\n', encoding="utf-8"
        )
        with caplog.at_level(logging.WARNING):
            cfg = load_dedup_config(bad)
        assert cfg.retry_class["search_web"] == "retryable"
        assert any("search_web" in record.message for record in caplog.records)

    def test_store_opens_from_config_db_path(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text(
            f'[dedup]\ndb_path = "{tmp_path / "from_cfg.sqlite"}"\n', encoding="utf-8"
        )
        cfg = load_dedup_config(cfg_file)
        store = open_dedup_store(cfg)
        res = store.try_acquire_execution("k1", "web_search", "h1", _SNAP, "owner-a")
        assert res.status == "acquired"
        store.close()
        assert (tmp_path / "from_cfg.sqlite").exists()


class TestConfigResolutionAndCache:
    @pytest.fixture(autouse=True)
    def _reset_config_cache(self):
        clear_dedup_config_cache()
        yield
        clear_dedup_config_cache()

    def test_default_path_honors_llmagent_config_dir(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "mcp_dedup.toml").write_text(
            "[dedup]\nretention_days = 21\n", encoding="utf-8"
        )
        monkeypatch.setenv("LLMAGENT_CONFIG_DIR", str(cfg_dir))
        cfg = load_dedup_config()
        assert cfg.retention_days == 21

    def test_explicit_path_still_loads(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text("[dedup]\nretention_days = 7\n", encoding="utf-8")
        cfg = load_dedup_config(cfg_file)
        assert cfg.retention_days == 7

    def test_second_load_serves_cache_without_file(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text("[dedup]\nretention_days = 7\n", encoding="utf-8")
        first = load_dedup_config(cfg_file)
        cfg_file.unlink()
        assert load_dedup_config(cfg_file) is first

    def test_cache_clear_forces_reload(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text("[dedup]\nretention_days = 7\n", encoding="utf-8")
        assert load_dedup_config(cfg_file).retention_days == 7
        cfg_file.write_text("[dedup]\nretention_days = 30\n", encoding="utf-8")
        clear_dedup_config_cache()
        assert load_dedup_config(cfg_file).retention_days == 30

    def test_missing_file_error_not_cached(self, tmp_path):
        missing = tmp_path / "absent.toml"
        with pytest.raises(ConfigMissingError):
            load_dedup_config(missing)
        with pytest.raises(ConfigMissingError):
            load_dedup_config(missing)

    def test_db_path_fallback_matches_convention(self, tmp_path):
        import dataclasses

        from db.config import DbConfig

        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text("[dedup]\nretention_days = 14\n", encoding="utf-8")
        cfg = load_dedup_config(cfg_file)
        assert cfg.db_path == DEFAULT_DB_PATH == "/opt/llm/db/mcp_dedup.sqlite"
        own_parent = Path(DEFAULT_DB_PATH).parent
        fallbacks = [
            f.default
            for f in dataclasses.fields(DbConfig)
            if f.name == "workflow_db_path"
        ]
        assert fallbacks and all(Path(v).parent == own_parent for v in fallbacks)


def test_dedup_config_fields_match_loader(tmp_path):
    # DedupConfig is the single source for the lease/attempt knobs.
    cfg = DedupConfig(db_path="/tmp/x.sqlite", lease_seconds=45, max_attempts=2)
    store = open_dedup_store(cfg)
    assert store._lease_seconds == 45
    assert store._max_attempts == 2
    store.close()
