#!/usr/bin/env python3
"""agent/commands/cmd_db.py
Database management mixin for CommandRegistry.

Provides _DbMixin with:
  _cmd_db         — /db dispatcher
  _db_stats       — DB record counts (delegates to DbMaintenanceService)
  _db_list_urls   — list document URLs via rag-pipeline-mcp
  _db_clean       — delete a document via rag-pipeline-mcp
  _db_rebuild_fts — rebuild the FTS5 index (delegates to DbMaintenanceService)
  _db_health      — print DB health metrics (delegates to DbMaintenanceService)
  _db_checkpoint  — run WAL checkpoint (delegates to DbMaintenanceService)
  _db_vacuum      — run VACUUM (delegates to DbMaintenanceService)
  _db_purge       — purge old sessions (delegates to DbMaintenanceService)
  _db_recover     — integrity check and restore (delegates to DbMaintenanceService)
"""

import inspect
import logging
from typing import Any

from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args, parse_flag_int
from agent.services.db_maintenance_service import DbMaintenanceService
from agent.services.rag_maintenance_service import RagMaintenanceService

logger = logging.getLogger(__name__)

DB_PARTS_COUNT = 2
URL_DISPLAY_MAX_LENGTH = 60
URL_DISPLAY_TRUNCATE_LENGTH = URL_DISPLAY_MAX_LENGTH - 3


