"""tests/db/test_migrations_workflow.py

workflow.sqlite migration registry accessors and the migrate_db CLI: rows survive a
registered upgrade, failures leave the original intact, dry-run is byte-identical,
and refusals map to exit codes.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from db.migrate_db import EXIT_FAILED, EXIT_OK, EXIT_REFUSED, main
from db.migrations_workflow import (
    MIGRATIONS,
    WORKFLOW_DOMAIN,
    connect_workflow,
    read_workflow_version,
    verify_workflow_shape,
    write_workflow_version,
)
from db.schema_sql import WORKFLOW_SCHEMA_VERSION, build_workflow_schema_sql
from shared.db_migrations import (
    MigrationFailedError,
    MigrationRefusedError,
    MigrationSpec,
    read_ledger,
    run_migrations,
)

NEXT_VERSION = "9.9.9"


def _add_column(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE tasks ADD COLUMN extra TEXT")


def _boom(conn: sqlite3.Connection) -> None:
    conn.execute("ALTER TABLE tasks ADD COLUMN extra TEXT")
    raise RuntimeError("injected")


UPGRADE = (MigrationSpec("wf-up", WORKFLOW_SCHEMA_VERSION, NEXT_VERSION, _add_column),)
FAILING = (MigrationSpec("wf-up", WORKFLOW_SCHEMA_VERSION, NEXT_VERSION, _boom),)


def _make_db(path: Path, version: str = WORKFLOW_SCHEMA_VERSION) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(build_workflow_schema_sql())
        conn.execute(
            "INSERT INTO workflow_schema_version (version) VALUES (?)", (version,)
        )
        conn.execute(
            "INSERT INTO tasks (task_id, workflow_version, task_nonce)"
            " VALUES ('t1', '1', 'k1'), ('t2', '1', 'k2')"
        )
        conn.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id)"
            " VALUES ('a1', 't1', 's1')"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _query(path: Path, sql: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(path)
    try:
        return [tuple(r) for r in conn.execute(sql)]
    finally:
        conn.close()


def test_registry_is_one_linear_chain_ending_at_the_current_version() -> None:
    ids = [spec.migration_id for spec in MIGRATIONS]
    assert len(ids) == len(set(ids))
    for earlier, later in zip(MIGRATIONS, MIGRATIONS[1:], strict=False):
        assert earlier.to_version == later.from_version
    if MIGRATIONS:
        assert MIGRATIONS[-1].to_version == WORKFLOW_SCHEMA_VERSION


def test_read_version_returns_the_newest_row_on_a_timestamp_tie(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    conn = connect_workflow(str(db))
    try:
        conn.execute("DELETE FROM workflow_schema_version")
        conn.executemany(
            "INSERT INTO workflow_schema_version (version, applied_at)"
            " VALUES (?, '2026-01-01T00:00:00Z')",
            [("1.0.0",), ("2.0.0",)],
        )
        assert read_workflow_version(conn) == "2.0.0"
        write_workflow_version(conn, "3.0.0")
        conn.commit()
        assert read_workflow_version(conn) == "3.0.0"
    finally:
        conn.close()


def test_read_version_is_none_without_the_version_table() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        assert read_workflow_version(conn) is None
    finally:
        conn.close()


def test_verify_shape_accepts_the_canonical_schema_and_detects_drift() -> None:
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(build_workflow_schema_sql())
        verify_workflow_shape(conn, WORKFLOW_SCHEMA_VERSION)
        verify_workflow_shape(conn, NEXT_VERSION)  # no canonical DDL: not checked
        conn.execute("ALTER TABLE tasks ADD COLUMN extra TEXT")
        with pytest.raises(RuntimeError, match="shape differs"):
            verify_workflow_shape(conn, WORKFLOW_SCHEMA_VERSION)
    finally:
        conn.close()


def test_registered_upgrade_preserves_rows_and_records_the_ledger(
    tmp_path: Path,
) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    report = run_migrations(
        db, WORKFLOW_DOMAIN, UPGRADE, NEXT_VERSION, tmp_path / "backups"
    )
    assert report.applied == ("wf-up",)
    assert _query(db, "SELECT task_id FROM tasks ORDER BY task_id") == [
        ("t1",),
        ("t2",),
    ]
    assert _query(db, "SELECT attempt_id FROM attempts") == [("a1",)]
    conn = sqlite3.connect(db)
    try:
        assert read_workflow_version(conn) == NEXT_VERSION
        assert read_ledger(conn) == ["wf-up"]
    finally:
        conn.close()


def test_failure_leaves_the_original_intact(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    with pytest.raises(MigrationFailedError, match="wf-up"):
        run_migrations(db, WORKFLOW_DOMAIN, FAILING, NEXT_VERSION, tmp_path / "b")
    conn = sqlite3.connect(db)
    try:
        assert read_workflow_version(conn) == WORKFLOW_SCHEMA_VERSION
        assert read_ledger(conn) == []
    finally:
        conn.close()
    columns = {r[1] for r in _query(db, "PRAGMA table_info(tasks)")}
    assert "extra" not in columns
    assert _query(db, "SELECT COUNT(*) FROM tasks") == [(2,)]


def test_backup_failure_before_migration_leaves_the_original_intact(
    tmp_path: Path,
) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    before = _sha(db)
    with patch("shared.db_migrations._integrity_ok", return_value=(False, "corrupt")):
        with pytest.raises(MigrationRefusedError, match="integrity"):
            run_migrations(db, WORKFLOW_DOMAIN, UPGRADE, NEXT_VERSION, tmp_path / "b")
    assert _sha(db) == before


def test_cli_status_works_on_a_database_without_a_ledger(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE schema_migrations")
    conn.commit()
    conn.close()
    assert main(["--status", "--db-path", str(db)]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"version: {WORKFLOW_SCHEMA_VERSION}" in out
    assert "ledger: absent" in out


def test_cli_dry_run_is_byte_identical_and_apply_migrates(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    before = _sha(db)
    args = ["--db-path", str(db), "--backup-dir", str(tmp_path / "backups")]
    with (
        patch("db.migrate_db.MIGRATIONS", UPGRADE),
        patch("db.migrate_db.WORKFLOW_SCHEMA_VERSION", NEXT_VERSION),
    ):
        assert main(["--dry-run", *args]) == EXIT_OK
        assert _sha(db) == before
        assert not (tmp_path / "backups").exists()
        assert main(["--apply", *args]) == EXIT_OK
    assert _sha(db) != before
    assert len(list((tmp_path / "backups").glob("*.sqlite"))) == 1


def test_cli_apply_reports_a_failed_migration_with_exit_3(tmp_path: Path) -> None:
    db = _make_db(tmp_path / "w.sqlite")
    with (
        patch("db.migrate_db.MIGRATIONS", FAILING),
        patch("db.migrate_db.WORKFLOW_SCHEMA_VERSION", NEXT_VERSION),
    ):
        code = main(
            ["--apply", "--db-path", str(db), "--backup-dir", str(tmp_path / "b")]
        )
    assert code == EXIT_FAILED


@pytest.mark.parametrize("version", ["0.0.1", "99.0.0"])
def test_cli_refuses_unknown_path_and_downgrade_with_exit_2(
    tmp_path: Path, version: str
) -> None:
    db = _make_db(tmp_path / "w.sqlite", version=version)
    before = _sha(db)
    code = main(["--apply", "--db-path", str(db), "--backup-dir", str(tmp_path / "b")])
    assert code == EXIT_REFUSED
    assert _sha(db) == before


def test_cli_refuses_a_missing_database(tmp_path: Path) -> None:
    assert main(["--apply", "--db-path", str(tmp_path / "none.sqlite")]) == EXIT_REFUSED
    assert (
        main(["--status", "--db-path", str(tmp_path / "none.sqlite")]) == EXIT_REFUSED
    )
