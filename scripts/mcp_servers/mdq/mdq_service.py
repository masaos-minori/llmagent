#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_service.py

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
    MdqDatabaseError,
    MdqNotFoundError,
    MdqValidationError,
    OutlineHeading,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsMetadata,
    SearchDocsRequest,
    StatsRequest,
    is_stale,
    outcome_text,
)
from mcp_servers.mdq.search import search_docs
from mcp_servers.mdq.startup_config import StartupConfig

logger = logging.getLogger(__name__)


class MdqService:
    """Main service class for Mdq functionality."""

    def __init__(self, startup: StartupConfig):
        """Initialize the MDQ service from the validated startup-configuration result.

        There is no configuration read and no fallback here: a missing or wrong-typed
        production configuration is a failure the caller sees before the server binds
        (REQ-007), and the database path comes from the result rather than a literal
        default. `MdqConfig` stays the shape holder for the declared keys.
        """
        cfg = MdqConfig.model_validate(
            dict(startup.values)
        )  # raises pydantic.ValidationError on invalid values
        self.db_path = startup.db_path
        self._allowed_dirs = cfg.allowed_dirs
        self.include_globs = cfg.include_globs
        self.exclude_globs = cfg.exclude_globs
        self.max_snippet_chars = cfg.max_snippet_chars
        self.max_chunk_chars = cfg.max_chunk_chars
        self.max_file_bytes = cfg.max_file_bytes
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

    def _ensure_index_lock(self) -> asyncio.Lock:
        """Ensure _index_lock is initialized before use."""
        if self._index_lock is None:
            self._index_lock = asyncio.Lock()
        return self._index_lock

    @property
    def allowed_dirs(self) -> list[str]:
        """Return the configured allowed directories for file access."""
        return self._allowed_dirs

    def _init_db(self) -> None:
        """Create the production tables."""
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
            raise MdqDatabaseError(f"Failed to open database: {e}") from e
        conn.row_factory = sqlite3.Row
        apply_connection_pragmas(
            conn, busy_timeout_ms=self.sqlite_busy_timeout, write_mode=True
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
            params: list[str | int] = [str(p)]

            if max_depth is not None:
                where_clauses.append("c.heading_level <= ?")
                params.append(max_depth)

            where_clause = " AND ".join(where_clauses)

            rows = conn.execute(
                f"SELECT c.chunk_id, c.heading, c.heading_level,"
                f" c.heading_path, c.start_line, c.end_line"
                f" FROM chunks c WHERE {where_clause}"
                f" ORDER BY c.heading_level, c.ordinal",  # nosec B608 — where_clauses fragments from fixed constants; values bound via params
                params,
            ).fetchall()

            stale_warning = self._check_stale_document(conn, p)

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

            result = self._render_outline(headings, max_items)
            if stale_warning:
                result += f"\n\n{stale_warning}"
            return result
        finally:
            conn.close()

    def _check_stale_document(self, conn: sqlite3.Connection, path: Path) -> str | None:
        """Return a stale-index warning message for path, or None if not stale/unknown."""
        doc_row = conn.execute(
            "SELECT mtime_ns, indexed_at FROM documents WHERE source_path = ?",
            (str(path),),
        ).fetchone()
        if (
            doc_row is None
            or doc_row["mtime_ns"] is None
            or doc_row["indexed_at"] is None
        ):
            return None
        if not is_stale(doc_row["mtime_ns"], doc_row["indexed_at"]):
            return None
        return (
            f"Warning: file has been modified since last indexing "
            f"(mtime={doc_row['mtime_ns']}, indexed_at={doc_row['indexed_at']})"
        )

    def _render_outline(
        self, headings: list[OutlineHeading], max_items: int | None
    ) -> str:
        """Render headings as indented text, truncating to max_items if set."""
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
        return result

    async def index_paths(
        self, req: IndexPathsRequest
    ) -> tuple[str, IndexPathsMetadata]:
        """Index a set of paths into the in-process SQLite DB."""
        lock = self._ensure_index_lock()
        async with lock:
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
        lock = self._ensure_index_lock()
        async with lock:
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
        """Format a RefreshSummary into human-readable status lines.

        The header is the outcome text derived from the counters, so a mixed run reads as
        partial_success rather than as a completed refresh (REQ-003). The counter lines are
        unchanged, and the file-level lines name the unit the counts actually describe.
        """
        header = outcome_text(
            committed_files=summary["committed_file_count"],
            discovered_files=summary["discovered_file_count"],
            skipped_files=summary["skipped_file_count"],
            failed_files=summary["failed_file_count"],
            skipped_paths=summary["skipped_count"],
            failed_paths=summary["failed_count"],
            unchanged_files=summary["unchanged_file_count"],
        )
        return [
            header,
            f"  Elapsed: {summary['elapsed_seconds']}s",
            f"  Indexed: {summary['indexed_count']}",
            f"  Skipped (unchanged): {summary['skipped_count']}",
            f"  Deleted from index: {summary['deleted_count']}",
            f"  Failed: {summary['failed_count']}",
            f"  Files discovered: {summary['discovered_file_count']}",
            f"  Files committed: {summary['committed_file_count']}",
            f"  Files skipped: {summary['skipped_file_count']}",
            f"  Files unchanged: {summary['unchanged_file_count']}",
            f"  Files failed: {summary['failed_file_count']}",
        ]

    async def stats(self, req: StatsRequest) -> str:
        """Return counts scoped to the currently authorized roots (REQ-002).

        The raw `index_state` metadata dict is not part of the response. The refusal for
        an empty allowlist happens before any query, so a caller with no authorized roots
        gets "no access" rather than a database-wide zero.
        """
        roots = [Path(root).resolve().as_posix() for root in self._allowed_dirs]
        if not roots:
            raise MdqAuthorizationError(
                "stats is scoped to the authorized roots and none are configured"
            )

        clauses = []
        params: list[object] = []
        for root in roots:
            # `source_path` is stored canonical (`path.resolve().as_posix()` at index time),
            # so the predicate compares canonical values without a LIKE metacharacter risk.
            clauses.append("(source_path = ? OR substr(source_path, 1, ?) = ?)")
            params.extend([root, len(root) + 1, f"{root}/"])
        where = " OR ".join(clauses)

        conn = self._get_db_connection()
        try:
            counts: dict[str, int] = {}
            for table in ("documents", "chunks", "chunks_fts"):
                row = conn.execute(
                    f"SELECT COUNT(*) as cnt FROM {table} WHERE {where}",  # nosec B608 — table names are fixed constants, roots are bound parameters
                    params,
                ).fetchone()
                counts[table] = row["cnt"]
            stale_count = conn.execute(
                f"SELECT COUNT(*) as cnt FROM documents WHERE {STALE_SQL_CONDITION} AND ({where})",  # nosec B608 — STALE_SQL_CONDITION is a fixed string constant, table names are fixed, roots are bound parameters
                params,
            ).fetchone()["cnt"]
            return (
                f"Documents: {counts['documents']}, Chunks: {counts['chunks']},"
                f" FTS rows: {counts['chunks_fts']}, Stale: {stale_count}"
            )
        finally:
            conn.close()

    def _resolve_grep_paths(self, req: GrepDocsRequest) -> list[str]:
        """Resolve and authorize grep_docs target paths: explicit paths, or all indexed paths."""
        if req.paths:
            for p in req.paths:
                if not authorize_path(Path(p), self.allowed_dirs):
                    raise MdqAuthorizationError(
                        f"Access denied: {p} is outside allowed directories"
                    )
            return req.paths

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
        return [p for p in all_paths if authorize_path(Path(p), self.allowed_dirs)]

    async def grep_docs(self, req: GrepDocsRequest) -> tuple[str, GrepDocsMetadata]:
        """Search Markdown chunks with a regex pattern."""
        if not self.enable_grep:
            raise MdqValidationError("grep_docs is disabled by configuration")
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise MdqValidationError(f"Invalid regex pattern: {e}")

        authorized_paths = self._resolve_grep_paths(req)
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
        max_chars = req.max_chars_per_match or self.max_chars_per_match
        # Only an absent value selects the configured default: an explicit zero means no
        # context lines and must reach grep_docs() (REQ-006).
        ctx_before = (
            self.context_before if req.context_before is None else req.context_before
        )
        ctx_after = (
            self.context_after if req.context_after is None else req.context_after
        )

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
