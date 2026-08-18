"""tests/mcp_servers/rag_pipeline/test_document_manager.py

Characterization tests for mcp_servers.rag_pipeline.document_manager.DocumentManager.

Existing service-layer tests (test_rag_pipeline_mcp_service.py) mock out
RagPipelineMCPService._doc_mgr entirely, so DocumentManager's own SQL (list_documents,
delete_document, _make_helper) was never exercised. These tests lock the current
behavior against a real (file-based) SQLite database before any refactor.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from mcp_servers.rag_pipeline.document_manager import DocumentManager

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url               TEXT    NOT NULL UNIQUE,
    title             TEXT,
    lang              TEXT    NOT NULL,
    fetched_at        TEXT    NOT NULL,
    chunking_strategy TEXT    NOT NULL DEFAULT 'text'
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks_vec (
    chunk_id INTEGER PRIMARY KEY
);
"""


def _make_db(path: Path) -> str:
    """Create a scratch rag-schema-shaped SQLite file at path; return its path as str."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    return str(path)


def _insert_document(
    db_path: str,
    *,
    url: str,
    title: str = "T",
    lang: str = "en",
    fetched_at: str = "2026-01-01T00:00:00Z",
    chunking_strategy: str = "text",
) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO documents (url, title, lang, fetched_at, chunking_strategy) "
            "VALUES (?, ?, ?, ?, ?)",
            (url, title, lang, fetched_at, chunking_strategy),
        )
        conn.commit()
        assert cur.lastrowid is not None
        return cur.lastrowid
    finally:
        conn.close()


def _insert_chunk(
    db_path: str, doc_id: int, chunk_index: int = 0, content: str = "c"
) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
            (doc_id, chunk_index, content),
        )
        conn.commit()
        assert cur.lastrowid is not None
        return cur.lastrowid
    finally:
        conn.close()


def _insert_chunk_vec(db_path: str, chunk_id: int) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT INTO chunks_vec (chunk_id) VALUES (?)", (chunk_id,))
        conn.commit()
    finally:
        conn.close()


def _count(db_path: str, table: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        return int(row[0])
    finally:
        conn.close()


@pytest.fixture
def rag_db(tmp_path: Path) -> str:
    """Path to a scratch SQLite file with the documents/chunks/chunks_vec schema."""
    return _make_db(tmp_path / "rag.sqlite")


# ── _make_helper ───────────────────────────────────────────────────────────


class TestMakeHelper:
    def test_uses_explicit_path_when_configured(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        helper = mgr._make_helper()
        assert helper.DB_PATH == rag_db

    def test_falls_back_to_default_rag_target_when_no_path_given(self) -> None:
        mgr = DocumentManager()
        helper = mgr._make_helper()
        # target="rag" resolves DB_PATH via db.config.build_db_config(); do not assert the
        # literal value (environment-configured), only that the default-target branch runs
        # without raising and yields a non-empty configured path.
        assert helper.DB_PATH


# ── list_documents ───────────────────────────────────────────────────────────


class TestListDocuments:
    def test_empty_db_returns_empty_list(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        assert mgr.list_documents() == []

    def test_returns_expected_fields_and_chunk_count(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        doc_id = _insert_document(
            rag_db,
            url="https://example.com/a",
            title="A",
            lang="en",
            fetched_at="2026-01-01T00:00:00Z",
            chunking_strategy="text",
        )
        _insert_chunk(rag_db, doc_id)
        _insert_chunk(rag_db, doc_id, chunk_index=1)

        result = mgr.list_documents()

        assert result == [
            {
                "url": "https://example.com/a",
                "title": "A",
                "lang": "en",
                "fetched_at": "2026-01-01T00:00:00Z",
                "chunking_strategy": "text",
                "chunk_count": 2,
            }
        ]

    def test_document_without_chunks_has_zero_chunk_count(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(rag_db, url="https://example.com/no-chunks")

        result = mgr.list_documents()

        assert result[0]["chunk_count"] == 0

    def test_filters_by_lang(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(rag_db, url="https://example.com/en", lang="en")
        _insert_document(rag_db, url="https://example.com/ja", lang="ja")

        result = mgr.list_documents(lang="ja")

        assert [r["url"] for r in result] == ["https://example.com/ja"]

    def test_lang_none_returns_all_languages(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(rag_db, url="https://example.com/en", lang="en")
        _insert_document(rag_db, url="https://example.com/ja", lang="ja")

        result = mgr.list_documents(lang=None)

        assert {r["url"] for r in result} == {
            "https://example.com/en",
            "https://example.com/ja",
        }

    def test_orders_by_fetched_at_descending(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(
            rag_db, url="https://example.com/old", fetched_at="2026-01-01T00:00:00Z"
        )
        _insert_document(
            rag_db, url="https://example.com/new", fetched_at="2026-01-03T00:00:00Z"
        )
        _insert_document(
            rag_db, url="https://example.com/mid", fetched_at="2026-01-02T00:00:00Z"
        )

        result = mgr.list_documents()

        assert [r["url"] for r in result] == [
            "https://example.com/new",
            "https://example.com/mid",
            "https://example.com/old",
        ]

    def test_respects_explicit_limit(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        for i in range(5):
            _insert_document(
                rag_db,
                url=f"https://example.com/{i}",
                fetched_at=f"2026-01-0{i + 1}T00:00:00Z",
            )

        result = mgr.list_documents(limit=2)

        assert len(result) == 2

    def test_default_limit_is_20(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        for i in range(25):
            _insert_document(
                rag_db,
                url=f"https://example.com/{i}",
                fetched_at=f"2026-01-{i + 1:02d}T00:00:00Z",
            )

        result = mgr.list_documents()

        assert len(result) == 20


# ── delete_document ──────────────────────────────────────────────────────────


class TestDeleteDocument:
    def test_returns_false_when_url_not_found(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        assert mgr.delete_document("https://example.com/missing") is False

    def test_returns_true_and_removes_document(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(rag_db, url="https://example.com/a")

        assert mgr.delete_document("https://example.com/a") is True
        assert _count(rag_db, "documents") == 0

    def test_cascades_to_chunks_and_removes_chunks_vec(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        doc_id = _insert_document(rag_db, url="https://example.com/a")
        chunk_id = _insert_chunk(rag_db, doc_id)
        _insert_chunk_vec(rag_db, chunk_id)

        assert mgr.delete_document("https://example.com/a") is True

        assert _count(rag_db, "documents") == 0
        assert _count(rag_db, "chunks") == 0
        assert _count(rag_db, "chunks_vec") == 0

    def test_does_not_affect_other_documents(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        doc_a = _insert_document(rag_db, url="https://example.com/a")
        doc_b = _insert_document(rag_db, url="https://example.com/b")
        chunk_a = _insert_chunk(rag_db, doc_a)
        chunk_b = _insert_chunk(rag_db, doc_b)
        _insert_chunk_vec(rag_db, chunk_a)
        _insert_chunk_vec(rag_db, chunk_b)

        assert mgr.delete_document("https://example.com/a") is True

        assert _count(rag_db, "documents") == 1
        assert _count(rag_db, "chunks") == 1
        assert _count(rag_db, "chunks_vec") == 1
        remaining = (
            sqlite3.connect(rag_db).execute("SELECT url FROM documents").fetchone()[0]
        )
        assert remaining == "https://example.com/b"

    def test_idempotent_second_delete_returns_false(self, rag_db: str) -> None:
        mgr = DocumentManager(rag_db_path=rag_db)
        _insert_document(rag_db, url="https://example.com/a")

        assert mgr.delete_document("https://example.com/a") is True
        assert mgr.delete_document("https://example.com/a") is False
