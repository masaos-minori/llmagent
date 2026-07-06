"""rebuild_ops.py — Memory rebuild operation handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from agent.context import AgentContext
from agent.memory.import_ops import import_from_jsonl
from agent.memory.rebuild_ops import rebuild_fts, rebuild_vec

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# Local import for shared types/functions
from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit


@dataclass
class RebuildResult:
    dry_run: bool
    jsonl_count: int
    sqlite_before: int
    inserted: int | None = None
    sqlite_after: int | None = None


class MemoryRebuildOps:
    """Handles memory rebuild operations (rebuild, rebuild-fts, rebuild-vec, check-consistency)."""

    def __init__(self, ctx: AgentContext, out: Any) -> None:
        self._ctx = ctx
        self._out = out

    def rebuild(self, mem: MemoryServices, args: list[str]) -> RebuildResult:
        """Rebuild memories from JSONL archive.

        Default is dry-run. Pass --confirm to perform the actual rebuild.
        """
        dry_run = "--confirm" not in args

        jsonl_store = mem.ingestion._jsonl
        jsonl_count = jsonl_store.count_all()
        consistency = mem.store.check_consistency()
        sqlite_before = consistency.memories

        self._out.write(f"  JSONL archive records:   {jsonl_count}")
        self._out.write(f"  Current SQLite memories: {sqlite_before}")
        self._out.write(f"  Expected after rebuild:  {jsonl_count}")
        self._out.write("  WARNING: delete/pin/unpin operations are NOT replayed.")
        self._out.write("           Deleted entries may be re-inserted from JSONL.")

        if dry_run:
            self._out.write("  [dry-run] No changes made. Add --confirm to proceed.")
            _emit_memory_audit(
                self._ctx,
                MemoryOpResult(
                    ok=True,
                    memory_id="",
                    action="rebuild",
                    dry_run=True,
                    count=jsonl_count,
                ),
            )
            return RebuildResult(
                dry_run=True, jsonl_count=jsonl_count, sqlite_before=sqlite_before
            )

        _, inserted = import_from_jsonl(jsonl_store, dry_run=False)
        self._out.write_success(
            f"Imported {inserted} entries from {jsonl_count} JSONL archive records."
        )
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(
                ok=True,
                memory_id="",
                action="rebuild",
                dry_run=False,
                count=jsonl_count,
            ),
        )

        self.check_consistency(mem)

        after_consistency = mem.store.check_consistency()
        return RebuildResult(
            dry_run=False,
            jsonl_count=jsonl_count,
            sqlite_before=sqlite_before,
            inserted=inserted,
            sqlite_after=after_consistency.memories,
        )

    def rebuild_fts(self, mem: MemoryServices) -> None:
        """Rebuild the memories_fts index from SQLite."""
        count = rebuild_fts()
        self._out.write_success(f"memories_fts rebuilt: {count} rows [Memory]")
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(ok=True, memory_id="", action="rebuild-fts", count=count),
        )

    def rebuild_vec(self, mem: MemoryServices) -> None:
        """Rebuild the memories_vec index from SQLite."""
        embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
        if not embed_enabled:
            self._out.write("  [memory] embedding disabled — cannot rebuild vec index")
            return
        count = rebuild_vec()
        self._out.write_success(f"memories_vec rebuilt: {count} rows [Memory]")
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(ok=True, memory_id="", action="rebuild-vec", count=count),
        )

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
        _emit_memory_audit(
            self._ctx, MemoryOpResult(ok=ok, memory_id="", action="check-consistency")
        )
