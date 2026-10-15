#!/usr/bin/env python3
"""scripts/agent/commands/cmd_memory.py

/memory slash-command mixin for CommandRegistry.

Subcommands:
  /memory status       — Show mode, counts, pinned count (runs on no-args too)
  /memory list [n]     — List memories with short IDs
  /memory delete <id>  — Delete one memory after confirmation
  /memory pin <id>     — Fix a memory
  /memory unpin <id>   — Release a memory
  /memory prune        — Delete stale memories (never pinned)
  /memory reindex      — Rebuild FTS/vec indexes only
  /memory rebuild      — Rebuild memories from the JSONL archive
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps

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
        dumps(
            {
                "event": "memory_op",
                "action": result.action,
                "memory_id": result.memory_id,
                "dry_run": result.dry_run,
                "count": result.count,
                "ok": result.ok,
                "ts": time.time(),
            },
        ),
    )


# M-02: emitted when the memory layer is disabled and a non-status subcommand runs.
# The normative target table/behavior lives in
# docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md.
_M02_DISABLED = "  [memory] M-02: memory layer is disabled (use_memory_layer=false)"


class _MemoryMixin(MixinBase):
    """Slash-command handlers for /memory."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the memory mixin via MixinBase constructor and data/rebuild operations."""
        super().__init__(*args, **kwargs)
        from agent.commands.memory_data_ops import MemoryDataOps
        from agent.commands.memory_rebuild_ops import MemoryRebuildOps

        self._data_ops = MemoryDataOps(self._ctx, self._out)
        self._rebuild_ops = MemoryRebuildOps(self._ctx, self._out)

    def _cmd_memory(self, args: str) -> None:
        """Dispatch memory subcommands: status, list, delete, pin, unpin, prune, reindex, rebuild."""
        ctx = self._ctx
        raw_tokens = args.strip().split()
        sub = raw_tokens[0] if raw_tokens else ""
        sub_tokens = raw_tokens[1:] if raw_tokens else []

        # No-args runs status.
        if not sub:
            self._memory_status(ctx.services_required.memory)
            return

        mem = ctx.services_required.memory

        # status is allowed even when memory is disabled
        if sub == "status":
            self._memory_status(mem)
            return

        # Every other subcommand requires the memory layer.
        if mem is None:
            self._out.write(_M02_DISABLED)
            return

        dispatch = {
            "list": lambda: self._data_ops.memory_list(mem, sub_tokens),
            "delete": lambda: self._data_ops.memory_delete(mem, sub_tokens),
            "pin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=True),
            "unpin": lambda: self._data_ops.memory_pin(mem, sub_tokens, pin=False),
            "prune": lambda: self._data_ops.memory_prune(mem, ctx, sub_tokens),
            "reindex": lambda: self._rebuild_ops.reindex(mem, sub_tokens),
            "rebuild": lambda: self._rebuild_ops.rebuild(mem, sub_tokens),
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

        status = build_memory_status(mem, self._ctx.cfg)
        assert status is not None
        if not status.embedding_enabled:
            self._out.write("  [memory] embed_client not available")
            return

        rows = build_status_table(status)
        self._out.write_table(["Field", "Value"], rows)
