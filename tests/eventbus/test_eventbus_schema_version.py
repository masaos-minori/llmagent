"""tests/eventbus/test_eventbus_schema_version.py

eventbus.sqlite no longer carries a schema version: open_db() accepts a missing
database (created from schema.sql) or an existing database whose whole shape
matches the shared schema fingerprint of that DDL. Every other existing database
is refused before any mutation and left byte-identical (REQ-003/REQ-004):
automatic migration and version stamping are not supported, the operator
archives and recreates.

Historical note: earlier revisions of this file gated on PRAGMA user_version
(pinned to 6). The fingerprint-cutover removed the version gate entirely; the
file name is kept for history, and every refusal here is a fingerprint refusal.
"""

from __future__ import annotations

import gc
import hashlib
import sqlite3
from pathlib import Path

import pytest
from eventbus.db_conn import open_db


def _sha256(path: Path) -> str:
    """File hash: the byte-fact a refusal must not change (AC-005)."""
    gc.collect()  # finalize any connection left open by a refused open_db()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_wal(path: Path, ddl: str | None = None) -> None:
    """Seed a WAL-mode database so a refused open_db() cannot change the header.

    Production databases already run in WAL; the refused open only re-applies
    the (no-op) journal_mode pragma, keeping the file byte-identical.
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")  # nosec B704 — fixed WAL seeding
        if ddl is not None:
            conn.executescript(ddl)
        conn.commit()
    finally:
        conn.close()


def _refused_unchanged(path: Path, match: str) -> None:
    """Assert open_db() refuses and leaves the database byte-identical."""
    before = _sha256(path)
    with pytest.raises(RuntimeError, match=match):
        open_db(str(path))
    assert _sha256(path) == before


def test_new_database_is_created_and_marker_free(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    conn = sqlite3.connect(path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()
    assert "schema_migrations" not in tables
    assert "workflow_schema_version" not in tables


def test_old_shape_is_refused_and_left_unchanged(tmp_path: Path) -> None:
    """A pre-cutover (old-shape) database is refused by the fingerprint gate and
    left byte-identical (REQ-003/REQ-004)."""
    path = tmp_path / "eventbus.sqlite"
    _seed_wal(path, "CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT);")
    _refused_unchanged(path, "does not match the current schema")


def test_new_database_has_redelivered_from_index(tmp_path: Path) -> None:
    """A fresh open_db() database must carry the partial unique redelivery index."""
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    try:
        row = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' "
            "AND name='idx_events_redelivered_from'"
        ).fetchone()
    finally:
        raw.close()
    assert row is not None
    sql = row[0]
    assert "UNIQUE" in sql
    assert "WHERE redelivered_from IS NOT NULL" in sql


def test_malformed_shape_is_refused_and_left_unchanged(tmp_path: Path) -> None:
    """A current-shape-minus-one-column database fails the fingerprint gate and
    is left as-is (REQ-004 / AC-005)."""
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("ALTER TABLE events DROP COLUMN consumer_id")  # nosec B608 — fixed test DDL
    raw.commit()
    raw.close()
    _refused_unchanged(path, "columns differ")
    conn = sqlite3.connect(path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
    finally:
        conn.close()
    assert "consumer_id" not in columns  # deviation preserved, nothing repaired


def test_extra_table_is_refused(tmp_path: Path) -> None:
    """An extra table (the mechanism the removed marker-table gate caught) is
    refused by the fingerprint comparison."""
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)")
    raw.commit()
    raw.close()
    _refused_unchanged(path, "unexpected table 'schema_migrations'")
