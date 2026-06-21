"""
tests/test_fts_fallback.py
Integration tests for FTS5 fallback behavior when normalized_content is NULL.

Verifies:
- COALESCE trigger falls back to content when normalized_content is NULL
- English and code chunk tokens are indexed via the fallback path
- Empty string normalized_content differs from NULL (COALESCE semantics)
- Mixed-language documents index each chunk independently

Resolves: OQ-6 (docs/03_rag_90_inconsistencies_and_known_issues.md)
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from rag.repository import fts_search

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
        (url, "Test", "en"),
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


# ── TestEnglishFtsFallback ────────────────────────────────────────────────────


class TestEnglishFtsFallback:
    def test_english_chunk_indexed_on_content_when_normalized_null(
        self, db: _FakeSQLiteHelper
    ) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://en1.example.com")
        _insert_chunk(conn, doc_id, "machine learning basics", None)
        results = fts_search("machine", top_k=5, db=db)
        assert len(results) == 1
        assert results[0].content == "machine learning basics"

    def test_english_multi_word_query(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://en2.example.com")
        _insert_chunk(conn, doc_id, "deep neural network architecture", None)
        results = fts_search("neural network", top_k=5, db=db)
        assert len(results) == 1
        assert results[0].content == "deep neural network architecture"

    def test_english_bm25_score_ordering(self, db: _FakeSQLiteHelper) -> None:
        # Chunk with higher term frequency scores better (more negative BM25).
        # Both chunks contain "widget"; the first repeats it, boosting relevance.
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://en3.example.com")
        _insert_chunk(
            conn, doc_id, "widget widget widget dashboard", None, chunk_index=0
        )
        _insert_chunk(conn, doc_id, "widget toolbar", None, chunk_index=1)
        results = fts_search("widget", top_k=5, db=db)
        assert len(results) == 2
        # BM25 scores are negative; more negative = higher relevance
        assert results[0].bm25_score <= results[1].bm25_score


# ── TestCodeFtsFallback ───────────────────────────────────────────────────────


class TestCodeFtsFallback:
    def test_code_chunk_with_symbols(self, db: _FakeSQLiteHelper) -> None:
        # Symbols are not alphanumeric; only tokens like "foo", "int", "str" are indexed
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://code1.example.com")
        _insert_chunk(conn, doc_id, "def foo(x: int) -> str: return str(x)", None)
        results = fts_search("foo", top_k=5, db=db)
        assert len(results) == 1

    def test_code_search_returns_original_content(self, db: _FakeSQLiteHelper) -> None:
        original = "class MyHandler: pass"
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://code2.example.com")
        _insert_chunk(conn, doc_id, original, None)
        results = fts_search("MyHandler", top_k=5, db=db)
        assert len(results) == 1
        assert results[0].content == original

    def test_code_chunk_indexed_on_content_when_normalized_null(
        self, db: _FakeSQLiteHelper
    ) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://code3.example.com")
        _insert_chunk(conn, doc_id, "async def handle_request(req)", None)
        results = fts_search("handle", top_k=5, db=db)
        assert len(results) == 1


# ── TestNormalizedContentEdgeCases ───────────────────────────────────────────


class TestNormalizedContentEdgeCases:
    def test_empty_string_vs_null_normalized(self, db: _FakeSQLiteHelper) -> None:
        # NULL → COALESCE returns content → searchable by content keyword
        # "" → COALESCE returns "" → nothing indexed → not searchable by content keyword
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://edge1.example.com")
        _insert_chunk(conn, doc_id, "searchable content token", None, chunk_index=0)
        _insert_chunk(conn, doc_id, "hidden content token", "", chunk_index=1)
        results = fts_search("token", top_k=5, db=db)
        assert len(results) == 1
        assert results[0].content == "searchable content token"

    def test_mixed_japanese_english_document(self, db: _FakeSQLiteHelper) -> None:
        conn = db._conn
        doc_id = _insert_doc(conn, url="http://mixed.example.com")
        # English chunk: NULL normalized → falls back to content
        _insert_chunk(conn, doc_id, "python programming tutorial", None, chunk_index=0)
        # Japanese chunk: normalized content provided
        _insert_chunk(
            conn,
            doc_id,
            "raw Japanese text",
            "食べる 料理",
            chunk_index=1,
        )
        en_results = fts_search("python", top_k=5, db=db)
        assert len(en_results) == 1
        assert en_results[0].content == "python programming tutorial"

        with patch(
            "rag.repository._build_fts_tokens_ja",
            return_value=["食べる"],
        ):
            ja_results = fts_search("食べた", top_k=5, db=db)
        assert len(ja_results) == 1
        assert ja_results[0].content == "raw Japanese text"
