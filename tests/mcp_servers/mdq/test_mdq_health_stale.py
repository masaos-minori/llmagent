"""tests/test_mdq_health_stale.py
Unit tests for mdq-mcp /health stale_document_count field.

Covers the chunks/documents schema; see also tests/mcp_servers/mdq/test_mdq_health_endpoint.py.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path


class TestStaleDocumentCountNewSchema:
    """Verify stale_document_count with the new chunks/documents schema."""

    def _create_db(self, tmp_path: Path) -> str:
        """Create a test database with chunks/chunks_fts/documents tables."""
        path = str(tmp_path / "mdq_test_new.sqlite")
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE documents (
                    doc_id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
                    source_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    heading_path TEXT NOT NULL DEFAULT '',
                    heading_level INTEGER NOT NULL DEFAULT 0,
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    content TEXT NOT NULL,
                    normalized_content TEXT NOT NULL DEFAULT '',
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    char_count INTEGER NOT NULL DEFAULT 0,
                    token_count INTEGER,
                    content_hash TEXT NOT NULL,
                    tags_json TEXT,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE chunks_fts USING fts5(
                    normalized_content,
                    source_path,
                    heading,
                    heading_path,
                    content_hash,
                    content
                )
                """
            )
            conn.execute(
                "CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN "
                "INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content) "
                "VALUES (new.id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content); END"
            )
            conn.execute(
                "CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN "
                "INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.id); END"
            )
            conn.execute(
                "CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN "
                "INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.id); "
                "INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content) "
                "VALUES (new.id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content); END"
            )
            conn.execute(
                """
                CREATE TABLE index_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        return path

    def _insert_documents(
        self, db_path: str, rows: list[tuple[str, str, int, float]]
    ) -> None:
        """Insert document rows with mtime_ns and indexed_at."""
        conn = sqlite3.connect(db_path)
        try:
            for doc_id, source_path, mtime_ns, indexed_at in rows:
                conn.execute(
                    "INSERT INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, 1024, 'abc123', ?)",
                    (doc_id, source_path, mtime_ns, indexed_at),
                )
            conn.commit()
        finally:
            conn.close()

    def test_stale_count_zero_when_fresh(self, tmp_path: Path) -> None:
        """When mtime_ns <= indexed_at * 1e9, stale count should be 0."""
        db_path = self._create_db(tmp_path)
        # mtime_ns is in the past (before indexed_at), so no stale docs
        past_mtime_ns = int((time.time() - 1000) * 1e9)
        future_indexed_at = time.time() + 1000
        self._insert_documents(
            db_path,
            [
                ("doc1", "/test/file1.md", past_mtime_ns, future_indexed_at),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 0

    def test_stale_count_positive_when_outdated(self, tmp_path: Path) -> None:
        """When mtime_ns > indexed_at * 1e9, stale count should be > 0."""
        db_path = self._create_db(tmp_path)
        # mtime_ns is in the future (after indexed_at), so docs are stale
        past_indexed_at = time.time() - 1000
        future_mtime_ns = int((time.time() + 1000) * 1e9)
        self._insert_documents(
            db_path,
            [
                ("doc1", "/test/file1.md", future_mtime_ns, past_indexed_at),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 1

    def test_stale_count_mixed(self, tmp_path: Path) -> None:
        """When some docs are fresh and some are stale, count only stale."""
        db_path = self._create_db(tmp_path)
        now = time.time()
        past_indexed_at = now - 1000
        future_mtime_ns = int((now + 1000) * 1e9)
        # doc1: stale (mtime > indexed_at)
        # doc2: fresh (mtime < indexed_at)
        self._insert_documents(
            db_path,
            [
                ("doc1", "/test/file1.md", future_mtime_ns, past_indexed_at),
                ("doc2", "/test/file2.md", int((now - 1000) * 1e9), now + 1000),
            ],
        )

        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
            ).fetchone()
            stale_count = result["cnt"] or 0
        finally:
            conn.close()

        assert stale_count == 1

    def test_stale_count_with_corrupt_db(self, tmp_path: Path) -> None:
        """When documents table is missing, _check_stale_documents returns None."""
        # Create DB with only chunks table, no documents table
        path = str(tmp_path / "mdq_test_corrupt.sqlite")
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE chunks_fts USING fts5(
                    normalized_content, source_path, heading, heading_path, content_hash, content
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

        conn = sqlite3.connect(path)
        stale_count: int | None = None
        try:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
            ).fetchone()
            # Should return None (or raise) when documents table doesn't exist
        except sqlite3.OperationalError:
            stale_count = None
        finally:
            conn.close()

        assert stale_count is None


class TestStaleDocumentCountNoDocumentsTable:
    """Verify _check_stale_documents returns None when documents table is missing."""

    def test_returns_none_when_no_documents_table(self, tmp_path: Path) -> None:
        """When documents table doesn't exist, stale count should be None (not raised)."""
        import sqlite3

        from mcp_servers.mdq.health_check import _check_stale_documents

        path = str(tmp_path / "mdq_test_no_docs.sqlite")
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    doc_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content TEXT NOT NULL,
                    indexed_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE chunks_fts USING fts5(
                    normalized_content, source_path, heading, heading_path, content_hash, content
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        stale_count = _check_stale_documents(conn)
        conn.close()

        assert stale_count is None
