"""tests/db/test_eventbus_schema_equivalence.py

eventbus.sqlite has one DDL source, scripts/eventbus/schema.sql (ADR-008 INV-04).
create_schema() reads that file, so the bulk-initialization path and the service's
first-start path must produce the same schema, and an existing database must be
migrated to it.
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
    # Service start-up on a database created by the bulk path applies _migrate().
    bulk_then_service = open_db(str(tmp_path / "bulk.sqlite"))

    assert _schema(bulk) == _schema(service)
    assert _schema(bulk_then_service) == _schema(service)


def test_existing_database_without_consumer_delivery_index_is_migrated(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy.sqlite"
    legacy = sqlite3.connect(path)
    legacy.executescript(build_eventbus_schema_sql())
    legacy.execute("DROP INDEX idx_consumer_delivery_consumer_ack")
    legacy.commit()
    legacy.close()

    migrated = open_db(str(path))
    names = {
        row[0]
        for row in migrated.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    assert "idx_consumer_delivery_consumer_ack" in names
