"""scripts/agent/commands/memory_data_ops.py — Memory data operation handlers (list, search, show, pin, delete, prune)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.commands.output_port import OutputPort
from agent.context import AgentContext
from agent.memory.pin_ops import pin as pin_mem
from agent.memory.pin_ops import unpin as unpin_mem
from agent.memory.types import MemoryEntry, MemoryQuery
from agent.memory.write_ops import delete as write_delete

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# Local import for shared types/functions
from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit


def _summary_preview(entry: MemoryEntry, max_chars: int = 60) -> str:
    """Return a single-line, length-capped preview: entry.summary or a content excerpt."""
    return (entry.summary or entry.content[:max_chars]).replace("\n", " ")[:max_chars]


def _emit_prune_event(memory_id: str) -> None:
    """Append a 'delete' change event after a prune removes one memory (REQ-005).

    Mirrors ``write_ops._emit_delete_event``: SQLite-first, so the archive append
    runs after the commit. A failed append propagates so the caller can surface
    M-07.
    """
    from pathlib import Path

    from shared.config_loader import ConfigLoader

    from agent.memory.jsonl_store import JsonlMemoryStore

    cfg = ConfigLoader().load("agent.toml")
    store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")
    store.append_event("delete", memory_id)


_MIN_SHORT_ID = 8


class MemoryDataOps:
    """Handles memory data operations: list, search, show, pin, delete, prune."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the memory data operations handler with context and output port."""
        self._ctx = ctx
        self._out = out

    def _resolve_id(self, mem: MemoryServices, token: str) -> tuple[str, str]:
        """Resolve a full or short ID token to a concrete memory_id.

        Returns ``(memory_id, "")`` for a full or unambiguous short ID. Returns
        ``("", "ambiguous")`` when the prefix matches more than one entry and
        ``("", "unknown")`` when it matches none. Uses ``startswith`` on loaded
        ids (no SQL injection); REQ-009.
        """
        store = mem.store
        if store.get_by_id(token) is not None:
            return token, ""
        if len(token) < _MIN_SHORT_ID:
            return "", "unknown"
        existing = store.list_entries(limit=1000)
        matches = [e.memory_id for e in existing if e.memory_id.startswith(token)]
        if len(matches) == 1:
            return matches[0], ""
        return "", "ambiguous" if matches else "unknown"

    def _count_pinned(self) -> int:
        """Return the number of currently pinned memories (SQLite-first, REQ-006)."""
        from db.helper import SQLiteHelper

        with SQLiteHelper("session").open() as db:
            rows = db.fetchall("SELECT count(*) FROM memories WHERE pinned = 1")
        return int(rows[0][0]) if rows else 0

    def memory_list(self, mem: MemoryServices, args: list[str]) -> None:
        """List entries by type with optional filtering."""
        _VALID_SOURCES = {"RULE", "DECISION", "FAILURE", "CONVERSATION"}

        source_type: str | None = None
        branch: str | None = None
        pinned_only = False
        remaining: list[str] = []
        i = 0
        while i < len(args):
            if args[i] == "--source" and i + 1 < len(args):
                source_type = args[i + 1].upper()
                if source_type not in _VALID_SOURCES:
                    self._out.write_validation_error(
                        f"--source must be one of: {', '.join(sorted(_VALID_SOURCES))}"
                    )
                    return
                i += 2
            elif args[i] == "--branch" and i + 1 < len(args):
                branch = args[i + 1]
                i += 2
            elif args[i] == "--pinned":
                pinned_only = True
                i += 1
            else:
                remaining.append(args[i])
                i += 1

        mem_type = next((a for a in remaining if a in ("semantic", "episodic")), "")
        limit_str = next(
            (a for a in remaining if a not in ("semantic", "episodic")), None
        )
        try:
            limit = int(limit_str) if limit_str else 10
        except (ValueError, TypeError):
            limit = 10

        if source_type or branch is not None:
            entries = mem.store.list_entries(
                source_type=source_type, branch=branch, limit=limit
            )
            if mem_type:
                entries = [e for e in entries if e.memory_type == mem_type]
        elif mem_type:
            entries = mem.store.search_by_type(memory_type=mem_type, limit=limit)
        else:
            sem = mem.store.search_by_type("semantic", limit=limit)
            epi = mem.store.search_by_type("episodic", limit=limit)
            entries = sorted(sem + epi, key=lambda e: (not e.pinned, -e.importance))[
                :limit
            ]

        if pinned_only:
            entries = [e for e in entries if e.pinned]

        if not entries:
            self._out.write("  [memory] No entries found")
            return
        self._out.write(f"  {'ID':36}  {'Type':8}  {'Imp':4}  {'Pin':3}  Summary")
        self._out.write(f"  {'-' * 36}  {'-' * 8}  {'-' * 4}  {'-' * 3}  {'-' * 40}")
        for e in entries:
            pin_mark = "Y" if e.pinned else "-"
            summary = _summary_preview(e)
            self._out.write(
                f"  {e.memory_id:36}  {e.memory_type:8}  {e.importance:.2f}  {pin_mark:3}  {summary}",
            )

    def memory_search(self, mem: MemoryServices, args: list[str]) -> None:
        """FTS5 search across all entries."""
        branch = ""
        query_tokens: list[str] = []
        i = 0
        while i < len(args):
            if args[i] == "--branch" and i + 1 < len(args):
                branch = args[i + 1]
                i += 2
            else:
                query_tokens.append(args[i])
                i += 1
        if not query_tokens:
            self._out.write_validation_error("/memory search <query>")
            return
        query = " ".join(query_tokens)
        hits = mem.retriever.search(MemoryQuery(query=query, limit=10), branch=branch)
        if not hits:
            self._out.write(f"  [memory] No results for {query!r}")
            return
        self._out.write(f"  Results for {query!r}:")
        for hit in hits:
            e = hit.entry
            summary = _summary_preview(e)
            self._out.write(
                f"    [{hit.score:+.3f}] {e.memory_type:8}  {e.memory_id[:12]}…  {summary}",
            )

    def memory_show(self, mem: MemoryServices, args: list[str]) -> None:
        """Show full content of one entry."""
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

    def memory_pin(self, mem: MemoryServices, args: list[str], *, pin: bool) -> None:
        """Pin or unpin an entry."""
        if not args:
            cmd = "pin" if pin else "unpin"
            self._out.write_validation_error(f"/memory {cmd} <id>")
            return
        raw = args[0]
        mid, status = self._resolve_id(mem, raw)
        if status == "ambiguous":
            self._out.write(
                f"  [memory] M-04: ambiguous short ID (matches multiple): {raw!r}"
            )
            return
        if status == "unknown":
            self._out.write(f"  [memory] M-03: unknown memory ID: {raw!r}")
            return
        if pin:
            pinned_now = self._count_pinned()
            max_pinned = self._ctx.cfg.memory.memory_max_pinned
            if pinned_now >= max_pinned:
                self._out.write(
                    f"  [memory] M-05: pin limit reached ({max_pinned}); "
                    f"cannot pin {mid!r}"
                )
                return
        ok = pin_mem(mid) if pin else unpin_mem(mid)
        action = "pinned" if pin else "unpinned"
        if ok:
            self._out.write(f"  [memory] {action}: {mid}")
            _emit_memory_audit(
                self._ctx, MemoryOpResult(ok=True, memory_id=mid, action=action)
            )
        else:
            self._out.write(f"  [memory] Entry not found: {mid!r}")

    def memory_delete(self, mem: MemoryServices, args: list[str]) -> None:
        """Delete one entry."""
        dry_run = "--dry-run" in args
        ids = [a for a in args if not a.startswith("--")]
        if not ids:
            self._out.write_validation_error("/memory delete [--dry-run] <id>")
            return
        raw = ids[0]
        mid, status = self._resolve_id(mem, raw)
        if status == "ambiguous":
            self._out.write(
                f"  [memory] M-04: ambiguous short ID (matches multiple): {raw!r}"
            )
            return
        if status == "unknown":
            self._out.write(f"  [memory] M-03: unknown memory ID: {raw!r}")
            return
        if dry_run:
            exists = mem.store.get_by_id(mid) is not None
            if exists:
                self._out.write(f"  [memory] (dry-run) would delete: {mid}")
            else:
                self._out.write(f"  [memory] (dry-run) Entry not found: {mid!r}")
            _emit_memory_audit(
                self._ctx,
                MemoryOpResult(
                    ok=exists, memory_id=mid, action="deleted", dry_run=True
                ),
            )
            return
        ok = write_delete(mid)
        if ok:
            self._out.write(f"  [memory] Deleted: {mid}")
        else:
            self._out.write(f"  [memory] Entry not found: {mid!r}")
        _emit_memory_audit(
            self._ctx, MemoryOpResult(ok=ok, memory_id=mid, action="deleted")
        )

    def memory_prune(
        self, mem: MemoryServices, ctx: AgentContext, args: list[str]
    ) -> None:
        """Delete entries older than N days."""
        from db.helper import SQLiteHelper
        from db.maintenance import prune_old_memories

        from agent.memory.count_ops import count_prunable

        dry_run = "--dry-run" in args
        day_str = next((a for a in args if a != "--dry-run"), None)
        try:
            days = int(day_str) if day_str else ctx.cfg.memory.memory_retention_days
        except (ValueError, TypeError):
            days = ctx.cfg.memory.memory_retention_days
        if dry_run:
            count = count_prunable(days)
            self._out.write(
                f"  [memory] (dry-run) would prune {count} entries older than {days} days"
            )
            _emit_memory_audit(
                ctx,
                MemoryOpResult(
                    ok=True, memory_id="", action="pruned", dry_run=True, count=count
                ),
            )
            return
        with SQLiteHelper("session").open(write_mode=True) as db:
            prune_result = prune_old_memories(db, days)
        deleted = (prune_result.data or {}).get("deleted", 0)
        pruned_ids = (prune_result.data or {}).get("pruned_ids", [])
        for mid in pruned_ids:
            _emit_prune_event(mid)
        self._out.write_success(f"Pruned {deleted} entries older than {days} days")
        _emit_memory_audit(
            ctx, MemoryOpResult(ok=True, memory_id="", action="pruned", count=deleted)
        )
