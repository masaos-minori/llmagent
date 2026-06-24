"""tests/test_fts_sync.py
In-memory SQLite tests for FTS5 trigger synchronization (chunks <-> chunks_fts).
"""

from __future__ import annotations

import sqlite3

import pytest

# Minimal RAG schema for FTS trigger tests; chunks_vec is stubbed (vec0 not required).
_FTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url                TEXT    NOT NULL UNIQUE,
    lang               TEXT    NOT NULL CHECK (lang IN ('ja', 'en')),
    fetched_at         TEXT    NOT NULL DEFAULT (datetime('now'))
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


@pytest.fixture()
def db() -> sqlite3.Connection:
    """In-memory SQLite with RAG schema and FTS5 triggers."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_FTS_SCHEMA_SQL)
    conn.commit()
    return conn


class TestFtsTriggerSync:
    def test_insert_syncs_to_fts(self, db: sqlite3.Connection) -> None:
        """Inserting a chunk automatically adds it to chunks_fts."""
        db.execute(
            "INSERT INTO documents(url, lang) VALUES(?, ?)", ("http://a.com", "en")
        )
        doc_id = db.execute("SELECT doc_id FROM documents").fetchone()["doc_id"]
        db.execute(
            "INSERT INTO chunks(doc_id, content, normalized_content, chunk_index) VALUES(?,?,?,?)",
            (doc_id, "hello world", "hello world", 0),
        )
        db.commit()
        rows = db.execute(
            "SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'hello'"
        ).fetchall()
        assert len(rows) == 1

    def test_delete_removes_from_fts(self, db: sqlite3.Connection) -> None:
        """Deleting a chunk removes it from chunks_fts."""
        db.execute(
            "INSERT INTO documents(url, lang) VALUES(?,?)", ("http://b.com", "en")
        )
        doc_id = db.execute("SELECT doc_id FROM documents").fetchone()["doc_id"]
        db.execute(
            "INSERT INTO chunks(doc_id, content, normalized_content, chunk_index) VALUES(?,?,?,?)",
            (doc_id, "delete me", "delete me", 0),
        )
        db.commit()
        chunk_id = db.execute("SELECT chunk_id FROM chunks").fetchone()["chunk_id"]
        db.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))
        db.commit()
        rows = db.execute(
            "SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'delete'"
        ).fetchall()
        assert len(rows) == 0

    def test_rollback_does_not_leave_orphan(self, db: sqlite3.Connection) -> None:
        """Rolling back a transaction does not leave orphan FTS entries."""
        db.execute("BEGIN")
        db.execute(
            "INSERT INTO documents(url, lang) VALUES(?,?)", ("http://c.com", "en")
        )
        doc_id = db.execute("SELECT doc_id FROM documents").fetchone()["doc_id"]
        db.execute(
            "INSERT INTO chunks(doc_id, content, normalized_content, chunk_index) VALUES(?,?,?,?)",
            (doc_id, "rollback test", "rollback test", 0),
        )
        db.execute("ROLLBACK")
        rows = db.execute(
            "SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'rollback'"
        ).fetchall()
        assert len(rows) == 0
