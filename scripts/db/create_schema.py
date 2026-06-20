#!/usr/bin/env python3
"""create_schema.py
Initialize SQLite schemas for rag.sqlite (RAG pipeline) and session.sqlite (sessions/memory).

Creates the latest schema only. No migration logic.
Existing tables are protected by IF NOT EXISTS for idempotent re-runs.

SQL templates are in db/schema_sql.py.

Functions:
  create_rag_schema()     — rag.sqlite: documents, chunks, chunks_vec, chunks_fts, triggers
  create_session_schema() — session.sqlite: sessions, messages, notes, tool_results, memory
  create_schema()         — convenience wrapper calling both
"""

import logging
import sqlite3
import sys

from db.helper import SQLiteHelper
from db.schema_sql import build_rag_schema_sql, build_session_schema_sql
from db.store_protocols import get_embedding_dims

logger = logging.getLogger(__name__)


def _migrate_rag_schema(conn: sqlite3.Connection) -> None:
    """Add missing chunk columns idempotently."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
    if "chunk_type" not in existing:
        conn.execute("ALTER TABLE chunks ADD COLUMN chunk_type TEXT")
    if "source_file" not in existing:
        conn.execute("ALTER TABLE chunks ADD COLUMN source_file TEXT")


def create_rag_schema() -> None:
    """Create rag.sqlite tables, virtual tables, and triggers."""
    dims = get_embedding_dims()
    with SQLiteHelper("rag").open(write_mode=True) as db:
        try:
            db.conn.executescript(build_rag_schema_sql(dims))  # type: ignore[union-attr]  # conn is set by open()
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute RAG schema DDL: %s", e)
            raise
        _migrate_rag_schema(db.conn)  # type: ignore[arg-type]  # conn is set by open()
    logger.info("RAG schema created successfully.")


def create_session_schema() -> None:
    """Create session.sqlite tables for conversations, notes, tool results, and memory."""
    dims = get_embedding_dims()
    with SQLiteHelper("session").open(write_mode=True) as db:
        try:
            db.conn.executescript(build_session_schema_sql(dims))  # type: ignore[union-attr]  # conn is set by open()
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.error("Failed to execute session schema DDL: %s", e)
            raise
    logger.info("Session schema created successfully.")


def create_schema() -> None:
    """Create schemas for both rag.sqlite and session.sqlite."""
    create_rag_schema()
    create_session_schema()
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
