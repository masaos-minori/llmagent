"""
tests/test_memory_retriever.py
Behavior-lock tests for MemoryRetriever (FTS5 search + scoring).

SQLiteHelper is patched with _FakeSQLiteHelper backed by in-memory SQLite.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.memory.retriever import (
    MemoryRetriever,
    _build_fts_query,
    _recency_boost,
    _score,
)
from agent.memory.types import MemoryEntry, MemoryQuery

# ── Schema ─────────────────────────────────────────────────────────────────────

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


def _insert(conn: sqlite3.Connection, **kwargs) -> None:
    defaults = dict(
        memory_id="test-id",
        memory_type="semantic",
        source_type="rule",
        session_id=None,
        turn_id=None,
        project="",
        repo="",
        branch="main",
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


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture()
def retriever(db_conn: sqlite3.Connection) -> Generator[MemoryRetriever]:
    fake = _FakeSQLiteHelper(db_conn)
    with patch("agent.memory.retriever.SQLiteHelper", return_value=fake):
        yield MemoryRetriever()


# ── Unit helpers ───────────────────────────────────────────────────────────────


class TestBuildFtsQuery:
    def test_single_word(self) -> None:
        assert _build_fts_query("policy") == "policy"

    def test_multi_word_joins_with_or(self) -> None:
        result = _build_fts_query("rule policy")
        assert "rule" in result
        assert "OR" in result
        assert "policy" in result

    def test_empty_string_returns_fallback(self) -> None:
        assert _build_fts_query("") == '""'

    def test_non_word_chars_stripped(self) -> None:
        result = _build_fts_query("!!! ???")
        assert result == '""'


class TestRecencyBoost:
    def test_today_returns_near_max(self) -> None:
        from datetime import UTC, datetime

        now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        boost = _recency_boost(now_str)
        # Should be close to _RECENCY_MAX_BOOST (0.2)
        assert boost > 0.15

    def test_old_entry_returns_zero(self) -> None:
        assert _recency_boost("2020-01-01T00:00:00Z") == pytest.approx(0.0)

    def test_invalid_date_returns_zero(self) -> None:
        assert _recency_boost("not-a-date") == pytest.approx(0.0)


class TestScore:
    def _make_entry(
        self,
        memory_type: str = "semantic",
        importance: float = 0.5,
        pinned: bool = False,
    ) -> MemoryEntry:
        return MemoryEntry(
            memory_id="id",
            memory_type=memory_type,
            source_type="rule",
            session_id=None,
            turn_id=None,
            project="proj",
            repo="repo",
            branch="main",
            content="content",
            summary="summary",
            tags=[],
            importance=importance,
            pinned=pinned,
            created_at="2020-01-01T00:00:00Z",
            updated_at="2020-01-01T00:00:00Z",
        )

    def test_pinned_entry_scores_higher(self) -> None:
        base = self._make_entry(pinned=False)
        pinned = self._make_entry(pinned=True)
        s_base = _score(0.0, base, "", "")
        s_pinned = _score(0.0, pinned, "", "")
        assert s_pinned > s_base

    def test_high_importance_semantic_scores_higher(self) -> None:
        low = self._make_entry(memory_type="semantic", importance=0.1)
        high = self._make_entry(memory_type="semantic", importance=0.9)
        assert _score(0.0, high, "", "") > _score(0.0, low, "", "")

    def test_context_boost_applied_on_project_match(self) -> None:
        entry = self._make_entry()
        s_no_match = _score(0.0, entry, "other", "")
        s_match = _score(0.0, entry, "proj", "")
        assert s_match > s_no_match

    def test_negative_bm25_rank_raises_score(self) -> None:
        entry = self._make_entry()
        # FTS5 BM25 rank is negative; more negative = better match → score = -rank
        s_good = _score(-10.0, entry, "", "")  # good FTS5 match (rank more negative)
        s_bad = _score(-1.0, entry, "", "")  # poor FTS5 match (rank less negative)
        assert s_good > s_bad


# ── MemoryRetriever.search() ───────────────────────────────────────────────────


class TestSearch:
    def test_returns_matching_entry(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(db_conn, memory_id="id-1", content="unique keyword match")
        q = MemoryQuery(query="unique keyword", memory_type="semantic")
        hits = retriever.search(q)
        assert len(hits) >= 1
        assert hits[0].entry.memory_id == "id-1"

    def test_returns_empty_for_no_match(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(db_conn, memory_id="id-1", content="some random text")
        q = MemoryQuery(query="zzznomatch", memory_type="semantic")
        hits = retriever.search(q)
        assert hits == []

    def test_filters_by_memory_type(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(
            db_conn, memory_id="sem-1", memory_type="semantic", content="policy rule"
        )
        _insert(
            db_conn, memory_id="epi-1", memory_type="episodic", content="policy rule"
        )
        q = MemoryQuery(query="policy rule", memory_type="semantic")
        hits = retriever.search(q)
        ids = [h.entry.memory_id for h in hits]
        assert "sem-1" in ids
        assert "epi-1" not in ids

    def test_respects_limit(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        for i in range(5):
            _insert(
                db_conn,
                memory_id=f"id-{i}",
                content=f"common keyword entry {i}",
            )
        q = MemoryQuery(query="common keyword", limit=2)
        hits = retriever.search(q)
        assert len(hits) <= 2

    def test_higher_importance_ranks_first_for_semantic(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(
            db_conn,
            memory_id="low",
            memory_type="semantic",
            content="important rule",
            importance=0.1,
        )
        _insert(
            db_conn,
            memory_id="high",
            memory_type="semantic",
            content="important rule",
            importance=0.9,
        )
        q = MemoryQuery(query="important rule", memory_type="semantic", limit=10)
        hits = retriever.search(q)
        ids = [h.entry.memory_id for h in hits]
        assert ids.index("high") < ids.index("low")

    def test_returns_empty_on_db_error(self) -> None:
        with patch(
            "agent.memory.retriever.SQLiteHelper", side_effect=Exception("db error")
        ):
            ret = MemoryRetriever()
            hits = ret.search(MemoryQuery(query="anything"))
        assert hits == []

    def test_empty_query_returns_empty(self, retriever: MemoryRetriever) -> None:
        q = MemoryQuery(query="")
        assert retriever.search(q) == []


# ── MemoryRetriever.top_semantic() ────────────────────────────────────────────


class TestTopSemantic:
    def test_returns_semantic_entries_only(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(db_conn, memory_id="sem-1", memory_type="semantic", importance=0.8)
        _insert(db_conn, memory_id="epi-1", memory_type="episodic", importance=0.9)
        entries = retriever.top_semantic()
        ids = [e.memory_id for e in entries]
        assert "sem-1" in ids
        assert "epi-1" not in ids

    def test_respects_min_importance(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(db_conn, memory_id="low", memory_type="semantic", importance=0.2)
        _insert(db_conn, memory_id="high", memory_type="semantic", importance=0.8)
        entries = retriever.top_semantic(min_importance=0.5)
        ids = [e.memory_id for e in entries]
        assert "high" in ids
        assert "low" not in ids

    def test_respects_limit(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        for i in range(10):
            _insert(
                db_conn,
                memory_id=f"sem-{i}",
                memory_type="semantic",
                importance=0.5,
            )
        entries = retriever.top_semantic(limit=3)
        assert len(entries) <= 3

    def test_returns_empty_when_no_semantic(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(db_conn, memory_id="epi-1", memory_type="episodic")
        assert retriever.top_semantic() == []

    def test_returns_empty_on_db_error(self) -> None:
        with patch(
            "agent.memory.retriever.SQLiteHelper", side_effect=Exception("db error")
        ):
            ret = MemoryRetriever()
            assert ret.top_semantic() == []

    def test_pinned_entry_ordered_first(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        _insert(
            db_conn,
            memory_id="unpinned",
            memory_type="semantic",
            importance=0.9,
            pinned=0,
        )
        _insert(
            db_conn,
            memory_id="pinned",
            memory_type="semantic",
            importance=0.5,
            pinned=1,
        )
        entries = retriever.top_semantic()
        assert entries[0].memory_id == "pinned"