class _DbMixin(MixinBase):
    """Database management slash-command handlers."""

    async def _cmd_db(self, args: str) -> None:
        """Handle /db rag <subcmd>, /db session <subcmd>, or /db help."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == DB_PARTS_COUNT else ""

        if subcmd == "rag":
            await self._cmd_db_rag(rest)
            return
        if subcmd == "session":
            await self._cmd_db_session(rest)
            return

        if subcmd == "help":
            self._db_help()
            return

        self._out.write_validation_error("/db rag <subcmd> | /db session <subcmd>")

    async def _cmd_db_rag(self, args: str) -> None:
        """Handle /db rag <subcmd>."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == DB_PARTS_COUNT else ""
        dispatch: dict[str, Any] = {
            "stats": self._db_rag_stats,
            "urls": lambda: self._db_list_urls(rest),
            "clean": lambda: self._db_clean(rest),
            "rebuild-fts": self._db_rebuild_fts,
            "vec-rebuild": self._db_vec_rebuild,
            "reconcile-url": self._db_reconcile_url,
            "recover": lambda: self._db_recover(rest.strip() or None),
            "consistency": self._db_consistency,
        }
        handler = dispatch.get(subcmd)
        if handler:
            result = handler()
            if inspect.isawaitable(result):
                await result
        else:
            self._db_help_rag()

    async def _cmd_db_session(self, args: str) -> None:
        """Handle /db session <subcmd>."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == DB_PARTS_COUNT else ""
        dispatch: dict[str, Any] = {
            "stats": self._db_session_stats,
            "health": self._db_health,
            "checkpoint": lambda: self._db_checkpoint(rest.strip().upper() or None),
            "vacuum": self._db_vacuum,
            "purge": lambda: self._db_purge(rest),
            "recover": lambda: self._db_recover_session(rest.strip() or None),
        }
        handler = dispatch.get(subcmd)
        if handler:
            result = handler()
            if inspect.isawaitable(result):
                await result
        else:
            self._db_help_session()

    def _db_help(self) -> None:
        """Print a help table for /db subcommands."""
        rows = [
            ["rag stats", "RAG", "", "Document/chunk counts"],
            ["rag urls", "RAG", "--lang --limit", "List document URLs"],
            ["rag clean", "RAG", "<url>", "Delete a document"],
            ["rag rebuild-fts", "RAG", "", "Rebuild FTS5 index"],
            ["rag vec-rebuild", "RAG", "", "Rebuild vector index"],
            [
                "rag reconcile-url",
                "RAG",
                "<url>",
                "Rebuild FTS/vec for a single URL",
            ],
            [
                "rag recover",
                "RAG",
                "[backup-path]",
                "(admin) Integrity check / restore",
            ],
            ["rag consistency", "RAG", "", "Chunks/FTS/vec sync check"],
            ["session stats", "Session", "", "Session/message counts"],
            ["session health", "Session", "", "(admin) Integrity check / size"],
            ["session checkpoint", "Session", "[MODE]", "(admin) WAL checkpoint"],
            ["session vacuum", "Session", "", "(admin) Reclaim free pages"],
            [
                "session purge",
                "Session",
                "--max-sessions N\n--max-age-days N",
                "(admin) Purge old sessions",
            ],
            [
                "session recover",
                "Session",
                "[backup-path]",
                "(admin) Integrity check / restore",
            ],
        ]
        self._out.write_table(
            ["Subcommand", "Target DB", "Arguments", "Description"],
            rows,
        )
        self._out.write(
            "Note: workflow data lives in session.sqlite; no separate workflow DB."
        )

    def _db_help_rag(self) -> None:
        """Print help for /db rag subcommands."""
        rows = [
            ["stats", "", "Document/chunk counts"],
            ["urls", "--lang --limit", "List document URLs"],
            ["clean", "<url>", "Delete a document"],
            ["rebuild-fts", "", "Rebuild FTS5 index"],
            ["vec-rebuild", "", "Rebuild vector index"],
            ["reconcile-url", "<url>", "Rebuild FTS/vec for a single URL"],
            ["recover", "[backup-path]", "(admin) Integrity check / restore"],
            ["consistency", "", "Chunks/FTS/vec sync check"],
        ]
        self._out.write_table(
            ["Subcommand (/db rag ...)", "Arguments", "Description"],
            rows,
        )

    def _db_help_session(self) -> None:
        """Print help for /db session subcommands."""
        rows = [
            ["stats", "", "Session/message counts"],
            ["health", "", "(admin) Integrity check / size"],
            ["checkpoint", "[MODE]", "(admin) WAL checkpoint"],
            ["vacuum", "", "(admin) Reclaim free pages"],
            [
                "purge",
                "--max-sessions N\n--max-age-days N",
                "(admin) Purge old sessions",
            ],
            ["recover", "[backup-path]", "(admin) Integrity check / restore"],
        ]
        self._out.write_table(
            ["Subcommand (/db session ...)", "Arguments", "Description"],
            rows,
        )

    async def _db_clean(self, rest: str) -> None:
        """Delete a document by URL from the vector store via rag-pipeline-mcp."""
        url = rest.strip()
        if not url:
            self._out.write_validation_error("/db clean <url>")
            return
        if self._ctx.services.tools is None:
            self._out.write_error(
                "rag-pipeline-mcp unavailable: tool executor not initialized"
            )
            return
        try:
            result = await self._ctx.services.tools.execute(
                "rag_delete_document", {"url": url}
            )
            if result.is_error:
                self._out.write_error(result.output)
            else:
                self._out.write(result.output)
        except Exception as e:  # noqa: BLE001
            self._out.write_error(f"rag-pipeline-mcp unavailable: {e}")

    def _db_stats(self) -> None:
        """Print document/chunk/session/message counts from both DBs."""
        rag_docs, rag_chunks = RagMaintenanceService().stats_rag()
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("documents", f"{rag_docs:,}"),
                ("chunks", f"{rag_chunks:,}"),
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Both"),
            ]
        )

    def _db_rag_stats(self) -> None:
        """Print document/chunk counts from the RAG database."""
        rag_docs, rag_chunks = RagMaintenanceService().stats_rag()
        self._out.write_kv(
            [
                ("documents", f"{rag_docs:,}"),
                ("chunks", f"{rag_chunks:,}"),
                ("target", "RAG"),
            ]
        )

    def _db_session_stats(self) -> None:
        """Print session/message counts from the Session database."""
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Session"),
            ]
        )

    async def _db_list_urls(self, rest: str) -> None:
        """List indexed documents via rag-pipeline-mcp."""
        tokens = rest.split()
        parsed = parse_command_args(tokens)
        lang_raw = parsed.flags.get("lang")
        lang: str | None = str(lang_raw) if lang_raw in ("ja", "en") else None
        limit = parse_flag_int(tokens, "--limit") or 20
        args_dict: dict[str, Any] = {"limit": limit}
        if lang:
            args_dict["lang"] = lang
        if self._ctx.services.tools is None:
            self._out.write_error(
                "rag-pipeline-mcp unavailable: tool executor not initialized"
            )
            return
        try:
            result = await self._ctx.services.tools.execute(
                "rag_list_documents", args_dict
            )
            if result.is_error:
                self._out.write_error(result.output)
            else:
                self._out.write(result.output)
        except Exception as e:  # noqa: BLE001
            self._out.write_error(f"rag-pipeline-mcp unavailable: {e}")

    def _db_rebuild_fts(self) -> None:
        """Rebuild the RAG full-text search index."""
        RagMaintenanceService().rebuild_fts()
        self._out.write_success("FTS5 index rebuilt [RAG]")

    def _db_vec_rebuild(self) -> None:
        """Rebuild the vector index from chunks."""
        count = RagMaintenanceService().rebuild_vec()
        self._out.write_success(f"Vec index rebuilt: {count} rows [RAG]")

    def _db_reconcile_url(self, rest: str) -> None:
        """Rebuild FTS/vec for a single URL."""
        url = rest.strip()
        if not url:
            self._out.write_validation_error("Usage: /db reconcile-url <url>")
            return
        result = RagMaintenanceService().reconcile_url(url)
        if not result["found"]:
            self._out.write_error(f"URL not found: {url}")
        else:
            self._out.write_success(
                f"Reconciled {result['chunks']} chunks for {url} [RAG]"
            )

    def _db_health(self) -> None:
        """Print DB health metrics: integrity, size."""
        info = DbMaintenanceService().health()
        self._out.write_kv(
            [
                ("integrity_ok", str(info.integrity_ok)),
                ("db_size", f"{info.size_bytes:,} bytes"),
                ("target", "Session"),
            ]
        )

    def _db_checkpoint(self, mode: str | None) -> None:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        result = DbMaintenanceService().checkpoint(mode)
        self._out.write_success(
            f"WAL checkpoint complete: mode={result.mode},"
            f" pages_written={result.pages_written} [Session]"
        )

    def _db_vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        DbMaintenanceService().vacuum()
        self._out.write_success("VACUUM complete. [Session]")

    def _db_purge(self, rest: str) -> None:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        parsed = parse_command_args(rest.split())
        max_sessions_raw = parsed.flags.get("max-sessions")
        max_age_days_raw = parsed.flags.get("max-age-days")
        try:
            max_sessions = int(max_sessions_raw) if max_sessions_raw else None
        except (ValueError, TypeError):
            max_sessions = None
        try:
            max_age_days = int(max_age_days_raw) if max_age_days_raw else None
        except (ValueError, TypeError):
            max_age_days = None
        result = DbMaintenanceService().purge(max_sessions, max_age_days)
        self._out.write_success(
            f"Purged: {result.sessions_removed} session(s) removed [Session]"
        )

    def _db_recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        result = RagMaintenanceService().recover(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail} [RAG]")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail} [RAG]")

    def _db_recover_session(self, backup_path: str | None) -> None:
        """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
        result = DbMaintenanceService().recover_session(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail} [Session]")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail} [Session]")

    def _db_consistency(self) -> None:
        """Run RAG search index synchronization check."""
        try:
            result = RagMaintenanceService().consistency()
            numeric_line = (
                f"  chunks: {result.report.chunks}  fts: {result.report.fts}  vec: {result.report.vec}"
                f"  fts_gap: {result.report.fts_gap}  orphan_vec: {result.report.orphan_vec_count}"
                f"  fts_orphan: {result.report.fts_orphan_count}"
            )
            if result.is_consistent:
                self._out.write_success(
                    f"{numeric_line}\nRAG consistency: OK (chunks/FTS/vec in sync)"
                )
            else:
                self._out.write(f"{numeric_line}\nRAG consistency: FAIL")
                for issue in result.issues:
                    self._out.write_error(f"Consistency issue: {issue}")
        except Exception as e:  # noqa: BLE001 — skip if rag.sqlite absent or unreadable
            logger.debug("RAG consistency check skipped: %s", e)
