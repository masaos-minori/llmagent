#!/usr/bin/env python3
"""mcp/mdq/service.py
Main service class for Mdq functionality — SQLite FTS5-backed.
"""

from __future__ import annotations

import asyncio
import logging
import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.mdq.auth import authorize_path
from mcp.mdq.db_fts import fts_consistency_check, fts_rebuild
from mcp.mdq.db_grep import find_grep_match, grep_docs
from mcp.mdq.db_schema import create_production_tables
from mcp.mdq.models import GrepDocMatch, MdqConsistencyError
from mcp.mdq.indexer import generate_chunk_id
from mcp.mdq.indexer import index_paths as _index_paths
from mcp.mdq.indexer import refresh_paths as _refresh_paths
from mcp.mdq.models import (
    FtsConsistencyCheckRequest,
    FtsRebuildRequest,
    GetChunkRequest,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqNotFoundError,
    MdqValidationError,
    OutlineHeading,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
    StatsRequest,
)
from mcp.mdq.search import search_docs

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MdqService:
    """Main service class for Mdq functionality."""

    def __init__(self, db_path: str | None = None):
        # Load config from ConfigLoader (auto-loads mdq_mcp_server.toml)
        try:
            from shared.config_loader import ConfigLoader

            cfg = ConfigLoader().load_all()
            mdq_cfg = (
                cfg.get("mdq_mcp_server", {})
                if isinstance(cfg.get("mdq_mcp_server"), dict)
                else {}
            )
        except (FileNotFoundError, KeyError, TypeError):
            mdq_cfg = {}

        self.db_path = db_path or mdq_cfg.get("db_path", "/opt/llm/db/mdq.sqlite")
        self._allowed_dirs: list[str] = mdq_cfg.get("allowed_dirs") or []
        self.include_globs: list[str] = mdq_cfg.get("include_globs", ["*.md"])
        self.exclude_globs: list[str] = mdq_cfg.get(
            "exclude_globs", [".git/**", "__pycache__/**"]
        )
        self.max_search_results: int = mdq_cfg.get("max_search_results", 100)
        self.max_snippet_chars: int = mdq_cfg.get("max_snippet_chars", 500)
        self.max_chunk_chars: int = mdq_cfg.get("max_chunk_chars", 10000)
        self.max_file_chars: int = mdq_cfg.get("max_file_chars", 100000)
        self.search_timeout_sec: int = mdq_cfg.get("search_timeout_sec", 30)
        self.enable_refresh: bool = mdq_cfg.get("enable_refresh", True)
        self.enable_grep: bool = mdq_cfg.get("enable_grep", True)
        self.audit_log_path: str | None = mdq_cfg.get(
            "audit_log_path", "/opt/llm/logs/mdq_audit.log"
        )
        self.max_grep_matches: int = mdq_cfg.get("max_grep_matches", 200)
        self.max_chars_per_match: int = mdq_cfg.get("max_chars_per_match", 500)
        self.context_before: int = mdq_cfg.get("context_before", 2)
        self.context_after: int = mdq_cfg.get("context_after", 2)

        # Result size limits
        self.max_results_limit: int = mdq_cfg.get("max_results_limit", 100)
        self.max_chars_per_chunk: int = mdq_cfg.get("max_chars_per_chunk", 10000)
        self.max_total_result_chars: int = mdq_cfg.get("max_total_result_chars", 100000)
        self.max_outline_items: int = mdq_cfg.get("max_outline_items", 500)
        self.max_outline_depth: int = mdq_cfg.get("max_outline_depth", 6)
        self.sqlite_busy_timeout: int = mdq_cfg.get("sqlite_busy_timeout", 5000)

        # Summary cache for large chunks
        self.summary_cache_enabled: bool = mdq_cfg.get("summary_cache_enabled", False)
        self.summary_threshold: int = mdq_cfg.get("summary_threshold", 5000)
        self.summary_model: str = mdq_cfg.get("summary_model", "default")

        # Embedding/hybrid search mode
        self.use_embedding: bool = mdq_cfg.get("use_embedding", False)
        self.vector_table: str = mdq_cfg.get("vector_table", "chunks_vec")
        self.embedding_model: str = mdq_cfg.get("embedding_model", "default")
        # Embedding dimension from common.toml (required for vec0 table creation)
        try:
            common_cfg = ConfigLoader().load("common.toml")
            self.embedding_dims: int = common_cfg.get("embedding_dims", 384)
        except (FileNotFoundError, KeyError):
            self.embedding_dims = 384

        # Validate required fields
        if not isinstance(self._allowed_dirs, list):
            logger.warning(
                "mdq_mcp_server.allowed_dirs must be a list; using empty list"
            )
            self._allowed_dirs = []

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
                self.use_embedding,
                self.vector_table,
                self.embedding_dims,
                self.sqlite_busy_timeout,
            )
        finally:
            conn.close()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Return a connection to the mdq database."""
        try:
            conn = sqlite3.connect(self.db_path)
        except sqlite3.OperationalError as e:
            from mcp.mdq.models import MdqDatabaseError

            raise MdqDatabaseError(f"Failed to open database: {e}") from e
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance
        conn.execute("PRAGMA journal_mode=WAL")
        # Set busy timeout to avoid "database is locked" errors
        conn.execute(f"PRAGMA busy_timeout = {self.sqlite_busy_timeout}")
        return conn

    async def search_docs(self, req: SearchDocsRequest) -> str:
        """Search indexed Markdown sections by query."""
        result = await search_docs(self, req)
        if self._is_indexing:
            result += (
                "\n\n[WARNING: Index is being updated — results may be incomplete]"
            )
        return result

    async def _generate_and_cache_summary(
        self, chunk_id: str, content: str, content_hash: str
    ) -> str | None:
        """Generate a summary for chunk_id and cache it in chunk_summaries.

        Returns the generated summary on success, or None on failure/stub.
        When summary_model == "default", no LLM integration is available — returns None.
        """
        try:
            if self.summary_model == "default":
                return None
            # Future: replace with actual LLM call
            # summary = await self._call_llm_for_summary(content)
            # conn = self._get_db_connection()
            # try:
            #     conn.execute("INSERT OR REPLACE INTO chunk_summaries ...", ...)
            #     conn.commit()
            # finally:
            #     conn.close()
            return None
        except Exception:
            return None

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
                "SELECT heading, content, content_hash FROM chunks WHERE chunk_id = ?",
                (req.chunk_id,),
            ).fetchone()
            if row is None:
                raise MdqNotFoundError(f"Chunk {req.chunk_id} not found")
            content = row["content"]

            # Check summary cache if use_summary is enabled and chunk exceeds threshold
            if (
                req.use_summary
                and self.summary_cache_enabled
                and len(content) > self.summary_threshold
            ):
                cached = conn.execute(
                    "SELECT summary, summary_model, content_hash FROM chunk_summaries WHERE chunk_id = ?",
                    (req.chunk_id,),
                ).fetchone()
                if cached is not None and cached["content_hash"] == row["content_hash"]:
                    try:
                        return f"## {row['heading']}\n\n[Summary — {len(content)} chars]\n\n{cached['summary']}"
                    except Exception:
                        logger.warning(
                            "Failed to retrieve cached summary for chunk %s",
                            req.chunk_id,
                        )
                elif cached is None:
                    # Cache miss: fire background summary generation (non-blocking)
                    import asyncio as _asyncio

                    _asyncio.create_task(
                        self._generate_and_cache_summary(
                            req.chunk_id, content, row["content_hash"]
                        )
                    )

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
                if doc_row["mtime_ns"] > doc_row["indexed_at"]:
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

    async def index_paths(self, req: IndexPathsRequest) -> str:
        """Index a set of paths into the in-process SQLite DB."""
        if self._index_lock is None:
            self._index_lock = asyncio.Lock()
        async with self._index_lock:
            self._is_indexing = True
            try:
                return await _index_paths(self, req)
            finally:
                self._is_indexing = False

    async def refresh_index(self, req: RefreshIndexRequest) -> str:
        """Incrementally refresh the index for a set of paths."""
        if self._index_lock is None:
            self._index_lock = asyncio.Lock()
        async with self._index_lock:
            self._is_indexing = True
            try:
                self._validate_paths(req.paths)
                summary = await _refresh_paths(self, req)
                return "\n".join(self._format_refresh_summary(summary))
            finally:
                self._is_indexing = False

    def _validate_paths(self, paths: list[str]) -> None:
        for path_str in paths:
            p = Path(path_str)
            if not p.exists():
                logger.warning("Path does not exist: %s", path_str)
                continue
            if not authorize_path(p, self.allowed_dirs):
                raise MdqAuthorizationError(
                    f"Access denied: {path_str} is outside allowed directories"
                )

    def _format_refresh_summary(self, summary: Any) -> list[str]:
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
                "SELECT COUNT(*) as cnt FROM documents"
                " WHERE mtime_ns > CAST(indexed_at * 1e9 AS INTEGER)"
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

    async def grep_docs(self, req: GrepDocsRequest) -> str:
        """Search Markdown chunks with a regex pattern."""
        if not self.enable_grep:
            raise MdqValidationError("grep_docs is disabled by configuration")
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise MdqValidationError(f"Invalid regex pattern: {e}")

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
            return grep_docs(
                conn, compiled, req.paths or [], max_matches, max_chars, ctx_before, ctx_after
            )
        finally:
            conn.close()

    async def fts_consistency_check(self, req: FtsConsistencyCheckRequest) -> str:
        """Check FTS5 consistency between chunks and chunks_fts tables."""
        conn = self._get_db_connection()
        try:
            return fts_consistency_check(conn)
        finally:
            conn.close()

    async def fts_rebuild(self, req: FtsRebuildRequest) -> str:
        """Rebuild the FTS5 index."""
        conn = self._get_db_connection()
        try:
            chunks_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks"
            ).fetchone()["cnt"]
            return fts_rebuild(conn, chunks_count)
        finally:
            conn.close()
