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
from mcp.mdq.indexer import index_paths as _index_paths
from mcp.mdq.indexer import refresh_paths as _refresh_paths
from mcp.mdq.models import (
    FtsConsistencyCheckRequest,
    FtsRebuildRequest,
    GetChunkRequest,
    GrepDocMatch,
    GrepDocsRequest,
    IndexPathsRequest,
    MdqAuthorizationError,
    MdqConsistencyError,
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
            # Check for legacy schema
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            if "sections" in tables:
                logger.info("Migrating from legacy sections schema")
                self._migrate_from_legacy(conn)
                return

            # Detect and rebuild old schema (id INTEGER PK + chunk_id TEXT UNIQUE)
            old_col = conn.execute("PRAGMA table_info(chunks)").fetchone()
            if old_col is not None and old_col["name"] == "id":
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
            if self.use_embedding:
                try:
                    conn.enable_load_extension(True)
                    conn.load_extension("/opt/llm/sqlite-vec/vec0.so")
                    conn.enable_load_extension(False)
                except sqlite3.OperationalError as e:
                    logger.error("Failed to load sqlite-vec extension: %s", e)
                    raise
                conn.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS {self.vector_table} USING vec0(
                        chunk_id TEXT PRIMARY KEY,
                        embedding float[{self.embedding_dims}]
                    )
                """)
            conn.commit()
        finally:
            conn.close()

    def _migrate_from_legacy(self, conn: sqlite3.Connection) -> None:
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
                    import hashlib
                    import time

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

    async def get_chunk(self, req: GetChunkRequest) -> str:
        """Retrieve a Markdown chunk by its ID."""
        max_chars = (
            getattr(req, "max_chars_per_chunk", None) or self.max_chars_per_chunk
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

            truncated = False
            if len(content) > max_chars:
                content = content[:max_chars]
                truncated = True
            result = f"## {row['heading']}\n\n{content}"
            if truncated:
                result += f"\n\n[Truncated — {len(row['content'])}/{max_chars} chars]"
            return result
        finally:
            conn.close()

    async def outline(self, req: OutlineRequest) -> str:
        """Get the heading structure of a Markdown file from the index."""
        max_depth = getattr(req, "max_depth", None) or self.max_outline_depth
        max_items = getattr(req, "max_items", None) or self.max_outline_items
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

            truncated = len(headings) >= max_items if max_items else False
            if truncated and max_items:
                headings = headings[:max_items]

            parts = []
            for h in headings:
                indent = "  " * (h.level - 1)
                parts.append(f"{indent}{h.heading}")

            result = "\n".join(parts) if headings else "(no headings)"
            if truncated:
                result += f"\n\n[Truncated — {len(headings)}/{max_items} headings]"
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
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise MdqValidationError(f"Invalid regex pattern: {e}")

        max_matches = getattr(req, "max_grep_matches", None) or self.max_grep_matches
        max_chars = (
            getattr(req, "max_chars_per_match", None) or self.max_chars_per_match
        )
        ctx_before = getattr(req, "context_before", None) or self.context_before
        ctx_after = getattr(req, "context_after", None) or self.context_after

        conn = self._get_db_connection()
        try:
            where_clauses = []
            params: list = []

            if req.paths:
                placeholders = ",".join("?" for _ in req.paths)
                where_clauses.append(f"source_path IN ({placeholders})")
                params.extend(req.paths)

            where_clause = (
                f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            )

            rows = conn.execute(
                f"SELECT chunk_id, source_path, heading_path, heading, content, start_line FROM chunks {where_clause}",
                params,
            ).fetchall()

            matches: list[GrepDocMatch] = []
            for row in rows:
                match = self._find_grep_match(
                    row, compiled, max_chars, ctx_before, ctx_after
                )
                if match is None:
                    continue
                matches.append(match)
                if len(matches) >= max_matches:
                    break

            truncated = len(matches) >= max_matches

            if not matches:
                return "No matches found."

            parts = []
            for m in matches:
                parts.append(f"File: {m.source_path}")
                parts.append(f"Chunk: {m.chunk_id}")
                if m.heading_path:
                    parts.append(f"Heading: {m.heading_path}")
                parts.append(f"Line: {m.line_number}")
                parts.append(f"Match: {m.match_text}")
                parts.append("---")

            result = "\n".join(parts)
            if truncated:
                result += f"\n\n[Truncated — {max_matches} matches shown]"
            return result
        finally:
            conn.close()

    def _find_grep_match(
        self,
        row: sqlite3.Row,
        compiled: re.Pattern[str],
        max_chars: int,
        ctx_before: int,
        ctx_after: int,
    ) -> GrepDocMatch | None:
        full_text = f"{row['heading']}\n{row['content']}"
        for re_match in compiled.finditer(full_text):
            match_start = re_match.start()
            lines = full_text.split("\n")
            match_line = 0
            line_offset = 0
            for i, line in enumerate(lines):
                if line_offset + len(line) >= match_start:
                    match_line = i
                    break
                line_offset += len(line) + 1
            start_idx = max(0, match_line - ctx_before)
            end_idx = min(len(lines), match_line + ctx_after + 1)
            _context_lines = lines[start_idx:end_idx]
            match_text = re_match.group()[:max_chars]
            return GrepDocMatch(
                chunk_id=row["chunk_id"],
                source_path=row["source_path"],
                heading_path=row["heading_path"],
                match_text=match_text,
                line_number=start_idx + 1,
            )
        return None

    async def fts_consistency_check(self, req: FtsConsistencyCheckRequest) -> str:
        """Check FTS5 consistency between chunks and chunks_fts tables."""
        conn = self._get_db_connection()
        try:
            chunks_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks"
            ).fetchone()["cnt"]
            fts_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chunks_fts"
            ).fetchone()["cnt"]
            consistent = chunks_count == fts_count
            return (
                f"FTS5 consistency check: {'consistent' if consistent else 'INCONSISTENT'}\n"
                f"  chunks rows: {chunks_count}\n"
                f"  chunks_fts rows: {fts_count}"
            )
        except sqlite3.OperationalError as e:
            raise MdqConsistencyError(f"FTS5 table missing or corrupted: {e}") from e
        finally:
            conn.close()

    async def fts_rebuild(self, req: FtsRebuildRequest) -> str:
        """Rebuild the FTS5 index."""
        conn = self._get_db_connection()
        try:
            conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            conn.commit()
            return "FTS5 index rebuilt successfully"
        except sqlite3.Error as e:
            return f"FTS5 rebuild failed: {e}"
        finally:
            conn.close()
