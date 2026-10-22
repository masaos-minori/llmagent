"""Pragma regression tests for scripts/eventbus/schema.py::_apply_eventbus_pragmas.

Verifies the four pragmas the EventBus layer sets on its SQLite connections.
"""

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def tmp_conn(tmp_path: Path) -> Generator[sqlite3.Connection]:
    """File-based SQLite connection matching the on-disk I/O path."""
    db_path = tmp_path / "eventbus.db"
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


class TestApplyEventbusPragmas:
    def test_apply_eventbus_pragmas_sets_all_four_pragmas(
        self, tmp_conn: sqlite3.Connection
    ) -> None:
        from eventbus.schema import _apply_eventbus_pragmas

        _apply_eventbus_pragmas(tmp_conn, busy_timeout_ms=9999)
        journal_mode = tmp_conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert journal_mode == "wal"
        synchronous = tmp_conn.execute("PRAGMA synchronous").fetchone()[0]
        assert synchronous == 1
        busy_timeout = tmp_conn.execute("PRAGMA busy_timeout").fetchone()[0]
        assert busy_timeout == 9999
        foreign_keys = tmp_conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert foreign_keys == 1
