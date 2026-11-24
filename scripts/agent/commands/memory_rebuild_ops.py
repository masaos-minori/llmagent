"""scripts/agent/commands/memory_rebuild_ops.py — Memory rebuild operation handlers."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from shared.json_utils import dumps as _json_dumps

from agent.commands.output_port import OutputPort
from agent.context import AgentContext
from agent.memory.import_ops import import_from_jsonl
from agent.memory.rebuild_ops import reindex as _reindex
from agent.services.maintenance_jobs import (
    ApprovalDecision,
    JobConflictError,
    JobState,
    MaintenanceJob,
    MaintenanceJobRegistry,
    StoreTarget,
)

if TYPE_CHECKING:
    from agent.memory.services import MemoryServices

# Local import for shared types/functions
from agent.commands.cmd_memory import MemoryOpResult, _emit_memory_audit

# The flag forms stay accepted, but only as recorded grants: they name how a run was
# approved and are not the authority that permits it (REQ-003, OD-03).
_GRANT_FLAGS: dict[str, str] = {"--confirm": "confirm", "--allow-loss": "allow_loss"}

# The index a `reindex` run names, keyed by the flag form the command reads.
_INDEX_FLAGS: dict[str, str] = {"--fts": "fts", "--vec": "vec"}


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
    # The run the result belongs to, so the reported outcome and the job record agree.
    job_id: str = ""
    # The consistency check's result, so a run that did not verify cannot read as success.
    verified: bool = False


class MemoryRebuildOps:
    """Handles memory rebuild/reindex operations (rebuild, reindex, check-consistency)."""

    def __init__(self, ctx: AgentContext, out: OutputPort) -> None:
        """Initialize the memory rebuild operations handler with context and output port."""
        self._ctx = ctx
        self._out = out

    async def rebuild(self, mem: MemoryServices, args: list[str]) -> RebuildResult:
        """Rebuild memories from the JSONL archive as a tracked job (REQ-006).

        The run is registered, approved by the level the registry declares for `rebuild`,
        and reported by its job id. `--confirm` and `--allow-loss` are read as recorded
        grants, so a run with no recorded grant is not approved and changes nothing — that
        is the summary the command has always shown for an unconfirmed run (REQ-003). A
        granted run backs up the current SQLite memories first, aborting on any backup
        failure, and refuses to drop SQLite-only memories unless `--allow-loss` was recorded.
        """
        job = self._register_run("rebuild", args)
        if job is None:
            return RebuildResult(
                dry_run=False, jsonl_count=0, sqlite_before=0, error="job refused"
            )

        summary = self._pre_run_summary(mem, job)
        if not self._approve_and_report(job):
            self._report_unapproved_run(job, summary)
            return replace(summary, dry_run=True)

        self._registry().start(job)
        try:
            outcome = await asyncio.to_thread(self._run_import, job, mem, summary)
        except asyncio.CancelledError:
            self._registry().mark_outcome_unknown(job)
            raise
        return outcome

    async def reindex(self, mem: MemoryServices, args: list[str]) -> None:
        """Rebuild only the requested FTS or vec index as a tracked job (REQ-006).

        ``/memory reindex [--fts|--vec]`` rebuilds the selected index in place;
        ``memories`` and the JSONL archive are unchanged. The run is decided by the level the
        registry declares for `reindex`; a recorded `--confirm` grant is what a
        non-interactive runbook supplies (REQ-003).
        """
        idx = self._index_target(args)
        if idx is None:
            return

        job = self._register_run("reindex", args)
        if job is None:
            return
        if not self._approve_and_report(job):
            return

        self._registry().start(job)
        try:
            await asyncio.to_thread(self._run_index, job, idx)
        except asyncio.CancelledError:
            self._registry().mark_outcome_unknown(job)
            raise

    def _index_target(self, args: list[str]) -> str | None:
        """Resolve the index the run names, or report why there is nothing to run."""
        idx = next((_INDEX_FLAGS[a] for a in args if a in _INDEX_FLAGS), None)
        if idx is None:
            self._out.write_validation_error("/memory reindex [--fts|--vec]")
            return None
        if idx == "vec" and not self._ctx.cfg.memory.memory_embed_enabled:
            self._out.write("  [memory] embedding disabled — cannot rebuild vec index")
            return None
        return idx

    def _registry(self) -> MaintenanceJobRegistry:
        """Return the single job registry the command path reaches."""
        return self._ctx.services_required.job_registry

    def _job_session_target(self) -> str:
        """Return the live session identity the run is attributed to (REQ-001)."""
        target = self._ctx.session.capture_target()
        return f"{target.session_id}:{target.generation}"

    def _register_run(self, operation: str, args: list[str]) -> MaintenanceJob | None:
        """Record one Memory maintenance run and the grants the caller observed on it.

        The flags are recorded as provenance, not as the authority (REQ-003). A second write
        job against a store that already has a running writer is refused naming that run, so
        the Memory path never takes the `session.sqlite` writer slot twice.
        """
        registry = self._registry()
        try:
            job = registry.register(
                operation=operation,
                store=StoreTarget.SESSION,
                session_target=self._job_session_target(),
            )
        except JobConflictError as exc:
            self._out.write_error(f"job refused: {exc}")
            return None
        for flag, name in _GRANT_FLAGS.items():
            if flag in args:
                registry.record_grant(job, name)
        return job

    def _approve_and_report(self, job: MaintenanceJob) -> bool:
        """Enforce the level the registry declares for the operation, not the command line.

        A run that is not approved is reported with the job id the registry decided for.
        """
        decision = self._registry().authorize(job, confirmed=bool(job.grants))
        if not decision.approved:
            self._report_refusal(job, decision)
        return decision.approved

    def _pre_run_summary(
        self, mem: MemoryServices, job: MaintenanceJob
    ) -> RebuildResult:
        """Report the pre-run summary and return the counts the run starts from."""
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
        return RebuildResult(
            dry_run=False,
            jsonl_count=jsonl_count,
            sqlite_before=sqlite_before,
            sqlite_only=sqlite_only,
            job_id=job.job_id,
        )

    def _run_import(
        self, job: MaintenanceJob, mem: MemoryServices, summary: RebuildResult
    ) -> RebuildResult:
        """Run the granted work, measure the postcondition, then report the run (REQ-004).

        The consistency check is the run's postcondition: it is measured before any success
        line and its result is carried into the reported outcome, so a run that did not
        verify is reported as the check result, never as success.
        """
        jsonl_store = mem.ingestion._jsonl
        try:
            self._backup_memories_as_jsonl(mem)
            if summary.sqlite_only > 0 and "allow_loss" not in job.grants:
                return self._refused_run(
                    job, summary, _loss_message(summary.sqlite_only), loss_blocked=True
                )
            import_result = import_from_jsonl(
                jsonl_store,
                dry_run=False,
                backup=True,
                allow_loss="allow_loss" in job.grants,
                db_config=self._ctx.cfg.db,
                stop=job.stop_event,
            )
            verified = self.check_consistency(mem)
            outcome = replace(
                summary,
                inserted=import_result.inserted,
                sqlite_after=mem.store.check_consistency().memories,
                verified=verified,
            )
        except Exception as exc:  # noqa: BLE001 — the run's outcome is recorded, not raised
            return self._refused_run(
                job, summary, f"Rebuild aborted: backup failed: {exc}", error=str(exc)
            )
        # The outcome is reported on the job record before any success line (REQ-004).
        self._finish_and_report(job, "", verified=verified)
        if not verified:
            # The check already stated its result, including the repair commands; the run is
            # reported as unverified, so nothing here may read as success.
            return outcome
        self._out.write_success(
            f"Imported {import_result.inserted} entries from {summary.jsonl_count} "
            "JSONL archive records."
        )
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(
                ok=True,
                memory_id="",
                action="rebuild",
                dry_run=False,
                count=summary.jsonl_count,
            ),
        )
        return outcome

    def _run_index(self, job: MaintenanceJob, idx: str) -> None:
        """Run the granted index rebuild and record its outcome on the job (REQ-006)."""
        try:
            result = _reindex(idx, db_config=self._ctx.cfg.db, stop=job.stop_event)
        except Exception as exc:  # noqa: BLE001 — the run's outcome is recorded, not raised
            self._finish_and_report(
                job, f"index rebuild failed: {exc}", state=JobState.FAILED
            )
            return
        if result.interrupted:
            # The transaction rolled back, so the run measured nothing and cannot read as success.
            self._finish_and_report(job, "index rebuild interrupted")
            return
        self._out.write_success(f"memories_{idx} rebuilt: {result.count} rows [Memory]")
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(
                ok=True, memory_id="", action=f"reindex-{idx}", count=result.count
            ),
        )
        self._finish_and_report(job, "", verified=result.verified)

    def _refused_run(
        self,
        job: MaintenanceJob,
        summary: RebuildResult,
        message: str,
        *,
        error: str | None = None,
        loss_blocked: bool = False,
    ) -> RebuildResult:
        """State a run that stopped before any write, and end it as failed on the record."""
        self._out.write(f"  [memory] {message}")
        self._finish_and_report(job, message, state=JobState.FAILED)
        return replace(summary, error=error, loss_blocked=loss_blocked)

    def _finish_and_report(
        self,
        job: MaintenanceJob,
        outcome: str,
        *,
        verified: bool = False,
        state: JobState = JobState.COMPLETED,
    ) -> None:
        """Record the terminal outcome, then report the run by its job id and state (REQ-004)."""
        if state is JobState.COMPLETED and job.stop_event.is_set():
            state = JobState.CANCELLED
        self._registry().finish(job, outcome=outcome, verified=verified, state=state)
        self._out.write(f"  job {job.job_id} {job.state}")

    def _report_refusal(self, job: MaintenanceJob, decision: ApprovalDecision) -> None:
        """State the refusal with the job id the registry decided for."""
        self._out.write_error(f"job {job.job_id}: {decision.detail}")

    def _report_unapproved_run(
        self, job: MaintenanceJob, summary: RebuildResult
    ) -> None:
        """Report the run that changed nothing, as the command has always reported it."""
        self._out.write("  [dry-run] No changes made. Add --confirm to proceed.")
        _emit_memory_audit(
            self._ctx,
            MemoryOpResult(
                ok=True,
                memory_id="",
                action="rebuild",
                dry_run=True,
                count=summary.jsonl_count,
            ),
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

    def check_consistency(self, mem: MemoryServices) -> bool:
        """Check consistency between SQLite, JSONL, FTS5, and vec row counts.

        Returns whether the state the check measured is consistent. The caller reports that
        as the run's postcondition, so a run that did not verify is not reported as success
        (REQ-004).
        """
        from agent.memory.exceptions import MemoryConsistencyError

        try:
            report = mem.store.check_consistency()
        except MemoryConsistencyError as e:
            self._out.write(f"  [memory] check-consistency error: {e}")
            return False
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
                self._out.write("    Repair: /memory reindex --fts")
            if embed_enabled and vec_gap > 0:
                self._out.write(
                    "    Repair: /memory reindex --vec (requires embedding regeneration)"
                )
        _emit_memory_audit(
            self._ctx, MemoryOpResult(ok=ok, memory_id="", action="check-consistency")
        )
        return ok


def _loss_message(count: int) -> str:
    """State the loss a run would cause, naming the grant that would have allowed it."""
    target = "memory" if count == 1 else "memories"
    return (
        f"Rebuild refused: {count} SQLite-only {target} would be lost. "
        "Re-run with --allow-loss to proceed."
    )
