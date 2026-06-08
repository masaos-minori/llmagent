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

import orjson

from agent.commands.mixin_base import MixinBase
from agent.context import AgentContext
from agent.memory.layer import MemoryLayer

logger = logging.getLogger(__name__)


@dataclass
class MemoryOpResult:
    """Structured result of a memory state-changing operation."""

    ok: bool
    memory_id: str
    action: str  # "deleted" | "pinned" | "unpinned" | "pruned"
    dry_run: bool = False
    count: int = 0  # number of entries affected by prune
    messages: list[str] = field(default_factory=list)


_MEMORY_HELP = """\
/memory list [semantic|episodic] [limit]  List entries (default: all, limit 10)
/memory search <query>                    FTS5 search across all entries
/memory show <id>                         Show full content of one entry
/memory pin <id>                          Pin an entry (always injected at session start)
/memory unpin <id>                        Remove pin from an entry
/memory delete <id>                       Delete one entry by memory_id
/memory prune [days]                      Delete entries older than N days (default: retention_days config)
"""


class _MemoryMixin(MixinBase):
    """Slash-command handlers for /memory."""

    def _cmd_memory(self, args: str) -> None:
        ctx = self._ctx
        mem = ctx.services.memory
        parts = args.strip().split()
        sub = parts[0] if parts else ""

        if not sub or sub == "help":
            print(_MEMORY_HELP)
            return

        if mem is None:
            print("  [memory] Memory layer is disabled (use_memory_layer=false)")
            return

        dispatch = {
            "list": lambda: self._memory_list(mem, parts[1:]),
            "search": lambda: self._memory_search(mem, parts[1:]),
            "show": lambda: self._memory_show(mem, parts[1:]),
            "pin": lambda: self._memory_pin(mem, parts[1:], pin=True),
            "unpin": lambda: self._memory_pin(mem, parts[1:], pin=False),
            "delete": lambda: self._memory_delete(mem, parts[1:]),
            "prune": lambda: self._memory_prune(mem, ctx, parts[1:]),
        }
        handler = dispatch.get(sub)
        if handler:
            handler()
        else:
            print(f"  Unknown subcommand: {sub!r}. Try /memory help")

    def _memory_list(self, mem: MemoryLayer, args: list[str]) -> None:
        layer = mem
        mem_type = next((a for a in args if a in ("semantic", "episodic")), "")
        limit_args = [a for a in args if a.isdigit()]
        limit = int(limit_args[0]) if limit_args else 10

        entries = layer.list_entries(mem_type=mem_type, limit=limit)

        if not entries:
            print("  [memory] No entries found")
            return
        print(f"  {'ID':36}  {'Type':8}  {'Imp':4}  {'Pin':3}  Summary")
        print(f"  {'-' * 36}  {'-' * 8}  {'-' * 4}  {'-' * 3}  {'-' * 40}")
        for e in entries:
            pin_mark = "Y" if e.pinned else "-"
            summary = (e.summary or e.content[:60]).replace("\n", " ")[:60]
            print(
                f"  {e.memory_id:36}  {e.memory_type:8}"
                f"  {e.importance:.2f}  {pin_mark:3}  {summary}",
            )

    def _memory_search(self, mem: MemoryLayer, args: list[str]) -> None:
        layer = mem
        if not args:
            print("  Usage: /memory search <query>")
            return
        query = " ".join(args)
        hits = layer.search(query, limit=10)
        if not hits:
            print(f"  [memory] No results for {query!r}")
            return
        print(f"  Results for {query!r}:")
        for hit in hits:
            e = hit.entry
            summary = (e.summary or e.content[:60]).replace("\n", " ")[:60]
            print(
                f"    [{hit.score:+.3f}] {e.memory_type:8}"
                f"  {e.memory_id[:12]}…  {summary}",
            )

    def _memory_show(self, mem: MemoryLayer, args: list[str]) -> None:
        layer = mem
        if not args:
            print("  Usage: /memory show <id>")
            return
        mid = args[0]
        entry = layer.get_entry(mid)
        if entry is None:
            print(f"  [memory] Entry not found: {mid!r}")
            return
        print(f"  memory_id  : {entry.memory_id}")
        print(f"  type       : {entry.memory_type} / {entry.source_type}")
        print(f"  importance : {entry.importance:.2f}  pinned: {entry.pinned}")
        print(
            f"  project    : {entry.project}  repo: {entry.repo}  branch: {entry.branch}",
        )
        print(f"  created_at : {entry.created_at}")
        print(f"  tags       : {entry.tags}")
        print(f"  summary    : {entry.summary}")
        print(f"  content:\n{entry.content}")

    def _memory_pin(self, mem: MemoryLayer, args: list[str], *, pin: bool) -> None:
        layer = mem
        if not args:
            cmd = "pin" if pin else "unpin"
            print(f"  Usage: /memory {cmd} <id>")
            return
        mid = args[0]
        ok = layer.pin_entry(mid) if pin else layer.unpin_entry(mid)
        action = "pinned" if pin else "unpinned"
        if ok:
            print(f"  [memory] {action}: {mid}")
            self._emit_memory_audit(
                MemoryOpResult(ok=True, memory_id=mid, action=action)
            )
        else:
            print(f"  [memory] Entry not found: {mid!r}")

    def _memory_delete(self, mem: MemoryLayer, args: list[str]) -> None:
        layer = mem
        dry_run = "--dry-run" in args
        ids = [a for a in args if not a.startswith("--")]
        if not ids:
            print("  Usage: /memory delete [--dry-run] <id>")
            return
        mid = ids[0]
        if dry_run:
            exists = layer.get_entry(mid) is not None
            if exists:
                print(f"  [memory] (dry-run) would delete: {mid}")
            else:
                print(f"  [memory] (dry-run) Entry not found: {mid!r}")
            self._emit_memory_audit(
                MemoryOpResult(ok=exists, memory_id=mid, action="deleted", dry_run=True)
            )
            return
        ok = layer.delete_entry(mid)
        if ok:
            print(f"  [memory] Deleted: {mid}")
        else:
            print(f"  [memory] Entry not found: {mid!r}")
        self._emit_memory_audit(MemoryOpResult(ok=ok, memory_id=mid, action="deleted"))

    def _memory_prune(
        self, mem: MemoryLayer, ctx: AgentContext, args: list[str]
    ) -> None:
        layer = mem
        dry_run = "--dry-run" in args
        day_args = [a for a in args if a.isdigit()]
        days = int(day_args[0]) if day_args else ctx.cfg.memory.memory_retention_days
        if dry_run:
            count = layer.count_prunable(days)
            print(
                f"  [memory] (dry-run) would prune {count} entries older than {days} days"
            )
            self._emit_memory_audit(
                MemoryOpResult(
                    ok=True, memory_id="", action="pruned", dry_run=True, count=count
                )
            )
            return
        deleted = layer.prune(days)
        print(f"  [memory] Pruned {deleted} entries older than {days} days")
        self._emit_memory_audit(
            MemoryOpResult(ok=True, memory_id="", action="pruned", count=deleted)
        )

    def _emit_memory_audit(self, result: MemoryOpResult) -> None:
        """audit_logger に memory 操作イベントを書き込む。None ガード付き。"""
        audit = self._ctx.services.audit_logger
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
