"""tests/test_sqlite_helper.py
Unit tests for db/helper.py: SQLiteHelper connection management and transactions.
"""

from __future__ import annotations

import sqlite3

import pytest
from db.helper import SQLiteHelper

# ── In-memory DB helper ───────────────────────────────────────────────────────


class _InMemoryHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conn = conn  # public attribute used by begin_* methods

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _InMemoryHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _InMemoryHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Open a real in-memory SQLite connection."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)"
    )
    c.commit()
    return c


@pytest.fixture
def helper(conn: sqlite3.Connection) -> SQLiteHelper:
    """Create a SQLiteHelper with an in-memory connection."""
    h = SQLiteHelper("rag")
    h.conn = conn
    return h


class TestBeginImmediateRollback:
    def test_rollback_on_value_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when ValueError is raised inside the block."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            with helper.begin_immediate():
                _raise_value_error()

    def test_rollback_on_runtime_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when RuntimeError is raised inside the block."""

        def _raise_runtime_error() -> None:
            raise RuntimeError("test error")

        with pytest.raises(RuntimeError, match="test error"):
            with helper.begin_immediate():
                _raise_runtime_error()

    def test_rollback_on_type_error(self, helper: SQLiteHelper) -> None:
        """begin_immediate() rolls back when TypeError is raised inside the block."""

        def _raise_type_error() -> None:
            raise TypeError("test error")

        with pytest.raises(TypeError, match="test error"):
            with helper.begin_immediate():
                _raise_type_error()

    def test_subsequent_insert_after_rollback(self, helper: SQLiteHelper) -> None:
        """A subsequent insert can run after rollback — no dangling transaction."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            with helper.begin_immediate():
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'before-error')"
                )
                _raise_value_error()

        # Verify the transaction was rolled back — insert should not have happened
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert rows == []

        # Subsequent insert should succeed
        with helper.begin_immediate():
            helper.execute(
                "INSERT INTO test_table (id, value) VALUES (2, 'after-rollback')"
            )
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=2")
        assert len(rows) == 1
        assert rows[0]["value"] == "after-rollback"

    def test_sqlite3_error_still_rolled_back(self, helper: SQLiteHelper) -> None:
        """Existing sqlite3 error behavior remains unchanged — rollback on sqlite3.Error."""
        with pytest.raises(sqlite3.IntegrityError):
            with helper.begin_immediate():
                helper.execute("INSERT INTO test_table (id, value) VALUES (1, 'first')")
                # Insert duplicate to trigger IntegrityError
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'duplicate')"
                )

        # Verify the transaction was rolled back — no inserts should exist
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert len(rows) == 0


class TestBeginExclusiveRollback:
    def test_rollback_on_value_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when ValueError is raised inside the block."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            with helper.begin_exclusive():
                _raise_value_error()

    def test_rollback_on_runtime_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when RuntimeError is raised inside the block."""

        def _raise_runtime_error() -> None:
            raise RuntimeError("test error")

        with pytest.raises(RuntimeError, match="test error"):
            with helper.begin_exclusive():
                _raise_runtime_error()

    def test_rollback_on_type_error(self, helper: SQLiteHelper) -> None:
        """begin_exclusive() rolls back when TypeError is raised inside the block."""

        def _raise_type_error() -> None:
            raise TypeError("test error")

        with pytest.raises(TypeError, match="test error"):
            with helper.begin_exclusive():
                _raise_type_error()

    def test_subsequent_insert_after_rollback(self, helper: SQLiteHelper) -> None:
        """A subsequent insert can run after rollback — no dangling transaction."""

        def _raise_value_error() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            with helper.begin_exclusive():
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'before-error')"
                )
                _raise_value_error()

        # Verify the transaction was rolled back — insert should not have happened
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert rows == []

        # Subsequent insert should succeed
        with helper.begin_exclusive():
            helper.execute(
                "INSERT INTO test_table (id, value) VALUES (2, 'after-rollback')"
            )
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=2")
        assert len(rows) == 1
        assert rows[0]["value"] == "after-rollback"

    def test_sqlite3_error_still_rolled_back(self, helper: SQLiteHelper) -> None:
        """Existing sqlite3 error behavior remains unchanged — rollback on sqlite3.Error."""
        with pytest.raises(sqlite3.IntegrityError):
            with helper.begin_exclusive():
                helper.execute("INSERT INTO test_table (id, value) VALUES (1, 'first')")
                # Insert duplicate to trigger IntegrityError
                helper.execute(
                    "INSERT INTO test_table (id, value) VALUES (1, 'duplicate')"
                )

        # Verify the transaction was rolled back — no inserts should exist
        rows = helper.fetchall("SELECT * FROM test_table WHERE id=1")
        assert len(rows) == 0


class TestSQLiteHelperMissingDbPathMessage:
    def test_missing_workflow_db_path_mentions_agent_toml(self) -> None:
        """Missing workflow_db_path must mention agent.toml, not common.toml."""
        from unittest.mock import patch

        from db.config import DbConfig

        cfg = DbConfig(
            rag_db_path="/tmp/rag.sqlite",
            session_db_path="/tmp/session.sqlite",
            workflow_db_path="/opt/llm/db/workflow.sqlite",
            eventbus_db_path="/tmp/eventbus.sqlite",
        )
        with patch("db.helper.build_db_config", return_value=cfg):
            helper = SQLiteHelper("workflow")
            # Simulate the case where _db_path was never set (e.g., stale DbConfig)
            helper._db_path = ""
            with pytest.raises(ValueError, match="agent.toml"):
                helper._connect()
