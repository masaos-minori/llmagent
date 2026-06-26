#!/usr/bin/env python3
"""mcp/mdq/service.py
Main service class for Mdq functionality — SQLite FTS5-backed.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.auth import authorize_path
from mcp.mdq.indexer import index_paths as _index_paths
from mcp.mdq.models import (
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqServiceError,
    OutlineRequest,
    ParseMarkdownRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp.mdq.parser import parse_markdown
from mcp.mdq.search import search_docs

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MdqService:
    """Main service class for Mdq functionality."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or "/opt/llm/db/mdq.sqlite"
        self._allowed_dirs: list[str] = []
        try:
            from shared.config_loader import ConfigLoader

            cfg = ConfigLoader().load_all()
            mdq_cfg = cfg.get("mdq_mcp_server", {}) if isinstance(cfg.get("mdq_mcp_server"), dict) else {}
            self._allowed_dirs = mdq_cfg.get("allowed_dirs") or []
        except (FileNotFoundError, KeyError, TypeError):
            self._allowed_dirs = []
        self._init_db()

    @property
    def allowed_dirs(self) -> list[str]:
        """Return the configured allowed directories for file access."""
        return self._allowed_dirs

    def _init_db(self) -> None:
        """Create production tables and migrate from legacy schema if needed."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            # Check for legacy schema
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "sections" in tables:
                logger.info("Migrating from legacy sections schema")
                self._migrate_from_legacy(conn)
                return

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
            # Triggers for FTS sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks
                BEGIN
                    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                    VALUES (new.chunk_id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks
                BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.chunk_id);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks
                BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.chunk_id);
                    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                    VALUES (new.chunk_id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
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

    def _migrate_from_legacy(self, conn: sqlite3.Connection) -> None:
        """Migrate data from legacy sections/sections_fts to new schema."""
        try:
            # Read legacy data
            rows = conn.execute("SELECT id, file_path, heading, content, file_mtime FROM sections").fetchall()

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
                    import hashlib
                    import time

                    doc_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
                    doc_id = f"doc_{doc_hash}"
                    doc_map[file_path] = {
                        "doc_id": doc_id,
                        "source_path": file_path,
                        "mtime_ns": int(file_mtime * 1e9),
                        "size_bytes": len(content.encode("utf-8")),
                        "content_hash": hashlib.sha256((file_path + str(file_mtime)).encode()).hexdigest(),
                        "indexed_at": time.time(),
                    }

                # Create chunk record
                import hashlib
                import time

                chunk_id = f"chunk_{hashlib.sha256(f'{file_path}:{legacy_id}'.encode()).hexdigest()[:16]}"
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
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
                    (doc["doc_id"], doc["source_path"], doc["mtime_ns"], doc["size_bytes"], doc["content_hash"], doc["indexed_at"]),
                )

            # Drop legacy tables
            conn.execute("DROP TABLE IF EXISTS sections_fts")
            conn.execute("DROP TABLE IF EXISTS sections")
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks
                BEGIN
                    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                    VALUES (new.chunk_id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks
                BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.chunk_id);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks
                BEGIN
                    INSERT INTO chunks_fts(chunks_fts, rowid) VALUES ('delete', old.chunk_id);
                    INSERT INTO chunks_fts(rowid, normalized_content, source_path, heading, heading_path, content_hash, content)
                    VALUES (new.chunk_id, new.normalized_content, new.source_path, new.heading, new.heading_path, new.content_hash, new.content);
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
            logger.info("Migration from legacy schema complete: %d documents, %d chunks", len(doc_map), chunk_count)
        except Exception as e:
            conn.rollback()
            logger.error("Migration failed: %s", e)
            raise

    def _get_db_connection(self) -> sqlite3.Connection:
        """Return a connection to the mdq database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def search_docs(self, req: SearchDocsRequest) -> str:
        """Search indexed Markdown sections by query."""
        return await search_docs(self, req)

    async def get_chunk(self, req: GetChunkRequest) -> str:
        """Retrieve a Markdown chunk by its ID."""
        conn = self._get_db_connection()
        try:
            row = conn.execute(
                "SELECT heading, content FROM sections WHERE id = ?",
                (req.chunk_id,),
            ).fetchone()
            if row is None:
                return f"Chunk {req.chunk_id} not found"
            return f"## {row['heading']}\n\n{row['content']}"
        finally:
            conn.close()

    async def outline(self, req: OutlineRequest) -> str:
        """Get the heading structure of a Markdown file."""
        p = Path(req.path)
        if not p.exists():
            return f"File not found: {req.path}"
        if not authorize_path(p, self.allowed_dirs):
            logger.warning("Path denied: %s (outside allowed dirs)", req.path)
            raise MdqServiceError(f"Access denied: {req.path} is outside allowed directories")
        sections = await parse_markdown(self, ParseMarkdownRequest(path=req.path))
        headings = [s["heading"] for s in sections]
        return "\n".join(headings) if headings else "(no headings)"

    async def index_paths(self, req: IndexPathsRequest) -> str:
        """Index a set of paths into the in-process SQLite DB."""
        return await _index_paths(self, req)

    async def refresh_index(self, req: RefreshIndexRequest) -> str:
        """Incrementally refresh the index for a set of paths."""
        from mcp.mdq.models import IndexPathsRequest  # noqa: PLC0415

        for path_str in req.paths:
            p = Path(path_str)
            if not p.exists():
                logger.warning("Path does not exist: %s", path_str)
                continue
            if not authorize_path(p, self.allowed_dirs):
                logger.warning("Path denied: %s (outside allowed dirs)", path_str)
                continue

        return await _index_paths(self, IndexPathsRequest(paths=req.paths))

    async def stats(self, req: StatsRequest) -> str:
        """Return document/chunk count and index metadata."""
        conn = self._get_db_connection()
        try:
            chunk_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM sections"
            ).fetchone()["cnt"]
            doc_count = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as cnt FROM sections"
            ).fetchone()["cnt"]
            return f"Documents: {doc_count}, Chunks: {chunk_count}"
        finally:
            conn.close()

    async def grep_docs(self, req: GrepDocsRequest) -> str:
        """Search Markdown chunks with a regex pattern."""
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            return f"Invalid regex pattern: {e}"

        conn = self._get_db_connection()
        try:
            matches = []
            rows = conn.execute("SELECT id, heading, content FROM sections").fetchall()
            for row in rows:
                if compiled.search(row["content"]) or compiled.search(row["heading"]):
                    matches.append(
                        f"Chunk {row['id']}: {row['heading']}\n{row['content'][:200]}"
                    )
            if not matches:
                return "No matches found."
            return "\n---\n".join(matches)
        finally:
            conn.close()
