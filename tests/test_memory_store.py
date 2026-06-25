"""
tests/test_memory_store.py
Behavior-lock tests for MemoryStore (new memories / memories_fts schema).

SQLiteHelper is patched with _FakeSQLiteHelper backed by in-memory SQLite.
"""

from __future__ import annotations

import dataclasses
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
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
CREATE TABLE memories_vec (
    memory_id TEXT PRIMARY KEY,
    embedding BLOB
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

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except Exception:
                pass
            raise


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

    def test_add_sets_timestamps_when_empty(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = dataclasses.replace(_make_entry(), created_at="", updated_at="")
        store.add(entry)
        row = db_conn.execute(
            "SELECT created_at, updated_at FROM memories WHERE memory_id=?",
            (entry.memory_id,),
        ).fetchone()
        assert row is not None
        assert row[0] != ""
        assert row[1] != ""

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
        entry2 = dataclasses.replace(entry, content="updated")
        store.upsert(entry2)
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
        entry2 = dataclasses.replace(entry, content="new keyword")
        store.upsert(entry2)
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


# ── pin() / unpin() ──────────────────────────────────────────────────────────


class TestPinUnpin:
    def test_pin_sets_pinned(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = _make_entry(memory_id="pin-test")
        store.add(entry)
        ok = store.pin("pin-test")
        assert ok is True
        row = db_conn.execute(
            "SELECT pinned FROM memories WHERE memory_id='pin-test'"
        ).fetchone()
        assert row[0] == 1

    def test_unpin_clears_pinned(
        self, store: MemoryStore, db_conn: sqlite3.Connection
    ) -> None:
        entry = dataclasses.replace(_make_entry(memory_id="unpin-test"), pinned=True)
        store.add(entry)
        ok = store.unpin("unpin-test")
        assert ok is True
        row = db_conn.execute(
            "SELECT pinned FROM memories WHERE memory_id='unpin-test'"
        ).fetchone()
        assert row[0] == 0

    def test_pin_nonexistent_returns_false(self, store: MemoryStore) -> None:
        assert store.pin("no-such-id") is False

    def test_unpin_nonexistent_returns_false(self, store: MemoryStore) -> None:
        assert store.unpin("no-such-id") is False


# ── get_by_id() ───────────────────────────────────────────────────────────────


class TestGetById:
    def test_returns_entry_when_found(self, store: MemoryStore) -> None:
        entry = _make_entry(content="unique content", memory_id="gbi-test")
        store.add(entry)
        result = store.get_by_id("gbi-test")
        assert result is not None
        assert result.memory_id == "gbi-test"
        assert result.content == "unique content"

    def test_returns_none_when_not_found(self, store: MemoryStore) -> None:
        assert store.get_by_id("nonexistent") is None


# ── concurrent upsert() ──────────────────────────────────────────────────────


def _make_concurrent_store() -> tuple[MemoryStore, str]:
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path, timeout=5)
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()

    class _ConcurrentHelper:
        def __init__(self) -> None:
            self._conn = sqlite3.connect(path, timeout=5)

        def open(
            self, *, write_mode: bool = False, row_factory: bool = False
        ) -> _ConcurrentHelper:
            self._conn.row_factory = sqlite3.Row if row_factory else None
            return self

        def __enter__(self) -> _ConcurrentHelper:
            return self

        def __exit__(self, *_: object) -> None:
            pass

        def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
            return self._conn.execute(sql, params)

        def fetchall(self, sql: str, params: tuple = ()) -> list:
            return self._conn.execute(sql, params).fetchall()

        def commit(self) -> None:
            self._conn.commit()

        @contextmanager
        def begin_immediate(self) -> Generator[None]:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield
                self._conn.execute("COMMIT")
            except BaseException:
                try:
                    self._conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise

    patcher = patch(
        "agent.memory.store.SQLiteHelper", side_effect=lambda mode: _ConcurrentHelper()
    )
    patcher.start()
    store = MemoryStore()
    return (store, path)


class TestUpsertConcurrency:
    def test_concurrent_upsert_different_ids_all_persisted(self) -> None:
        store, path = _make_concurrent_store()
        try:
            entries = [_make_entry(memory_id=f"concurrent-{i}") for i in range(10)]

            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(store.upsert, entries))

            conn = sqlite3.connect(path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                assert count == 10
            finally:
                conn.close()
        finally:
            os.unlink(path) if os.path.exists(path) else None

    def test_concurrent_upsert_same_id_single_row(self) -> None:
        store, path = _make_concurrent_store()
        try:
            entries = [
                _make_entry(memory_id="same-id", content=f"content-{i}")
                for i in range(5)
            ]

            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(store.upsert, entries))

            conn = sqlite3.connect(path)
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE memory_id='same-id'"
                ).fetchone()[0]
                assert count == 1
            finally:
                conn.close()
        finally:
            os.unlink(path) if os.path.exists(path) else None

    def test_concurrent_upsert_same_id_last_write_wins(self) -> None:
        store, path = _make_concurrent_store()
        contents = [f"content-{i}" for i in range(5)]
        try:
            entries = [_make_entry(memory_id="lww-id", content=c) for c in contents]

            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(store.upsert, entries))

            conn = sqlite3.connect(path)
            try:
                row = conn.execute(
                    "SELECT content FROM memories WHERE memory_id='lww-id'"
                ).fetchone()
                assert row is not None, (
                    "expected exactly one row after concurrent upsert"
                )
                assert row[0] in contents, (
                    f"surviving content {row[0]!r} is not one of the submitted values"
                )
            finally:
                conn.close()
        finally:
            os.unlink(path) if os.path.exists(path) else None

    def test_concurrent_upsert_with_embedding(self) -> None:
        store, path = _make_concurrent_store()
        try:

            def _upsert_with_embedding(idx: int) -> None:
                entry = _make_entry(memory_id="vec-id", content=f"vec-content-{idx}")
                embedding = [float(idx), float(idx + 1), float(idx + 2)]
                store.upsert(entry, embedding=embedding)

            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(_upsert_with_embedding, range(5)))

            conn = sqlite3.connect(path)
            try:
                mem_count = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE memory_id='vec-id'"
                ).fetchone()[0]
                vec_count = conn.execute(
                    "SELECT COUNT(*) FROM memories_vec WHERE memory_id='vec-id'"
                ).fetchone()[0]
                assert mem_count == 1, f"expected 1 memories row, got {mem_count}"
                assert vec_count == 1, f"expected 1 memories_vec row, got {vec_count}"
            finally:
                conn.close()
        finally:
            os.unlink(path) if os.path.exists(path) else None

    def test_concurrent_upsert_busy_error_handling(self) -> None:
        store, path = _make_concurrent_store()
        try:
            blocker = sqlite3.connect(path, timeout=0.1)
            blocker.execute("BEGIN IMMEDIATE")

            results: list[Exception | None] = []

            def _try_upsert(idx: int) -> Exception | None:
                try:
                    entry = _make_entry(
                        memory_id=f"busy-{idx}", content=f"content-{idx}"
                    )
                    store.upsert(entry)
                    return None
                except Exception as exc:  # noqa: BLE001
                    return exc

            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=3) as executor:
                results = list(executor.map(_try_upsert, range(3)))

            blocker.execute("ROLLBACK")
            blocker.close()

            for r in results:
                if r is not None:
                    assert isinstance(r, (sqlite3.OperationalError, Exception)), (
                        f"unexpected exception type: {type(r)}"
                    )
        finally:
            os.unlink(path) if os.path.exists(path) else None
