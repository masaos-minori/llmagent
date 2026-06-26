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
        """Create sections table and FTS5 virtual table if they don't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_mtime REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
                    content,
                    file_path,
                    heading
                )
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS sections_ai AFTER INSERT ON sections
                BEGIN
                    INSERT INTO sections_fts(rowid, content, file_path, heading)
                    VALUES (new.id, new.content, new.file_path, new.heading);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS sections_ad AFTER DELETE ON sections
                BEGIN
                    INSERT INTO sections_fts(sections_fts, rowid, content)
                    VALUES ('delete', old.id, old.content);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS sections_au AFTER UPDATE ON sections
                BEGIN
                    INSERT INTO sections_fts(sections_fts, rowid, content)
                    VALUES ('delete', old.id, old.content);
                    INSERT INTO sections_fts(rowid, content, file_path, heading)
                    VALUES (new.id, new.content, new.file_path, new.heading);
                END
            """)
            conn.commit()
        finally:
            conn.close()

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
