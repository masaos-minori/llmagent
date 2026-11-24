#!/usr/bin/env python3
"""scripts/agent/commands/cmd_session.py

Session management mixin for CommandRegistry.

Provides _SessionMixin with:
  _cmd_session             — /session dispatcher (list/load/rename/delete/export/stats/health/checkpoint/vacuum/purge/recover)
  _generate_session_title  — background task: LLM-generated short title (delegates to SessionTitleService)
  _session_load_safe       — safe session restore by ID
  _session_delete          — session deletion with self-guard
  _load_session            — switch sessions atomically (delegates to SessionTransitionService)
  _cmd_jobs                — /jobs dispatcher (running jobs/status/cancel), reads the job record
"""

import asyncio
import logging
import shutil
import threading
from collections.abc import Awaitable, Callable
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from agent.commands.db_session_ops import DbSessionOps
from agent.commands.exceptions import CommandValidationError, UnknownSubcommandError
from agent.commands.mixin_base import MixinBase
from agent.commands.output_port import OutputPort
from agent.commands.session_title import SessionTitleGen
from agent.commands.utils import parse_command_args, parse_int_arg
from agent.repl_input_controller import (
    InputBusyError,
    InputOutcome,
    InputRequest,
    PromptKind,
    get_input_controller,
)
from agent.services.db_maintenance_service import DbMaintenanceService
from agent.services.export_formatter import render_export, write_export
from agent.services.maintenance_jobs import (
    ApprovalLevel,
    JobConflictError,
    JobState,
    MaintenanceJob,
    StoreTarget,
    profile_for,
)
from agent.services.models import RagFtsRebuildResult, RagVecPruneResult, SessionRow
from agent.services.rag_maintenance_service import RagMaintenanceService

logger = logging.getLogger(__name__)


