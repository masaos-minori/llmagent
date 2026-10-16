"""scripts/agent/commands/memory_data_ops.py — Memory data operation handlers (list, search, show, pin, delete, prune)."""

from __future__ import annotations

from dataclasses import dataclass
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


def _confirm(prompt: str) -> bool:
    """Return True only for a y/yes answer; EOFError or any other answer returns False."""
    try:
        answer = input(prompt)
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


@dataclass(frozen=True)
class _ListOptions:
    """Parsed arguments for ``memory_list``."""

    limit: int
    memory_type: str
    pinned_only: bool
    query: str


def _parse_list_options(self, tokens: list[str]) -> _ListOptions | None:
    """Parse ``memory_list`` tokens into ``_ListOptions`` or write an error and return None.

    A bare all-digit token sets the limit (1-200); ``--type`` requires ``semantic`` or
    ``episodic``; ``--pinned`` sets the flag; ``--query`` consumes following tokens up to
    the next ``--`` token. Any other ``--`` option or bare token is a validation error.
    """
    limit = 20
    memory_type = ""
    pinned_only = False
    query_parts: list[str] = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "--query":
            i += 1
            while i < n and not tokens[i].startswith("--"):
                query_parts.append(tokens[i])
                i += 1
            continue
        if tok.isdigit():
            value = int(tok)
            if value < 1 or value > 200:
                self._out.write_validation_error("/memory list [n]")
                return None
            limit = value
            i += 1
            continue
        if tok == "--type":
            if i + 1 >= n:
                self._out.write_validation_error(
                    "/memory list [--type semantic|episodic]"
                )
                return None
            memory_type = tokens[i + 1]
            if memory_type not in ("semantic", "episodic"):
                self._out.write_validation_error(
                    "/memory list [--type semantic|episodic]"
                )
                return None
            i += 2
            continue
        if tok == "--pinned":
            pinned_only = True
            i += 1
            continue
        if tok.startswith("--"):
            self._out.write_validation_error(
                "/memory list [n] [--type semantic|episodic] [--pinned] [--query <text>]"
            )
            return None
        self._out.write_validation_error(
            "/memory list [n] [--type semantic|episodic] [--pinned] [--query <text>]"
        )
        return None
    return _ListOptions(
        limit=limit,
        memory_type=memory_type,
        pinned_only=pinned_only,
        query=" ".join(query_parts),
    )


def _parse_prune_days(self, tokens: list[str], default_days: int) -> int | None:
    """Parse ``--days`` for ``memory_prune`` or write an error and return None.

    ``--days`` must be an integer of at least 1. With no argument (and no positional
    token) the provided retention default is used. ``--dry-run`` is ignored.
    """
    clean = [t for t in tokens if t != "--dry-run"]
    if "--days" in clean:
        idx = clean.index("--days")
        raw = clean[idx + 1] if idx + 1 < len(clean) else ""
        try:
            days = int(raw)
        except (ValueError, TypeError):
            self._out.write_validation_error("/memory prune [--days <n>]")
            return None
        if days < 1:
            self._out.write_validation_error("/memory prune [--days <n>]")
            return None
        return days
    if not clean:
        return int(default_days)
    self._out.write_validation_error("/memory prune [--days <n>]")
    return None


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
        options = _parse_list_options(self, args)
        if options is None:
            return

        if options.query:
            hits = mem.retriever.search(
                MemoryQuery(query=options.query, limit=200), branch=""
            )
            entries = [hit.entry for hit in hits]
        elif options.memory_type:
            entries = mem.store.search_by_type(
                memory_type=options.memory_type, limit=200
            )
        else:
            sem = mem.store.search_by_type(memory_type="semantic", limit=200)
            epi = mem.store.search_by_type(memory_type="episodic", limit=200)
            entries = sem + epi

        entries = sorted(entries, key=lambda e: (not e.pinned, -e.importance))
        if options.pinned_only:
            entries = [e for e in entries if e.pinned]
        entries = entries[: options.limit]

        if not entries:
            self._out.write("  [memory] No entries found")
            return
        self._out.write(f"  {'ID':10}  {'Type':8}  {'Imp':4}  {'Pin':3}  Summary")
        self._out.write(f"  {'-' * 10}  {'-' * 8}  {'-' * 4}  {'-' * 3}  {'-' * 40}")
        for e in entries:
            pin_mark = "Y" if e.pinned else "-"
            summary = _summary_preview(e)
            self._out.write(
                f"  {e.memory_id[:8]:10}  {e.memory_type:8}  {e.importance:.2f}  {pin_mark:3}  {summary}",
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
        if not _confirm(f"Delete memory {mid}? [y/N]: "):
            self._out.write("  [memory] Cancelled: nothing was deleted")
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
        from db.store_impl import SQLiteMemoryDeleteStore

        days = _parse_prune_days(self, args, ctx.cfg.memory.memory_retention_days)
        if days is None:
            return

        dry_run = "--dry-run" in args
        with SQLiteHelper("session").open() as db:
            store = SQLiteMemoryDeleteStore(db)
            prunable_ids = store.collect_prunable_ids(days)
        count = len(prunable_ids)

        if dry_run:
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

        if count == 0:
            self._out.write("  [memory] Nothing is prunable")
            return

        if not _confirm(
            f"Delete {count} memories not updated for {days} days? [y/N]: "
        ):
            self._out.write("  [memory] Cancelled: nothing was deleted")
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
