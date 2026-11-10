"""tests/eventbus/test_eventbus_schema_version.py

eventbus.sqlite carries a schema version (PRAGMA user_version stamped by
schema.sql). open_db() accepts only a database stamped with the current version
whose shape matches the shared schema fingerprint. Every other existing database
— including an unstamped one (user_version 0) — is refused before any mutation
and left byte-identical (REQ-003/REQ-004): automatic migration and version
stamping are not supported, the operator archives and recreates. A missing
database is created and stamped through the canonical schema.sql DDL.

The version is pinned to 6 (ebschema001 rebuilt dlq_outbox down to a single inline
FK via the registered 5 -> 6 step; dlqbox001 added the dlq_outbox table at version
5; version 4 added the forward-only migration ledger schema_migrations via dbmig001;
version 3 enforced the date-time format check via rfc3339-validator plus removed the
dead published_at schema default; version 2 was the idx_events_redelivered_from
unique index bump); a database still stamped 1 must be refused with the
archive-and-recreate message.
"""

from __future__ import annotations

import gc
import hashlib
import sqlite3
from pathlib import Path

import pytest
from eventbus.db_conn import open_db
from eventbus.db_tools import schema_version as eventbus_schema_version
from eventbus.schema import _SCHEMA_PATH, _expected_schema_version


def _version(path: Path) -> int:
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def _sha256(path: Path) -> str:
    """File hash: the byte-fact a refusal must not change (AC-005)."""
    gc.collect()  # finalize any connection left open by a refused open_db()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_wal(path: Path, ddl: str | None = None, *, stamp: int | None = None) -> None:
    """Seed a WAL-mode database so a refused open_db() cannot change the header.

    Production databases already run in WAL; the refused open only re-applies
    the (no-op) journal_mode pragma, keeping the file byte-identical.
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")  # nosec B704 — fixed WAL seeding
        if ddl is not None:
            conn.executescript(ddl)
        if stamp is not None:
            conn.execute(f"PRAGMA user_version = {stamp}")  # nosec B608 — fixed test int
        conn.commit()
    finally:
        conn.close()


def _refused_unchanged(path: Path, match: str) -> None:
    """Assert open_db() refuses and leaves the database byte-identical."""
    before = _sha256(path)
    with pytest.raises(RuntimeError, match=match):
        open_db(str(path))
    assert _sha256(path) == before


def test_db_layer_and_service_agree_on_the_version() -> None:
    expected = _expected_schema_version(_SCHEMA_PATH.read_text())
    assert eventbus_schema_version() == expected


def test_new_database_is_stamped_and_marker_free(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    assert _version(path) == eventbus_schema_version()
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


def test_mismatched_version_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 99")
    raw.close()
    _refused_unchanged(path, "does not match the current schema")


def test_unstamped_current_shape_is_refused_and_left_unstamped(tmp_path: Path) -> None:
    """A current-shape database left unstamped (user_version 0) is refused and
    stays unstamped: version stamping is not supported (REQ-003)."""
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 0")
    raw.close()
    _refused_unchanged(path, "does not match the current schema")
    assert _version(path) == 0


def test_unstamped_old_shape_is_refused_and_left_unstamped(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    _seed_wal(path, "CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT);")
    _refused_unchanged(path, "does not match the current schema")
    assert _version(path) == 0


def test_schema_version_is_pinned_to_six() -> None:
    """Contract lock: schema.sql must stamp PRAGMA user_version = 6.

    dbmig001 added the forward-only migration ledger (schema_migrations) moving
    version 3 -> 4; dlqbox001 added the dlq_outbox table moving version 4 -> 5;
    ebschema001 rebuilt dlq_outbox down to a single inline FK moving version
    5 -> 6.
    """
    assert eventbus_schema_version() == 6


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


def test_database_stamped_one_is_refused(tmp_path: Path) -> None:
    """A database still stamped version 1 (pre-index era) is refused by open_db().

    Stamping 1 onto a current-shape file isolates the version gate itself: the
    gate runs before any shape comparison, so this proves the 1 -> 2 bump makes
    pre-index databases unusable rather than silently missing the index.
    """
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 1")
    raw.close()
    _refused_unchanged(path, "does not match the current schema")


def test_registered_era_version_is_refused(tmp_path: Path) -> None:
    """A database at the pre-cutover baseline (user_version 5) is refused.

    The registered 5 -> 6 migration path no longer exists (REQ-003): a lower-
    but-registered version is refused with the archive-and-recreate guidance
    and left byte-identical.
    """
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 5")  # nosec B608 — fixed test int
    raw.close()
    _refused_unchanged(path, "does not match the current schema")
    assert _version(path) == 5


def test_malformed_current_version_is_refused(tmp_path: Path) -> None:
    """A current-shape-minus-one-column database stamped 6 fails the fingerprint
    gate and is left as-is (REQ-004 / AC-005)."""
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
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()
    assert "consumer_id" not in columns  # deviation preserved, nothing repaired
    assert version == eventbus_schema_version()


def test_future_version_is_refused(tmp_path: Path) -> None:
    """A database stamped beyond the baseline (user_version 7) refuses at startup.

    No automatic path reaches or accepts a version above the current schema, so
    startup keeps the archive-and-recreate guidance (fail-closed, REQ-003).
    """
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 7")  # nosec B608 — fixed test int
    raw.close()
    _refused_unchanged(path, "does not match the current schema")
