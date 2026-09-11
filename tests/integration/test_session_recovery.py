"""tests/integration/test_session_recovery.py

Integration tests: Agent Session <-> SQLite, real corruption + recovery
(TC-E01 through TC-E05).

Companion to test_session_sqlite.py (TC-B01-B08, which covers WAL/busy
-lock/FK/rollback but not physical corruption or recover_corruption()).
Uses the corrupt_wal_db fixture (tests/integration/conftest.py) for a
real, byte-truncated SQLite file rather than a MagicMock connection
(see tests/test_db_maintenance.py::TestRecoverCorruption for the
existing mock-based unit coverage this file complements).

Neither AgentSession nor recover_corruption() accept a direct db_path
override (confirmed by direct read of agent/session.py and db/recovery.py);
both resolve their target path via SQLiteHelper(target), which calls
db.config.build_db_config() internally. db/helper.py and db/recovery.py
each import build_db_config into their own module namespace, so both
bindings are monkeypatched together by _patch_db_config() below.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.integration.conftest import hold_write_lock


def _patch_db_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, session_db_path: str
) -> None:
    """Point build_db_config() at session_db_path for both db.helper and db.recovery.

    rag/workflow/eventbus paths are unused placeholders in tmp_path -- DbConfig
    only requires their parent directory to exist, not the files themselves.
    sqlite_timeout/sqlite_busy_timeout_ms are shortened so lock-contention
    tests (E05) resolve quickly instead of waiting out the 30s default.
    """
    from db.config import DbConfig

    cfg = DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=session_db_path,
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
        eventbus_db_path=str(tmp_path / "eventbus.sqlite"),
        sqlite_timeout=1,
        sqlite_busy_timeout_ms=500,
    )
    monkeypatch.setattr("db.helper.build_db_config", lambda: cfg)
    monkeypatch.setattr("db.recovery.build_db_config", lambda: cfg)


def test_e01_session_start_on_corrupted_db_raises(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AgentSession.start() on a physically corrupted DB raises, not a silent session_id=None."""
    from agent.session import AgentSession

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)

    session = AgentSession()
    with pytest.raises((sqlite3.DatabaseError, sqlite3.OperationalError)):
        session.start()
    assert session.session_id is None


def test_e02_recover_corruption_raises_uncaught_database_error(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """_run_integrity_check()'s except clause now catches Exception broadly
    (widened since this test was first written, per its own follow-up
    candidate below), so sqlite3.DatabaseError from the corrupt target no
    longer propagates uncaught -- recover_corruption() classifies it and
    proceeds to _restore_from_backup(), which then finds the supplied
    backup_path itself isn't a valid SQLite file either (placeholder text),
    and returns a graceful "bad_backup" result rather than raising.

    Historical note (no longer current): this test used to document a latent
    bug where _run_integrity_check()'s except clause only caught
    (sqlite3.OperationalError, ValueError, RuntimeError), letting
    sqlite3.DatabaseError from `PRAGMA journal_mode=WAL` propagate uncaught.
    """
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)
    backup_path = str(tmp_path / "backup.sqlite")
    Path(backup_path).write_bytes(
        b"placeholder backup -- presence is all that matters here"
    )

    result = recover_corruption(backup_path, target="session")
    assert result.success is False
    assert result.action == "bad_backup"


def test_e03_recover_corruption_no_backup_raises_uncaught_database_error(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same widened except-clause behavior as test_e02 (see its docstring),
    with no backup_path at all -- the corrupt target is classified rather
    than raising, and _restore_from_backup()'s own None-check then produces
    action="no_backup"."""
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)

    result = recover_corruption(None, target="session")
    assert result.success is False
    assert result.action == "no_backup"


def test_e04_recover_corruption_dry_run_raises_before_mutation_check(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same widened except-clause behavior as test_e02 (see its docstring).
    dry_run=True short-circuits recover_corruption() before it ever reaches
    _restore_from_backup(): the corrupt-condition dry_run branch returns
    action="error" without touching the file, preserving the "no mutation"
    guarantee."""
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)
    before_mtime = Path(corrupt_wal_db).stat().st_mtime
    before_size = Path(corrupt_wal_db).stat().st_size

    result = recover_corruption(None, target="session", dry_run=True)
    assert result.success is False
    assert result.dry_run is True

    after_mtime = Path(corrupt_wal_db).stat().st_mtime
    after_size = Path(corrupt_wal_db).stat().st_size
    assert before_mtime == after_mtime
    assert before_size == after_size


