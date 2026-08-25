"""Regression tests for scripts/eventbus/db.py::_migrate().

Requires SQLite >= 3.35.0 for ALTER TABLE ... DROP COLUMN support.
Current environment: SQLite 3.46.1 (confirmed).
"""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from scripts.eventbus.db import _migrate


@pytest.fixture
def tmp_conn(tmp_path: Path) -> Generator[sqlite3.Connection]:
    """File-based SQLite connection matching the on-disk I/O path."""
    db_path = tmp_path / "eventbus.db"
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def pre_migration_conn(tmp_conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """SQLite connection with the pre-migration events table schema.

    Has retry_count column present; delivery_failure_count, dlq_requeue_count,
    and the two DLQ indexes absent. Also has dlq_at and seq columns needed by
    the DLQ index creation step.
    """
    conn = tmp_conn
    conn.execute(
        """
        CREATE TABLE events (
            event_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            payload TEXT NOT NULL,
            published_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            dlq_at TEXT,
            seq INTEGER
        )
        """
    )
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


class TestMigrateAddsNewColumns:
    def test_migrate_adds_new_columns(
        self, pre_migration_conn: sqlite3.Connection
    ) -> None:
        _migrate(pre_migration_conn)
        info = pre_migration_conn.execute("PRAGMA table_info(events)").fetchall()
        cols = {row[1] for row in info}
        assert "delivery_failure_count" in cols
        assert "dlq_requeue_count" in cols
        assert "retry_count" not in cols

    def test_migrate_creates_dlq_indexes(
        self, pre_migration_conn: sqlite3.Connection
    ) -> None:
        _migrate(pre_migration_conn)
        indexes = pre_migration_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
        ).fetchall()
        idx_names = {row[0] for row in indexes}
        assert "idx_events_dlq_at" in idx_names
        assert "idx_events_dlq_seq" in idx_names

    def test_migrate_does_not_raise_on_already_migrated_table(
        self, tmp_conn: sqlite3.Connection
    ) -> None:
        tmp_conn.execute(
            """
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                published_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                delivery_failure_count INTEGER NOT NULL DEFAULT 0,
                dlq_requeue_count INTEGER NOT NULL DEFAULT 0,
                dlq_at TEXT,
                seq INTEGER
            )
            """
        )
        tmp_conn.commit()
        _migrate(tmp_conn)

    def test_migrate_preserves_data(
        self, pre_migration_conn: sqlite3.Connection
    ) -> None:
        pre_migration_conn.execute(
            "INSERT INTO events (event_id, topic, payload, published_at, status, retry_count)"
            " VALUES ('evt-1', 'test-topic', '{\"key\": \"value\"}', '2024-01-01T00:00:00Z', 'pending', 0)"
        )
        pre_migration_conn.commit()
        _migrate(pre_migration_conn)
        row = pre_migration_conn.execute(
            "SELECT event_id, topic, payload, published_at, status,"
            " delivery_failure_count, dlq_requeue_count FROM events WHERE event_id='evt-1'"
        ).fetchone()
        assert row is not None
        assert row[0] == "evt-1"
        assert row[1] == "test-topic"
        assert row[2] == '{"key": "value"}'
        assert row[3] == "2024-01-01T00:00:00Z"
        assert row[4] == "pending"
        assert row[5] == 0
        assert row[6] == 0

    def test_migrate_is_idempotent(
        self, pre_migration_conn: sqlite3.Connection
    ) -> None:
        _migrate(pre_migration_conn)
        first_cols = {
            row[1]
            for row in pre_migration_conn.execute(
                "PRAGMA table_info(events)"
            ).fetchall()
        }
        _migrate(pre_migration_conn)
        second_cols = {
            row[1]
            for row in pre_migration_conn.execute(
                "PRAGMA table_info(events)"
            ).fetchall()
        }
        assert first_cols == second_cols


class TestApplyEventbusPragmas:
    def test_apply_eventbus_pragmas_sets_all_four_pragmas(
        self, tmp_conn: sqlite3.Connection
    ) -> None:
        from scripts.eventbus.db import _apply_eventbus_pragmas

        _apply_eventbus_pragmas(tmp_conn, busy_timeout_ms=9999)
        journal_mode = tmp_conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal_mode == "wal"
        synchronous = tmp_conn.execute("PRAGMA synchronous").fetchone()[0]
        assert synchronous == 1
        busy_timeout = tmp_conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert busy_timeout == 9999
        foreign_keys = tmp_conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert foreign_keys == 1
