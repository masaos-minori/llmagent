"""Store identity and start-state matrix for the dedup store (mcpdl002 Plan Phase 1, row 11).

Test-first evidence: written against the identity contract that row 01 will
implement (REQ-005..REQ-007; AC-4, AC-5). Against the pre-change store the
suite fails by design (no identity row, no marker, no start-state
classification, no operator resolution); from Phase 2 on it is a passing
regression member.

Contract asserted (public surface only, per row 11 Design decisions):
- DedupStore.start_state: first_initialization | healthy on safe opens.
- Unsafe opens raise the typed store_error taxonomy (mcp_dedup.DedupStoreError)
  with .state = lost | replaced | legacy_or_unverified | schema_mismatch.
- Creation writes store_meta + PRAGMA user_version = 1 + the external
  installation marker atomically.
- resolve_store(path) is the operator resolution: validates state, archives the
  old file, issues a new generation, logs the decision. An empty file alone
  never resolves; a healthy store refuses resolution.

Legacy fixtures are built inline from the pre-change single-table DDL so they
stay stable after row 01 rewrites the canonical schema.
All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import shared.mcp_dedup as mcp_dedup
from shared.mcp_dedup import DedupStore

_MARKER_NAME = ".mcp_dedup_installed"
_STORE_TABLES = {"dedup_call_state", "store_meta", "call_attempt_history"}

_LEGACY_DDL = (
    "CREATE TABLE IF NOT EXISTS tool_call_state ("
    "key TEXT PRIMARY KEY, tool_name TEXT NOT NULL, args_hash TEXT NOT NULL, "
    "status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'interrupted')), "
    "snapshot_json TEXT NOT NULL, created_epoch REAL NOT NULL, "
    "updated_epoch REAL NOT NULL, result_json TEXT); "
    "CREATE INDEX IF NOT EXISTS idx_tcs_updated ON tool_call_state(updated_epoch); "
    "CREATE INDEX IF NOT EXISTS idx_tcs_status ON tool_call_state(status);"
)


def _store_error() -> type[Exception]:
    """Typed store_error taxonomy surfaced through the store module."""
    return mcp_dedup.DedupStoreError


def _marker(path: str | Path) -> Path:
    return Path(path).parent / _MARKER_NAME


def _user_version(path: str | Path) -> int:
    conn = sqlite3.connect(str(path))
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def _tables(path: str | Path) -> set[str]:
    conn = sqlite3.connect(str(path))
    try:
        return {
            str(r[0])
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


def _store_meta(path: str | Path) -> dict[str, object]:
    conn = sqlite3.connect(str(path))
    try:
        conn.row_factory = sqlite3.Row
        rec = conn.execute(
            "SELECT store_uuid, generation, schema_fingerprint, config_fingerprint, "
            "created_epoch FROM store_meta"
        ).fetchone()
    finally:
        conn.close()
    if rec is None:
        raise AssertionError("store_meta has no identity row")
    return dict(rec)


def _make_healthy(tmp_path: Path) -> tuple[str, DedupStore]:
    path = str(tmp_path / "dedup.sqlite")
    store = DedupStore(path)
    return path, store


def _build_legacy_db(path: str) -> None:
    """Pre-change fixture: single-table ledger, user_version = 0, no marker."""
    conn = sqlite3.connect(path)
    conn.executescript(_LEGACY_DDL)
    conn.execute(
        "INSERT INTO tool_call_state (key, tool_name, args_hash, status, snapshot_json,"
        " created_epoch, updated_epoch, result_json) VALUES ('old1', 'write_file',"
        " 'h', 'completed', '{}', 1.0, 1.0, '\"done\"')"
    )
    conn.commit()
    conn.close()


class TestFirstInitialization:
    def test_creation_writes_identity_stamp_and_marker_atomically(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        store = DedupStore(path)
        try:
            assert store.start_state == "first_initialization"
        finally:
            store.close()
        assert _user_version(path) == 1
        assert _tables(path) >= _STORE_TABLES
        meta = _store_meta(path)
        assert str(meta["store_uuid"])
        assert int(meta["generation"]) == 1
        assert str(meta["schema_fingerprint"])
        assert str(meta["config_fingerprint"])
        assert float(meta["created_epoch"]) > 0
        marker = _marker(path)
        assert marker.exists()
        assert str(meta["store_uuid"]) in marker.read_text(encoding="utf-8")

    def test_reopen_of_healthy_store_classifies_healthy(self, tmp_path):
        path, store = _make_healthy(tmp_path)
        acquired = store.try_acquire_execution(
            "k1", "write_file", "h1", {"deployed_rev": "x"}, "owner-A"
        )
        assert acquired.status == "acquired"
        store.record_completed("k1", {"deployed_rev": "x"}, "done", "owner-A")
        store.close()
        reopened = DedupStore(path)
        try:
            assert reopened.start_state == "healthy"
            assert reopened.generation == 1
        finally:
            reopened.close()


class TestStartStateMatrix:
    def test_db_only_deletion_classifies_lost(self, tmp_path):
        path, store = _make_healthy(tmp_path)
        store.close()
        Path(path).unlink()
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        assert exc.value.state == "lost"
        assert _marker(path).exists()

    def test_marker_only_deletion_is_not_silently_healthy(self, tmp_path):
        path, store = _make_healthy(tmp_path)
        store.close()
        _marker(path).unlink()
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        # Marker-state asymmetry: DB identity present, installation marker gone.
        assert exc.value.state == "legacy_or_unverified"

    def test_replaced_foreign_store_uuid_classifies_replaced(self, tmp_path):
        path, store = _make_healthy(tmp_path)
        meta_uuid = str(_store_meta(path)["store_uuid"])
        store.close()
        conn = sqlite3.connect(path)
        conn.execute("UPDATE store_meta SET store_uuid = 'foreign-uuid-999'")
        conn.commit()
        conn.close()
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        assert exc.value.state == "replaced"
        assert meta_uuid != "foreign-uuid-999"

    def test_legacy_db_without_identity_classifies_legacy_or_unverified(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        _build_legacy_db(path)
        assert _user_version(path) == 0
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        # Never first_initialization and never healthy.
        assert exc.value.state == "legacy_or_unverified"

    def test_empty_file_after_loss_is_not_healthy(self, tmp_path):
        """REQ-007: creating an empty file alone does not resolve a lost store."""
        path, store = _make_healthy(tmp_path)
        store.close()
        Path(path).unlink()
        Path(path).touch()  # the removed touch() recovery shape
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        assert exc.value.state in ("lost", "legacy_or_unverified")

    def test_unsafe_states_produce_no_usable_handle(self, tmp_path):
        """AC-5 store level: unsafe classification happens before any write path."""
        path, store = _make_healthy(tmp_path)
        store.close()
        Path(path).unlink()
        with pytest.raises(_store_error()):
            store2 = DedupStore(path)
            store2.try_acquire_execution("k1", "write_file", "h1", {}, "owner-X")


class TestSchemaMismatch:
    def test_drifted_ledger_shape_raises_typed_store_error(self, tmp_path):
        """REQ-006: shape drift on an otherwise valid identity is typed, not a
        raw RuntimeError."""
        path, store = _make_healthy(tmp_path)
        store.close()
        conn = sqlite3.connect(path)
        conn.execute("ALTER TABLE dedup_call_state ADD COLUMN drifted TEXT")
        conn.commit()
        conn.close()
        with pytest.raises(_store_error()) as exc:
            DedupStore(path)
        assert exc.value.state == "schema_mismatch"
        assert not isinstance(exc.value, RuntimeError)


class TestOperatorResolution:
    def test_resolution_rolls_generation_and_logs_decision(self, tmp_path, caplog):
        path, store = _make_healthy(tmp_path)
        store.close()
        Path(path).unlink()
        mcp_dedup.resolve_store(path)
        reopened = DedupStore(path)
        try:
            assert reopened.start_state == "healthy"
            assert reopened.generation == 2
            meta = _store_meta(path)
            assert int(meta["generation"]) == 2
            assert str(meta["store_uuid"]) in _marker(path).read_text(encoding="utf-8")
        finally:
            reopened.close()
        assert any("generation" in rec.getMessage() for rec in caplog.records)

    def test_resolution_archives_the_old_file(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        _build_legacy_db(path)
        mcp_dedup.resolve_store(path)
        archives = list(Path(path).parent.glob("dedup.sqlite.corrupt-*"))
        assert archives, "operator resolution must archive the replaced file"
        reopened = DedupStore(path)
        try:
            assert reopened.start_state == "healthy"
            assert reopened.generation == 1
        finally:
            reopened.close()

    def test_resolution_refused_for_healthy_store(self, tmp_path):
        path, store = _make_healthy(tmp_path)
        store.close()
        with pytest.raises(_store_error()):
            mcp_dedup.resolve_store(path)
        reopened = DedupStore(path)
        try:
            assert reopened.start_state == "healthy"
        finally:
            reopened.close()

    def test_resolve_lost_store_and_touch_are_removed(self):
        """REQ-007: the removed resolution shapes must not remain callable."""
        assert not hasattr(mcp_dedup, "resolve_lost_store")
        # The store family is split across shared/mcp_dedup*.py (module size
        # gate); the scan must cover every module of the family.
        store_src = "\n".join(
            p.read_text(encoding="utf-8")
            for p in sorted(Path(mcp_dedup.__file__).parent.glob("mcp_dedup*.py"))
        )
        assert ".touch()" not in store_src
