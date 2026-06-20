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
from agent.commands.utils import parse_command_args
from agent.services.db_maintenance_service import DbMaintenanceService

logger = logging.getLogger(__name__)

DB_PARTS_COUNT = 2
URL_DISPLAY_MAX_LENGTH = 60
URL_DISPLAY_TRUNCATE_LENGTH = URL_DISPLAY_MAX_LENGTH - 3


class _DbMixin(MixinBase):
    """Database management slash-command handlers."""

    async def _cmd_db(self, args: str) -> None:
        """Handle /db stats|urls|clean|rebuild-fts|health|checkpoint|vacuum|purge|recover."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == DB_PARTS_COUNT else ""
        dispatch: dict[str, Any] = {
            "help": self._db_help,
            "stats": self._db_stats,
            "urls": lambda: self._db_list_urls(rest),
            "clean": lambda: self._db_clean(rest),
            "rebuild-fts": self._db_rebuild_fts,
            "health": self._db_health,
            "checkpoint": lambda: self._db_checkpoint(rest.strip().upper() or None),
            "vacuum": self._db_vacuum,
            "purge": lambda: self._db_purge(rest),
            "recover": lambda: self._db_recover(rest.strip() or None),
            "consistency": self._db_consistency,
        }
        handler = dispatch.get(subcmd)
        if handler:
            result = handler()
            if inspect.isawaitable(result):
                await result
        else:
            self._out.write_validation_error(
                "/db help | /db stats | /db urls [--lang ja|en] [--limit N]"
                " | /db clean <url> | /db rebuild-fts"
                " | /db health | /db checkpoint [MODE]"
                " | /db vacuum | /db purge [--max-sessions N] [--max-age-days N]"
                " | /db recover [<backup-path>] | /db consistency"
            )

    def _db_help(self) -> None:
        """Print a help table for /db subcommands."""
        rows = [
            ["stats", "RAG + Session", "", "Record counts"],
            ["urls", "RAG", "--lang --limit", "List document URLs"],
            ["clean", "RAG", "<url>", "Delete a document"],
            ["rebuild-fts", "RAG", "", "Rebuild FTS5 index"],
            ["health", "Session", "", "Integrity check / size"],
            ["checkpoint", "Session", "[MODE]", "WAL checkpoint"],
            ["vacuum", "Session", "", "Reclaim free pages"],
            [
                "purge",
                "Session",
                "--max-sessions N\n--max-age-days N",
                "Purge old sessions",
            ],
            ["recover", "RAG", "[backup-path]", "Integrity check / restore"],
            ["consistency", "RAG", "", "Chunks/FTS/vec sync check"],
        ]
        self._out.write_table(
            ["Subcommand", "Target DB", "Arguments", "Description"],
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
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("documents", f"{result.docs:,}"),
                ("chunks", f"{result.chunks:,}"),
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "RAG + Session"),
            ]
        )

    async def _db_list_urls(self, rest: str) -> None:
        """List indexed documents via rag-pipeline-mcp."""
        parsed = parse_command_args(rest.split())
        lang_raw = parsed.flags.get("lang")
        lang: str | None = str(lang_raw) if lang_raw in ("ja", "en") else None
        limit_raw = parsed.flags.get("limit")
        limit = int(limit_raw) if limit_raw and str(limit_raw).isdigit() else 20
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
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        DbMaintenanceService().rebuild_fts()
        self._out.write_success("FTS5 index rebuilt [RAG]")

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
        max_sessions = (
            int(max_sessions_raw)
            if max_sessions_raw and str(max_sessions_raw).isdigit()
            else None
        )
        max_age_days = (
            int(max_age_days_raw)
            if max_age_days_raw and str(max_age_days_raw).isdigit()
            else None
        )
        result = DbMaintenanceService().purge(max_sessions, max_age_days)
        self._out.write_success(
            f"Purged: {result.sessions_removed} session(s) removed [Session]"
        )

    def _db_recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        result = DbMaintenanceService().recover(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail} [RAG]")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail} [RAG]")

    def _db_consistency(self) -> None:
        """Run RAG consistency check: chunks vs FTS vs vec index sync."""
        consistent, issues = DbMaintenanceService().consistency()
        if consistent:
            self._out.write_success(
                "RAG consistency: OK (chunks/FTS/vec in sync) [RAG]"
            )
        else:
            for issue in issues:
                self._out.write_error(f"Consistency issue: {issue} [RAG]")
