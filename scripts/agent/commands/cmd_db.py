#!/usr/bin/env python3
"""agent/commands/cmd_db.py
Database management mixin for CommandRegistry.

Provides _DbMixin with:
  _cmd_db         — /db dispatcher
  _db_stats       — DB record counts (delegates to DbMaintenanceService)
  _db_list_urls   — list document URLs with filters
  _db_clean       — delete a document from the vector store
  _db_rebuild_fts — rebuild the FTS5 index (delegates to DbMaintenanceService)
  _db_health      — print DB health metrics (delegates to DbMaintenanceService)
  _db_checkpoint  — run WAL checkpoint (delegates to DbMaintenanceService)
  _db_vacuum      — run VACUUM (delegates to DbMaintenanceService)
  _db_purge       — purge old sessions (delegates to DbMaintenanceService)
  _db_recover     — integrity check and restore (delegates to DbMaintenanceService)
"""

import logging

from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args
from agent.services.db_maintenance_service import DbMaintenanceService

logger = logging.getLogger(__name__)

DB_PARTS_COUNT = 2
URL_DISPLAY_MAX_LENGTH = 60
URL_DISPLAY_TRUNCATE_LENGTH = URL_DISPLAY_MAX_LENGTH - 3


class _DbMixin(MixinBase):
    """Database management slash-command handlers."""

    def _cmd_db(self, args: str) -> None:
        """Handle /db stats|urls|clean|rebuild-fts|health|checkpoint|vacuum|purge|recover."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == DB_PARTS_COUNT else ""
        dispatch = {
            "stats": self._db_stats,
            "urls": lambda: self._db_list_urls(rest),
            "clean": lambda: self._db_clean(rest),
            "rebuild-fts": self._db_rebuild_fts,
            "health": self._db_health,
            "checkpoint": lambda: self._db_checkpoint(rest.strip().upper() or None),
            "vacuum": self._db_vacuum,
            "purge": lambda: self._db_purge(rest),
            "recover": lambda: self._db_recover(rest.strip() or None),
        }
        handler = dispatch.get(subcmd)
        if handler:
            handler()
        else:
            self._out.write_validation_error(
                "/db stats | /db urls [--lang ja|en] [--limit N]"
                " | /db clean <url> | /db rebuild-fts"
                " | /db health | /db checkpoint [MODE]"
                " | /db vacuum | /db purge [--max-sessions N] [--max-age-days N]"
                " | /db recover [<backup-path>]"
            )

    def _db_clean(self, rest: str) -> None:
        """Delete a document by URL from the vector store."""
        url = rest.strip()
        if not url:
            self._out.write_validation_error("/db clean <url>")
            return
        ok = DbMaintenanceService().delete_document(url)
        if ok:
            self._out.write_success(f"Document deleted: {url}")
        else:
            self._out.write_no_data(f"Document not found: {url}")

    def _db_stats(self) -> None:
        """Print document/chunk/session/message counts from both DBs."""
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("documents", f"{result.docs:,}"),
                ("chunks", f"{result.chunks:,}"),
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
            ]
        )

    def _db_list_urls(self, rest: str) -> None:
        """Parse --lang / --limit options from rest and delegate to DbMaintenanceService."""
        parsed = parse_command_args(rest.split())
        lang_raw = parsed.flags.get("lang")
        lang: str | None = str(lang_raw) if lang_raw in ("ja", "en") else None
        limit_raw = parsed.flags.get("limit")
        limit = int(limit_raw) if limit_raw and str(limit_raw).isdigit() else 20
        rows = DbMaintenanceService().list_documents(lang, limit)
        if not rows:
            self._out.write_no_data("No documents found")
            return
        table_rows = []
        for r in rows:
            url = r["url"]
            if not isinstance(url, str):
                raise TypeError(f"url must be str, got {type(url).__name__}")
            url_display = (
                url[:URL_DISPLAY_TRUNCATE_LENGTH] + "..."
                if len(url) > URL_DISPLAY_MAX_LENGTH
                else url
            )

            lang_val = r["lang"]
            lang_display = lang_val if isinstance(lang_val, str) else "?"

            chunk_count = r["chunk_count"]
            if not isinstance(chunk_count, int):
                raise TypeError(
                    f"chunk_count must be int, got {type(chunk_count).__name__}"
                )
            chunk_display = str(chunk_count)

            fetched_at = r["fetched_at"]
            fetched_display = fetched_at if isinstance(fetched_at, str) else ""

            strategy_display = r.get("chunking_strategy") or "text"

            table_rows.append(
                [
                    url_display,
                    lang_display,
                    chunk_display,
                    fetched_display,
                    strategy_display,
                ]
            )
        self._out.write_table(
            ["URL", "Lang", "Chunks", "Fetched", "Strategy"], table_rows
        )

    def _db_rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        DbMaintenanceService().rebuild_fts()
        self._out.write_success("FTS5 index rebuilt.")

    def _db_health(self) -> None:
        """Print DB health metrics: integrity, size."""
        info = DbMaintenanceService().health()
        self._out.write_kv(
            [
                ("integrity_ok", str(info.integrity_ok)),
                ("db_size", f"{info.size_bytes:,} bytes"),
            ]
        )

    def _db_checkpoint(self, mode: str | None) -> None:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        result = DbMaintenanceService().checkpoint(mode)
        self._out.write_success(
            f"WAL checkpoint complete: mode={result.mode},"
            f" pages_written={result.pages_written}"
        )

    def _db_vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        DbMaintenanceService().vacuum()
        self._out.write_success("VACUUM complete.")

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
        self._out.write_success(f"Purged: {result.sessions_removed} session(s) removed")

    def _db_recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        result = DbMaintenanceService().recover(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail}")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail}")
