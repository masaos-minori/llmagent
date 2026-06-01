#!/usr/bin/env python3
"""agent/commands/cmd_memory.py
/memory slash-command mixin for CommandRegistry.

Subcommands:
  /memory list [semantic|episodic] [limit]  — List entries by type
  /memory search <query>                    — FTS5 search across all entries
  /memory show <id>                         — Show full content of one entry
  /memory pin <id>                          — Pin an entry
  /memory unpin <id>                        — Unpin an entry
  /memory delete <id>                       — Delete one entry
  /memory prune [days]                      — Delete entries older than N days
"""

from __future__ import annotations

import logging

from agent.context import AgentContext
from agent.memory.types import MemoryQuery

logger = logging.getLogger(__name__)

_MEMORY_HELP = """\
/memory list [semantic|episodic] [limit]  List entries (default: all, limit 10)
/memory search <query>                    FTS5 search across all entries
/memory show <id>                         Show full content of one entry
/memory pin <id>                          Pin an entry (always injected at session start)
/memory unpin <id>                        Remove pin from an entry
/memory delete <id>                       Delete one entry by memory_id
/memory prune [days]                      Delete entries older than N days (default: retention_days config)
"""


class _MemoryMixin:
    """Slash-command handlers for /memory."""

    _ctx: AgentContext

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

    def _memory_list(self, mem: object, args: list[str]) -> None:
        from agent.memory.layer import MemoryLayer

        if not isinstance(mem, MemoryLayer):
            return
        mem_type = next((a for a in args if a in ("semantic", "episodic")), "")
        limit_args = [a for a in args if a.isdigit()]
        limit = int(limit_args[0]) if limit_args else 10

        if mem_type:
            entries = mem._store.search_by_type(memory_type=mem_type, limit=limit)
        else:
            # Show both types merged and sorted when no filter
            sem = mem._store.search_by_type("semantic", limit=limit)
            epi = mem._store.search_by_type("episodic", limit=limit)
            entries = sorted(sem + epi, key=lambda e: (not e.pinned, -e.importance))[
                :limit
            ]

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

    def _memory_search(self, mem: object, args: list[str]) -> None:
        from agent.memory.layer import MemoryLayer

        if not isinstance(mem, MemoryLayer):
            return
        if not args:
            print("  Usage: /memory search <query>")
            return
        query = " ".join(args)
        hits = mem._retriever.search(
            MemoryQuery(query=query, limit=10),
            project=mem._project,
            repo=mem._repo,
        )
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

    def _memory_show(self, mem: object, args: list[str]) -> None:
        from agent.memory.layer import MemoryLayer

        if not isinstance(mem, MemoryLayer):
            return
        if not args:
            print("  Usage: /memory show <id>")
            return
        mid = args[0]
        entry = mem._store.get_by_id(mid)
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

    def _memory_pin(self, mem: object, args: list[str], *, pin: bool) -> None:
        from agent.memory.layer import MemoryLayer

        if not isinstance(mem, MemoryLayer):
            return
        if not args:
            cmd = "pin" if pin else "unpin"
            print(f"  Usage: /memory {cmd} <id>")
            return
        mid = args[0]
        ok = mem._store.pin(mid) if pin else mem._store.unpin(mid)
        action = "pinned" if pin else "unpinned"
        if ok:
            print(f"  [memory] {action}: {mid}")
        else:
            print(f"  [memory] Entry not found: {mid!r}")

    def _memory_delete(self, mem: object, args: list[str]) -> None:
        from agent.memory.layer import MemoryLayer

        if not isinstance(mem, MemoryLayer):
            return
        if not args:
            print("  Usage: /memory delete <id>")
            return
        mid = args[0]
        ok = mem._store.delete(mid)
        if ok:
            logger.info(f"memory.delete memory_id={mid!r}")
            print(f"  [memory] Deleted: {mid}")
        else:
            print(f"  [memory] Entry not found: {mid!r}")

    def _memory_prune(self, mem: object, ctx: AgentContext, args: list[str]) -> None:
        from agent.memory.layer import MemoryLayer
        from db.helper import SQLiteHelper
        from db.maintenance import prune_old_memories

        if not isinstance(mem, MemoryLayer):
            return
        days = (
            int(args[0])
            if args and args[0].isdigit()
            else ctx.cfg.memory_retention_days
        )
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                deleted = prune_old_memories(db, days)
            print(f"  [memory] Pruned {deleted} entries older than {days} days")
        except Exception as e:
            print(f"  [memory] Prune failed: {e}")
