"""tests/test_tool_result_store.py
Unit tests for ToolResultStore: store, get, list_recent.
SQLiteHelper is replaced with an in-memory SQLite connection (session target).

DB errors are re-raised (fail-fast); callers (tool_runner.py) must handle them.
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

    def test_returns_non_optional_int(self, store: ToolResultStore) -> None:
        """store() always returns int on success; callers no longer need to handle None."""
        row_id = store.store(
            session_id=1,
            turn=1,
            tool_name="read_file",
            args_masked='{"path": "/tmp/x"}',
            full_text="file content",
            summary="content summary",
            is_error=False,
        )
        assert row_id is not None  # type narrowing: int, not int | None
        assert isinstance(row_id, int)

    def test_raises_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            with pytest.raises(RuntimeError, match="db unavailable"):
                ToolResultStore().store(
                    session_id=None,
                    turn=1,
                    tool_name="tool",
                    args_masked="{}",
                    full_text="text",
                    summary=None,
                    is_error=False,
                )

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
        assert row_id is not None  # type narrowing: int, not int | None
        row = store.get(row_id)
        assert row is not None
        assert row.is_error is True

    def test_stored_result_fetchable_by_returned_id(self, store: ToolResultStore) -> None:
        """Successful store returns an ID that can fetch the stored result."""
        row_id = store.store(
            session_id=10,
            turn=3,
            tool_name="write_file",
            args_masked='{"path": "/tmp/y"}',
            full_text="written content",
            summary="wrote /tmp/y",
            is_error=False,
        )
        assert isinstance(row_id, int)
        row = store.get(row_id)
        assert row is not None
        assert row.full_text == "written content"
        assert row.summary == "wrote /tmp/y"

    def test_lastrowid_none_raises_runtime_error(self) -> None:
        """Simulated lastrowid is None raises RuntimeError."""
        class _FakeCursor:
            lastrowid = None

        class _FakeHelper:
            def __init__(self, target: str = "session") -> None:  # noqa: ARG001
                pass

            def open(
                self, *, write_mode: bool = False, row_factory: bool = False  # noqa: ARG002
            ) -> "_FakeHelper":
                return self

            def execute(self, sql: str, params: tuple) -> "_FakeCursor":  # noqa: ARG001
                return _FakeCursor()

            def commit(self) -> None:
                pass

            def close(self) -> None:
                pass

            def __enter__(self) -> "_FakeHelper":
                return self

            def __exit__(self, *_: object) -> None:
                pass

        with patch("db.tool_results.SQLiteHelper", _FakeHelper):
            with pytest.raises(RuntimeError, match="lastrowid is None"):
                ToolResultStore().store(
                    session_id=1,
                    turn=1,
                    tool_name="tool",
                    args_masked="{}",
                    full_text="text",
                    summary=None,
                    is_error=False,
                )


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
        assert isinstance(row_id, int)
        row = store.get(row_id)
        assert row is not None
        assert row.tool_name == "list_dir"
        assert row.full_text == "dir listing"
        assert row.session_id == 5

    def test_returns_none_for_missing_id(self, store: ToolResultStore) -> None:
        assert store.get(99999) is None

    def test_raises_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            with pytest.raises(RuntimeError, match="db unavailable"):
                ToolResultStore().get(1)


class TestToolResultStoreListRecent:
    def test_returns_empty_for_none_session(self, store: ToolResultStore) -> None:
        assert store.list_recent(None) == []

    def test_returns_results_for_session(self, store: ToolResultStore) -> None:
        store.store(1, 1, "tool_a", "{}", "out_a", None, False)
        store.store(1, 2, "tool_b", "{}", "out_b", None, False)
        store.store(2, 1, "tool_c", "{}", "out_c", None, False)
        results = store.list_recent(1)
        assert len(results) == 2
        names = [r.tool_name for r in results]
        assert "tool_a" in names
        assert "tool_b" in names

    def test_results_ordered_oldest_first(self, store: ToolResultStore) -> None:
        store.store(1, 1, "first", "{}", "out1", None, False)
        store.store(1, 2, "second", "{}", "out2", None, False)
        results = store.list_recent(1)
        assert results[0].tool_name == "first"
        assert results[1].tool_name == "second"

    def test_respects_n_limit(self, store: ToolResultStore) -> None:
        for i in range(10):
            store.store(1, i, f"tool_{i}", "{}", f"out_{i}", None, False)
        results = store.list_recent(1, n=3)
        assert len(results) == 3

    def test_raises_on_db_error(self) -> None:
        def _raise(target: str = "session") -> None:  # noqa: ARG001
            raise RuntimeError("db unavailable")

        with patch("db.tool_results.SQLiteHelper", side_effect=_raise):
            with pytest.raises(RuntimeError, match="db unavailable"):
                ToolResultStore().list_recent(1)

    def test_no_full_text_in_results(self, store: ToolResultStore) -> None:
        store.store(1, 1, "tool", "{}", "full content here", "summary text", False)
        results = store.list_recent(1)
        assert len(results) == 1
        assert results[0].full_text == ""
        assert results[0].summary == "summary text"

    def test_n_zero_returns_empty(self, store: ToolResultStore) -> None:
        """list_recent(session_id, n=0) returns [] without querying the database."""
        store.store(1, 1, "tool_a", "{}", "out_a", None, False)
        results = store.list_recent(1, n=0)
        assert results == []

    def test_n_negative_returns_empty(self, store: ToolResultStore) -> None:
        """list_recent(session_id, n=-1) returns [] without querying the database."""
        store.store(1, 1, "tool_a", "{}", "out_a", None, False)
        results = store.list_recent(1, n=-1)
        assert results == []

    def test_n_one_returns_single_result(self, store: ToolResultStore) -> None:
        """list_recent(session_id, n=1) returns one result."""
        store.store(1, 1, "tool_a", "{}", "out_a", None, False)
        store.store(1, 2, "tool_b", "{}", "out_b", None, False)
        results = store.list_recent(1, n=1)
        assert len(results) == 1
        assert results[0].tool_name == "tool_b"

    def test_n_less_than_one_no_db_query(self, store: ToolResultStore) -> None:
        """n < 1 returns [] without querying the database (no DB calls made)."""
        with patch.object(store, "_make_helper") as mock_make_helper:
            mock_make_helper.return_value.__enter__ = lambda self: self
            mock_make_helper.return_value.__exit__ = lambda *a: None
            mock_make_helper.return_value.fetchall = lambda sql, params: []  # noqa: ARG005

            results = store.list_recent(1, n=-5)
            assert results == []
            mock_make_helper.assert_not_called()
