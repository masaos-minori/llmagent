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
import sqlite3

from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_flag_int, parse_flag_str
from agent.services.db_maintenance_service import DbMaintenanceService

logger = logging.getLogger(__name__)


class _DbMixin(MixinBase):
    """Database management slash-command handlers."""

    def _cmd_db(self, args: str) -> None:
        """Handle /db stats|urls|clean|rebuild-fts|health|checkpoint|vacuum|purge|recover."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == 2 else ""
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
            print(
                "Usage: /db stats | /db urls [--lang ja|en] [--limit N]"
                " | /db clean <url> | /db rebuild-fts"
                " | /db health | /db checkpoint [MODE]"
                " | /db vacuum | /db purge [--max-sessions N] [--max-age-days N]"
                " | /db recover [<backup-path>]",
            )

    def _db_clean(self, rest: str) -> None:
        """Delete a document by URL from the vector store."""
        url = rest.strip()
        if not url:
            print("Usage: /db clean <url>")
            return
        ok = self._ctx.session.delete_document(url)
        print(f"Document deleted: {url}" if ok else f"Document not found: {url}")

    def _db_stats(self) -> None:
        """Print document/chunk/session/message counts from both DBs."""
        try:
            result = DbMaintenanceService().stats()
            print(f"documents : {result['docs']:,}")
            print(f"chunks    : {result['chunks']:,}")
            print(f"sessions  : {result['sessions']:,}")
            print(f"messages  : {result['messages']:,}")
        except sqlite3.Error as e:
            print(f"DB stats error: {e}")
        except Exception as e:
            print(f"DB stats unexpected error: {e}")

    def _db_list_urls(self, rest: str) -> None:
        """Parse --lang / --limit options from rest and delegate to AgentSession."""
        tokens = rest.split()
        lang_raw = parse_flag_str(tokens, "--lang")
        lang: str | None = lang_raw if lang_raw in ("ja", "en") else None
        limit = parse_flag_int(tokens, "--limit") or 20
        rows = self._ctx.session.list_documents(lang, limit)
        if not rows:
            print("No documents found")
            return
        print(f"{'URL':<60}  {'Lang'}  {'Chunks':>6}  Fetched")
        for r in rows:
            url = str(r["url"])
            url_disp = url[:57] + "..." if len(url) > 60 else url
            print(
                f"{url_disp:<60}  {r['lang'] or '?':>4}  {r['chunk_count']:>6}"
                f"  {r['fetched_at']}"
            )

    def _db_rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        try:
            DbMaintenanceService().rebuild_fts()
            print("FTS5 index rebuilt.")
        except sqlite3.Error as e:
            print(f"FTS rebuild error: {e}")
        except Exception as e:
            print(f"FTS rebuild unexpected error: {e}")

    def _db_health(self) -> None:
        """Print DB health metrics: journal mode, integrity, page stats."""
        try:
            info = DbMaintenanceService().health()
            print(f"journal_mode    : {info['journal_mode']}")
            print(f"integrity       : {info['integrity']}")
            print(f"page_count      : {info['page_count']:,}")
            print(f"page_size       : {info['page_size']:,} bytes")
            print(f"freelist_count  : {info['freelist_count']:,}")
            print(f"db_size         : {info['db_size_bytes']:,} bytes")
        except sqlite3.Error as e:
            print(f"DB health error: {e}")
        except Exception as e:
            print(f"DB health unexpected error: {e}")

    def _db_checkpoint(self, mode: str | None) -> None:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        try:
            result = DbMaintenanceService().checkpoint(mode)
            print(f"WAL checkpoint complete: {result}")
        except sqlite3.Error as e:
            print(f"Checkpoint error: {e}")
        except Exception as e:
            print(f"Checkpoint unexpected error: {e}")

    def _db_vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        try:
            DbMaintenanceService().vacuum()
            print("VACUUM complete.")
        except sqlite3.Error as e:
            print(f"VACUUM error: {e}")
        except Exception as e:
            print(f"VACUUM unexpected error: {e}")

    def _db_purge(self, rest: str) -> None:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        tokens = rest.split()
        max_sessions = parse_flag_int(tokens, "--max-sessions")
        max_age_days = parse_flag_int(tokens, "--max-age-days")
        try:
            result = DbMaintenanceService().purge(max_sessions, max_age_days)
            print(
                f"Purged: {result['age_deleted']} by age, {result['count_deleted']} by count",
            )
        except sqlite3.Error as e:
            print(f"Purge error: {e}")
        except Exception as e:
            print(f"Purge unexpected error: {e}")

    def _db_recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        try:
            ok = DbMaintenanceService().recover(backup_path)
            print("Recovery succeeded." if ok else "Recovery failed — check logs.")
        except Exception as e:
            print(f"Recovery error: {e}")
