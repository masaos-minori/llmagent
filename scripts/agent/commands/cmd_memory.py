#!/usr/bin/env python3
"""agent/commands/cmd_memory.py
/memory slash-command mixin for CommandRegistry.

Subcommands:
  /memory list [semantic|episodic] [limit]  — List entries by type
  /memory search <query>                    — FTS5 search across all entries
  /memory show <id>                         — Show full content of one entry
  /memory pin <id>                          — Pin an entry
  /memory unpin <id>                        — Unpin an entry
  /memory delete [--dry-run] <id>           — Delete one entry
  /memory prune [--dry-run] [days]          — Delete entries older than N days
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import orjson

from agent.commands.enums import MemoryAction
from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.memory_status import build_memory_status, build_status_table
from agent.commands.mixin_base import MixinBase
from agent.memory.services import MemoryServices

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


@dataclass
class MemoryOpResult:
    """Structured result of a memory state-changing operation."""

    ok: bool
    memory_id: str
    action: MemoryAction | str
    dry_run: bool = False
    count: int = 0  # number of entries affected by prune
    messages: list[str] = field(default_factory=list)


def _emit_memory_audit(ctx: AgentContext, result: MemoryOpResult) -> None:
    """Write memory operation event to audit_logger."""
    audit = ctx.services_required.audit_logger
    if audit is None:
        return
    audit.info(
        orjson.dumps(
            {
                "event": "memory_op",
                "action": result.action,
                "memory_id": result.memory_id,
                "dry_run": result.dry_run,
                "count": result.count,
                "ok": result.ok,
                "ts": time.time(),
            },
        ).decode(),
    )


_MEMORY_HELP = """\
/memory list [semantic|episodic] [--source RULE|DECISION|FAILURE|CONVERSATION] [--branch <branch>] [limit]
                                          List entries (default: all, limit 10)
/memory search <query> [--branch <branch>]  FTS5 search across all entries
/memory show <id>                         Show full content of one entry
/memory pin <id>                          Pin an entry (always injected at session start)
/memory unpin <id>                        Remove pin from an entry
/memory delete <id>                       Delete one entry by memory_id
/memory prune [days]                      Delete entries older than N days (default: retention_days config)
/memory status                            Embedding enabled, circuit state, retrieval mode
/memory check-consistency                 Compare JSONL, SQLite, FTS5, and vec row counts
 /memory rebuild [--dry-run]               Import records from JSONL archive (does not replay deletes or pin state)
 /memory rebuild-fts                       Rebuild memories_fts index from SQLite
 /memory rebuild-vec                       Rebuild memories_vec index from SQLite
"""


class _MemoryMixin(MixinBase):
    """Slash-command handlers for /memory."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        from agent.commands.memory_data_ops import MemoryDataOps  # noqa: PLC0415
        from agent.commands.memory_rebuild_ops import MemoryRebuildOps  # noqa: PLC0415

        self._data_ops = MemoryDataOps(self._ctx, self._out)
        self._rebuild_ops = MemoryRebuildOps(self._ctx, self._out)

    def _cmd_memory(self, args: str) -> None:
        ctx = self._ctx
        raw_tokens = args.strip().split()
        sub = raw_tokens[0] if raw_tokens else ""
        sub_tokens = raw_tokens[1:] if raw_tokens else []

        if not sub or sub == "help":
            self._out.write(_MEMORY_HELP)
            return

        mem = ctx.services_required.memory

        # status is allowed even when memory is disabled
        if sub == "status":
            self._memory_status(mem)
            return

        if mem is None:
            self._out.write(
                "  [memory] Memory layer is disabled (use_memory_layer=false)"
            )
            return

        dispatch = {
            "list": lambda: self._data_ops.memory_list(mem, sub_tokens),
            "search": lambda: self._data_ops.memory_search(mem, sub_tokens),
            "show": lambda: self._data_ops.memory_show(mem, sub_tokens),
            "pin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=True),
            "unpin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=False),
            "delete": lambda: self._data_ops.memory_delete(mem, sub_tokens),
            "prune": lambda: self._data_ops.memory_prune(mem, ctx, sub_tokens),
            "check-consistency": lambda: self._rebuild_ops.check_consistency(mem),
            "rebuild": lambda: self._rebuild_ops.rebuild(mem, sub_tokens),
            "import-jsonl": lambda: self._rebuild_ops.rebuild(mem, sub_tokens),
            "rebuild-fts": lambda: self._rebuild_ops.rebuild_fts(mem),
            "rebuild-vec": lambda: self._rebuild_ops.rebuild_vec(mem),
        }
        handler = dispatch.get(sub)
        if handler:
            handler()
        else:
            raise UnknownSubcommandError(sub, tuple(dispatch.keys()))

    def _memory_status(self, mem: MemoryServices | None) -> None:
        """Display memory layer status."""
        if mem is None:
            self._out.write(
                "  [memory] Memory layer: disabled (use_memory_layer=false)"
            )
            return
        embed_client = mem.retriever.embed_client
        if embed_client is None:
            self._out.write("  [memory] embed_client not available")
            return

        status = build_memory_status(mem)
        if status is None:
            self._out.write("  [memory] embed_client not available")
            return

        rows = build_status_table(status)
        self._out.write_table(["Field", "Value"], rows)
