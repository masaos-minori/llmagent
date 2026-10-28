"""tests/eventbus/test_eventbus_schema_version.py

eventbus.sqlite carries a schema version (PRAGMA user_version stamped by
schema.sql). open_db() refuses a database stamped with another version, stamps an
unstamped database only when its tables match schema.sql, and refuses the rest.

The version is pinned to 2 (the idx_events_redelivered_from unique index bump); a
database still stamped 1 must be refused with the recreate message.
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


def test_schema_version_is_pinned_to_two() -> None:
    """Contract lock for this plan: schema.sql must stamp PRAGMA user_version = 2."""
    assert eventbus_schema_version() == 2


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
