#!/usr/bin/env python3
"""
create_schema.py
Initialize the SQLite database schema including the sqlite-vec extension.
Run once only. Existing tables are protected by IF NOT EXISTS.
"""

import sys

from logger import Logger
from sqlite_helper import SQLiteHelper

# Entry script: use Logger with a dedicated log file.
logger = Logger(__name__, "/opt/llm/logs/create_schema.log")

# DDL for all tables, virtual tables, and triggers.
# chunks_fts uses external-content mode; triggers keep it in sync with chunks.
_SCHEMA_SQL: str = """
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
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
        chunk_id  INTEGER PRIMARY KEY,
        embedding float[384]
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
    CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
    AFTER DELETE ON chunks BEGIN
        DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
    END;
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT    NOT NULL DEFAULT (datetime('now')),
        title      TEXT
    );
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role       TEXT    NOT NULL,
        content    TEXT    NOT NULL,
        tool_calls TEXT,
        created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS notes (
        note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        content    TEXT    NOT NULL,
        created_at TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS tool_results (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        turn       INTEGER NOT NULL,
        tool_name  TEXT    NOT NULL,
        args_json  TEXT,
        full_text  TEXT    NOT NULL,
        summary    TEXT,
        is_error   INTEGER NOT NULL DEFAULT 0,
        created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    CREATE INDEX IF NOT EXISTS idx_tool_results_session
        ON tool_results(session_id);
"""


# ALTER TABLE statements for migrating existing databases.
# SQLite does not support IF NOT EXISTS on ADD COLUMN; errors are silently ignored.
_MIGRATE_SQL: list[str] = [
    "ALTER TABLE documents ADD COLUMN etag TEXT",
    "ALTER TABLE documents ADD COLUMN last_modified TEXT",
    # Add normalized_content column for FTS5/LLM content separation
    "ALTER TABLE chunks ADD COLUMN normalized_content TEXT",
    # Recreate triggers to use COALESCE(normalized_content, content) for FTS5 index
    "DROP TRIGGER IF EXISTS chunks_ai",
    "DROP TRIGGER IF EXISTS chunks_ad",
    "DROP TRIGGER IF EXISTS chunks_au",
    """CREATE TRIGGER IF NOT EXISTS chunks_ai
       AFTER INSERT ON chunks BEGIN
           INSERT INTO chunks_fts (rowid, content)
           VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
       END""",
    """CREATE TRIGGER IF NOT EXISTS chunks_ad
       AFTER DELETE ON chunks BEGIN
           INSERT INTO chunks_fts (chunks_fts, rowid, content)
           VALUES ('delete', old.chunk_id,
                   COALESCE(old.normalized_content, old.content));
       END""",
    """CREATE TRIGGER IF NOT EXISTS chunks_au
       AFTER UPDATE ON chunks BEGIN
           INSERT INTO chunks_fts (chunks_fts, rowid, content)
           VALUES ('delete', old.chunk_id,
                   COALESCE(old.normalized_content, old.content));
           INSERT INTO chunks_fts (rowid, content)
           VALUES (new.chunk_id, COALESCE(new.normalized_content, new.content));
       END""",
    # chunks_vec sync trigger: keep chunks_vec in sync with chunks on DELETE
    "DROP TRIGGER IF EXISTS chunks_vec_ad",
    """CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
       AFTER DELETE ON chunks BEGIN
           DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
       END""",
]


def _migrate_schema() -> None:
    """Add new columns/tables to existing databases; errors are silently ignored."""
    # CREATE TABLE IF NOT EXISTS for tables added after initial release
    _new_tables = [
        "CREATE TABLE IF NOT EXISTS notes ("
        "note_id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " content TEXT NOT NULL,"
        " created_at TEXT NOT NULL DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS tool_results ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " session_id INTEGER,"
        " turn INTEGER NOT NULL,"
        " tool_name TEXT NOT NULL,"
        " args_json TEXT,"
        " full_text TEXT NOT NULL,"
        " summary TEXT,"
        " is_error INTEGER NOT NULL DEFAULT 0,"
        " created_at TEXT NOT NULL DEFAULT"
        " (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')))",
        "CREATE INDEX IF NOT EXISTS idx_tool_results_session"
        " ON tool_results(session_id)",
    ]
    with SQLiteHelper().open(write_mode=True) as db:
        for stmt in _new_tables:
            try:
                db.execute(stmt)
            except Exception:
                pass
        for stmt in _MIGRATE_SQL:
            try:
                db.execute(stmt)
            except Exception:
                pass  # column already exists in this database
        db.commit()
    logger.info("Schema migration applied.")


def create_schema() -> None:
    """Create all tables, virtual tables, and triggers required by the RAG pipeline."""
    with SQLiteHelper().open() as db:
        assert db.conn is not None
        try:
            # executescript runs multiple DDL statements in one call and auto-commits.
            db.conn.executescript(_SCHEMA_SQL)
        except Exception as e:
            logger.error(f"Failed to execute schema DDL: {e}")
            raise
    _migrate_schema()
    logger.info("Schema created successfully.")


if __name__ == "__main__":
    try:
        create_schema()
    except Exception as e:
        logger.exception(f"Schema creation failed: {e}")
        sys.exit(1)
