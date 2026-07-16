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
    """Documents a latent bug in recover_corruption() (plan Risk R-2 -- test-only
    scope, not fixed here): scripts/db/recovery.py::_run_integrity_check()'s
    except clause only catches (sqlite3.OperationalError, ValueError,
    RuntimeError). Real SQLite page-level corruption (confirmed empirically
    against the corrupt_wal_db fixture) raises sqlite3.DatabaseError from the
    `PRAGMA journal_mode=WAL` call inside SQLiteHelper.open() -- DatabaseError
    is not a subclass of OperationalError, so it propagates uncaught instead
    of _run_integrity_check() returning (None, error_detail) as its own
    docstring implies for "cannot be opened" cases. recover_corruption() never
    reaches _restore_from_backup(), so this holds regardless of whether a
    valid backup_path is supplied (see test_e03/test_e04 below for the
    no-backup and dry_run variants of the same root cause).

    Follow-up candidate: widen _run_integrity_check()'s except clause to also
    catch sqlite3.DatabaseError (or sqlite3.Error, the common base).
    """
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)
    backup_path = str(tmp_path / "backup.sqlite")
    Path(backup_path).write_bytes(
        b"placeholder backup -- presence is all that matters here"
    )

    with pytest.raises(sqlite3.DatabaseError):
        recover_corruption(backup_path, target="session")


def test_e03_recover_corruption_no_backup_raises_uncaught_database_error(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same latent bug as test_e02 (see its docstring), with no backup_path at
    all -- confirms the crash happens before _restore_from_backup()'s own
    None-check, so action="no_backup" (this plan's originally expected
    result for this scenario) is not actually reached for this corruption mode.
    """
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)

    with pytest.raises(sqlite3.DatabaseError):
        recover_corruption(None, target="session")


def test_e04_recover_corruption_dry_run_raises_before_mutation_check(
    corrupt_wal_db: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Same latent bug as test_e02 (see its docstring). dry_run=True does not
    change the outcome: the crash happens inside _run_integrity_check(),
    before recover_corruption() ever inspects dry_run. The file happens to
    stay unmutated (the crash occurs on a read-only open/pragma sequence
    before any write), so the dry-run "no mutation" guarantee holds -- but not
    via the clean _handle_dry_run() branch the plan originally described.
    """
    from db.recovery import recover_corruption

    _patch_db_config(monkeypatch, tmp_path, corrupt_wal_db)
    before_mtime = Path(corrupt_wal_db).stat().st_mtime
    before_size = Path(corrupt_wal_db).stat().st_size

    with pytest.raises(sqlite3.DatabaseError):
        recover_corruption(None, target="session", dry_run=True)

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
    except Exception:
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
