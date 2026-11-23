"""Tests for shared.mcp_dedup_metrics: read-only capacity metrics (mcpdl005 REQ-004, REQ-008).

Rows in several states are written through the store's own API, then the payload is compared with
the rows the store actually holds. Read-only is proven by comparing row counts and row content
before and after the call. All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.

The read helpers are the metrics view bound to the ledger, defined in shared/mcp_dedup_rows.py
(same Plan, row 07); the threshold/hold fields are the config contract of row 08, and the facade
names are row 06.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time

import pytest
from shared import mcp_dedup_ledger
from shared.mcp_dedup import DedupStoreConfig, open_dedup_store
from shared.mcp_dedup_metrics import (
    METRICS_SCHEMA_VERSION,
    STATUS_FAIL,
    STATUS_OK,
    STATUS_WARNING,
    _metric_status,
    collect_dedup_metrics,
)

# Component-keyed snapshot (execution_snapshot.COMPONENT_KEYS shape).
_SNAP = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "dedup": "gen=1;schema=deadbeef",
}


def _rows(store) -> list[tuple[str, str, float]]:
    """(key, status, updated_epoch) rows from dedup_call_state, for the before/after compare."""
    conn = sqlite3.connect(store.db_path)
    try:
        return sorted(
            (rec[0], rec[1], rec[2])
            for rec in conn.execute(
                "SELECT key, status, updated_epoch FROM dedup_call_state"
            )
        )
    finally:
        conn.close()


def _history_count(store) -> int:
    conn = sqlite3.connect(store.db_path)
    try:
        return int(
            conn.execute("SELECT COUNT(*) FROM call_attempt_history").fetchone()[0]
        )
    finally:
        conn.close()


@pytest.fixture()
def config(tmp_path) -> DedupStoreConfig:
    return DedupStoreConfig(db_path=str(tmp_path / "mcp_dedup.sqlite"))


@pytest.fixture()
def store(config):
    s = open_dedup_store(config)
    yield s
    s.close()


def _seed_states(store, config) -> float:
    """One row in each stored state plus history; returns the seed epoch (inside the hour)."""
    now = time.time()
    store.try_acquire_execution(
        "k-pending", "web_search", "h1", _SNAP, "owner-a", now_epoch=now
    )
    store.try_acquire_execution(
        "k-completed", "web_search", "h2", _SNAP, "owner-a", now_epoch=now
    )
    store.record_completed("k-completed", _SNAP, "done", "owner-a", now_epoch=now)
    store.try_acquire_execution(
        "k-failed", "web_search", "h3", _SNAP, "owner-a", now_epoch=now
    )
    store.record_failed("k-failed", "timeout", "owner-a", now_epoch=now)
    store.try_acquire_execution(
        "k-interrupted", "web_search", "h4", _SNAP, "owner-a", now_epoch=now
    )
    store.mark_interrupted("k-interrupted", "owner-a", now_epoch=now)
    return now


class TestMetricsPayload:
    def test_every_documented_field_is_reported(self, store, config):
        now = _seed_states(store, config)
        payload = collect_dedup_metrics(store, config, now_epoch=now)
        for field in (
            "schema_version",
            "db_path",
            "generated_epoch",
            "row_states",
            "pending_overdue",
            "growth_rows_per_hour",
            "wal_size_bytes",
            "lock_wait_ms",
            "legal_hold_states",
            "held_past_retention",
        ):
            assert field in payload, field
        assert payload["schema_version"] == METRICS_SCHEMA_VERSION
        assert payload["db_path"] == config.db_path
        assert payload["generated_epoch"] == now
        assert payload["row_states"] == {
            "pending": 1,
            "completed": 1,
            "failed": 1,
            "interrupted": 1,
        }
        # No lease has expired at the read time, and every row was created inside the hour.
        assert payload["pending_overdue"] == 0
        assert payload["growth_rows_per_hour"] == 4
        assert payload["legal_hold_states"] == []
        assert payload["held_past_retention"] == 0
        # JSON-safe without extra conversion.
        assert isinstance(json.dumps(payload), str)

    def test_read_issues_no_write(self, store, config):
        now = _seed_states(store, config)
        before_rows = _rows(store)
        before_history = _history_count(store)
        collect_dedup_metrics(store, config, now_epoch=now)
        assert _rows(store) == before_rows
        assert _history_count(store) == before_history
        # A metrics read cannot extend a lease: the pending row still holds its original lease.
        row = store.get_execution("k-pending")
        assert row is not None and row.status == "pending"

    def test_pending_overdue_counts_expired_leases_without_mutation(
        self, store, config
    ):
        now = _seed_states(store, config)
        payload = collect_dedup_metrics(store, config, now_epoch=now + 3600)
        assert payload["pending_overdue"] == 1
        row = store.get_execution("k-pending")
        assert row is not None and row.status == "pending"


class TestThresholdBlocks:
    def test_absent_thresholds_report_no_status_block(self, store, config):
        now = _seed_states(store, config)
        payload = collect_dedup_metrics(store, config, now_epoch=now)
        for block in ("rows", "growth", "wal"):
            assert block not in payload, block

    def test_configured_threshold_reports_value_threshold_and_status(self, tmp_path):
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "mcp_dedup.sqlite"),
            max_dedup_rows=10,
            max_dedup_growth_per_hour=10,
            max_dedup_wal_mb=4096,
        )
        store = open_dedup_store(cfg)
        try:
            now = _seed_states(store, cfg)
            payload = collect_dedup_metrics(store, cfg, now_epoch=now)
            for block, threshold in (
                ("rows", 10),
                ("growth", 10),
                ("wal", 4096),
            ):
                assert payload[block]["threshold"] == threshold
                assert payload[block]["status"] == STATUS_OK
            assert payload["rows"]["value"] == 4
            assert payload["growth"]["value"] == 4
        finally:
            store.close()

    def test_breached_threshold_reports_warning_or_fail(self, tmp_path):
        cfg = DedupStoreConfig(
            db_path=str(tmp_path / "mcp_dedup.sqlite"),
            max_dedup_rows=5,
            max_dedup_growth_per_hour=4,
            max_dedup_wal_mb=1,
        )
        store = open_dedup_store(cfg)
        try:
            now = _seed_states(store, cfg)
            payload = collect_dedup_metrics(store, cfg, now_epoch=now)
            # 4 rows against a 5-row boundary: at or above the reporting fraction, so warning.
            assert payload["rows"]["status"] == STATUS_WARNING
            assert payload["growth"]["status"] == STATUS_FAIL
            assert payload["wal"]["value"] < 1
            assert payload["wal"]["status"] == STATUS_OK
        finally:
            store.close()

    def test_reporting_fractions_are_the_documented_boundaries(self):
        # The configured value is the fail boundary; its warning fraction reads as warning.
        assert _metric_status(3, 5) == STATUS_OK
        assert _metric_status(4, 5) == STATUS_WARNING
        assert _metric_status(5, 5) == STATUS_FAIL
        assert _metric_status(None, 5) is None
        assert _metric_status(9, None) is None


class TestFacadeReExport:
    def test_public_names_are_reexported_through_the_facade(self, store, config):
        # Row 06 owns the facade re-export; it is asserted here because this row has no
        # companion file of its own.
        import shared.mcp_dedup as facade

        now = _seed_states(store, config)
        assert "METRICS_SCHEMA_VERSION" in facade.__all__
        assert "collect_dedup_metrics" in facade.__all__
        assert facade.METRICS_SCHEMA_VERSION == METRICS_SCHEMA_VERSION
        payload = facade.collect_dedup_metrics(store, config, now_epoch=now)
        assert payload["schema_version"] == METRICS_SCHEMA_VERSION


class TestLockDeadline:
    def test_lock_wait_is_reported_and_never_raises_on_a_deadline_miss(
        self, store, config, monkeypatch
    ):
        now = _seed_states(store, config)
        monkeypatch.setattr(
            mcp_dedup_ledger.DedupLedger, "DEDUP_READ_TIMEOUT_SECONDS", 0.01
        )
        held = threading.Thread(target=lambda: store._lock.acquire())
        held.start()
        time.sleep(0.2)  # let the thread take the lock before the read is attempted
        try:
            payload = collect_dedup_metrics(store, config, now_epoch=now)
        finally:
            store._lock.release()
            held.join()
        # Unavailable reads report null values; /health must still answer (no raise).
        assert payload["row_states"] is None
        assert payload["pending_overdue"] is None
        assert payload["growth_rows_per_hour"] is None
        assert payload["held_past_retention"] is None
        assert payload["lock_wait_ms"] >= 10
