#!/usr/bin/env python3
"""mcp_servers/mdq/db_schema.py

Database schema creation for MdqService.

Dependency direction: db_schema → models
Import from here:  from mcp_servers.mdq.db_schema import create_production_tables
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from db.helper import apply_connection_pragmas

logger = logging.getLogger(__name__)


def create_production_tables(
    conn: sqlite3.Connection,
    db_path: str,
    sqlite_busy_timeout: int,
) -> None:
    """Create production tables and migrate from legacy schema if needed."""
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        apply_connection_pragmas(
            conn, busy_timeout_ms=sqlite_busy_timeout, write_mode=False
        )

        # Detect and rebuild old schema (id INTEGER PK + chunk_id TEXT UNIQUE)
        old_col = conn.execute("PRAGMA table_info(chunks)").fetchone()
        if old_col is not None and old_col[1] == "id":  # index 1 = name column
            logger.info(
                "Detected old chunks schema (id column); rebuilding to chunk_id PRIMARY KEY"
            )
            conn.execute("DROP TABLE IF EXISTS chunks_fts")
            conn.execute("DROP TABLE IF EXISTS chunks")
            conn.execute("DROP TRIGGER IF EXISTS chunks_ai")
            conn.execute("DROP TRIGGER IF EXISTS chunks_ad")
            conn.execute("DROP TRIGGER IF EXISTS chunks_au")

        # Create production tables
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

        # Triggers for FTS sync — use rowid (chunks.rowid = implicit rowid of TEXT PK table)
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
                DELETE FROM chunks_fts WHERE rowid = old.rowid;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks
            BEGIN
                DELETE FROM chunks_fts WHERE rowid = old.rowid;
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
    except sqlite3.OperationalError as e:
        logger.error("Failed to create production tables: %s", e)
        raise
