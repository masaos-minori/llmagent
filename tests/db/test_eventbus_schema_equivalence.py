"""tests/db/test_eventbus_schema_equivalence.py

eventbus.sqlite has one DDL source, scripts/eventbus/schema.sql (ADR-008 INV-04).
create_schema() reads that file, so the bulk-initialization path and the service's
first-start path must produce the same schema, and reopening an existing database
leaves it unchanged.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from db.schema_sql import EVENTBUS_SCHEMA_SQL_PATH, build_eventbus_schema_sql
from eventbus.db_conn import open_db
from eventbus.schema import _SCHEMA_PATH


def _schema(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    return [(t, n, " ".join((s or "").split())) for t, n, s in rows]


def test_db_layer_reads_the_eventbus_schema_file() -> None:
    assert EVENTBUS_SCHEMA_SQL_PATH.resolve() == _SCHEMA_PATH.resolve()
    assert build_eventbus_schema_sql() == _SCHEMA_PATH.read_text(encoding="utf-8")


def test_bootstrap_paths_produce_same_schema(tmp_path: Path) -> None:
    bulk = sqlite3.connect(tmp_path / "bulk.sqlite")
    bulk.executescript(build_eventbus_schema_sql())
    service = open_db(str(tmp_path / "service.sqlite"))
    # Service start-up on an existing database leaves it unchanged.
    bulk_then_service = open_db(str(tmp_path / "bulk.sqlite"))

    assert _schema(bulk) == _schema(service)
    assert _schema(bulk_then_service) == _schema(service)


def test_existing_database_is_unchanged_on_restart(tmp_path: Path) -> None:
    """Reopening a current database runs _init_schema(), which now leaves it
    untouched; the schema listing and a stored row are identical before and after."""
    path = tmp_path / "eventbus.sqlite"
    conn = open_db(str(path))
    conn.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at)"
        " VALUES ('evt-1', 'test-topic', '{}', 'producer-1',"
        " '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    before_schema = _schema(conn)
    before_row = conn.execute(
        "SELECT event_id, topic, payload, producer FROM events WHERE event_id='evt-1'"
    ).fetchone()
    conn.close()

    reopened = open_db(str(path))
    assert _schema(reopened) == before_schema
    reopened_row = reopened.execute(
        "SELECT event_id, topic, payload, producer FROM events WHERE event_id='evt-1'"
    ).fetchone()
    assert reopened_row == before_row