class _SessionMixin(MixinBase):
    """Session management slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the session mixin via MixinBase constructor and sub-components."""
        super().__init__(*args, **kwargs)
        self._title_gen = SessionTitleGen(self._ctx, self._out)
        self._db_session_ops = DbSessionOps(self._ctx, self._out)

    async def _generate_session_title(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task)."""
        await self._title_gen.generate(first_input)

    def _parse_positive_session_id(self, arg: str) -> int | None:
        """Parse arg as a positive session ID; write a validation error and return None on failure."""
        try:
            sid = int(arg)
            if sid <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self._out.write_validation_error(
                "Invalid session ID: must be a positive integer"
            )
            return None
        return sid

    async def _session_load_safe(self, arg: str) -> None:
        """Parse arg as an integer session ID and load it; print error on invalid."""
        sid = self._parse_positive_session_id(arg)
        if sid is None:
            return
        await self._load_session(sid)

    def _session_delete(self, arg: str) -> None:
        """Parse arg as an integer session ID and delete it; guard current session."""
        sid = self._parse_positive_session_id(arg)
        if sid is None:
            return
        if sid == self._ctx.session.session_id:
            self._out.write_validation_error("Cannot delete the current session.")
            return
        ok = self._ctx.session.delete_session(sid)
        if ok:
            self._out.write_success(f"Session {sid} deleted.")
        else:
            self._out.write_no_data(f"Session {sid} not found.")

    def _session_list(self, limit_arg: str) -> None:
        """List sessions table; limit_arg is the raw CLI positional (digit string or empty)."""
        from agent.commands.session_title import (  # lazy import
            SESSION_TITLE_DISPLAY_MAX_CHARS,
            SESSION_TITLE_TRUNCATE_AT,
        )

        try:
            limit = parse_int_arg(
                limit_arg, usage="/session list [n]", default=20, minimum=1, maximum=200
            )
        except CommandValidationError:
            self._out.write_validation_error("/session list [n]")
            return
        assert limit is not None
        raw_rows = self._ctx.session.list_sessions(limit)
        if not raw_rows:
            self._out.write_no_data("No sessions found")
            return
        session_rows = []
        for r in raw_rows:
            ca = r.get("created_at")
            if ca is not None and not isinstance(ca, str):
                raise TypeError(
                    f"created_at must be str or None, got {type(ca).__name__}"
                )
            session_rows.append(
                SessionRow(
                    session_id=r["session_id"],
                    title=r.get("title"),
                    created_at=ca if ca is not None else "",
                    is_current=bool(r.get("is_current", False)),
                    message_count=int(r.get("message_count", 0)),
                )
            )
        table_rows = []
        for sr in session_rows:
            if self._ctx.session.is_title_pending(sr.session_id):
                title_display = "(generating...)"
            elif sr.title:
                title_display = (
                    sr.title[:SESSION_TITLE_TRUNCATE_AT] + "..."
                    if len(sr.title) > SESSION_TITLE_DISPLAY_MAX_CHARS
                    else sr.title
                )
            else:
                title_display = "(no title)"
            table_rows.append(
                [
                    f"{sr.session_id:>4}{'*' if sr.is_current else ' '}",
                    title_display,
                    sr.created_at,
                    str(sr.message_count),
                ]
            )
        self._out.write_table(["ID  ", "Title", "Created", "Messages"], table_rows)

    def _db_session_stats(self) -> None:
        """Print session/message counts from the Session database."""
        result = DbMaintenanceService(
            self._ctx.cfg.db, self._ctx.cfg.maintenance
        ).stats()
        self._out.write_kv(
            [
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Session"),
            ]
        )

    def _rag_consistency(self) -> None:
        """Print RAG index consistency status (is_consistent + any issues)."""
        result = RagMaintenanceService(self._ctx.cfg.db).consistency()
        self._out.write_kv([("is_consistent", str(result.is_consistent))])
        for issue in result.issues:
            self._out.write(issue)

    def _rag_rebuild_fts(self, stop: threading.Event | None) -> RagFtsRebuildResult:
        """Rebuild the RAG FTS5 index (chunks_fts) from current chunk content.

        The result is returned, not printed: the message is the job record, so a run that
        did not measure its postcondition cannot read as success (REQ-004).
        """
        return RagMaintenanceService(self._ctx.cfg.db).rebuild_fts(stop=stop)

    def _rag_prune_vec(self, stop: threading.Event | None) -> RagVecPruneResult:
        """Remove chunks_vec rows that have no chunks row.

        The embeddings live only in chunks_vec, so the run removes rows and cannot rebuild
        the table. The result is returned for the same reason as the FTS path: a stopped
        run is reported as cancelled, not as success (REQ-004).
        """
        return RagMaintenanceService(self._ctx.cfg.db).prune_orphan_vectors(stop=stop)

    def _session_export(self, args: str) -> None:
        """Export the current conversation history to Markdown or JSON.

        Usage: /session export [markdown|md|json] [filename]
        """
        ctx = self._ctx
        parts = args.strip().split()
        fmt = "md"
        outfile: str | None = None
        for part in parts:
            if part in ("markdown", "md"):
                fmt = "md"
            elif part == "json":
                fmt = "json"
            else:
                outfile = part
        content = render_export(ctx.conv.history, fmt)
        write_export(content, outfile, len(ctx.conv.history))

    def _job_session_target(self) -> str:
        """Return the live session identity the job is attributed to (REQ-001)."""
        target = self._ctx.session.capture_target()
        return f"{target.session_id}:{target.generation}"

    def _free_space_guard(self) -> bool:
        """Guard precondition for VACUUM: free space must cover twice the DB file."""
        db_path = Path(self._ctx.cfg.db.session_db_path)
        try:
            return shutil.disk_usage(db_path.parent).free >= 2 * db_path.stat().st_size
        except OSError:
            return False

    async def _confirm_for_job(self, job: MaintenanceJob, out: OutputPort) -> bool:
        """Ask one approval for a run through the request-bound input controller.

        The approval is bound to this run because the operation id is the job id: a
        confirmation obtained for another run is not accepted (REQ-003).
        """
        request = InputRequest(
            PromptKind.NORMAL,
            f"Approve {job.operation} on {job.store} (job {job.job_id})? [y/N] ",
            operation_id=job.job_id,
            destructive=True,
        )
        try:
            result = await get_input_controller().submit(request)
        except InputBusyError:
            out.write("  [approval] Input is busy; approval refused")
            return False
        if result.outcome is not InputOutcome.COMPLETED:
            return False
        return result.text.strip().lower() in {"y", "yes"}

    def _report_job(self, job: MaintenanceJob, result: object) -> None:
        """Emit the job id and its terminal state, then the values the result measured.

        A stopped run is reported as `cancelled`, never as success (REQ-004).
        """
        self._out.write(f"  job {job.job_id} {job.state}")
        if not is_dataclass(result) or isinstance(result, type):
            return
        pairs = [
            (name, str(value))
            for name, value in asdict(result).items()
            if name not in ("verified", "interrupted")
        ]
        if pairs:
            self._out.write_kv(pairs)

    async def _run_maintenance_job(
        self,
        operation: str,
        store: StoreTarget,
        run: Callable[[threading.Event | None], object],
    ) -> None:
        """Record one maintenance run: register, approve, run, report, in that order.

        A second write job against a store that already has a running writer is
        refused naming the running job id, not queued (REQ-001). The run receives the
        job's cancellation event, so `/jobs cancel <id>` is the only way it stops, and
        an awaiter cancelled before the worker finished ends as `outcome_unknown`
        (REQ-002, REQ-004).
        """
        registry = self._ctx.services_required.job_registry
        profile = profile_for(operation)
        guard = (
            self._free_space_guard
            if profile.approval_level is ApprovalLevel.GUARD
            else None
        )
        try:
            job = registry.register(
                operation=operation,
                store=store,
                session_target=self._job_session_target(),
                precondition=guard,
            )
        except JobConflictError as exc:
            self._out.write_error(f"job refused: {exc}")
            return
        approved = (
            profile.approval_level is ApprovalLevel.NONE
            or await self._confirm_for_job(job, self._out)
        )
        decision = registry.authorize(job, confirmed=approved)
        if not decision.approved:
            self._out.write_error(f"job {job.job_id}: {decision.detail}")
            return
        registry.start(job)
        try:
            outcome = await asyncio.to_thread(run, job.stop_event)
        except asyncio.CancelledError:
            registry.mark_outcome_unknown(job)
            raise
        except Exception as exc:
            registry.finish(
                job, outcome=str(exc), verified=False, state=JobState.FAILED
            )
            raise
        state = (
            JobState.CANCELLED
            if getattr(outcome, "interrupted", False)
            else JobState.COMPLETED
        )
        registry.finish(
            job,
            outcome="",
            verified=bool(getattr(outcome, "verified", False)),
            state=state,
        )
        self._report_job(job, outcome)

    async def _cmd_session(self, args: str) -> None:
        """Handle /session list [n] | load <id> | rename <title> | delete <id>
        | export markdown|md|json [file]
        | stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts|rag-prune-vec.
        """
        parsed = parse_command_args(args.strip().split())
        sub = parsed.subcommand or "list"

        if sub == "list":
            self._session_list(parsed.positional[0] if parsed.positional else "20")
            return

        if sub == "load":
            arg = parsed.positional[0] if parsed.positional else ""
            await self._session_load_safe(arg)
            return

        if sub == "rename":
            title = " ".join(parsed.positional)
            if not title:
                self._out.write_validation_error("/session rename <title>")
                return
            from agent.session import SESSION_TITLE_STORAGE_MAX_CHARS  # lazy import

            persisted = self._ctx.session.set_title(title)
            if not persisted:
                self._out.write_validation_error("/session rename <title>")
                return
            self._out.write_success(
                f"Session renamed: {title[:SESSION_TITLE_STORAGE_MAX_CHARS]!r}"
            )
            return

        if sub == "delete":
            arg = parsed.positional[0] if parsed.positional else ""
            self._session_delete(arg)
            return

        rest = args.strip()[len(sub) :].strip()
        # Each maintenance entry is register -> run -> report through the registry, so a
        # refused duplicate run reports the running job id instead of starting (REQ-001).
        # The offload shape is unchanged: the registry records the run, it does not move
        # where the work happens. The RAG handlers receive the event in Phase 4, so the
        # entries that cannot pass it do not call with it.
        db_dispatch: dict[str, Callable[[], Awaitable[None]]] = {
            "export": lambda: asyncio.to_thread(self._session_export, rest),
            "stats": lambda: self._run_maintenance_job(
                "stats", StoreTarget.SESSION, lambda stop: self._db_session_stats()
            ),
            "health": lambda: self._run_maintenance_job(
                "health",
                StoreTarget.SESSION,
                lambda stop: self._db_session_ops.health(),
            ),
            "checkpoint": lambda: self._run_maintenance_job(
                "checkpoint",
                StoreTarget.SESSION,
                lambda stop: self._db_session_ops.checkpoint(
                    rest.strip().upper() or None, stop=stop
                ),
            ),
            "vacuum": lambda: self._run_maintenance_job(
                "vacuum",
                StoreTarget.SESSION,
                lambda stop: self._db_session_ops.vacuum(stop=stop),
            ),
            "purge": lambda: self._run_maintenance_job(
                "purge",
                StoreTarget.SESSION,
                lambda stop: self._db_session_ops.purge(rest, stop=stop),
            ),
            "recover": lambda: self._run_maintenance_job(
                "recover",
                StoreTarget.SESSION,
                lambda stop: self._db_session_ops.recover(
                    rest.strip() or None, stop=stop
                ),
            ),
            "rag-consistency": lambda: self._run_maintenance_job(
                "consistency", StoreTarget.RAG, lambda stop: self._rag_consistency()
            ),
            "rag-rebuild-fts": lambda: self._run_maintenance_job(
                "rebuild", StoreTarget.RAG, self._rag_rebuild_fts
            ),
            "rag-prune-vec": lambda: self._run_maintenance_job(
                "prune", StoreTarget.RAG, self._rag_prune_vec
            ),
        }
        handler = db_dispatch.get(sub)
        if handler is not None:
            await handler()
            return

        self._out.write_validation_error(
            "/session list [n] | /session load <id>"
            " | /session rename <title> | /session delete <id>"
            " | /session export markdown|md|json [file]"
            " | /session stats|health|checkpoint|vacuum|purge|recover|rag-consistency|rag-rebuild-fts|rag-prune-vec"
        )

    def _job_status_pairs(self, job: MaintenanceJob) -> list[tuple[str, str]]:
        """Render one job record as key-value lines, in the order the record holds it."""
        pairs = [
            ("job", job.job_id),
            ("operation", job.operation),
            ("store", str(job.store)),
            ("approval", str(job.approval_level)),
            ("cancelability", str(job.cancelability)),
            ("state", str(job.state)),
            ("progress", str(job.progress)),
        ]
        if job.started_at is not None:
            pairs.append(("started", str(job.started_at)))
        if job.outcome:
            pairs.append(("outcome", job.outcome))
        return pairs

    def _cmd_jobs(self, args: str) -> None:
        """Handle /jobs (running jobs) | status <id> | cancel <id>.

        Every line is read from the job record; the handler decides nothing itself,
        because approval is a property of the operation decided at registration
        (REQ-003). `cancel` only requests the interruption: the run reaches `cancelled`
        at its next progress callback, and a job declared `not_cancelable` states the
        reason the registry recorded for the refusal (REQ-002).
        """
        parsed = parse_command_args(args.strip().split())
        registry = self._ctx.services_required.job_registry
        sub = parsed.subcommand
        if sub is None:
            running = registry.running_jobs()
            if not running:
                self._out.write_success("no running jobs")
                return
            self._out.write_table(
                ["Job", "Operation", "Store", "State"],
                [
                    [job.job_id, job.operation, str(job.store), str(job.state)]
                    for job in running
                ],
            )
            return

        if sub not in ("status", "cancel"):
            raise UnknownSubcommandError(sub, ("status", "cancel"))

        job_id = parsed.positional[0] if parsed.positional else ""
        if not job_id:
            self._out.write_validation_error(f"/jobs {sub} <id>")
            return

        if sub == "status":
            job = registry.lookup(job_id)
            if job is None:
                self._out.write_error(f"unknown job id: {job_id}")
                return
            self._out.write_kv(self._job_status_pairs(job))
            return

        result = registry.cancel(job_id)
        if result.interrupted:
            self._out.write(f"  job {result.job_id} {result.reason}")
        else:
            self._out.write_error(f"job {result.job_id}: {result.reason}")

    async def _load_session(self, session_id: int) -> None:
        """Switch to a stored session through the atomic transition service."""
        from agent.services.exceptions import (  # lazy import
            SessionNotFoundError,
        )
        from agent.services.session_transition import (  # lazy import
            SessionTransitionRefusedError,
            SessionTransitionService,
        )

        try:
            result = await SessionTransitionService.for_context(self._ctx).load(
                session_id
            )
        except SessionNotFoundError as e:
            self._out.write_no_data(str(e))
        except SessionTransitionRefusedError as e:
            self._out.write_validation_error(str(e))
        else:
            self._out.write_success(
                f"Session {result.session_id} loaded: {result.fetched} fetched, "
                f"{result.synthesized} synthesized, {result.dropped} dropped, "
                f"{result.restored} restored."
            )
