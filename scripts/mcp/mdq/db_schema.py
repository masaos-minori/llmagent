#!/usr/bin/env python3
"""mcp/mdq/db_schema.py

Database schema creation for MdqService.

Dependency direction: db_schema → models
Import from here:  from mcp.mdq.db_schema import create_production_tables, migrate_from_legacy
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import time
from pathlib import Path

from mcp.mdq.auth import authorize_path
from mcp.mdq.indexer import generate_chunk_id
from mcp.mdq.models import MdqAuthorizationError, MdqConsistencyError

logger = logging.getLogger(__name__)


def create_production_tables(
    conn: sqlite3.Connection,
    db_path: str,
    use_embedding: bool,
    vector_table: str,
    embedding_dims: int,
    sqlite_busy_timeout: int,
) -> None:
    """Create production tables and migrate from legacy schema if needed."""
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout = {sqlite_busy_timeout}")
        # Check for legacy schema
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        if "sections" in tables:
            logger.info("Migrating from legacy sections schema")
            migrate_from_legacy(conn)
            return

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunk_summaries (
                chunk_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                summary_model TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create vector table conditionally based on use_embedding config
        if use_embedding:
            vec0_path: str = "/opt/llm/sqlite-vec/vec0.so"
            try:
                conn.enable_load_extension(True)
                try:
                    conn.load_extension(vec0_path)
                except sqlite3.OperationalError as inner:
                    # Some SQLite builds auto-append .so, causing .so.so
                    if ".so.so" in str(inner) and vec0_path.endswith(".so"):
                        conn.load_extension(vec0_path[:-3])
                    else:
                        raise
                conn.enable_load_extension(False)
            except sqlite3.OperationalError as e:
                conn.enable_load_extension(False)
                logger.error("Failed to load sqlite-vec extension: %s", e)
                raise
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {vector_table} USING vec0(
                    chunk_id TEXT PRIMARY KEY,
                    embedding float[{embedding_dims}]
                )
            """)
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.error("Failed to create production tables: %s", e)
        raise


def migrate_from_legacy(conn: sqlite3.Connection) -> None:
    """Migrate data from legacy sections/sections_fts to new schema."""
    try:
        # Read legacy data
        rows = conn.execute(
            "SELECT id, file_path, heading, content, file_mtime FROM sections"
        ).fetchall()

        # Create new tables (they may not exist yet)
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

        # Track unique documents by file_path
        doc_map: dict[str, dict] = {}

        for row in rows:
            legacy_id, file_path, heading, content, file_mtime = row
            normalized_content = " ".join(content.split())

            # Get or create document record
            if file_path not in doc_map:
                doc_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
                doc_id = f"doc_{doc_hash}"
                doc_map[file_path] = {
                    "doc_id": doc_id,
                    "source_path": file_path,
                    "mtime_ns": int(file_mtime * 1e9),
                    "size_bytes": len(content.encode("utf-8")),
                    "content_hash": hashlib.sha256(
                        (file_path + str(file_mtime)).encode()
                    ).hexdigest(),
                    "indexed_at": time.time(),
                }

            # Create chunk record
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunk_id = generate_chunk_id(
                Path(file_path).resolve().as_posix(), "", 0, content_hash
            )
            conn.execute(
                "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk_id,
                    doc_map[file_path]["doc_id"],
                    file_path,
                    heading,
                    "",
                    0,
                    0,
                    content,
                    normalized_content,
                    1,
                    len(content.splitlines()),
                    len(content),
                    None,
                    content_hash,
                    None,
                    time.time(),
                ),
            )

        # Insert documents
        for doc in doc_map.values():
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    doc["doc_id"],
                    doc["source_path"],
                    doc["mtime_ns"],
                    doc["size_bytes"],
                    doc["content_hash"],
                    doc["indexed_at"],
                ),
            )

        # Drop legacy tables
        conn.execute("DROP TABLE IF EXISTS sections_fts")
        conn.execute("DROP TABLE IF EXISTS sections")
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
        chunk_count = sum(1 for _ in conn.execute("SELECT 1 FROM chunks"))
        logger.info(
            "Migration from legacy schema complete: %d documents, %d chunks",
            len(doc_map),
            chunk_count,
        )
    except Exception as e:
        conn.rollback()
        logger.error("Migration failed: %s", e)
        raise
