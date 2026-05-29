#!/usr/bin/env python3
"""
create_schema.py
Initialize SQLite schemas for rag.sqlite (RAG pipeline) and session.sqlite (sessions/memory).
Run once only. Existing tables are protected by IF NOT EXISTS.

Functions:
  create_rag_schema()     — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema() — session.sqlite: sessions, messages, notes, tool_results, memory
  create_schema()         — convenience wrapper calling both
"""

import sys

from shared.logger import Logger

from db.helper import SQLiteHelper

# Entry script: use Logger with a dedicated log file.
logger = Logger(__name__, "/opt/llm/logs/create_schema.log")

# DDL for rag.sqlite: document storage and vector/FTS search.
_RAG_SCHEMA_SQL: str = """
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
"""

# DDL for session.sqlite: conversation history, notes, tool results, memory.
_SESSION_SCHEMA_SQL: str = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT    NOT NULL DEFAULT (datetime('now')),
        title      TEXT
    );
    CREATE TABLE IF NOT EXISTS messages (
        message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  INTEGER NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role        TEXT    NOT NULL,
        content     TEXT    NOT NULL,
        tool_calls  TEXT,
        tool_call_id TEXT,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
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
    CREATE TABLE IF NOT EXISTS memory_entries (
        entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        mem_type   TEXT NOT NULL CHECK (mem_type IN ('long_term', 'task')),
        content    TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS memory_vec USING vec0(
        entry_id  INTEGER PRIMARY KEY,
        embedding float[384]
    );
"""

# ALTER TABLE migration statements for rag.sqlite.
_RAG_MIGRATE_SQL: list[str] = [
    "ALTER TABLE documents ADD COLUMN etag TEXT",
    "ALTER TABLE documents ADD COLUMN last_modified TEXT",
    "ALTER TABLE chunks ADD COLUMN normalized_content TEXT",
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
    "DROP TRIGGER IF EXISTS chunks_vec_ad",
    """CREATE TRIGGER IF NOT EXISTS chunks_vec_ad
       AFTER DELETE ON chunks BEGIN
           DELETE FROM chunks_vec WHERE chunk_id = old.chunk_id;
       END""",
]

# ALTER TABLE migration statements for session.sqlite.
_SESSION_MIGRATE_SQL: list[str] = [
    "ALTER TABLE messages ADD COLUMN tool_call_id TEXT",
    "CREATE VIRTUAL TABLE IF NOT EXISTS memory_vec USING vec0("
    "entry_id INTEGER PRIMARY KEY, embedding float[384])",
]


def _run_migrations(db: SQLiteHelper, stmts: list[str]) -> None:
    """Execute migration DDL statements; silently ignore column-already-exists errors."""
    for stmt in stmts:
        try:
            db.execute(stmt)
        except Exception:
            pass
    db.commit()


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    with SQLiteHelper("rag").open(write_mode=True) as db:
        assert db.conn is not None
        try:
            db.conn.executescript(_RAG_SCHEMA_SQL)
        except Exception as e:
            logger.error(f"Failed to execute RAG schema DDL: {e}")
            raise
        _run_migrations(db, _RAG_MIGRATE_SQL)
    logger.info("RAG schema created/migrated successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations, notes, tool results, and memory."""
    with SQLiteHelper("session").open(write_mode=True) as db:
        assert db.conn is not None
        try:
            db.conn.executescript(_SESSION_SCHEMA_SQL)
        except Exception as e:
            logger.error(f"Failed to execute session schema DDL: {e}")
            raise
        _run_migrations(db, _SESSION_MIGRATE_SQL)
        # Verify tool_call_id column exists after migration.
        cols = [row[1] for row in db.fetchall("PRAGMA table_info(messages)")]
        if "tool_call_id" not in cols:
            logger.error(
                "Migration check failed: messages.tool_call_id column not found."
                " Run manually: ALTER TABLE messages ADD COLUMN tool_call_id TEXT"
            )
    logger.info("Session schema created/migrated successfully.")


def create_schema() -> None:
    """Create schemas for both rag.sqlite and session.sqlite."""
    create_rag_schema()
    create_session_schema()
    logger.info("All schemas created successfully.")


if __name__ == "__main__":
    try:
        create_schema()
    except Exception as e:
        logger.exception(f"Schema creation failed: {e}")
        sys.exit(1)
