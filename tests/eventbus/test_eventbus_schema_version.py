"""tests/eventbus/test_eventbus_schema_version.py

eventbus.sqlite carries a schema version (PRAGMA user_version stamped by
schema.sql). open_db() refuses a database stamped with another version, stamps an
unstamped database only when its tables match schema.sql, and refuses the rest.
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
