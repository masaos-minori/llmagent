#!/usr/bin/env python3
"""agent/commands/cmd_db.py
Database management mixin for CommandRegistry.

Provides _DbMixin with:
  _cmd_db         — /db dispatcher
  _db_clean       — delete a document via rag-pipeline-mcp
  _db_list_urls   — list document URLs via rag-pipeline-mcp
"""

import inspect
import logging
from typing import Any

from agent.commands.db_help_display import DbHelpDisplay
from agent.commands.db_rag_ops import DbRagOps
from agent.commands.db_session_ops import DbSessionOps
from agent.commands.db_stats_display import DbStatsDisplay
from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)

DB_PARTS_COUNT = 2


class _DbMixin(MixinBase, DbHelpDisplay, DbStatsDisplay):
    """Database management slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._rag_ops = DbRagOps(self._ctx, self._out)
        self._session_ops = DbSessionOps(self._ctx, self._out)

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
            "urls": lambda: self._rag_ops.list_urls(rest),
            "clean": lambda: self._rag_ops.clean(rest),
            "rebuild-fts": self._rag_ops.rebuild_fts,
            "vec-rebuild": self._rag_ops.vec_rebuild,
            "reconcile-url": self._rag_ops.reconcile_url,
            "recover": lambda: self._rag_ops.recover(rest.strip() or None),
            "consistency": self._rag_ops.consistency,
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
            "health": self._session_ops.health,
            "checkpoint": lambda: self._session_ops.checkpoint(
                rest.strip().upper() or None
            ),
            "vacuum": self._session_ops.vacuum,
            "purge": lambda: self._session_ops.purge(rest),
            "recover": lambda: self._session_ops.recover(rest.strip() or None),
        }
        handler = dispatch.get(subcmd)
        if handler:
            result = handler()
            if inspect.isawaitable(result):
                await result
        else:
            self._db_help_session()
