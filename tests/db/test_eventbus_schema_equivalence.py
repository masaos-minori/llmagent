"""tests/db/test_eventbus_schema_equivalence.py

eventbus.sqlite has one DDL source, scripts/eventbus/schema.sql (ADR-008 INV-04).
create_schema() reads that file, so the bulk-initialization path and the service's
first-start path must produce the same schema, and reopening an existing database
leaves it unchanged.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from db.schema_sql import EVENTBUS_SCHEMA_SQL_PATH, build_eventbus_schema_sql
from eventbus.db_conn import open_db
from eventbus.migrations import REGISTRY
from eventbus.schema import _SCHEMA_PATH
from shared import eventbus_schema_fingerprint
from shared.db_migrations import MigrationRunner, read_ledger
from shared.eventbus_schema_fingerprint import (
    apply_schema_in_memory,
    assert_matches,
    build_fingerprint,
    validate_canonical,
)


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


def _no_op_backup_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Passing backup verifier (the convergence test never restores from a backup)."""


def _fk_entry_count(conn: sqlite3.Connection, table: str) -> int:
    return len(conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall())  # nosec B608 — table name from a fixed test list


def _migrated_v6_db(db_path: Path) -> sqlite3.Connection:
    """Build a version-6 database through the registered 3 -> 4 -> 5 -> 6 chain.

    The scratch start is the current schema.sql with the version-4 ledger and
    version-5 dlq_outbox objects removed and the stamp reset to 3, i.e. the
    pre-ledger baseline shape. dlq_outbox rows (all three status values, NULL
    optionals) are seeded between the 4 -> 5 and 5 -> 6 steps so the FK-dedup
    rebuild must carry real data across the create-copy-drop-rename.
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("DROP TABLE dlq_outbox")  # nosec B608 — fixed test DDL
    conn.execute("DROP TABLE schema_migrations")  # nosec B608 — fixed test DDL
    conn.execute("PRAGMA user_version = 3")  # nosec B608 — fixed test int
    for i in (1, 2, 3):
        conn.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            f" VALUES ('evt-{i}', 't-{i}', '{{}}', 'p', '2026-01-01T00:00:00Z')"  # nosec B608 — fixed test values
        )
    conn.commit()
    runner = MigrationRunner()
    runner.apply(
        conn, runner.plan(3, read_ledger(conn), REGISTRY, 5), _no_op_backup_verifier
    )
    conn.executescript(
        "INSERT INTO dlq_outbox (event_id, requested_at, status) VALUES"
        " ('evt-1', '2026-01-01T00:00:00Z', 'pending'),"
        " ('evt-2', '2026-01-01T00:00:00Z', 'done'),"
        " ('evt-3', '2026-01-01T00:00:00Z', 'failed');"
    )
    conn.commit()
    runner.apply(
        conn, runner.plan(5, read_ledger(conn), REGISTRY, 6), _no_op_backup_verifier
    )
    return conn


def test_fresh_v6_and_migrated_v6_are_fingerprint_equal(tmp_path: Path) -> None:
    """AC-005/AC-006: the registered 3 -> 4 -> 5 -> 6 chain converges on the
    fresh canonical fingerprint, including a single dlq_outbox foreign key."""
    fresh = apply_schema_in_memory()
    migrated = _migrated_v6_db(tmp_path / "migrated.sqlite")
    try:
        assert build_fingerprint(migrated) == build_fingerprint(fresh)
        assert _fk_entry_count(migrated, "dlq_outbox") == 1
        assert _fk_entry_count(fresh, "dlq_outbox") == 1
        assert (
            migrated.execute("SELECT COUNT(*) FROM dlq_outbox").fetchone()[0] == 3
        )  # seeded rows survived the rebuild
        assert int(migrated.execute("PRAGMA user_version").fetchone()[0]) == 6
        validate_canonical(migrated)
    finally:
        fresh.close()
        migrated.close()


def test_fingerprint_refuses_an_added_view() -> None:
    conn = apply_schema_in_memory()
    try:
        conn.execute("CREATE VIEW event_topics AS SELECT DISTINCT topic FROM events")
        with pytest.raises(RuntimeError):
            assert_matches(conn)
    finally:
        conn.close()


def test_fingerprint_detects_altered_partial_index_predicate() -> None:
    conn = apply_schema_in_memory()
    try:
        conn.execute("DROP INDEX idx_events_redelivered_from")  # nosec B608 — fixed test DDL
        conn.execute(
            "CREATE UNIQUE INDEX idx_events_redelivered_from ON events(redelivered_from)"
            " WHERE redelivered_from IS NOT NULL AND redelivered_from <> 'x'"  # nosec B608 — fixed test DDL
        )
        conn.commit()
        with pytest.raises(RuntimeError):
            assert_matches(conn)
    finally:
        conn.close()


def test_validate_canonical_passes_a_canonical_connection() -> None:
    conn = apply_schema_in_memory()
    try:
        validate_canonical(conn)  # no false positive on the current canonical shape
    finally:
        conn.close()


def test_validate_canonical_refuses_a_version_mismatch() -> None:
    conn = apply_schema_in_memory()
    try:
        conn.execute("PRAGMA user_version = 99")  # nosec B608 — fixed test int
        with pytest.raises(RuntimeError, match="user_version 99"):
            validate_canonical(conn)
    finally:
        conn.close()


def test_version_gate_refuses_a_schema_file_without_a_stamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A schema.sql missing its PRAGMA stamp fails the version gate closed."""
    stampless = tmp_path / "stampless.sql"
    stampless.write_text(
        "CREATE TABLE events (seq INTEGER PRIMARY KEY);", encoding="utf-8"
    )
    monkeypatch.setattr(eventbus_schema_fingerprint, "_SCHEMA_PATH", stampless)
    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(RuntimeError, match="no PRAGMA user_version stamp"):
            validate_canonical(conn)
    finally:
        conn.close()
