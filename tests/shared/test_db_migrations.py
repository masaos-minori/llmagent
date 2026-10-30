"""tests/shared/test_db_migrations.py

Regression tests for the forward-only migration framework: ordered migration, the
verified-backup gate, refusals, rollback on failure, and byte-identical dry-run.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from shared.db_migrations import (
    MigrationDomain,
    MigrationFailedError,
    MigrationRefusedError,
    MigrationSpec,
    ensure_ledger,
    read_ledger,
    resolve_path,
    run_migrations,
)


def _read_version(conn: sqlite3.Connection) -> str | None:
    value = int(conn.execute("PRAGMA user_version").fetchone()[0])
    return str(value) if value else None


def _write_version(conn: sqlite3.Connection, version: str) -> None:
    conn.execute(f"PRAGMA user_version = {int(version)}")  # nosec B608 — int-cast test value


def _verify_shape(conn: sqlite3.Connection, version: str) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(t)")}
    expected = {"1": {"id"}, "2": {"id", "a"}, "3": {"id", "a", "b"}}[version]
    if cols != expected:
        raise RuntimeError(f"shape mismatch at {version}: {sorted(cols)}")


DOMAIN = MigrationDomain(
    "test", sqlite3.connect, _read_version, _write_version, _verify_shape
)


def _add_a(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE t ADD COLUMN a TEXT")


def _add_b(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE t ADD COLUMN b TEXT")


SPECS = (
    MigrationSpec("m-1-2", "1", "2", _add_a),
    MigrationSpec("m-2-3", "2", "3", _add_b),
)


def _make_db(path: Path, version: int = 1) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.executemany("INSERT INTO t (id) VALUES (?)", [(1,), (2,), (3,)])
        conn.execute(f"PRAGMA user_version = {version}")  # nosec B608 — int test value
        conn.commit()
    finally:
        conn.close()
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path: Path) -> list[tuple[int]]:
    conn = sqlite3.connect(path)
    try:
        return [(int(r[0]),) for r in conn.execute("SELECT id FROM t ORDER BY id")]
    finally:
        conn.close()


def _version(path: Path) -> str | None:
    conn = sqlite3.connect(path)
    try:
        return _read_version(conn)
    finally:
        conn.close()


def _ledger(path: Path) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        ensure_ledger(conn)
        return read_ledger(conn)
    finally:
        conn.close()


def test_chain_applies_in_order_with_ledger_and_backup(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite")
    report = run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups")
    assert report.applied == ("m-1-2", "m-2-3")
    assert report.dry_run is False
    assert _version(db) == "3"
    assert _ledger(db) == ["m-1-2", "m-2-3"]
    assert _rows(db) == [(1,), (2,), (3,)]
    assert report.backup_path is not None and report.backup_path.exists()
    assert _version(report.backup_path) == "1"


def test_already_at_target_is_a_noop_without_backup(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite", version=3)
    conn = sqlite3.connect(db)
    conn.execute("ALTER TABLE t ADD COLUMN a TEXT")
    conn.execute("ALTER TABLE t ADD COLUMN b TEXT")
    conn.commit()
    conn.close()
    before = _sha(db)
    report = run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups")
    assert report.applied == ()
    assert report.backup_path is None
    assert not (tmp_path / "backups").exists()
    assert _sha(db) == before


def test_downgrade_is_refused_and_leaves_database_untouched(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite", version=3)
    before = _sha(db)
    with pytest.raises(MigrationRefusedError, match="downgrade or unknown"):
        run_migrations(db, DOMAIN, SPECS, "1", tmp_path / "backups")
    assert _sha(db) == before
    assert not (tmp_path / "backups").exists()


def test_unknown_current_version_is_refused(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite", version=9)
    with pytest.raises(MigrationRefusedError):
        run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups")


def test_unversioned_database_is_refused(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite", version=0)
    with pytest.raises(MigrationRefusedError, match="no schema version"):
        run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups")


def test_missing_database_is_refused(tmp_path: Path) -> None:
    with pytest.raises(MigrationRefusedError, match="not found"):
        run_migrations(tmp_path / "none.sqlite", DOMAIN, SPECS, "3", tmp_path / "b")


def test_ambiguous_path_is_refused() -> None:
    specs = (*SPECS, MigrationSpec("dup", "1", "3", _add_a))
    with pytest.raises(MigrationRefusedError, match="ambiguous"):
        resolve_path(specs, "1", "3")


def test_cycle_is_refused() -> None:
    specs = (
        MigrationSpec("a", "1", "2", _add_a),
        MigrationSpec("b", "2", "1", _add_b),
    )
    with pytest.raises(MigrationRefusedError, match="cycle"):
        resolve_path(specs, "1", "9")


def test_failure_mid_migration_rolls_back_and_keeps_original(tmp_path: Path) -> None:
    def boom(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE t ADD COLUMN b TEXT")
        raise RuntimeError("injected")

    specs = (SPECS[0], MigrationSpec("m-2-3", "2", "3", boom))
    db = _make_db(tmp_path / "t.sqlite")
    with pytest.raises(MigrationFailedError, match="m-2-3") as info:
        run_migrations(db, DOMAIN, specs, "3", tmp_path / "backups")
    assert info.value.migration_id == "m-2-3"
    assert _version(db) == "2"
    assert _ledger(db) == ["m-1-2"]
    assert _rows(db) == [(1,), (2,), (3,)]
    conn = sqlite3.connect(db)
    assert {r[1] for r in conn.execute("PRAGMA table_info(t)")} == {"id", "a"}
    conn.close()


def test_interrupted_migration_rolls_back(tmp_path: Path) -> None:
    def interrupt(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE t ADD COLUMN a TEXT")
        raise KeyboardInterrupt

    db = _make_db(tmp_path / "t.sqlite")
    specs = (MigrationSpec("m-1-2", "1", "2", interrupt),)
    with pytest.raises(KeyboardInterrupt):
        run_migrations(db, DOMAIN, specs, "2", tmp_path / "backups")
    assert _version(db) == "1"
    assert _ledger(db) == []
    conn = sqlite3.connect(db)
    assert {r[1] for r in conn.execute("PRAGMA table_info(t)")} == {"id"}
    conn.close()


def test_failed_postcondition_rolls_back(tmp_path: Path) -> None:
    def bad_post(conn: sqlite3.Connection) -> None:
        raise RuntimeError("postcondition")

    db = _make_db(tmp_path / "t.sqlite")
    specs = (MigrationSpec("m-1-2", "1", "2", _add_a, postcondition=bad_post),)
    with pytest.raises(MigrationFailedError):
        run_migrations(db, DOMAIN, specs, "2", tmp_path / "backups")
    assert _version(db) == "1"
    assert _ledger(db) == []


def test_shape_verification_failure_rolls_back(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite")
    specs = (MigrationSpec("m-1-2", "1", "2", _add_b),)  # adds the wrong column
    with pytest.raises(MigrationFailedError, match="shape mismatch"):
        run_migrations(db, DOMAIN, specs, "2", tmp_path / "backups")
    assert _version(db) == "1"
    assert _ledger(db) == []


def test_backup_gate_refuses_when_backup_fails_integrity(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite")
    before = _sha(db)
    with patch(
        "shared.db_migrations._integrity_ok", return_value=(False, "corrupt page")
    ):
        with pytest.raises(MigrationRefusedError, match="integrity"):
            run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups")
    assert _sha(db) == before
    assert list((tmp_path / "backups").glob("*")) == []


def test_dry_run_leaves_database_byte_identical(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite")
    before = _sha(db)
    report = run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups", dry_run=True)
    assert report.dry_run is True
    assert report.applied == ("m-1-2", "m-2-3")
    assert report.backup_path is None
    assert _sha(db) == before
    assert not (tmp_path / "backups").exists()


def test_dry_run_still_refuses_unknown_path(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "t.sqlite", version=9)
    with pytest.raises(MigrationRefusedError):
        run_migrations(db, DOMAIN, SPECS, "3", tmp_path / "backups", dry_run=True)
