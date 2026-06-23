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

from agent.commands.enums import MemoryAction
from agent.commands.exceptions import UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.context import AgentContext
from agent.memory.services import MemoryServices
from agent.memory.types import MemoryQuery

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


_MEMORY_HELP = """\
/memory list [semantic|episodic] [limit]  List entries (default: all, limit 10)
/memory search <query>                    FTS5 search across all entries
/memory show <id>                         Show full content of one entry
/memory pin <id>                          Pin an entry (always injected at session start)
/memory unpin <id>                        Remove pin from an entry
/memory delete <id>                       Delete one entry by memory_id
/memory prune [days]                      Delete entries older than N days (default: retention_days config)
/memory status                            Embedding enabled, circuit state, retrieval mode
/memory check-consistency                 Compare JSONL, SQLite, FTS5, and vec row counts
/memory rebuild [--dry-run]               Rebuild SQLite from JSONL source of truth
"""


class _MemoryMixin(MixinBase):
    """Slash-command handlers for /memory."""

    def _cmd_memory(self, args: str) -> None:
        ctx = self._ctx
        mem = ctx.services.memory
        raw_tokens = args.strip().split()
        sub = raw_tokens[0] if raw_tokens else ""
        sub_tokens = raw_tokens[1:] if raw_tokens else []

        if not sub or sub == "help":
            self._out.write(_MEMORY_HELP)
            return

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
            "list": lambda: self._memory_list(mem, sub_tokens),
            "search": lambda: self._memory_search(mem, sub_tokens),
            "show": lambda: self._memory_show(mem, sub_tokens),
            "pin": lambda: self._memory_pin(mem, sub_tokens, pin=True),
            "unpin": lambda: self._memory_pin(mem, sub_tokens, pin=False),
            "delete": lambda: self._memory_delete(mem, sub_tokens),
            "prune": lambda: self._memory_prune(mem, ctx, sub_tokens),
            "check-consistency": lambda: self._memory_check_consistency(mem),
            "rebuild": lambda: self._memory_rebuild(mem, sub_tokens),
        }
        handler = dispatch.get(sub)
        if handler:
            handler()
        else:
            raise UnknownSubcommandError(sub, tuple(dispatch.keys()))

    def _memory_list(self, mem: MemoryServices, args: list[str]) -> None:
        mem_type = next((a for a in args if a in ("semantic", "episodic")), "")
        limit_args = [a for a in args if a.isdigit()]
        limit = int(limit_args[0]) if limit_args else 10

        if mem_type:
            entries = mem.store.search_by_type(memory_type=mem_type, limit=limit)
        else:
            sem = mem.store.search_by_type("semantic", limit=limit)
            epi = mem.store.search_by_type("episodic", limit=limit)
            entries = sorted(sem + epi, key=lambda e: (not e.pinned, -e.importance))[
                :limit
            ]

        if not entries:
            self._out.write("  [memory] No entries found")
            return
        self._out.write(f"  {'ID':36}  {'Type':8}  {'Imp':4}  {'Pin':3}  Summary")
        self._out.write(f"  {'-' * 36}  {'-' * 8}  {'-' * 4}  {'-' * 3}  {'-' * 40}")
        for e in entries:
            pin_mark = "Y" if e.pinned else "-"
            summary = (e.summary or e.content[:60]).replace("\n", " ")[:60]
            self._out.write(
                f"  {e.memory_id:36}  {e.memory_type:8}"
                f"  {e.importance:.2f}  {pin_mark:3}  {summary}",
            )

    def _memory_search(self, mem: MemoryServices, args: list[str]) -> None:
        if not args:
            self._out.write_validation_error("/memory search <query>")
            return
        query = " ".join(args)
        hits = mem.retriever.search(MemoryQuery(query=query, limit=10))
        if not hits:
            self._out.write(f"  [memory] No results for {query!r}")
            return
        self._out.write(f"  Results for {query!r}:")
        for hit in hits:
            e = hit.entry
            summary = (e.summary or e.content[:60]).replace("\n", " ")[:60]
            self._out.write(
                f"    [{hit.score:+.3f}] {e.memory_type:8}"
                f"  {e.memory_id[:12]}…  {summary}",
            )

    def _memory_show(self, mem: MemoryServices, args: list[str]) -> None:
        if not args:
            self._out.write_validation_error("/memory show <id>")
            return
        mid = args[0]
        entry = mem.store.get_by_id(mid)
        if entry is None:
            self._out.write(f"  [memory] Entry not found: {mid!r}")
            return
        self._out.write(f"  memory_id  : {entry.memory_id}")
        self._out.write(f"  type       : {entry.memory_type} / {entry.source_type}")
        self._out.write(
            f"  importance : {entry.importance:.2f}  pinned: {entry.pinned}"
        )
        self._out.write(
            f"  project    : {entry.project}  repo: {entry.repo}  branch: {entry.branch}",
        )
        self._out.write(f"  created_at : {entry.created_at}")
        self._out.write(f"  tags       : {entry.tags}")
        self._out.write(f"  summary    : {entry.summary}")
        self._out.write(f"  content:\n{entry.content}")

    def _memory_pin(self, mem: MemoryServices, args: list[str], *, pin: bool) -> None:
        if not args:
            cmd = "pin" if pin else "unpin"
            self._out.write_validation_error(f"/memory {cmd} <id>")
            return
        mid = args[0]
        ok = mem.store.pin(mid) if pin else mem.store.unpin(mid)
        action = "pinned" if pin else "unpinned"
        if ok:
            self._out.write(f"  [memory] {action}: {mid}")
            self._emit_memory_audit(
                MemoryOpResult(ok=True, memory_id=mid, action=action)
            )
        else:
            self._out.write(f"  [memory] Entry not found: {mid!r}")

    def _memory_delete(self, mem: MemoryServices, args: list[str]) -> None:
        dry_run = "--dry-run" in args
        ids = [a for a in args if not a.startswith("--")]
        if not ids:
            self._out.write_validation_error("/memory delete [--dry-run] <id>")
            return
        mid = ids[0]
        if dry_run:
            exists = mem.store.get_by_id(mid) is not None
            if exists:
                self._out.write(f"  [memory] (dry-run) would delete: {mid}")
            else:
                self._out.write(f"  [memory] (dry-run) Entry not found: {mid!r}")
            self._emit_memory_audit(
                MemoryOpResult(ok=exists, memory_id=mid, action="deleted", dry_run=True)
            )
            return
        ok = mem.store.delete(mid)
        if ok:
            self._out.write(f"  [memory] Deleted: {mid}")
        else:
            self._out.write(f"  [memory] Entry not found: {mid!r}")
        self._emit_memory_audit(MemoryOpResult(ok=ok, memory_id=mid, action="deleted"))

    def _memory_prune(
        self, mem: MemoryServices, ctx: AgentContext, args: list[str]
    ) -> None:
        from db.helper import SQLiteHelper
        from db.maintenance import prune_old_memories

        dry_run = "--dry-run" in args
        day_args = [a for a in args if a.isdigit()]
        days = int(day_args[0]) if day_args else ctx.cfg.memory.memory_retention_days
        if dry_run:
            count = mem.store.count_prunable(days)
            self._out.write(
                f"  [memory] (dry-run) would prune {count} entries older than {days} days"
            )
            self._emit_memory_audit(
                MemoryOpResult(
                    ok=True, memory_id="", action="pruned", dry_run=True, count=count
                )
            )
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            prune_result = prune_old_memories(db, days)
        deleted = (prune_result.data or {}).get("deleted", 0)
        self._out.write_success(f"Pruned {deleted} entries older than {days} days")
        self._emit_memory_audit(
            MemoryOpResult(ok=True, memory_id="", action="pruned", count=deleted)
        )

    def _memory_status(self, mem: MemoryServices | None) -> None:
        if mem is None:
            self._out.write(
                "  [memory] Memory layer: disabled (use_memory_layer=false)"
            )
            return
        embed_client = mem.retriever.embed_client
        if embed_client is None:
            self._out.write("  [memory] embed_client not available")
            return
        status = embed_client.get_status()
        circuit_detail = ""
        if status.circuit_open and status.resets_in_sec is not None:
            circuit_detail = f" (resets in {status.resets_in_sec:.0f}s)"
        rows = [
            ["Memory layer", "enabled"],
            ["Embedding enabled", "Yes" if status.enabled else "No"],
            [
                "Circuit",
                ("OPEN" + circuit_detail) if status.circuit_open else "closed",
            ],
            ["Consecutive failures", str(status.fail_count)],
            ["Last retrieval mode", mem.retriever.last_retrieval_mode],
        ]
        self._out.write_table(["Field", "Value"], rows)

    def _memory_check_consistency(self, mem: MemoryServices) -> None:
        from agent.memory.exceptions import MemoryConsistencyError

        try:
            report = mem.store.check_consistency()
        except MemoryConsistencyError as e:
            self._out.write(f"  [memory] check-consistency error: {e}")
            return
        jsonl_store = mem.ingestion._jsonl
        jsonl_count = jsonl_store.count_all()
        embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
        vec_expected = embed_enabled
        ok = (
            (jsonl_count == report.memories)
            and (report.memories == report.fts)
            and (not vec_expected or report.vec == report.memories)
        )
        rows = [
            ["JSONL records", str(jsonl_count)],
            ["SQLite memories", str(report.memories)],
            ["FTS5 rows", str(report.fts)],
            ["Vec rows", str(report.vec)],
            ["Vec check required", "Yes" if vec_expected else "No (embedding disabled)"],
            ["Consistent", "Yes" if ok else "NO - use /memory rebuild to repair"],
        ]
        self._out.write_table(["Metric", "Value"], rows)
        if not ok:
            self._ctx.stats.stat_memory_consistency_failures += 1
        self._emit_memory_audit(
            MemoryOpResult(ok=ok, memory_id="", action="check-consistency")
        )

    def _memory_rebuild(self, mem: MemoryServices, args: list[str]) -> None:
        dry_run = "--dry-run" in args
        jsonl_store = mem.ingestion._jsonl
        jsonl_count, inserted = mem.store.rebuild_from_jsonl(
            jsonl_store, dry_run=dry_run
        )
        if dry_run:
            self._out.write(
                f"  [memory] (dry-run) would rebuild from {jsonl_count} JSONL records"
            )
        else:
            self._out.write_success(
                f"Rebuilt {inserted} entries from {jsonl_count} JSONL records"
            )
            embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
            if embed_enabled:
                self._out.write(
                    "  Note: memories_vec cleared -- embeddings not re-indexed."
                    " Run /memory rebuild again after re-embedding or disable use to silence."
                )
        self._emit_memory_audit(
            MemoryOpResult(
                ok=True,
                memory_id="",
                action="rebuild",
                dry_run=dry_run,
                count=jsonl_count,
            )
        )

    def _emit_memory_audit(self, result: MemoryOpResult) -> None:
        """Write memory operation event to audit_logger."""
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
