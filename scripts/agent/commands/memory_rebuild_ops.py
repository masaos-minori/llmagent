"""rebuild_ops.py — Memory rebuild operation handlers."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import orjson

from agent.commands.enums import MemoryAction
from agent.context import AgentContext

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# Local import for shared types/functions
from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit


class MemoryRebuildOps:
    """Handles memory rebuild operations (rebuild, rebuild-fts, rebuild-vec, check-consistency)."""

    def __init__(self, ctx: AgentContext, out: Any) -> None:
        self._ctx = ctx
        self._out = out

    def rebuild(self, mem: MemoryServices, args: list[str]) -> None:
        """Rebuild memories from JSONL archive."""
        dry_run = "--dry-run" in args
        jsonl_store = mem.ingestion._jsonl
        jsonl_count, inserted = mem.store.import_from_jsonl(jsonl_store, dry_run=dry_run)
        if dry_run:
            self._out.write(
                f"  [memory] (dry-run) would import from {jsonl_count} JSONL archive records"
            )
        else:
            self._out.write_success(
                f"Imported {inserted} entries from {jsonl_count} JSONL archive records. "
                "Note: deletions and pin state are NOT replayed. "
                "Deleted entries may have been re-inserted."
            )
            embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
            if embed_enabled:
                self._out.write(
                    "  Note: memories_vec cleared -- embeddings not re-indexed."
                    " Run /memory rebuild again after re-embedding or disable use to silence."
                )
        _emit_memory_audit(self._ctx, MemoryOpResult(ok=True, memory_id="", action="rebuild", dry_run=dry_run, count=jsonl_count))

    def rebuild_fts(self, mem: MemoryServices) -> None:
        """Rebuild the memories_fts index from SQLite."""
        count = mem.store.rebuild_fts()
        self._out.write_success(f"memories_fts rebuilt: {count} rows [Memory]")
        _emit_memory_audit(self._ctx, MemoryOpResult(ok=True, memory_id="", action="rebuild-fts", count=count))

    def rebuild_vec(self, mem: MemoryServices) -> None:
        """Rebuild the memories_vec index from SQLite."""
        embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
        if not embed_enabled:
            self._out.write("  [memory] embedding disabled — cannot rebuild vec index")
            return
        count = mem.store.rebuild_vec()
        self._out.write_success(f"memories_vec rebuilt: {count} rows [Memory]")
        _emit_memory_audit(self._ctx, MemoryOpResult(ok=True, memory_id="", action="rebuild-vec", count=count))

    def check_consistency(self, mem: MemoryServices) -> None:
        """Check consistency between SQLite, JSONL, FTS5, and vec row counts."""
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
        ok = (report.memories == report.fts) and (
            not vec_expected or report.vec == report.memories
        )
        rows = [
            ["SQLite memories (authoritative)", str(report.memories)],
            ["JSONL archive records (info only)", str(jsonl_count)],
            ["FTS5 rows", str(report.fts)],
            ["Vec rows", str(report.vec)],
            [
                "Vec check required",
                "Yes" if vec_expected else "No (embedding disabled)",
            ],
            [
                "Consistent",
                "Yes" if ok else "NO — see repair commands below",
            ],
        ]
        self._out.write_table(["Metric", "Value"], rows)
        if not ok:
            self._ctx.stats.stat_memory_consistency_failures += 1
            embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
            fts_gap = abs(report.memories - report.fts)
            vec_gap = abs(report.memories - report.vec)
            self._out.write(
                "  [memory] Inconsistency detected.\n"
                f"    FTS gap: {fts_gap} rows (SQLite vs FTS5)\n"
                f"    Vec gap: {vec_gap} rows (SQLite vs vector index)"
            )
            if fts_gap > 0:
                self._out.write("    Repair: /memory rebuild-fts")
            if embed_enabled and vec_gap > 0:
                self._out.write(
                    "    Repair: /memory rebuild-vec (requires embedding regeneration)"
                )
        _emit_memory_audit(self._ctx, MemoryOpResult(ok=ok, memory_id="", action="check-consistency"))
