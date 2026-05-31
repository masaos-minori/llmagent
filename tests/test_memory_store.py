"""
tests/test_memory_store.py
Behavior-lock tests for MemoryStore (new memories / memories_fts schema).

SQLiteHelper is patched with _FakeSQLiteHelper backed by in-memory SQLite.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.memory.store import MemoryStore
from agent.memory.types import MemoryEntry

# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE memories (
    memory_id   TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
    source_type TEXT NOT NULL DEFAULT 'conversation',
    session_id  INTEGER,
    turn_id     TEXT,
    project     TEXT NOT NULL DEFAULT '',
    repo        TEXT NOT NULL DEFAULT '',
    branch      TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    summary     TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '[]',
    importance  REAL NOT NULL DEFAULT 0.5,
    pinned      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE memories_fts USING fts5(
    memory_id UNINDEXED,
    content,
    summary,
    tags
);
"""


def _make_entry(
    memory_type: str = "semantic",
    content: str = "test content",
    importance: float = 0.5,
    session_id: int | None = None,
    memory_id: str | None = None,
) -> MemoryEntry:
    import uuid

    return MemoryEntry(
        memory_id=memory_id or str(uuid.uuid4()),
        memory_type=memory_type,
        source_type="rule" if memory_type == "semantic" else "conversation",
        session_id=session_id,
        turn_id=None,
        project="proj",
        repo="repo",
        branch="main",
        content=content,
        summary=content[:50],
        tags=["test"],
        importance=importance,
        pinned=False,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


class _FakeSQLiteHelper:
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

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def store(db_conn: sqlite3.Connection) -> Generator[MemoryStore]:
    fake = _FakeSQLiteHelper(db_conn)
    with patch("agent.memory.store.SQLiteHelper", return_value=fake):
        yield MemoryStore()


# ── add() ─────────────────────────────────────────────────────────────────────


class TestAdd:
    def test_add_inserts_to_memories(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry()
        store.add(entry)
        rows = db_conn.execute("SELECT memory_id FROM memories").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == entry.memory_id

    def test_add_syncs_fts(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry(content="unique content here")
        store.add(entry)
        rows = db_conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memories_fts MATCH 'unique'"
        ).fetchall()
        assert len(rows) == 1

    def test_add_sets_timestamps_when_empty(self, store: MemoryStore) -> None:
        entry = _make_entry()
        entry.created_at = ""
        entry.updated_at = ""
        store.add(entry)
        assert entry.created_at != ""
        assert entry.updated_at != ""

    def test_add_multiple_unique_ids(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(_make_entry())
        store.add(_make_entry(memory_type="episodic"))
        rows = db_conn.execute("SELECT COUNT(*) FROM memories").fetchall()
        assert rows[0][0] == 2


# ── upsert() ──────────────────────────────────────────────────────────────────


class TestUpsert:
    def test_upsert_inserts_new(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry()
        store.upsert(entry)
        rows = db_conn.execute("SELECT memory_id FROM memories").fetchall()
        assert len(rows) == 1

    def test_upsert_replaces_existing(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry(content="original", memory_id="fixed-id")
        store.upsert(entry)
        entry.content = "updated"
        store.upsert(entry)
        rows = db_conn.execute(
            "SELECT content FROM memories WHERE memory_id='fixed-id'"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "updated"

    def test_upsert_updates_fts(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry(content="old word", memory_id="fixed-id")
        store.upsert(entry)
        entry.content = "new keyword"
        store.upsert(entry)
        rows = db_conn.execute(
            "SELECT memory_id FROM memories_fts WHERE memories_fts MATCH 'new'"
        ).fetchall()
        assert len(rows) == 1


# ── delete() ─────────────────────────────────────────────────────────────────


class TestDelete:
    def test_delete_existing_returns_true(self, store: MemoryStore) -> None:
        entry = _make_entry()
        store.add(entry)
        assert store.delete(entry.memory_id) is True

    def test_delete_nonexistent_returns_false(self, store: MemoryStore) -> None:
        assert store.delete("no-such-id") is False

    def test_delete_removes_from_memories(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry()
        store.add(entry)
        store.delete(entry.memory_id)
        rows = db_conn.execute(
            "SELECT memory_id FROM memories WHERE memory_id=?", (entry.memory_id,)
        ).fetchall()
        assert rows == []


# ── clear_by_session() ───────────────────────────────────────────────────────


class TestClearBySession:
    def test_clear_removes_only_matching_session(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        store.add(_make_entry(session_id=1))
        store.add(_make_entry(session_id=2, memory_type="episodic"))
        count = store.clear_by_session(1)
        assert count == 1
        remaining = db_conn.execute("SELECT session_id FROM memories").fetchall()
        assert len(remaining) == 1
        assert remaining[0][0] == 2

    def test_clear_empty_returns_zero(self, store: MemoryStore) -> None:
        assert store.clear_by_session(99) == 0


# ── search_by_type() ─────────────────────────────────────────────────────────


class TestSearchByType:
    def test_returns_matching_type(self, store: MemoryStore) -> None:
        store.add(_make_entry(memory_type="semantic", content="semantic fact"))
        store.add(_make_entry(memory_type="episodic", content="episodic note"))
        results = store.search_by_type("semantic")
        assert len(results) == 1
        assert results[0].memory_type == "semantic"
        assert results[0].content == "semantic fact"

    def test_respects_limit(self, store: MemoryStore) -> None:
        for _ in range(5):
            store.add(_make_entry(memory_type="semantic"))
        results = store.search_by_type("semantic", limit=3)
        assert len(results) == 3

    def test_respects_min_importance(self, store: MemoryStore) -> None:
        store.add(_make_entry(memory_type="semantic", importance=0.2))
        store.add(_make_entry(memory_type="semantic", importance=0.8))
        results = store.search_by_type("semantic", min_importance=0.5)
        assert len(results) == 1
        assert results[0].importance == 0.8

    def test_returns_empty_when_none(self, store: MemoryStore) -> None:
        assert store.search_by_type("semantic") == []


# ── count_by_type() ──────────────────────────────────────────────────────────


class TestCountByType:
    def test_count_by_type(self, store: MemoryStore) -> None:
        store.add(_make_entry(memory_type="semantic"))
        store.add(_make_entry(memory_type="semantic"))
        store.add(_make_entry(memory_type="episodic"))
        counts = store.count_by_type()
        assert counts.get("semantic") == 2
        assert counts.get("episodic") == 1

    def test_empty_returns_empty_dict(self, store: MemoryStore) -> None:
        assert store.count_by_type() == {}
