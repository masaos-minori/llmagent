"""scripts/agent/commands/memory_rebuild_ops.py — Memory rebuild operation handlers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from shared.json_utils import dumps as _json_dumps

from agent.commands.output_port import OutputPort
from agent.context import AgentContext
from agent.memory.import_ops import import_from_jsonl
from agent.memory.rebuild_ops import reindex as _reindex

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# Local import for shared types/functions
from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit


@dataclass
class RebuildResult:
    """Result of a memory rebuild operation."""

    dry_run: bool
    jsonl_count: int
    sqlite_before: int
    inserted: int | None = None
    sqlite_after: int | None = None
    sqlite_only: int = 0
    loss_blocked: bool = False
    error: str | None = None


class MemoryRebuildOps:
    """Handles memory rebuild/reindex operations (rebuild, reindex, check-consistency)."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the memory rebuild operations handler with context and output port."""
        self._ctx = ctx
        self._out = out

    def rebuild(self, mem: MemoryServices, args: list[str]) -> RebuildResult:
        """Rebuild memories from the JSONL archive.

        Default is dry-run. Pass ``--confirm`` to perform the actual rebuild; a
        confirmed run backs up the current SQLite memories first (aborting on
        backup failure) and refuses to drop SQLite-only memories unless
        ``--allow-loss`` is given (REQ-007).
        """
        confirm = "--confirm" in args
        allow_loss = "--allow-loss" in args

        jsonl_store = mem.ingestion._jsonl
        jsonl_count = jsonl_store.count_all()
        sqlite_before = mem.store.check_consistency().memories
        sqlite_only = self._count_sqlite_only(mem, jsonl_store)

        # Dry-run table (spec 5.8-1)
        self._out.write_table(
            ["Metric", "Value"],
            [
                ["JSONL archive records", str(jsonl_count)],
                ["Current SQLite memories", str(sqlite_before)],
                ["Expected after rebuild", str(jsonl_count)],
                ["SQLite-only (at risk)", str(sqlite_only)],
            ],
        )
        if not confirm:
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
                dry_run=True,
                jsonl_count=jsonl_count,
                sqlite_before=sqlite_before,
                sqlite_only=sqlite_only,
            )

        # Pre-run backup (abort on failure)
        try:
            self._backup_memories_as_jsonl(mem)
        except Exception as e:  # noqa: BLE001 — REQ-007: abort rebuild on ANY backup failure
            self._out.write(f"  [memory] Rebuild aborted: backup failed: {e}")
            return RebuildResult(
                dry_run=False,
                jsonl_count=jsonl_count,
                sqlite_before=sqlite_before,
                sqlite_only=sqlite_only,
                error=str(e),
            )

        # Refuse SQLite-only loss unless allowed
        if sqlite_only > 0 and not allow_loss:
            self._out.write(
                f"  [memory] Rebuild refused: {sqlite_only} SQLite-only memor"
                f"{'y' if sqlite_only == 1 else 'ies'} would be lost. "
                "Re-run with --allow-loss to proceed."
            )
            return RebuildResult(
                dry_run=False,
                jsonl_count=jsonl_count,
                sqlite_before=sqlite_before,
                sqlite_only=sqlite_only,
                loss_blocked=True,
            )

        _, inserted = import_from_jsonl(
            jsonl_store, dry_run=False, backup=True, allow_loss=allow_loss
        )
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
        after = mem.store.check_consistency().memories
        return RebuildResult(
            dry_run=False,
            jsonl_count=jsonl_count,
            sqlite_before=sqlite_before,
            inserted=inserted,
            sqlite_after=after,
            sqlite_only=sqlite_only,
        )

    def reindex(self, mem: MemoryServices, args: list[str]) -> None:
        """Rebuild only the requested FTS or vec index (REQ-008).

        ``/memory reindex [--fts|--vec]`` rebuilds the selected index in place;
        ``memories`` and the JSONL archive are unchanged.
        """
        mode = next((a for a in args if a in ("--fts", "--vec")), None)
        if mode not in ("--fts", "--vec"):
            self._out.write_validation_error("/memory reindex [--fts|--vec]")
            return
        idx = "fts" if mode == "--fts" else "vec"
        embed_enabled = self._ctx.cfg.memory.memory_embed_enabled
        if idx == "vec" and not embed_enabled:
            self._out.write("  [memory] embedding disabled — cannot rebuild vec index")
            return
        count = _reindex(idx)
        self._out.write_success(f"memories_{idx} rebuilt: {count} rows [Memory]")
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(ok=True, memory_id="", action=f"reindex-{idx}", count=count),
        )

    def _count_sqlite_only(self, mem: MemoryServices, jsonl_store) -> int:
        """Count SQLite memory ids absent from the JSONL archive."""
        seen = {
            d.get("memory_id")
            for kind, d in jsonl_store.iter_records()
            if kind == "memory"
        }
        seen.discard(None)
        existing = mem.store.list_entries(limit=100000)
        return sum(1 for e in existing if e.memory_id not in seen)

    def _backup_memories_as_jsonl(self, mem: MemoryServices) -> None:
        """Write the current SQLite memories to a JSONL backup file. Raise on failure."""
        entries = mem.store.list_entries(limit=100000)
        base_dir = self._ctx.cfg.memory.memory_jsonl_dir
        ts = datetime.now(UTC).isoformat()
        backup_path = Path(base_dir) / f"memories-backup-{ts}.jsonl"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with backup_path.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(_json_dumps(asdict(e)) + "\n")

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
