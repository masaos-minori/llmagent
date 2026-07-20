#!/usr/bin/env python3
"""mcp_servers/mdq/service.py

Main service class for Mdq functionality — SQLite FTS5-backed.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sqlite3
from pathlib import Path

from db.helper import apply_connection_pragmas

from mcp_servers.mdq.auth import authorize_path
from mcp_servers.mdq.db_grep import grep_docs
from mcp_servers.mdq.db_schema import create_production_tables
from mcp_servers.mdq.indexer import (
    RefreshSummary,
)
from mcp_servers.mdq.indexer import (
    index_paths as _index_paths,
)
from mcp_servers.mdq.indexer import (
    refresh_paths as _refresh_paths,
)
from mcp_servers.mdq.mdq_models import (
    STALE_SQL_CONDITION,
    GetChunkRequest,
    GrepDocsMetadata,
    GrepDocsRequest,
    IndexPathsMetadata,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqConfig,
    MdqNotFoundError,
    MdqValidationError,
    OutlineHeading,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsMetadata,
    SearchDocsRequest,
    StatsRequest,
    is_stale,
)
from mcp_servers.mdq.search import search_docs

logger = logging.getLogger(__name__)


class MdqService:
    """Main service class for Mdq functionality."""

    def __init__(self, db_path: str | None = None):
        """Initialize the MDQ service with database path and configuration from TOML file."""
        try:
            from shared.config_loader import ConfigLoader

            mdq_cfg = ConfigLoader().load("mdq_mcp_server.toml")
        except (FileNotFoundError, KeyError, TypeError):
            mdq_cfg = {}

        cfg = MdqConfig(**mdq_cfg)  # raises pydantic.ValidationError on invalid values
        self.db_path = db_path or mdq_cfg.get("db_path", "/opt/llm/db/mdq.sqlite")
        self._allowed_dirs = cfg.allowed_dirs
        self.include_globs = cfg.include_globs
        self.exclude_globs = cfg.exclude_globs
        self.max_snippet_chars = cfg.max_snippet_chars
        self.max_chunk_chars = cfg.max_chunk_chars
        self.max_file_chars = cfg.max_file_chars
        self.search_timeout_sec = cfg.search_timeout_sec
        self.enable_grep = cfg.enable_grep
        self.max_grep_matches = cfg.max_grep_matches
        self.max_chars_per_match = cfg.max_chars_per_match
        self.context_before = cfg.context_before
        self.context_after = cfg.context_after

        # Result size limits
        self.max_results_limit = cfg.max_results_limit
        self.max_chars_per_chunk = cfg.max_chars_per_chunk
        self.max_total_result_chars = cfg.max_total_result_chars
        self.max_outline_items = cfg.max_outline_items
        self.max_outline_depth = cfg.max_outline_depth
        self.sqlite_busy_timeout = cfg.sqlite_busy_timeout

        if not self._allowed_dirs:
            logger.warning(
                "MDQ allowed_dirs is empty — all path-based operations will be denied. "
                "Configure allowed_dirs in mdq_mcp_server.toml to enable indexing and path operations."
            )

        # Concurrency control for indexing operations
        self._index_lock: asyncio.Lock | None = None
        self._is_indexing: bool = False

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
            create_production_tables(
                conn,
                self.db_path,
                self.sqlite_busy_timeout,
            )
        finally:
            conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Return a connection to the mdq database."""
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as e:
            from mcp_servers.mdq.mdq_models import MdqDatabaseError

            raise MdqDatabaseError(f"Failed to open database: {e}") from e
        conn.row_factory = sqlite3.Row
        apply_connection_pragmas(
            conn, busy_timeout_ms=self.sqlite_busy_timeout, write_mode=False
        )
        return conn

    async def search_docs(
        self, req: SearchDocsRequest
    ) -> tuple[str, SearchDocsMetadata]:
        """Search indexed Markdown sections by query."""
        text, metadata = await search_docs(self, req)
        if self._is_indexing:
            text += "\n\n[WARNING: Index is being updated — results may be incomplete]"
        return text, metadata

    async def get_chunk(self, req: GetChunkRequest) -> str:
        """Retrieve a Markdown chunk by its ID."""
        request_limit = req.max_chars_per_chunk
        config_cap = self.max_chars_per_chunk
        max_chars = (
            min(request_limit, config_cap) if request_limit is not None else config_cap
        )
        conn = self._get_db_connection()
        try:
            row = conn.execute(
                "SELECT heading, content, content_hash, source_path FROM chunks WHERE chunk_id = ?",
                (req.chunk_id,),
            ).fetchone()
            if row is None:
                raise MdqNotFoundError(f"Chunk {req.chunk_id} not found")
            if not authorize_path(Path(row["source_path"]), self.allowed_dirs):
                raise MdqAuthorizationError(
                    f"Access denied: chunk {req.chunk_id} is not authorized"
                )
            content = row["content"]
            truncated = False
            if len(content) > max_chars:
                content = content[:max_chars]
                truncated = True
            result = f"## {row['heading']}\n\n{content}"
            if truncated:
                result += (
                    f"\n\n[Truncated — {len(row['content'])}/{max_chars} chars. "
                    f"Use a narrower chunk_id or reduce max_chars_per_chunk.]"
                )
            return result
        finally:
            conn.close()

    async def outline(self, req: OutlineRequest) -> str:
        """Get the heading structure of a Markdown file from the index."""
        max_depth = req.max_depth or self.max_outline_depth
        request_items = req.max_outline_items
        config_cap = self.max_outline_items
        max_items = (
            min(request_items, config_cap) if request_items is not None else config_cap
        )
        p = Path(req.path)
        if not p.exists():
            raise MdqNotFoundError(f"File not found: {req.path}")
        if not authorize_path(p, self.allowed_dirs):
            logger.warning("Path denied: %s (outside allowed dirs)", req.path)
            raise MdqAuthorizationError(
                f"Access denied: {req.path} is outside allowed directories"
            )

        conn = self._get_db_connection()
        try:
            where_clauses = ["c.source_path = ?"]
            params: list = [str(p)]

            if max_depth is not None:
                where_clauses.append("c.heading_level <= ?")
                params.append(max_depth)

            where_clause = " AND ".join(where_clauses)

            rows = conn.execute(
                f"SELECT c.chunk_id, c.heading, c.heading_level, c.heading_path, c.start_line, c.end_line FROM chunks c WHERE {where_clause} ORDER BY c.heading_level, c.ordinal",
                params,
            ).fetchall()

            # Check for stale index
            stale_warning = None
            doc_row = conn.execute(
                "SELECT mtime_ns, indexed_at FROM documents WHERE source_path = ?",
                (str(p),),
            ).fetchone()
            if (
                doc_row is not None
                and doc_row["mtime_ns"] is not None
                and doc_row["indexed_at"] is not None
            ):
                if is_stale(doc_row["mtime_ns"], doc_row["indexed_at"]):
                    stale_warning = (
                        f"Warning: file has been modified since last indexing "
                        f"(mtime={doc_row['mtime_ns']}, indexed_at={doc_row['indexed_at']})"
                    )

            headings = [
                OutlineHeading(
                    heading=row["heading"],
                    level=row["heading_level"],
                    heading_path=row["heading_path"],
                    chunk_id=row["chunk_id"],
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                )
                for row in rows
            ]

            total_headings = len(headings)
            truncated = total_headings > max_items if max_items else False
            if truncated and max_items:
                headings = headings[:max_items]

            parts = []
            for h in headings:
                indent = "  " * (h.level - 1)
                parts.append(f"{indent}{h.heading}")

            result = "\n".join(parts) if headings else "(no headings)"
            if truncated:
                result += (
                    f"\n\n[Truncated — {total_headings} headings found, "
                    f"{max_items} shown. "
                    f"Use a deeper path_prefix filter or reduce max_outline_items.]"
                )
            if stale_warning:
                result += f"\n\n{stale_warning}"
            return result
        finally:
            conn.close()

    async def index_paths(
        self, req: IndexPathsRequest
    ) -> tuple[str, IndexPathsMetadata]:
        """Index a set of paths into the in-process SQLite DB."""
        if self._index_lock is None:
            self._index_lock = asyncio.Lock()
        async with self._index_lock:
            self._is_indexing = True
            try:
                text, metadata = await _index_paths(self, req)
                return text, metadata
            finally:
                self._is_indexing = False

    async def refresh_index(
        self, req: RefreshIndexRequest
    ) -> tuple[str, RefreshSummary]:
        """Incrementally refresh the index for a set of paths."""
        if self._index_lock is None:
            self._index_lock = asyncio.Lock()
        async with self._index_lock:
            self._is_indexing = True
            try:
                self._validate_paths(req.paths)
                summary = await _refresh_paths(self, req)
                text = "\n".join(self._format_refresh_summary(summary))
                return text, summary
            finally:
                self._is_indexing = False

    def _validate_paths(self, paths: list[str]) -> None:
        """Validate each path exists and is within allowed directories; raises MdqAuthorizationError on violation."""
        for path_str in paths:
            p = Path(path_str)
            if not p.exists():
                logger.warning("Path does not exist: %s", path_str)
                continue
            if not authorize_path(p, self.allowed_dirs):
                raise MdqAuthorizationError(
                    f"Access denied: {path_str} is outside allowed directories"
                )

    def _format_refresh_summary(self, summary: RefreshSummary) -> list[str]:
        """Format a RefreshSummary into human-readable status lines."""
        return [
            f"Refresh complete in {summary['elapsed_seconds']}s",
            f"  Indexed: {summary['indexed_count']}",
            f"  Skipped (unchanged): {summary['skipped_count']}",
            f"  Deleted from index: {summary['deleted_count']}",
            f"  Failed: {summary['failed_count']}",
        ]

    async def stats(self, req: StatsRequest) -> str:
        """Return document/chunk count and index metadata."""
        conn = self._get_db_connection()
        try:
            chunk_count = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()[
                "cnt"
            ]
            doc_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM documents"
            ).fetchone()["cnt"]
            fts_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks_fts"
            ).fetchone()["cnt"]
            stale_count = conn.execute(
                f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION}"
            ).fetchone()["cnt"]
            rows = conn.execute("SELECT key, value FROM index_state").fetchall()
            index_metadata = dict((row["key"], row["value"]) for row in rows)
            return (
                f"Documents: {doc_count}, Chunks: {chunk_count},"
                f" FTS rows: {fts_count}, Stale: {stale_count},"
                f" Metadata: {index_metadata}"
            )
        finally:
            conn.close()

    async def grep_docs(self, req: GrepDocsRequest) -> tuple[str, GrepDocsMetadata]:
        """Search Markdown chunks with a regex pattern."""
        if not self.enable_grep:
            raise MdqValidationError("grep_docs is disabled by configuration")
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise MdqValidationError(f"Invalid regex pattern: {e}")

        if req.paths:
            for p in req.paths:
                if not authorize_path(Path(p), self.allowed_dirs):
                    raise MdqAuthorizationError(
                        f"Access denied: {p} is outside allowed directories"
                    )
            authorized_paths = req.paths
        else:
            conn_check = self._get_db_connection()
            try:
                all_paths = [
                    row["source_path"]
                    for row in conn_check.execute(
                        "SELECT DISTINCT source_path FROM chunks"
                    ).fetchall()
                ]
            finally:
                conn_check.close()
            authorized_paths = [
                p for p in all_paths if authorize_path(Path(p), self.allowed_dirs)
            ]
            if not authorized_paths:
                return "No matches found.", GrepDocsMetadata(
                    pattern_preview=req.pattern[:80],
                    path_filter_count=0,
                    match_count=0,
                    truncated=False,
                    grep_enabled=True,
                )

        request_matches = req.max_grep_matches
        config_cap_matches = self.max_grep_matches
        max_matches = (
            min(request_matches, config_cap_matches)
            if request_matches is not None
            else config_cap_matches
        )
        max_chars = (
            getattr(req, "max_chars_per_match", None) or self.max_chars_per_match
        )
        ctx_before = getattr(req, "context_before", None) or self.context_before
        ctx_after = getattr(req, "context_after", None) or self.context_after

        conn = self._get_db_connection()
        try:
            text, metadata = grep_docs(
                conn,
                compiled,
                authorized_paths,
                max_matches,
                max_chars,
                ctx_before,
                ctx_after,
            )
            return text, metadata
        finally:
            conn.close()
