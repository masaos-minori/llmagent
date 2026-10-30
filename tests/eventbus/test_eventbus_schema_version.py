"""tests/eventbus/test_eventbus_schema_version.py

eventbus.sqlite carries a schema version (PRAGMA user_version stamped by
schema.sql). open_db() refuses a database stamped with another version, stamps an
unstamped database only when its tables match schema.sql, and refuses the rest.

The version is pinned to 4 (the forward-only migration ledger added by
dbmig001; version 3 enforced the date-time format check via rfc3339-validator
plus removed the dead published_at schema default; version 2 was the
idx_events_redelivered_from unique index bump); a database still stamped 1 must
be refused with the recreate message.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from db.schema_sql import eventbus_schema_version
from eventbus.db_conn import open_db
from eventbus.schema import _SCHEMA_PATH, _expected_schema_version


def _version(path: Path) -> int:
    conn = sqlite3.connect(path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def test_db_layer_and_service_agree_on_the_version() -> None:
    expected = _expected_schema_version(_SCHEMA_PATH.read_text())
    assert eventbus_schema_version() == expected


def test_new_database_is_stamped(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    assert _version(path) == eventbus_schema_version()


def test_mismatched_version_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 99")
    raw.close()
    with pytest.raises(RuntimeError, match="recreate the database"):
        open_db(str(path))


def test_unstamped_current_database_is_stamped(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 0")
    raw.close()
    open_db(str(path)).close()
    assert _version(path) == eventbus_schema_version()


def test_unstamped_old_shape_is_refused_and_left_unstamped(tmp_path: Path) -> None:
    path = tmp_path / "eventbus.sqlite"
    raw = sqlite3.connect(path)
    raw.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT)")
    raw.close()
    with pytest.raises(RuntimeError, match="recreate the database"):
        open_db(str(path))
    assert _version(path) == 0


def test_schema_version_is_pinned_to_four() -> None:
    """Contract lock for this plan: schema.sql must stamp PRAGMA user_version = 4.

    dbmig001 added the forward-only migration ledger (schema_migrations) to the
    EventBus baseline, which is a schema change that moves the fingerprint source
    from version 3 to version 4 (see scripts/eventbus/migrations.py bootstrap).
    """
    assert eventbus_schema_version() == 4


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
    with pytest.raises(RuntimeError, match="recreate the database"):
        open_db(str(path))


def test_registered_v3_database_migrates_at_startup(tmp_path: Path) -> None:
    """A database at the pre-ledger baseline (user_version 3) migrates at startup.

    The registered 3 -> 4 bootstrap step runs through the shared runner gate-gated
    (row 03 wiring): startup succeeds, the ledger records the step, and the shared
    fingerprint passes. This is the dbmig001 behaviour that replaces today's hard
    refusal for a lower-but-registered version.
    """
    path = tmp_path / "eventbus.sqlite"
    # Seed a realistic pre-migration database: the full current shape minus the
    # ledger table, stamped at the pre-ledger baseline (user_version 3).
    seed = sqlite3.connect(str(path))
    try:
        seed.execute("PRAGMA journal_mode=WAL")  # nosec B704 — WAL is required for the gate
        seed.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
        seed.commit()
        seed.execute("DROP TABLE schema_migrations")
        seed.execute("PRAGMA user_version = 3")  # nosec B608 — fixed test int
        seed.commit()
    finally:
        seed.close()

    migrated = open_db(str(path))
    try:
        assert _version(path) == 4
        rows = migrated.execute(
            "SELECT id, from_version, to_version FROM schema_migrations ORDER BY id"
        ).fetchall()
        assert [(r[0], r[1], r[2]) for r in rows] == [
            ("eventbus_ledger_baseline", 3, 4)
        ]
    finally:
        migrated.close()


def test_future_version_is_refused(tmp_path: Path) -> None:
    """A database stamped beyond the baseline (user_version 5) refuses at startup.

    No registered forward path reaches a target below the current version, so the
    runner raises an unknown-path refusal and startup keeps the recreate guidance
    (fail-closed, REQ-003/REQ-005).
    """
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()
    raw = sqlite3.connect(path)
    raw.execute("PRAGMA user_version = 5")
    raw.close()
    with pytest.raises(RuntimeError, match="recreate the database"):
        open_db(str(path))
