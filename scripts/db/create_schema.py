#!/usr/bin/env python3
"""create_schema.py
Initialize SQLite schemas for rag.sqlite (RAG pipeline) and session.sqlite (sessions/memory).

Creates the latest schema only. No migration logic.
Existing tables are protected by IF NOT EXISTS for idempotent re-runs.

SQL templates are in db/schema_sql.py.

Functions:
  create_rag_schema()        — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema()    — session.sqlite: sessions, messages, tool_results, memory
  create_workflow_schema()   — workflow.sqlite: tasks, attempts, processed_events, artifacts, approvals
  create_schema()            — convenience wrapper calling all three
"""

import logging
import sqlite3
import sys

from db.helper import SQLiteHelper
from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)


def _migrate_rag_schema(conn: sqlite3.Connection) -> None:
    """Add missing chunk columns idempotently."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
    if "chunk_type" not in existing:
        conn.execute("ALTER TABLE chunks ADD COLUMN chunk_type TEXT")
    if "source_file" not in existing:
        conn.execute("ALTER TABLE chunks ADD COLUMN source_file TEXT")


def _migrate_add_undone_column(conn: sqlite3.Connection) -> None:
    """Add undone column to tool_results if not already present."""
    existing = {
        row[1] for row in conn.execute("PRAGMA table_info(tool_results)").fetchall()
    }
    if "undone" not in existing:
        conn.execute(
            "ALTER TABLE tool_results ADD COLUMN undone INTEGER NOT NULL DEFAULT 0"
        )
        conn.commit()


def _migrate_session_schema(conn: sqlite3.Connection) -> None:
    """Add FK constraint to tool_results.session_id if not already present."""
    fk_info = conn.execute("PRAGMA foreign_key_list(tool_results)").fetchall()
    if fk_info:
        return

    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        BEGIN;
        CREATE TABLE tool_results_new (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
            turn       INTEGER NOT NULL,
            tool_name  TEXT    NOT NULL,
            args_masked  TEXT,
            full_text  TEXT    NOT NULL,
            summary    TEXT,
            is_error   INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
        INSERT INTO tool_results_new
            SELECT id, session_id, turn, tool_name, args_masked, full_text, summary, is_error, created_at
            FROM tool_results;
        DROP TABLE tool_results;
        ALTER TABLE tool_results_new RENAME TO tool_results;
        CREATE INDEX IF NOT EXISTS idx_tool_results_session ON tool_results(session_id);
        COMMIT;
    """)


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        try:
            db.executescript(build_rag_schema_sql(dims))
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute RAG schema DDL: %s", e)
            raise
        _migrate_rag_schema(db.conn)  # type: ignore[arg-type]  # conn is set by open()
    logger.info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations, tool results, and memory."""
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True) as db:
        try:
            db.executescript(build_session_schema_sql(dims))
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute session schema DDL: %s", e)
            raise
        _migrate_session_schema(db.conn)  # type: ignore[arg-type]  # conn is set by open()
        _migrate_add_undone_column(db.conn)  # type: ignore[arg-type]
    logger.info("Session schema created successfully.")


def create_workflow_schema() -> None:
    """Create workflow.sqlite tables (tasks, attempts, processed_events, artifacts, approvals)."""
    with SQLiteHelper("workflow").open(write_mode=True) as db:
        try:
            db.executescript(build_workflow_schema_sql())
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute workflow schema DDL: %s", e)
            raise
    logger.info("Workflow schema created successfully.")


def create_schema() -> None:
    """Create schemas for rag.sqlite, session.sqlite, and workflow.sqlite."""
    create_rag_schema()
    create_session_schema()
    create_workflow_schema()
    logger.info("All schemas created successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        create_schema()
    except (
        RuntimeError,
        sqlite3.OperationalError,
        sqlite3.DatabaseError,
        OSError,
    ) as e:
        logger.exception("Schema creation failed: %s", e)
        sys.exit(1)
