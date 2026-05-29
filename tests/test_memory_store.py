"""
tests/test_memory_store.py
Behavior-lock tests for MemoryStore.

SQLiteHelper is replaced with a _FakeSQLiteHelper backed by an in-memory
SQLite connection (same pattern as test_agent_session.py).  The vec0 extension
is NOT available in the test environment; all memory_vec operations should
gracefully degrade without raising exceptions.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.memory.store import MemoryStore

# ── In-memory schema ──────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memory_entries (
    entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    mem_type   TEXT NOT NULL CHECK (mem_type IN ('long_term', 'task')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper drop-in backed by a real in-memory SQLite connection.

    The vec0 virtual table is NOT created; memory_vec operations will raise
    sqlite3.OperationalError which MemoryStore guards via try/except.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.conn: sqlite3.Connection | None = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        self.conn = self._conn
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection]:
    """Provide a fresh in-memory SQLite connection with the memory_entries schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute(_SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def store(db_conn: sqlite3.Connection) -> Generator[MemoryStore]:
    """Provide a MemoryStore patched to use the in-memory _FakeSQLiteHelper."""
    fake = _FakeSQLiteHelper(db_conn)
    with patch("agent.memory.store.SQLiteHelper", return_value=fake):
        yield MemoryStore()


# ── add() ─────────────────────────────────────────────────────────────────────


class TestAdd:
    def test_add_returns_positive_entry_id(self, store: MemoryStore) -> None:
        entry_id = store.add(session_id=None, mem_type="long_term", content="test fact")
        assert entry_id > 0

    def test_add_persists_content(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(session_id=1, mem_type="task", content="task note")
        rows = db_conn.execute(
            "SELECT content, mem_type FROM memory_entries"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "task note"
        assert rows[0][1] == "task"

    def test_add_with_session_id(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(session_id=42, mem_type="long_term", content="session fact")
        rows = db_conn.execute("SELECT session_id FROM memory_entries").fetchall()
        assert rows[0][0] == 42

    def test_add_without_embedding_does_not_raise(self, store: MemoryStore) -> None:
        # vec0 is unavailable; embedding=None should skip memory_vec INSERT silently
        entry_id = store.add(
            session_id=None, mem_type="long_term", content="no embedding"
        )
        assert entry_id > 0

    def test_add_with_embedding_gracefully_degrades(self, store: MemoryStore) -> None:
        # vec0 is not available in test env; MemoryStore should log warning and continue
        embedding = [0.0] * 384
        entry_id = store.add(
            session_id=None,
            mem_type="long_term",
            content="with embedding",
            embedding=embedding,
        )
        # entry_id should still be valid even if memory_vec INSERT failed
        assert entry_id > 0

    def test_add_multiple_entries_unique_ids(self, store: MemoryStore) -> None:
        id1 = store.add(None, "long_term", "fact 1")
        id2 = store.add(None, "task", "task 1")
        assert id1 != id2


# ── search_by_type() ──────────────────────────────────────────────────────────


class TestSearchByType:
    def test_search_returns_matching_type(self, store: MemoryStore) -> None:
        store.add(None, "long_term", "long fact")
        store.add(None, "task", "task note")
        results = store.search_by_type("long_term")
        assert len(results) == 1
        assert results[0]["content"] == "long fact"
        assert results[0]["mem_type"] == "long_term"

    def test_search_respects_limit(self, store: MemoryStore) -> None:
        for i in range(5):
            store.add(None, "task", f"task {i}")
        results = store.search_by_type("task", limit=3)
        assert len(results) == 3

    def test_search_empty_when_no_entries(self, store: MemoryStore) -> None:
        results = store.search_by_type("long_term")
        assert results == []

    def test_search_returns_dict_with_expected_keys(self, store: MemoryStore) -> None:
        store.add(None, "long_term", "fact")
        results = store.search_by_type("long_term")
        assert "entry_id" in results[0]
        assert "content" in results[0]
        assert "mem_type" in results[0]


# ── delete() ─────────────────────────────────────────────────────────────────


class TestDelete:
    def test_delete_existing_entry_returns_true(self, store: MemoryStore) -> None:
        entry_id = store.add(None, "long_term", "to delete")
        result = store.delete(entry_id)
        assert result is True

    def test_delete_nonexistent_entry_returns_false(self, store: MemoryStore) -> None:
        result = store.delete(99999)
        assert result is False

    def test_delete_removes_entry_from_db(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry_id = store.add(None, "long_term", "to remove")
        store.delete(entry_id)
        rows = db_conn.execute(
            "SELECT * FROM memory_entries WHERE entry_id = ?", (entry_id,)
        ).fetchall()
        assert rows == []


# ── clear() ──────────────────────────────────────────────────────────────────


class TestClear:
    def test_clear_all_removes_all_entries(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(None, "long_term", "fact 1")
        store.add(1, "task", "task 1")
        count = store.clear()
        assert count == 2
        rows = db_conn.execute("SELECT COUNT(*) FROM memory_entries").fetchall()
        assert rows[0][0] == 0

    def test_clear_by_session_removes_only_matching_entries(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(session_id=1, mem_type="long_term", content="session 1 fact")
        store.add(session_id=2, mem_type="task", content="session 2 task")
        count = store.clear(session_id=1)
        assert count == 1
        remaining = db_conn.execute("SELECT session_id FROM memory_entries").fetchall()
        assert len(remaining) == 1
        assert remaining[0][0] == 2

    def test_clear_empty_store_returns_zero(self, store: MemoryStore) -> None:
        count = store.clear()
        assert count == 0