def test_e05_concurrent_session_start_under_exclusive_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Extends TC-B02's pattern (test_session_sqlite.py), but driven through
    AgentSession.start() itself rather than raw SQL -- confirms the documented
    "no try/except, propagates" behavior is the actual behavior through the
    real class, not just raw SQL.
    """
    from agent.session import AgentSession
    from db.schema_sql import build_session_schema_sql

    db_path = str(tmp_path / "e05.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(build_session_schema_sql(4))
    except Exception:  # noqa: BLE001 — memories_vec may be unavailable without sqlite-vec; ignore
        pass  # memories_vec may be unavailable without sqlite-vec; ignore
    conn.commit()
    conn.close()

    _patch_db_config(monkeypatch, tmp_path, db_path)

    lock_t = hold_write_lock(db_path, 2.0)
    time.sleep(0.1)  # let lock thread acquire before starting the session
    try:
        session = AgentSession()
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            session.start()
    finally:
        lock_t.join(timeout=3.0)


def test_e06_recover_corruption_unknown_preserves_session_db(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """UNKNOWN classification preserves the session DB file untouched."""
    from unittest.mock import patch

    from db.recovery import DbCondition, recover_corruption

    session_db = tmp_path / "session.sqlite"
    original_bytes = b"not a real sqlite file, but presence/content is what matters"
    session_db.write_bytes(original_bytes)
    _patch_db_config(monkeypatch, tmp_path, str(session_db))

    with patch(
        "db.recovery._run_integrity_check",
        return_value=(DbCondition.UNKNOWN, "simulated unclassifiable failure"),
    ):
        with patch("db.recovery._restore_from_backup") as mock_restore:
            result = recover_corruption(target="session")

    mock_restore.assert_not_called()
    assert result.success is False
    assert result.action == "preserved_operator_intervention_required"
    assert "operator intervention required" in result.detail
    assert session_db.read_bytes() == original_bytes


def _make_partial_session_db(tmp_path: Path, table_to_drop: str | None = None) -> str:
    """Create a session.sqlite with optional table dropped, return path."""
    from db.schema_sql import build_session_schema_sql

    db_path = str(tmp_path / "partial.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    schema = build_session_schema_sql(4)
    if table_to_drop:
        # Drop the specified table from the schema before executing
        tables_to_drop = [table_to_drop]
        for tbl in tables_to_drop:
            schema = schema.replace(f"\nCREATE TABLE IF NOT EXISTS {tbl}", "")
            schema = schema.replace(f"\nCREATE INDEX IF NOT EXISTS idx_{tbl}", "")
    try:
        conn.executescript(schema)
    except Exception:  # noqa: BLE001 — memories_vec may be unavailable without sqlite-vec; ignore
        pass
    conn.commit()
    conn.close()
    return db_path


def _make_orphaned_message_db(tmp_path: Path) -> str:
    """Create a session.sqlite with an orphaned messages row, return path."""
    from db.schema_sql import build_session_schema_sql

    db_path = str(tmp_path / "orphan_msg.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(build_session_schema_sql(4))
    except Exception:  # noqa: BLE001 — memories_vec may be unavailable without sqlite-vec; ignore
        pass
    conn.execute(
        "INSERT INTO sessions(session_id, created_at) VALUES (1, '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO messages(message_id, session_id, role, content) VALUES (9999, 9999, 'user', 'orphan_content_placeholder')"
    )
    conn.commit()
    conn.close()
    return db_path


def _make_orphaned_memory_link_db(tmp_path: Path) -> str:
    """Create a session.sqlite with an orphaned memory_links row, return path."""
    from db.schema_sql import build_session_schema_sql

    db_path = str(tmp_path / "orphan_memlink.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(build_session_schema_sql(4))
    except Exception:  # noqa: BLE001 — memories_vec may be unavailable without sqlite-vec; ignore
        pass
    conn.execute(
        "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('valid_src', 'semantic', 'src_content', 'src')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('valid_dst', 'semantic', 'dst_content', 'dst')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('orph_src', 'semantic', 'osrc', 'osrc')"
    )
    conn.execute(
        "INSERT OR IGNORE INTO memories(memory_id, memory_type, content, summary) VALUES ('orph_dst', 'semantic', 'odst', 'odst')"
    )
    conn.execute(
        "INSERT INTO memory_links(src_id, dst_id) VALUES ('orph_src', 'orph_dst')"
    )
    conn.commit()
    conn.close()
    return db_path


def test_e07_session_logical_verify_failed_on_missing_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Recovering from a backup missing a required table should fail logical verification."""
    from db.recovery import DbCondition, recover_corruption

    session_db = tmp_path / "session.sqlite"
    backup_db = tmp_path / "backup.sqlite"
    # Create a minimal backup with ONLY the sessions table (missing messages and memory_links)
    backup_conn = sqlite3.connect(str(backup_db))
    # Only create the sessions table, not the full schema
    sessions_ddl = """
CREATE TABLE IF NOT EXISTS sessions(
    session_id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
    backup_conn.executescript(sessions_ddl)
    backup_conn.commit()
    backup_conn.close()
    # Corrupt the target DB so recovery is triggered
    session_db.write_bytes(b"corrupted data")
    _patch_db_config(monkeypatch, tmp_path, str(session_db))

    with patch(
        "db.recovery._run_integrity_check",
        side_effect=[
            (DbCondition.CORRUPTION, "DB corruption"),  # current DB
            (DbCondition.HEALTHY, None),  # backup
            (DbCondition.HEALTHY, None),  # post-restore
        ],
    ):
        # session_db/backup_db are real files created above, so their own
        # .exists() checks resolve naturally -- no need to (and, since
        # _restore_from_backup() now also probes for nonexistent -wal/-shm
        # sidecar files via Path.exists(), actively harmful to) blanket-patch
        # Path.exists() to always return True.
        result = recover_corruption(backup_path=str(backup_db), target="session")

    assert result.success is False
    assert result.action == "logical_verify_failed"
    # Verify no content leaked into detail string
    assert "placeholder" not in result.detail.lower()
    assert "content" not in result.detail.lower()
    assert "message" not in result.detail.lower()
    assert "memory" not in result.detail.lower()
