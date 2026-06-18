"""
tests/test_fts_japanese.py
Regression tests for Japanese FTS5 search quality.

Verifies:
- chunks_ai trigger indexes normalized_content via COALESCE(normalized_content, content)
- _build_fts_query() applies Sudachi POS filter for Japanese, ASCII regex for English
- fts_search() finds morphological variants through normalized_content indexing
- chunks_au and chunks_ad triggers maintain the FTS index on update and delete
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from rag.repository import _build_fts_query, fts_search

# Full RAG schema; chunks_vec is stubbed (vec0 not required for FTS tests)
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    title              TEXT,
    lang               TEXT    NOT NULL DEFAULT 'ja'
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id             INTEGER NOT NULL
                           REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index        INTEGER NOT NULL,
    content            TEXT    NOT NULL,
    normalized_content TEXT
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai
AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad
AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
END;
CREATE TRIGGER IF NOT EXISTS chunks_au
AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts (chunks_fts, rowid, content)
    VALUES ('delete', old.chunk_id, COALESCE(old.normalized_content, old.content));
    INSERT INTO chunks_fts (rowid, content)
    VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
END;
"""


class _FakeSQLiteHelper:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
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

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def db() -> Generator[_FakeSQLiteHelper]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    yield _FakeSQLiteHelper(conn)
    conn.close()


def _insert_doc(conn: sqlite3.Connection, url: str = "http://example.com") -> int:
    cur = conn.execute(
        "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
        (url, "Test", "ja"),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _insert_chunk(
    conn: sqlite3.Connection,
    doc_id: int,
    content: str,
    normalized_content: str | None = None,
    chunk_index: int = 0,
) -> int:
    cur = conn.execute(
        "INSERT INTO chunks (doc_id, chunk_index, content, normalized_content)"
        " VALUES (?, ?, ?, ?)",
        (doc_id, chunk_index, content, normalized_content),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _fts_rowids(conn: sqlite3.Connection, query: str) -> list[int]:
    """Direct FTS5 query; bypasses the chunks JOIN to inspect raw index state."""
    rows = conn.execute(
        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ?", (query,)
    ).fetchall()
    return [r[0] for r in rows]


# ── chunks_ai trigger ──────────────────────────────────────────────────────────


class TestChunksAiTrigger:
    def test_ja_normalized_content_indexed_in_fts(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        _insert_chunk(conn, doc_id, "raw Japanese text", "食べる 料理")
        assert len(_fts_rowids(conn, '"食べる"')) == 1

    def test_ja_raw_content_fallback_when_normalized_null(
        self, db: _FakeSQLiteHelper
    ) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://en.example.com")
        _insert_chunk(conn, doc_id, "machine learning basics", None)
        assert len(_fts_rowids(conn, '"machine"')) == 1

    def test_trigger_uses_coalesce_order(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        _insert_chunk(conn, doc_id, "unique_raw_token", "unique_norm_token")
        assert len(_fts_rowids(conn, '"unique_norm_token"')) == 1
        assert len(_fts_rowids(conn, '"unique_raw_token"')) == 0


# ── _build_fts_query() ────────────────────────────────────────────────────────


class TestBuildFtsQuery:
    def test_build_fts_query_ja_extracts_nouns_verbs_adjectives(self) -> None:
        with patch(
            "rag.repository._build_fts_tokens_ja",
            return_value=["食べ物", "美味しい"],
        ):
            result = _build_fts_query("食べ物は美味しい")
        assert result == '"食べ物" "美味しい"'

    def test_build_fts_query_en_uses_ascii_extraction(self) -> None:
        result = _build_fts_query("hello world 123")
        assert result == '"hello" "world" "123"'

    def test_build_fts_query_escapes_fts_metacharacters(self) -> None:
        with patch(
            "rag.repository._build_fts_tokens_ja",
            return_value=['te"st'],
        ):
            result = _build_fts_query("test日本語")
        assert result == '"test"'


# ── fts_search() quality ──────────────────────────────────────────────────────


class TestFtsSearchQuality:
    def test_ja_morphological_variant_returns_same_results(
        self, db: _FakeSQLiteHelper
    ) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        # normalized_content stores dictionary form; query uses inflected form
        _insert_chunk(conn, doc_id, "past tense text", "食べる")
        # Sudachi normalizes inflected form "食べた" to dictionary form "食べる"
        results = fts_search("食べた", top_k=5, db=db)
        assert len(results) == 1

    def test_empty_japanese_query_returns_no_hits(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        _insert_chunk(conn, doc_id, "some content", "何か コンテンツ")
        with patch("rag.repository._build_fts_tokens_ja", return_value=[]):
            results = fts_search("は", top_k=5, db=db)
        assert results == []


# ── trigger lifecycle ─────────────────────────────────────────────────────────


class TestTriggerLifecycle:
    def test_update_trigger_reindexes_normalized_content_change(
        self, db: _FakeSQLiteHelper
    ) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        chunk_id = _insert_chunk(conn, doc_id, "some content", "old_token")
        conn.execute(
            "UPDATE chunks SET normalized_content = ? WHERE chunk_id = ?",
            ("new_token", chunk_id),
        )
        conn.commit()
        assert len(_fts_rowids(conn, '"new_token"')) == 1
        assert len(_fts_rowids(conn, '"old_token"')) == 0

    def test_delete_trigger_removes_from_fts(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn)
        chunk_id = _insert_chunk(conn, doc_id, "searchable content", "search_token")
        assert len(_fts_rowids(conn, '"search_token"')) == 1
        conn.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        conn.commit()
        assert len(_fts_rowids(conn, '"search_token"')) == 0
