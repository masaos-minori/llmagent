"""tests/test_tool_result_store.py
Unit tests for ToolResultStore: store, get, list_recent.
SQLiteHelper is replaced with an in-memory SQLite connection (session target).
"""

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from db.tool_results import ToolResultStore

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tool_results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    turn       INTEGER NOT NULL,
    tool_name  TEXT    NOT NULL,
    args_masked  TEXT,
    full_text  TEXT    NOT NULL,
    summary    TEXT,
    is_error   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_tool_results_session ON tool_results(session_id);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> "_FakeSQLiteHelper":
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> "_FakeSQLiteHelper":
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def store() -> Generator[ToolResultStore]:
    """ToolResultStore wired to a fresh in-memory SQLite DB."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "session") -> _FakeSQLiteHelper:  # noqa: ARG001
        return _FakeSQLiteHelper(conn)

    with patch("db.tool_results.SQLiteHelper", side_effect=_make):
        yield ToolResultStore()


class TestToolResultStoreStore:
    def test_returns_integer_id(self, store: ToolResultStore) -> None:
        row_id = store.store(
            session_id=1,
            turn=1,
            tool_name="read_file",
            args_masked='{"path": "/tmp/x"}',
            full_text="file content",
            summary="content summary",
            is_error=False,
        )
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_returns_none_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            result = ToolResultStore().store(
                session_id=None,
                turn=1,
                tool_name="tool",
                args_masked="{}",
                full_text="text",
                summary=None,
                is_error=False,
            )
        assert result is None

    def test_stores_error_flag(self, store: ToolResultStore) -> None:
        row_id = store.store(
            session_id=1,
            turn=2,
            tool_name="bad_tool",
            args_masked="{}",
            full_text="error output",
            summary=None,
            is_error=True,
        )
        assert row_id is not None
        row = store.get(row_id)
        assert row is not None
        assert row["is_error"] == 1


class TestToolResultStoreGet:
    def test_returns_dict_for_existing_id(self, store: ToolResultStore) -> None:
        row_id = store.store(
            session_id=5,
            turn=1,
            tool_name="list_dir",
            args_masked='{"path": "/"}',
            full_text="dir listing",
            summary=None,
            is_error=False,
        )
        assert row_id is not None
        row = store.get(row_id)
        assert row is not None
        assert row["tool_name"] == "list_dir"
        assert row["full_text"] == "dir listing"
        assert row["session_id"] == 5

    def test_returns_none_for_missing_id(self, store: ToolResultStore) -> None:
        assert store.get(99999) is None

    def test_returns_none_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            assert ToolResultStore().get(1) is None


class TestToolResultStoreListRecent:
    def test_returns_empty_for_none_session(self, store: ToolResultStore) -> None:
        assert store.list_recent(None) == []

    def test_returns_results_for_session(self, store: ToolResultStore) -> None:
        store.store(1, 1, "tool_a", "{}", "out_a", None, False)
        store.store(1, 2, "tool_b", "{}", "out_b", None, False)
        store.store(2, 1, "tool_c", "{}", "out_c", None, False)
        results = store.list_recent(1)
        assert len(results) == 2
        names = [r["tool_name"] for r in results]
        assert "tool_a" in names
        assert "tool_b" in names

    def test_results_ordered_oldest_first(self, store: ToolResultStore) -> None:
        store.store(1, 1, "first", "{}", "out1", None, False)
        store.store(1, 2, "second", "{}", "out2", None, False)
        results = store.list_recent(1)
        assert results[0]["tool_name"] == "first"
        assert results[1]["tool_name"] == "second"

    def test_respects_n_limit(self, store: ToolResultStore) -> None:
        for i in range(10):
            store.store(1, i, f"tool_{i}", "{}", f"out_{i}", None, False)
        results = store.list_recent(1, n=3)
        assert len(results) == 3

    def test_returns_empty_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            assert ToolResultStore().list_recent(1) == []
