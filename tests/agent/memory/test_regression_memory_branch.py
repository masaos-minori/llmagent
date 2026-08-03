"""
tests/test_regression_memory_branch.py
Regression tests: branch-aware memory retrieval.

Locks down the "untagged always matches" policy:
  - top_semantic(branch='feat-x') returns entries with branch='feat-x'.
  - top_semantic(branch='feat-x') ALSO returns entries with branch='' (untagged).
  - top_semantic(branch='feat-x') excludes entries with branch='feat-y'.
  - search(branch='feat-x') applies same filter via FTS path.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.memory.retriever import HybridRetriever
from agent.memory.types import MemoryQuery

_VEC_AVAILABLE: bool = Path("/opt/llm/sqlite-vec/vec0.so").exists()

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


def _insert(conn: sqlite3.Connection, **kwargs: object) -> None:
    defaults: dict[str, object] = dict(
        memory_id="test-id",
        memory_type="semantic",
        source_type="rule",
        session_id=None,
        turn_id=None,
        project="",
        repo="",
        branch="",
        content="test content",
        summary="test summary",
        tags='["test"]',
        importance=0.5,
        pinned=0,
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )
    defaults.update(kwargs)
    conn.execute(
        """INSERT INTO memories VALUES (
            :memory_id,:memory_type,:source_type,:session_id,:turn_id,
            :project,:repo,:branch,:content,:summary,:tags,
            :importance,:pinned,:created_at,:updated_at
        )""",
        defaults,
    )
    conn.execute(
        "INSERT INTO memories_fts(memory_id,content,summary,tags) VALUES (?,?,?,?)",
        (
            defaults["memory_id"],
            defaults["content"],
            defaults["summary"],
            defaults["tags"],
        ),
    )
    conn.commit()


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def commit(self) -> None:
        self._conn.commit()

    @contextmanager
    def begin_immediate(self) -> Generator[None]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._conn.execute("COMMIT")
        except Exception:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise

    def close(self) -> None:
        pass


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def retriever(db_conn: sqlite3.Connection) -> Generator[HybridRetriever]:
    fake = _FakeSQLiteHelper(db_conn)
    with patch("agent.memory.retriever.SQLiteHelper", return_value=fake):
        yield HybridRetriever()


class TestTopSemanticBranchFilter:
    def test_includes_same_branch_entry(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """top_semantic(branch='feat-x') returns entries with branch='feat-x'."""
        _insert(db_conn, memory_id="feat-x-id", branch="feat-x", content="feat-x rule")

        entries = retriever.top_semantic(branch="feat-x", limit=10)

        assert any(e.memory_id == "feat-x-id" for e in entries)

    def test_includes_untagged_entries(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """top_semantic(branch='feat-x') also returns entries with branch='' (untagged always matches)."""
        _insert(db_conn, memory_id="untagged-id", branch="", content="global rule")

        entries = retriever.top_semantic(branch="feat-x", limit=10)

        # Current policy: untagged entries (branch='') always match regardless of branch filter.
        assert any(e.memory_id == "untagged-id" for e in entries)

    def test_excludes_different_branch_entry(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """top_semantic(branch='feat-x') excludes entries with branch='feat-y'."""
        _insert(db_conn, memory_id="feat-y-id", branch="feat-y", content="feat-y rule")

        entries = retriever.top_semantic(branch="feat-x", limit=10)

        assert not any(e.memory_id == "feat-y-id" for e in entries)

    def test_excludes_other_branch_includes_untagged(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """top_semantic(branch='feat-x') excludes feat-y but includes untagged."""
        _insert(db_conn, memory_id="feat-y-id", branch="feat-y", content="feat-y rule")
        _insert(db_conn, memory_id="untagged-id", branch="", content="global rule")

        entries = retriever.top_semantic(branch="feat-x", limit=10)

        assert not any(e.memory_id == "feat-y-id" for e in entries)
        assert any(e.memory_id == "untagged-id" for e in entries)

    def test_empty_branch_returns_all(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """top_semantic(branch='') returns all entries regardless of their branch."""
        _insert(db_conn, memory_id="feat-x-id", branch="feat-x", content="feat-x")
        _insert(db_conn, memory_id="global-id", branch="", content="global")

        entries = retriever.top_semantic(branch="", limit=10)

        ids = {e.memory_id for e in entries}
        assert "feat-x-id" in ids
        assert "global-id" in ids


class TestSearchBranchFilter:
    def test_fts_search_includes_same_branch(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """search(branch='feat-x') via FTS returns same-branch entries."""
        _insert(
            db_conn,
            memory_id="feat-x-hit",
            branch="feat-x",
            content="feature specific content",
        )

        hits = retriever.search(
            MemoryQuery(query="feature specific", memory_type="semantic", limit=10),
            branch="feat-x",
        )

        assert any(h.entry.memory_id == "feat-x-hit" for h in hits)

    def test_fts_search_excludes_other_branch(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """search(branch='feat-x') via FTS excludes entries from 'feat-y'."""
        _insert(
            db_conn,
            memory_id="feat-y-hit",
            branch="feat-y",
            content="other branch content",
        )

        hits = retriever.search(
            MemoryQuery(query="other branch", memory_type="semantic", limit=10),
            branch="feat-x",
        )

        assert not any(h.entry.memory_id == "feat-y-hit" for h in hits)

    def test_fts_search_includes_untagged(
        self, retriever: HybridRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """search(branch='feat-x') via FTS includes untagged (branch='') entries."""
        _insert(
            db_conn,
            memory_id="global-hit",
            branch="",
            content="global shared content",
        )

        hits = retriever.search(
            MemoryQuery(query="global shared", memory_type="semantic", limit=10),
            branch="feat-x",
        )

        assert any(h.entry.memory_id == "global-hit" for h in hits)
