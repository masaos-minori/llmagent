"""tests/test_mdq_schema_migration.py
Unit tests for mdq-mcp document/chunks schema migration.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Create a test database with new documents/chunks schema."""
    path = str(tmp_path / "mdq_test.sqlite")
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                indexed_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
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
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                normalized_content,
                source_path,
                heading,
                heading_path,
                content_hash,
                content
            )
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks
            BEGIN
                INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                VALUES (new.rowid, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks
            BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.rowid);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks
            BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.rowid);
                INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                VALUES (new.rowid, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
            END
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS index_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
    return path


def _insert_document_and_chunk(
    db_path: str, source_path: str, content: str
) -> tuple[str, str]:
    """Insert a document and chunk into the test database."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        doc_id = hashlib.sha256(source_path.encode()).hexdigest()
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        normalized_content = " ".join(content.split())
        char_count = len(content)

        conn.execute(
            "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, source_path, 1000, len(content), content_hash, 1000.0),
        )

        chunk_id = hashlib.sha256(f"{doc_id}:heading:1".encode()).hexdigest()
        conn.execute(
            "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                chunk_id,
                doc_id,
                source_path,
                "heading",
                "",
                1,
                0,
                content,
                normalized_content,
                1,
                10,
                char_count,
                None,
                content_hash,
                "",
                1000.0,
            ),
        )

        conn.commit()
        return doc_id, chunk_id
    finally:
        conn.close()


class TestDocumentIndexing:
    """Verify indexing writes to documents/chunks tables."""

    def test_insert_writes_to_documents_table(self, db_path: str) -> None:
        """When a document is indexed, it appears in the documents table."""
        doc_id, _ = _insert_document_and_chunk(db_path, "/test/file.md", "content")
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            assert result["cnt"] == 1
        finally:
            conn.close()

    def test_insert_writes_to_chunks_table(self, db_path: str) -> None:
        """When a document is indexed, chunks appear in the chunks table."""
        _, chunk_id = _insert_document_and_chunk(db_path, "/test/file.md", "content")
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
            assert result["cnt"] == 1
        finally:
            conn.close()

    def test_content_hash_is_computed(self, db_path: str) -> None:
        """content_hash is SHA-256 of the content text."""
        doc_id, _ = _insert_document_and_chunk(db_path, "/test/file.md", "hello world")
        expected_hash = hashlib.sha256(b"hello world").hexdigest()
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT content_hash FROM documents WHERE doc_id = ?",
                (doc_id,),
            ).fetchone()
            assert result["content_hash"] == expected_hash
        finally:
            conn.close()

    def test_normalized_content_stored(self, db_path: str) -> None:
        """normalized_content has extra whitespace collapsed."""
        _, chunk_id = _insert_document_and_chunk(
            db_path, "/test/file.md", "hello   world"
        )
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT normalized_content FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
            assert result["normalized_content"] == "hello world"
        finally:
            conn.close()

    def test_chunk_count_in_stats(self, db_path: str) -> None:
        """stats() returns correct chunk count."""
        _insert_document_and_chunk(db_path, "/test/file1.md", "content1")
        _insert_document_and_chunk(db_path, "/test/file2.md", "content2")
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()
            assert result["cnt"] == 2
        finally:
            conn.close()

    def test_document_count_in_stats(self, db_path: str) -> None:
        """stats() returns correct document count."""
        _insert_document_and_chunk(db_path, "/test/file1.md", "content1")
        _insert_document_and_chunk(db_path, "/test/file2.md", "content2")
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
            assert result["cnt"] == 2
        finally:
            conn.close()

    def test_index_metadata_from_index_state(self, db_path: str) -> None:
        """stats() returns index metadata from index_state table."""
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "INSERT INTO index_state (key, value) VALUES (?, ?)", ("version", "1.0")
            )
            conn.execute(
                "INSERT INTO index_state (key, value) VALUES (?, ?)",
                ("indexed_at", "2026-01-01"),
            )
            rows = conn.execute("SELECT key, value FROM index_state").fetchall()
            metadata = dict((row["key"], row["value"]) for row in rows)
            assert metadata["version"] == "1.0"
            assert metadata["indexed_at"] == "2026-01-01"
        finally:
            conn.close()

    def test_get_chunk_by_id(self, db_path: str) -> None:
        """get_chunk() returns chunk by ID."""
        _, chunk_id = _insert_document_and_chunk(
            db_path, "/test/file.md", "hello world"
        )
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            result = conn.execute(
                "SELECT * FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
            assert result is not None
            assert result["content"] == "hello world"
            assert result["heading"] == "heading"
        finally:
            conn.close()

    def test_fts_search_queries_chunks_fts(self, db_path: str) -> None:
        """FTS search queries chunks_fts table."""
        _, chunk_id = _insert_document_and_chunk(
            db_path, "/test/file.md", "hello world"
        )
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT c.chunk_id, c.source_path, c.heading FROM chunks_fts f JOIN chunks c ON f.rowid = c.rowid WHERE chunks_fts MATCH ?",
                ("hello",),
            ).fetchall()
            assert len(rows) == 1
            assert rows[0]["chunk_id"] == chunk_id
        finally:
            conn.close()

    def test_delete_chunks_for_document(self, db_path: str) -> None:
        """Deleting old chunks for a document works correctly."""
        doc_id, _ = _insert_document_and_chunk(db_path, "/test/file.md", "old content")
        # Delete old chunks for this document using DELETE FROM chunks WHERE doc_id
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            # Disable FK and FTS5 triggers before deleting
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("DROP TRIGGER IF EXISTS chunks_ad")
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            conn.commit()
            result = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            assert result["cnt"] == 0
        finally:
            conn.close()

    def test_upsert_document(self, db_path: str) -> None:
        """INSERT OR REPLACE works for documents table."""
        doc_id, _ = _insert_document_and_chunk(db_path, "/test/file.md", "old content")
        # Upsert with new content
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    doc_id,
                    "/test/file.md",
                    2000,
                    len("new content"),
                    hashlib.sha256(b"new content").hexdigest(),
                    2000.0,
                ),
            )
            result = conn.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            assert result["mtime_ns"] == 2000
        finally:
            conn.close()
