#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/db_schema.py

Database schema creation for MdqService.

On open: create the tables when absent; when the mdq tables already exist,
validate them against the canonical shape (_CREATE_STATEMENTS) with the shared
fingerprint and refuse a mismatch with the archive-and-recreate message
(ADR-008: no automatic migration, no version stamping).

Dependency direction: db_schema → models
Import from here:  from mcp_servers.mdq.db_schema import create_production_tables
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from db.helper import apply_connection_pragmas
from shared.schema_fingerprint import assert_matches

logger = logging.getLogger(__name__)

_DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    mtime_ns INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at REAL NOT NULL
)
"""

_CHUNKS_DDL = """
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
"""

_CHUNKS_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    normalized_content,
    source_path,
    heading,
    heading_path,
    content_hash,
    content
)
"""

# FTS sync — triggers use rowid (chunks.rowid = implicit rowid of TEXT PK table).
_FTS_SYNC_TRIGGERS_DDL = (
    """
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks
BEGIN
    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
    VALUES (new.rowid, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
END
""",
    """
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks
BEGIN
    DELETE FROM chunks_fts WHERE rowid = old.rowid;
END
""",
    """
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks
BEGIN
    DELETE FROM chunks_fts WHERE rowid = old.rowid;
    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
    VALUES (new.rowid, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
END
""",
)

_INDEX_STATE_DDL = """
CREATE TABLE IF NOT EXISTS index_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

# Single source of the mdq shape: executed on create and passed to the
# fingerprint validator on open (the two can never drift apart).
_CREATE_STATEMENTS: tuple[str, ...] = (
    _DOCUMENTS_DDL,
    _CHUNKS_DDL,
    _CHUNKS_FTS_DDL,
    *_FTS_SYNC_TRIGGERS_DDL,
    _INDEX_STATE_DDL,
)


def create_production_tables(
    conn: sqlite3.Connection,
    db_path: str,
    sqlite_busy_timeout: int,
) -> None:
    """Create the production tables, or fingerprint-validate an existing database."""
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        apply_connection_pragmas(
            conn, busy_timeout_ms=sqlite_busy_timeout, write_mode=False
        )
        existing = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone()
        if existing is None:
            for ddl in _CREATE_STATEMENTS:
                conn.execute(ddl)
        else:
            # Present-but-different shape is refused, not repaired (ADR-008).
            assert_matches(
                conn, ";\n".join(_CREATE_STATEMENTS) + ";", label="mdq.sqlite"
            )
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.error("Failed to create production tables: %s", e)
        raise
