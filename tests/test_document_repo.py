"""
tests/test_document_repo.py
Behavior-lock tests for DocumentRepository.

SQLiteHelper is replaced with an in-memory SQLite connection so no
real DB file is required. The schema covers documents, chunks, and a
stub chunks_vec table (vec0 virtual table not needed).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from unittest.mock import patch

import pytest
from agent.document_repo import DocumentRepository

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT    NOT NULL UNIQUE,
    title         TEXT,
    lang          TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    etag          TEXT,
    last_modified TEXT
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
def repo() -> Generator[DocumentRepository]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()

    def _make(target: str = "rag") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
        yield DocumentRepository()


# ── list_documents() ───────────────────────────────────────────────────────────


class TestListDocuments:
    def test_empty_db_returns_empty_list(self, repo: DocumentRepository) -> None:
        assert repo.list_documents() == []

    def test_returns_documents(self, repo: DocumentRepository) -> None:
        with patch("agent.document_repo.SQLiteHelper", repo.__class__.__module__):
            pass

    def test_without_lang_filter(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://a.com", "A", "en"),
        )
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://b.com", "B", "ja"),
        )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            docs = DocumentRepository().list_documents()
        assert len(docs) == 2

    def test_with_lang_filter(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://a.com", "A", "en"),
        )
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://b.com", "B", "ja"),
        )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            docs = DocumentRepository().list_documents(lang="en")
        assert len(docs) == 1
        assert docs[0]["url"] == "https://a.com"
        assert docs[0]["lang"] == "en"

    def test_limit(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        for i in range(5):
            conn.execute(
                "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
                (f"https://{i}.com", f"Title{i}", "en"),
            )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            docs = DocumentRepository().list_documents(limit=2)
        assert len(docs) == 2

    def test_returns_correct_keys(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://a.com", "TitleA", "en"),
        )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            docs = DocumentRepository().list_documents()
        assert len(docs) == 1
        assert set(docs[0].keys()) == {
            "url",
            "title",
            "lang",
            "fetched_at",
            "chunk_count",
        }

    def test_db_error_returns_empty_list(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        fake = _FakeSQLiteHelper(conn)
        fake.fetchall = lambda sql, params: (_ for _ in ()).throw(Exception("DB error"))

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            docs = DocumentRepository().list_documents()
        assert docs == []


# ── delete_document() ──────────────────────────────────────────────────────────


class TestDeleteDocument:
    def test_not_found_returns_false(self, repo: DocumentRepository) -> None:
        assert repo.delete_document("https://nonexistent.com") is False

    def test_found_deletes_and_returns_true(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://a.com", "TitleA", "en"),
        )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            result = DocumentRepository().delete_document("https://a.com")
        assert result is True

    def test_db_error_returns_false(self, repo: DocumentRepository) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO documents (url, title, lang) VALUES (?, ?, ?)",
            ("https://a.com", "TitleA", "en"),
        )
        conn.commit()

        fake = _FakeSQLiteHelper(conn)
        real_execute = fake.execute

        def broken_execute(sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
            if "DELETE FROM chunks_vec" in sql:
                raise Exception("DB error")
            return real_execute(sql, params)

        fake.execute = broken_execute

        def _make(target: str = "rag") -> _FakeSQLiteHelper:
            return fake

        with patch("agent.document_repo.SQLiteHelper", side_effect=_make):
            result = DocumentRepository().delete_document("https://a.com")
        assert result is False
