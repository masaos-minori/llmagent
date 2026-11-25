#!/usr/bin/env python3
"""scripts/agent/resource_shutdown_coordinator.py

ResourceShutdownCoordinator — the single owner of the bounded shutdown sequence.

Responsibilities:
  - Run the eight named shutdown steps in one order, each bounded by the budget
  - Settle the tracked writers before the final checkpoint (OD-01)
  - Record one ShutdownStepRecord per step and report the sequence once

Consumers arm the budget and read the report; no consumer runs a step on its own.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from db.write_gate import get_write_gate

from agent.cli_view import CLIView
from agent.shutdown_budget import (
    SHUTDOWN_STEPS,
    STEP_BACKUP,
    STEP_CHECKPOINT,
    STEP_CLOSE_HOOKS,
    STEP_ENTER_SHUTDOWN,
    STEP_PERSIST_SNAPSHOT,
    STEP_REPORT,
    STEP_SETTLE_WRITERS,
    STEP_TERMINATE_LIFECYCLES,
    ShutdownBudget,
    ShutdownOutcome,
    ShutdownReport,
    ShutdownStepRecord,
)
from agent.wal_checkpoint_manager import WalCheckpointManager, wal_step_outcome

if TYPE_CHECKING:
    from db.helper import SQLiteHelper

    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Fallback window used when a coordinator is built without a ShutdownBudget: the
# one bound every blocking step gets. A budget-supplied coordinator never reads it.
_SHUTDOWN_TIMEOUT_S: float = 30.0

# Fallback for AgentConfig.shutdown_settle_seconds when the config is not a number.
_SETTLE_TIMEOUT_S: float = 10.0

# Share of the settle window spent joining the cancelled tasks; the rest is left to
# the SQLite interrupt to unwind the statement a cancelled task was blocked on.
_SETTLE_JOIN_FRACTION: Final = 0.8

# A step record detail is a reason category plus a bounded summary (REQ-013).
_MAX_DETAIL_CHARS: Final = 200

# Extra time the coordinator gives an offloaded WAL worker past the deadline it was given,
# so the worker's own "I stopped at the deadline" report arrives before the outer bound
# fires (REQ-008). The bound stays the last resort for a worker that ignores its deadline,
# and the grace is charged to the budget: the next step's window shrinks by it.
_WORKER_REPORT_GRACE_S: Final = 2.0


def _reason(label: str, exc: BaseException | None = None) -> str:
    """Return one reason category, naming the exception class but not its text.

    Exception text and absolute paths stay in the logger; the record carries only
    what is safe to print (REQ-013).
    """
    if exc is None:
        return label
    return f"{label}: {type(exc).__name__}"


def _detail(reasons: Iterable[str]) -> str:
    """Join reason categories into one bounded detail string (REQ-012)."""
    text = "; ".join(reasons)
    if len(text) <= _MAX_DETAIL_CHARS:
        return text
    return text[: _MAX_DETAIL_CHARS - 3] + "..."


@dataclass
class _StepResult:
    """What one step body reported to the sequence."""

    outcome: ShutdownOutcome
    detail: str = ""
    unsettled_writers: tuple[str, ...] = ()


@dataclass
class _SequenceState:
    """What the sequence knows about itself between steps."""

    budget: ShutdownBudget
    records: list[ShutdownStepRecord] = field(default_factory=list)
    unsettled_writers: tuple[str, ...] = ()
    checkpoint_truncated: bool = False


class ResourceShutdownCoordinator:
    """Coordinates resource shutdown as one bounded, reported step sequence.

    One owner, one deadline, one record per step (REQ-001, REQ-012). The order is
    fixed by SHUTDOWN_STEPS: enter_shutdown, settle_writers, persist_snapshot,
    checkpoint, backup, terminate_lifecycles, close_hooks, report.

    Settle-before-checkpoint ordering (OD-01, supersedes REQ-RSC001B-1): the write
    gate closes, in-flight writers are interrupted and joined within the settle
    window, and only then does the final checkpoint run. A writer that is still
    running when the settle window ends is recorded outcome_unknown, and the
    checkpoint is then recorded not_started rather than racing it (OD-02). The
    backup step still runs on that branch, so checkpoint-before-backup
    (docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md) is preserved.

    Among the settled tasks there is no defined order: the registry is an
    unordered set, so cancellation order is arbitrary. No artificial settlement
    delay is applied; every joined task is awaited before the next step starts.
    """

    def __init__(
        self,
        ctx: AgentContext,
        view: CLIView,
        wal: WalCheckpointManager,
        *,
        budget: ShutdownBudget | None = None,
    ) -> None:
        """Initialize with AgentContext, CLIView, and WalCheckpointManager references.

        budget is optional: a coordinator built without one bounds every step by
        _SHUTDOWN_TIMEOUT_S, which is the behavior before the budget existed.
        """
        self._ctx = ctx
        self._view = view
        self._wal = wal
        self._budget = budget
        self._close_hooks: list[tuple[str, Callable[[], None]]] = []
        self._snapshot_step: Callable[[float], Awaitable[None]] | None = None
        self._tracked_writers: list[tuple[str, SQLiteHelper]] = []
        self._report = ShutdownReport()

    @property
    def report(self) -> ShutdownReport:
        """Return the report of the sequence that ran, empty before it ran."""
        return self._report

    def register_close_hook(self, name: str, hook: Callable[[], None]) -> None:
        """Register a synchronous zero-argument close hook to run last in close_resources.

        Hooks are component-agnostic owners of a resource to release on shutdown
        (e.g. the orchestrator's workflow StateStore). They run after background-task
        cancellation and service lifecycle shutdown, so turn-processing resources
        settle before the store closes.
        """
        self._close_hooks.append((name, hook))

    def register_snapshot_step(self, step: Callable[[float], Awaitable[None]]) -> None:
        """Register the persist_snapshot step body (REQ-007).

        The step is owned by the coordinator because only the coordinator can give
        it a deadline and a record. The body captures one snapshot and passes it to
        every persist call; the coordinator runs it gate-authorized and bounded, and
        hands the body the window so the reads inside it can stop early instead of
        being cut off mid-write.
        """
        self._snapshot_step = step

    def register_tracked_writer(self, name: str, db: SQLiteHelper) -> None:
        """Register a long-lived write connection the settle step interrupts (REQ-005).

        The settle step can only interrupt a connection it can reach: background
        tasks are cancelled through the turn registry, a store's open connection is
        interrupted through SQLiteHelper.interrupt_when. A store that is not
        registered here is invisible to settling, which is why registration is the
        consumer's responsibility.
        """
        self._tracked_writers.append((name, db))

    async def close_resources(self) -> ShutdownReport:
        """Run the shutdown sequence once and return its report.

        Called in the run() finally block. A second call returns the report of the
        sequence that already ran rather than running the steps twice.
        """
        if self._report.records:
            return self._report

        budget = self._budget or ShutdownBudget(_SHUTDOWN_TIMEOUT_S)
        self._view.write_history()
        state = _SequenceState(budget=budget)
        handlers = {
            STEP_ENTER_SHUTDOWN: self._step_enter_shutdown,
            STEP_SETTLE_WRITERS: self._step_settle_writers,
            STEP_PERSIST_SNAPSHOT: self._step_persist_snapshot,
            STEP_CHECKPOINT: self._step_checkpoint,
            STEP_BACKUP: self._step_backup,
            STEP_TERMINATE_LIFECYCLES: self._step_terminate_lifecycles,
            STEP_CLOSE_HOOKS: self._step_close_hooks,
            STEP_REPORT: self._step_report,
        }

        for name in SHUTDOWN_STEPS:
            window = budget.remaining()
            # The report step always runs: a sequence that ran out of time must
            # still say so (REQ-012).
            if window <= 0.0 and name != STEP_REPORT:
                self._record(
                    state, name, ShutdownOutcome.NOT_STARTED, 0.0, "deadline exhausted"
                )
                continue
            started = time.monotonic()
            result = await handlers[name](state, window)
            self._record(
                state,
                name,
                result.outcome,
                time.monotonic() - started,
                result.detail,
            )
            state.unsettled_writers += result.unsettled_writers

        self._report = ShutdownReport(
            records=tuple(state.records),
            refused_write_count=get_write_gate().refused_count,
            unsettled_writers=state.unsettled_writers,
        )
        return self._report

    def _record(
        self,
        state: _SequenceState,
        name: str,
        outcome: ShutdownOutcome,
        elapsed_s: float,
        detail: str,
    ) -> None:
        """Append one step record and log it when it is not a clean completion."""
        state.records.append(
            ShutdownStepRecord(
                name=name,
                outcome=outcome,
                elapsed_s=round(elapsed_s, 3),
                detail=detail,
            )
        )
        if outcome is not ShutdownOutcome.COMPLETED:
            logger.warning(
                "shutdown step %s: %s (%s)", name, outcome.value, detail or "no detail"
            )

    def _settle_seconds(self) -> float:
        """Return the configured writer-settle window, or the module fallback."""
        value = getattr(
            getattr(self._ctx, "cfg", None), "shutdown_settle_seconds", None
        )
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
        ):
            return float(value)
        return _SETTLE_TIMEOUT_S

    def _interrupt_stop(self) -> threading.Event | None:
        """Return the budget's interrupt event for a worker thread, or None without a budget.

        The WAL steps run on a worker thread, and the db layer's progress handler takes a
        ``threading.Event``, so the budget's own event is what a second SIGINT can set to
        stop a checkpoint or backup already in flight (REQ-008).
        """
        return self._budget.interrupt_event if self._budget is not None else None

    async def _step_enter_shutdown(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Arm the budget and move the write gate to closing (REQ-001, REQ-004)."""
        first = state.budget.arm()
        gate = get_write_gate()
        gate.close()
        logger.info(
            "shutdown sequence began: first_request=%s deadline_remaining=%.3fs gate=%s",
            first,
            window,
            gate.state.value,
        )
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_settle_writers(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Interrupt and join the in-flight writers, then close the gate (REQ-005).

        The registry is a ``set`` of ``asyncio.Task`` objects with no creation
        order, so cancellation order is arbitrary; ``reversed()`` over the snapshot
        is an arbitrary-order reversal, not LIFO. A clean cancellation is not an
        error (``CancelledError`` is not an ``Exception``).

        ``asyncio.wait`` is used instead of ``wait_for(gather(...))`` on purpose:
        ``wait_for`` cancels everything it is waiting on when it times out, which
        would make an unfinished writer look settled. ``asyncio.wait`` leaves the
        pending tasks running, so the step can interrupt them and then report them
        as unsettled (OD-02).
        """
        settle_window = min(window, self._settle_seconds())
        join_window = settle_window * _SETTLE_JOIN_FRACTION
        unwind_window = settle_window - join_window

        stop = threading.Event()
        interrupted = self._install_writer_interrupts(stop)
        tasks = list(self._ctx.turn.background_tasks)
        self._ctx.turn.background_tasks.clear()
        for task in reversed(tasks):
            task.cancel()

        reasons: list[str] = []
        unsettled: tuple[str, ...] = ()
        if tasks:
            logger.info(
                "Cancelling %d tracked background tasks during shutdown", len(tasks)
            )
            _, pending = await asyncio.wait(tasks, timeout=join_window)
            if pending:
                stop.set()
                _, pending = await asyncio.wait(pending, timeout=unwind_window)
                logger.warning(
                    "writer settle window of %gs expired: %d task(s) still running",
                    settle_window,
                    len(pending),
                )
            unsettled = tuple(task.get_name() for task in pending)
            for task in tasks:
                if task.cancelled() or task in pending:
                    continue
                exc = task.exception()
                if exc is not None:
                    logger.error(
                        "tracked background task raised during cancellation: %s", exc
                    )
                    reasons.append(_reason("task_cancellation", exc))

        get_write_gate().close()
        self._release_writer_interrupts(interrupted)

        if unsettled:
            return _StepResult(
                ShutdownOutcome.OUTCOME_UNKNOWN,
                _detail([f"unsettled writer(s): {', '.join(unsettled)}", *reasons]),
                unsettled,
            )
        if reasons:
            return _StepResult(ShutdownOutcome.FAILED, _detail(reasons))
        return _StepResult(ShutdownOutcome.COMPLETED)

    def _install_writer_interrupts(self, stop: threading.Event) -> list[str]:
        """Arm interrupt_when on every registered writer; return the armed names."""
        armed: list[str] = []
        for name, db in self._tracked_writers:
            try:
                db.interrupt_when(stop)
            except Exception as e:  # noqa: BLE001 — an uninterruptible writer is reported, not fatal to settling
                logger.error("could not interrupt writer %s: %s", name, e)
            else:
                armed.append(name)
        return armed

    def _release_writer_interrupts(self, armed: Iterable[str]) -> None:
        """Remove the progress handlers armed by settling so a later open is unaffected."""
        by_name = dict(self._tracked_writers)
        for name in armed:
            db = by_name.get(name)
            if db is None:
                continue
            try:
                db.interrupt_when(None)
            except Exception as e:  # noqa: BLE001 — the handler is cleanup; a closed store is not a shutdown failure
                logger.debug("could not clear the writer interrupt on %s: %s", name, e)

    async def _step_persist_snapshot(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Run the registered snapshot-persist step, gate-authorized and bounded (REQ-007)."""
        if self._snapshot_step is None:
            logger.debug("no snapshot step registered; persist_snapshot is not started")
            return _StepResult(
                ShutdownOutcome.NOT_STARTED, "no snapshot step registered"
            )
        try:
            with get_write_gate().authorize(STEP_PERSIST_SNAPSHOT):
                await asyncio.wait_for(self._snapshot_step(window), timeout=window)
        except TimeoutError:
            logger.error(
                "session snapshot persist timed out after %gs on shutdown", window
            )
            return _StepResult(
                ShutdownOutcome.TIMED_OUT,
                _detail([f"persist_snapshot_timeout: bound of {window:g}s expired"]),
            )
        except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any persist failure, not propagate
            logger.error("Unexpected error during session snapshot persist: %s", e)
            return _StepResult(
                ShutdownOutcome.FAILED, _reason("persist_snapshot_error", e)
            )
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_checkpoint(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Run the final WAL checkpoint only when no writer is still running (REQ-006)."""
        if state.unsettled_writers:
            return _StepResult(
                ShutdownOutcome.NOT_STARTED,
                _detail([f"unsettled writer(s): {', '.join(state.unsettled_writers)}"]),
            )
        try:
            with get_write_gate().authorize(STEP_CHECKPOINT):
                truncated, errors = await asyncio.wait_for(
                    self._wal.checkpoint_sync(
                        deadline=time.monotonic() + window,
                        stop=self._interrupt_stop(),
                    ),
                    timeout=window + _WORKER_REPORT_GRACE_S,
                )
        except TimeoutError:
            logger.error(
                "WAL checkpoint timed out after %gs on shutdown: the worker did not report stopping",
                window,
            )
            return _StepResult(
                ShutdownOutcome.TIMED_OUT,
                _detail([f"wal_checkpoint_timeout: bound of {window:g}s expired"]),
            )
        except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any checkpoint failure, not propagate
            logger.error("Unexpected error during WAL checkpoint: %s", e)
            return _StepResult(
                ShutdownOutcome.FAILED, _reason("wal_checkpoint_error", e)
            )

        state.checkpoint_truncated = truncated
        if errors:
            for label, text in errors:
                logger.error("WAL checkpoint recorded %s: %s", label, text)
            return _StepResult(
                wal_step_outcome(errors), _detail([label for label, _ in errors])
            )
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_backup(self, state: _SequenceState, window: float) -> _StepResult:
        """Publish the WAL backup when the checkpoint did not truncate the WAL (REQ-009)."""
        if state.checkpoint_truncated:
            return _StepResult(ShutdownOutcome.COMPLETED, "not required: WAL truncated")
        try:
            with get_write_gate().authorize(STEP_BACKUP):
                _backup_path, errors = await asyncio.wait_for(
                    self._wal.backup_sync(
                        deadline=time.monotonic() + window,
                        stop=self._interrupt_stop(),
                    ),
                    timeout=window + _WORKER_REPORT_GRACE_S,
                )
        except TimeoutError:
            logger.error(
                "WAL backup timed out after %gs on shutdown: the worker did not report stopping",
                window,
            )
            return _StepResult(
                ShutdownOutcome.TIMED_OUT,
                _detail([f"wal_backup_timeout: bound of {window:g}s expired"]),
            )
        except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any backup failure, not propagate
            logger.error("Unexpected error during WAL backup: %s", e)
            return _StepResult(ShutdownOutcome.FAILED, _reason("wal_backup_error", e))

        if errors:
            for label, text in errors:
                logger.error("WAL backup recorded %s: %s", label, text)
            return _StepResult(
                wal_step_outcome(errors), _detail([label for label, _ in errors])
            )
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_terminate_lifecycles(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Shut down services and terminate MCP lifecycles with the time that is left.

        The step is not cut off by wait_for: termination must always deliver SIGTERM
        and SIGKILL (OD-05), so only the confirmation waits inside it are clamped,
        which the termination modules do from their own remaining-deadline argument.
        The HTTP client is closed in the same gather as today, keeping INV-07.
        """
        reasons: list[str] = []
        svc = self._ctx.services
        if svc is None:
            logger.debug("No services available to shut down")
            return _StepResult(ShutdownOutcome.COMPLETED)

        svc_results = await asyncio.gather(
            svc.lifecycle.shutdown_all(), svc.http.aclose(), return_exceptions=True
        )
        for i, res in enumerate(svc_results):
            if isinstance(res, Exception):
                err_name = "lifecycle_shutdown" if i == 0 else "http_close"
                logger.error("%s failed: %s", err_name, res)
                reasons.append(_reason(err_name, res))
            elif i == 0 and isinstance(res, list):
                for server_key, outcome in res:
                    logger.error(
                        "MCP server %r not confirmed stopped (%s)", server_key, outcome
                    )
                    reasons.append(f"http_termination: {server_key} ({outcome})")

        # Plain-REPL session intent store (factory-wired, mcpdl001 REQ-007):
        # closed with the other services, after turn processing settled.
        if svc.session_intent_close is not None:
            try:
                svc.session_intent_close()
            except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any store-close failure, not propagate
                logger.error("session intent store close failed: %s", e)
                reasons.append(_reason("intent_store_close", e))

        if reasons:
            return _StepResult(ShutdownOutcome.FAILED, _detail(reasons))
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_close_hooks(
        self, state: _SequenceState, window: float
    ) -> _StepResult:
        """Run the registered close hooks last, after every turn-processing step."""
        reasons: list[str] = []
        for name, hook in self._close_hooks:
            try:
                hook()
            except Exception as e:  # noqa: BLE001 — shutdown path must record and continue past any hook failure, not propagate
                logger.error("close_hook %r failed: %s", name, e)
                reasons.append(f"close_hook: {name} ({type(e).__name__})")
        if reasons:
            return _StepResult(ShutdownOutcome.FAILED, _detail(reasons))
        return _StepResult(ShutdownOutcome.COMPLETED)

    async def _step_report(self, state: _SequenceState, window: float) -> _StepResult:
        """Print one line per step that did not complete, plus the summary line (REQ-012)."""
        issues = [
            r for r in state.records if r.outcome is not ShutdownOutcome.COMPLETED
        ]
        for record in issues:
            self._view.write_warning(
                f"Shutdown {record.name}: {record.outcome.value}"
                + (f" ({record.detail})" if record.detail else "")
            )
        if issues:
            summary = "; ".join(f"{r.name}: {r.outcome.value}" for r in issues)
            unsettled = state.unsettled_writers
            if unsettled:
                summary += f"; unsettled_writers: {', '.join(unsettled)}"
            refused = get_write_gate().refused_count
            if refused:
                summary += f"; refused_writes: {refused}"
            logger.error("Resource close errors (%d): %s", len(issues), summary)
            self._view.write_warning(f"Shutdown completed with errors: {summary}")
        state.budget.mark_closed()
        return _StepResult(ShutdownOutcome.COMPLETED)
