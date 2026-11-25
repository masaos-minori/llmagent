"""tests/agent/test_resource_shutdown_coordinator.py

Regression tests for ResourceShutdownCoordinator.close_resources() as the single
owner of the bounded shutdown sequence: the settle-before-checkpoint order
(REQ-001, REQ-006, OD-01), one ShutdownStepRecord per step with an outcome from
the shared vocabulary (REQ-012), the not_started rule for a step the deadline or
an unsettled writer blocks (REQ-006, OD-02), and the writer settling that
interrupts registered connections and joins tracked tasks (REQ-005).
"""

from __future__ import annotations

import asyncio
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import agent.resource_shutdown_coordinator as coordinator_module
import pytest
from agent.context import TurnState
from agent.conversation_state_manager import ConversationStateManager
from agent.http_lifecycle_errors import TerminationOutcome
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator
from agent.shutdown_budget import (
    SHUTDOWN_STEPS,
    STEP_BACKUP,
    STEP_CHECKPOINT,
    STEP_CLOSE_HOOKS,
    STEP_PERSIST_SNAPSHOT,
    STEP_SETTLE_WRITERS,
    STEP_TERMINATE_LIFECYCLES,
    ShutdownBudget,
    ShutdownOutcome,
    ShutdownReport,
)
from agent.wal_checkpoint_manager import WalCheckpointManager
from db.helper import SQLiteHelper as RealHelper
from db.models import WalCheckpointCounts
from db.write_gate import WriteGateState, get_write_gate


def _make_coordinator(
    budget: ShutdownBudget | None = None,
) -> ResourceShutdownCoordinator:
    ctx = MagicMock()
    ctx.services = None
    view = MagicMock()
    wal = MagicMock()
    wal.checkpoint_sync = AsyncMock(return_value=(True, []))
    wal.backup_sync = AsyncMock(return_value=("", []))
    coordinator = ResourceShutdownCoordinator(ctx, view, wal, budget=budget)
    # A healthy production shutdown always carries a persist step; registering a
    # no-op body keeps these cases about the step they name.
    coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
    return coordinator


def _record(report: ShutdownReport, name: str) -> Any:
    """Return the one record the sequence produced for ``name``."""
    matches = [r for r in report.records if r.name == name]
    assert len(matches) == 1, f"{name} produced {len(matches)} records"
    return matches[0]


def _warnings(view: MagicMock) -> list[str]:
    """Every console warning line the sequence printed, in order."""
    return [c.args[0] for c in view.write_warning.call_args_list]


async def _long_running_first_turn(_line: str) -> str:
    """A stand-in for ``_generate_session_title``: pending long enough to be cancelled."""
    await asyncio.sleep(30)
    return "stubbed-title"


async def _register_first_turn_task(ctx: MagicMock) -> set[asyncio.Task[object]]:
    """Register one real first-turn task through the real producer."""
    manager = ConversationStateManager(
        ctx,
        tasks=ctx.turn.background_tasks,
        on_discard=lambda _task: None,
        on_first_turn=_long_running_first_turn,
    )
    await manager.append_user_message("first")
    return ctx.turn.background_tasks


def _registry_ctx() -> MagicMock:
    """A MagicMock ctx with a real TurnState registry and the minimal conv/stats/session
    stubs that ``append_user_message`` touches."""
    ctx = MagicMock()
    ctx.services = None
    ctx.conv = MagicMock()
    ctx.conv.system_prompt_content = ""  # skip sync_system_prompt's validation branch
    ctx.conv.append_message = AsyncMock()
    ctx.stats = MagicMock()
    ctx.stats.stat_turns = 0  # append increments to 1, firing the first-turn branch
    ctx.session = MagicMock()
    ctx.turn = TurnState()  # real, empty background_tasks set
    # append_user_message() persists through the turn's atomic boundary (SEQ-06);
    # give this non-turn test an awaitable stand-in handle.
    ctx.turn.persistence_boundary = AsyncMock()
    return ctx


class TestStepSequenceContract:
    """REQ-001, REQ-012: one ordered sequence, one record per step, one vocabulary."""

    @pytest.mark.asyncio
    async def test_every_step_is_recorded_once_in_the_declared_order(self) -> None:
        coordinator = _make_coordinator()

        report = await coordinator.close_resources()

        assert [r.name for r in report.records] == list(SHUTDOWN_STEPS)
        assert all(r.outcome in set(ShutdownOutcome) for r in report.records), (
            "every outcome comes from the shared vocabulary"
        )
        assert all(r.elapsed_s >= 0.0 for r in report.records)

    @pytest.mark.asyncio
    async def test_healthy_shutdown_records_only_completed_steps(self) -> None:
        coordinator = _make_coordinator()

        report = await coordinator.close_resources()

        assert [r.outcome for r in report.records] == [ShutdownOutcome.COMPLETED] * len(
            SHUTDOWN_STEPS
        )
        coordinator._view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_healthy_shutdown_completes_promptly(self) -> None:
        """A healthy shutdown (no pending tasks, checkpoint/backup succeed
        immediately) completes well under the shutdown bound.

        Exercises stubbed ``checkpoint_sync``/``backup_sync`` (AsyncMock): it documents the
        ordering contract, not the real blocking step (see TestRealContendedStepIsBounded).
        """
        coordinator = _make_coordinator()
        start = time.monotonic()
        await coordinator.close_resources()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_no_shutdown_error_entries_after_settlement_block_removal(
        self,
    ) -> None:
        """No shutdown_timeout/shutdown_error entries are recorded — the
        settlement block that used to produce them no longer exists.

        Exercises stubbed ``checkpoint_sync``/``backup_sync`` (AsyncMock): it documents the
        error-collection contract, not the real blocking step.
        """
        coordinator = _make_coordinator()
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("shutdown_timeout" in msg for msg in error_messages)
        assert not any("shutdown_error" in msg for msg in error_messages)

    @pytest.mark.asyncio
    async def test_close_resources_runs_the_sequence_once(self) -> None:
        """A second call returns the report of the sequence that already ran."""
        coordinator = _make_coordinator()

        first = await coordinator.close_resources()
        second = await coordinator.close_resources()

        assert second is first
        coordinator._wal.checkpoint_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deadline_exhausted_records_not_started_and_still_reports(
        self,
    ) -> None:
        """REQ-012: a step the deadline cannot cover is a record, not a silent skip."""
        coordinator = _make_coordinator(budget=ShutdownBudget(0.0))

        report = await coordinator.close_resources()

        assert [r.outcome for r in report.records] == [ShutdownOutcome.NOT_STARTED] * (
            len(SHUTDOWN_STEPS) - 1
        ) + [ShutdownOutcome.COMPLETED]
        coordinator._wal.checkpoint_sync.assert_not_awaited()
        summary = _warnings(coordinator._view)[-1]
        assert "Shutdown completed with errors" in summary
        assert "checkpoint: not_started" in summary

    @pytest.mark.asyncio
    async def test_budget_phase_is_closed_by_the_report_step(self) -> None:
        """REQ-003: the sequence, not a consumer, moves the phase to closed."""
        budget = ShutdownBudget(45.0)
        coordinator = _make_coordinator(budget=budget)

        await coordinator.close_resources()

        assert budget.armed is True
        assert budget.phase.value == "closed"

    @pytest.mark.asyncio
    async def test_write_gate_is_closed_by_the_sequence(self) -> None:
        """REQ-004, REQ-005: the gate is stepping closed before settling and closed after."""
        gate = get_write_gate()
        gate.reset()
        coordinator = _make_coordinator()

        await coordinator.close_resources()

        assert gate.state is WriteGateState.CLOSED


class TestSettleBeforeCheckpoint:
    """REQ-001, REQ-005, REQ-006, OD-01: writers settle first; the checkpoint follows."""

    @pytest.mark.asyncio
    async def test_tracked_task_is_cancelled_before_the_checkpoint_starts(self) -> None:
        """OD-01 supersedes REQ-RSC001B-1: the cancel happens while the checkpoint waits."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        order: list[str] = []

        async def _checkpoint(
            *, deadline: float | None = None, stop: threading.Event | None = None
        ) -> tuple[bool, list[tuple[str, str]]]:
            order.append("checkpoint_start")
            await asyncio.sleep(0.05)
            order.append("checkpoint_done")
            return True, []

        wal.checkpoint_sync = AsyncMock(side_effect=_checkpoint)
        wal.backup_sync = AsyncMock(return_value=("", []))

        tasks = await _register_first_turn_task(ctx)
        (running,) = tuple(tasks)

        async def _cancel_probe() -> None:
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                order.append("cancel")
                raise

        probe = asyncio.get_running_loop().create_task(_cancel_probe())
        ctx.turn.background_tasks.add(probe)
        await asyncio.sleep(0)  # let the probe reach its await point before cancelling

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
        report = await coordinator.close_resources()

        assert order == ["cancel", "checkpoint_start", "checkpoint_done"], order
        assert running.cancelled() is True
        assert _record(report, STEP_SETTLE_WRITERS).outcome is ShutdownOutcome.COMPLETED
        assert _record(report, STEP_CHECKPOINT).outcome is ShutdownOutcome.COMPLETED

    @pytest.mark.asyncio
    async def test_uninterruptible_writer_records_outcome_unknown_and_checkpoint_not_started(
        self,
    ) -> None:
        """OD-02: an unsettled writer makes the checkpoint a decision, not a race."""
        ctx = _registry_ctx()
        ctx.cfg.shutdown_settle_seconds = 0.2
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        async def _unkillable_writer() -> None:
            loop = asyncio.get_running_loop()
            try:
                await loop.create_future()
            except asyncio.CancelledError:
                # A writer that ignores the cancel and keeps running: settling must
                # report it rather than assume it stopped.
                await loop.create_future()

        writer = asyncio.get_running_loop().create_task(
            _unkillable_writer(), name="history-writer"
        )
        ctx.turn.background_tasks.add(writer)
        await asyncio.sleep(0)  # the writer must be running before settling cancels it

        coordinator = ResourceShutdownCoordinator(
            ctx, view, wal, budget=ShutdownBudget(0.4)
        )
        try:
            report = await coordinator.close_resources()
        finally:
            writer.cancel()
            await asyncio.gather(writer, return_exceptions=True)

        settle = _record(report, STEP_SETTLE_WRITERS)
        assert settle.outcome is ShutdownOutcome.OUTCOME_UNKNOWN
        assert "history-writer" in settle.detail
        assert report.unsettled_writers == ("history-writer",)
        checkpoint = _record(report, STEP_CHECKPOINT)
        assert checkpoint.outcome is ShutdownOutcome.NOT_STARTED
        wal.checkpoint_sync.assert_not_awaited()
        # The backup branch still runs for a checkpoint that did not truncate.
        wal.backup_sync.assert_awaited_once()
        assert _record(report, STEP_BACKUP).outcome is ShutdownOutcome.COMPLETED

    @pytest.mark.asyncio
    async def test_registered_writer_connection_is_interrupted_and_released(
        self,
    ) -> None:
        """REQ-005: settling arms interrupt_when on a registered writer and clears it."""
        coordinator = _make_coordinator()
        writer = MagicMock(spec=RealHelper)
        coordinator.register_tracked_writer("workflow_store", writer)

        await coordinator.close_resources()

        calls = writer.interrupt_when.call_args_list
        assert len(calls) == 2, "armed once during settling, cleared after it"
        armed = calls[0].args[0]
        assert isinstance(armed, threading.Event)
        assert armed.is_set() is False, "a clean settle has nothing left to interrupt"
        assert calls[1].args[0] is None, (
            "the progress handler must not outlive the step"
        )

    @pytest.mark.asyncio
    async def test_uninterruptible_registered_writer_is_recorded_not_fatal(
        self,
    ) -> None:
        """A writer whose interrupt cannot be installed is reported; the sequence continues."""
        coordinator = _make_coordinator()
        writer = MagicMock(spec=RealHelper)
        writer.interrupt_when.side_effect = sqlite3.ProgrammingError("cross-thread")
        coordinator.register_tracked_writer("workflow_store", writer)

        report = await coordinator.close_resources()

        assert _record(report, STEP_CHECKPOINT).outcome is ShutdownOutcome.COMPLETED
        coordinator._wal.checkpoint_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_settle_window_is_bounded_by_the_configured_seconds(self) -> None:
        """REQ-005: the settle step waits at most shutdown_settle_seconds, not the deadline."""
        ctx = _registry_ctx()
        ctx.cfg.shutdown_settle_seconds = 0.2
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))
        coordinator = ResourceShutdownCoordinator(
            ctx, view, wal, budget=ShutdownBudget(30.0)
        )
        writer = MagicMock(spec=RealHelper)
        coordinator.register_tracked_writer("history_store", writer)

        async def _unkillable_writer() -> None:
            loop = asyncio.get_running_loop()
            try:
                await loop.create_future()
            except asyncio.CancelledError:
                await loop.create_future()

        task = asyncio.get_running_loop().create_task(
            _unkillable_writer(), name="slow-writer"
        )
        ctx.turn.background_tasks.add(task)
        await asyncio.sleep(0)  # the writer must be running before settling cancels it

        start = time.monotonic()
        report = await coordinator.close_resources()
        elapsed = time.monotonic() - start

        assert elapsed < 1.0, f"settling ignored the configured window: {elapsed:.2f}s"
        settle = _record(report, STEP_SETTLE_WRITERS)
        assert settle.outcome is ShutdownOutcome.OUTCOME_UNKNOWN
        assert "slow-writer" in settle.detail
        armed = writer.interrupt_when.call_args_list[0].args[0]
        assert armed.is_set() is True, (
            "the expired window must fire the writer interrupt"
        )
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


class TestHttpTerminationReported:
    """Servers whose exit was not confirmed enter the shutdown report."""

    @staticmethod
    def _coordinator_with_services(
        unconfirmed: list[tuple[str, TerminationOutcome]],
    ) -> ResourceShutdownCoordinator:
        coordinator = _make_coordinator()
        svc = MagicMock()
        svc.lifecycle.shutdown_all = AsyncMock(return_value=unconfirmed)
        svc.http.aclose = AsyncMock()
        coordinator._ctx.services = svc
        return coordinator

    @pytest.mark.asyncio
    async def test_each_unconfirmed_server_is_one_http_termination_entry(self) -> None:
        coordinator = self._coordinator_with_services(
            [
                ("a", TerminationOutcome.EXIT_UNCONFIRMED),
                ("b", TerminationOutcome.SIGNAL_NOT_DELIVERED),
            ]
        )

        report = await coordinator.close_resources()

        record = _record(report, STEP_TERMINATE_LIFECYCLES)
        assert record.outcome is ShutdownOutcome.FAILED
        assert record.detail.count("http_termination") == 2
        assert "a (exit_unconfirmed)" in record.detail
        assert "b (signal_not_delivered)" in record.detail
        # The other steps still ran.
        coordinator._ctx.services.http.aclose.assert_awaited_once()
        coordinator._wal.checkpoint_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clean_shutdown_adds_no_entry(self) -> None:
        coordinator = self._coordinator_with_services([])

        await coordinator.close_resources()

        coordinator._view.write_warning.assert_not_called()


class TestSelectiveTaskCancellation:
    """Real tasks in a real registry: only tracked background tasks are cancelled at shutdown."""

    @pytest.mark.asyncio
    async def test_only_tracked_background_tasks_cancelled(self) -> None:
        """A task registered through the real producer is cancelled, joined, and released."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        tasks = await _register_first_turn_task(ctx)
        assert len(tasks) == 1
        (running,) = tuple(tasks)

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
        await coordinator.close_resources()

        assert running.cancelled() is True
        assert running.done() is True
        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()  # no "Resource close errors" for a clean cancellation

    @pytest.mark.asyncio
    async def test_empty_registry_cancels_nothing_and_raises_nothing(self) -> None:
        """An empty registry leaves shutdown intact (replaces the deleted-guard test)."""
        ctx = _registry_ctx()  # registry intentionally empty
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
        await coordinator.close_resources()  # must not raise

        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_critical_operations_not_cancelled(self) -> None:
        """Untracked work (WAL checkpoint, history write) is not cancelled; the registry empties."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
        await coordinator.close_resources()

        assert (
            ctx.turn.background_tasks == set()
        )  # nothing was registered, nothing remains
        view.write_history.assert_called()  # the history write still ran


class TestRealContendedStepIsBounded:
    """The unstubbed counterpart of the stub-based cases above.

    A real WalCheckpointManager runs against a real WAL database held by a reader, so its
    step body genuinely blocks; the coordinator's own wait_for must abandon it and still
    run the later cleanup steps.
    """

    @pytest.mark.asyncio
    async def test_contended_checkpoint_is_abandoned_and_cleanup_still_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "session.db"
        writer = sqlite3.connect(path, isolation_level=None)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE t (v INTEGER)")
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        reader = sqlite3.connect(path, isolation_level=None)
        reader.execute("BEGIN")
        reader.execute("SELECT count(*) FROM t").fetchone()
        for i in range(20):
            writer.execute("INSERT INTO t VALUES (?)", (i,))
        closed = threading.Event()

        class _Helper(RealHelper):
            def checkpoint(self, mode: str = "TRUNCATE") -> WalCheckpointCounts:
                if mode == "PASSIVE":
                    raise sqlite3.OperationalError("database is locked")
                return super().checkpoint(mode)

            def close(self) -> None:
                super().close()
                closed.set()

        ctx = MagicMock()
        ctx.cfg.approval.allowed_root = str(tmp_path)
        ctx.session.session_id = 1
        ctx.services = None
        background = asyncio.ensure_future(asyncio.sleep(30))
        ctx.turn.background_tasks = {background}
        view = MagicMock()
        monkeypatch.setattr(coordinator_module, "_SHUTDOWN_TIMEOUT_S", 0.3)
        coordinator = ResourceShutdownCoordinator(ctx, view, WalCheckpointManager(ctx))
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))
        try:
            with patch(
                "agent.wal_checkpoint_manager.SQLiteHelper",
                lambda *_a, **_k: _Helper(
                    db_path=str(path), sqlite_busy_timeout_ms=3000
                ),
            ):
                report = await coordinator.close_resources()
        finally:
            reader.close()
            await asyncio.to_thread(closed.wait, 15)
            writer.close()

        # The settle step ran first, so the tracked task is already cancelled.
        assert background.cancelled()
        checkpoint = _record(report, STEP_CHECKPOINT)
        assert checkpoint.outcome is ShutdownOutcome.TIMED_OUT
        assert re.search(r"bound of 0\.\d+s expired", checkpoint.detail), (
            checkpoint.detail
        )
        summary = _warnings(view)[-1]
        assert "checkpoint: timed_out" in summary


class TestCloseHooks:
    """REQ-003: ResourceShutdownCoordinator.register_close_hook registers a terminal close
    hook that runs last, records hook failures without propagating, and is a no-op when empty.
    """

    @staticmethod
    def _coordinator_with_services() -> ResourceShutdownCoordinator:
        coordinator = _make_coordinator()
        svc = MagicMock()
        svc.http.aclose = AsyncMock()
        svc.lifecycle.shutdown_all = AsyncMock(return_value=[])
        coordinator._ctx.services = svc
        return coordinator

    @pytest.mark.asyncio
    async def test_registered_hook_runs_once(self) -> None:
        coordinator = _make_coordinator()
        calls: list[int] = []
        coordinator.register_close_hook("wf", lambda: calls.append(1))
        await coordinator.close_resources()
        assert calls == [1]

    @pytest.mark.asyncio
    async def test_raising_hook_is_recorded_and_later_hook_runs(self) -> None:
        coordinator = _make_coordinator()
        order: list[str] = []

        def raising() -> None:
            order.append("raising")
            raise RuntimeError("store boom")

        def later() -> None:
            order.append("later")

        coordinator.register_close_hook("bad", raising)
        coordinator.register_close_hook("good", later)
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            report = await coordinator.close_resources()

        # The failing hook does not skip the later hook; both run in registration order.
        assert order == ["raising", "later"]
        # The failure is recorded once, labeled "close_hook", and surfaces in the report.
        record = _record(report, STEP_CLOSE_HOOKS)
        assert record.outcome is ShutdownOutcome.FAILED
        assert record.detail.count("close_hook") == 1
        assert "bad (RuntimeError)" in record.detail
        # REQ-013: the exception text stays in the logger, not on the console.
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert any(
            "close_hook" in msg and "store boom" in msg for msg in error_messages
        )
        assert not any("store boom" in line for line in _warnings(coordinator._view))

    @pytest.mark.asyncio
    async def test_hook_runs_after_services_shutdown(self) -> None:
        """The hook body observes that service lifecycle shutdown already ran."""
        coordinator = self._coordinator_with_services()
        order: list[str] = []

        async def _shutdown_all() -> list:
            order.append("services")
            return []

        coordinator._ctx.services.lifecycle.shutdown_all = AsyncMock(
            side_effect=_shutdown_all
        )
        coordinator.register_close_hook("wf", lambda: order.append("hook"))
        await coordinator.close_resources()

        assert order == ["services", "hook"]

    @pytest.mark.asyncio
    async def test_no_hooks_completes_without_error_entries(self) -> None:
        coordinator = _make_coordinator()
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("close_hook" in msg for msg in error_messages)


class TestSessionIntentStoreClose:
    """mcpdl001 REQ-007: the factory-wired plain-REPL intent store is closed
    with the other services; a close failure is recorded, never propagated."""

    @staticmethod
    def _coordinator_with_services() -> ResourceShutdownCoordinator:
        coordinator = _make_coordinator()
        svc = MagicMock()
        svc.http.aclose = AsyncMock()
        svc.lifecycle.shutdown_all = AsyncMock(return_value=[])
        coordinator._ctx.services = svc
        return coordinator

    @pytest.mark.asyncio
    async def test_intent_store_close_runs_when_wired(self) -> None:
        coordinator = self._coordinator_with_services()
        closed: list[bool] = []
        coordinator._ctx.services.session_intent_close = lambda: closed.append(True)
        await coordinator.close_resources()
        assert closed == [True]

    @pytest.mark.asyncio
    async def test_unwired_store_is_a_noop(self) -> None:
        coordinator = self._coordinator_with_services()
        coordinator._ctx.services.session_intent_close = None
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("intent_store_close" in msg for msg in error_messages)

    @pytest.mark.asyncio
    async def test_raising_close_is_recorded_not_propagated(self) -> None:
        coordinator = self._coordinator_with_services()

        def raising() -> None:
            raise RuntimeError("intent store boom")

        coordinator._ctx.services.session_intent_close = raising
        hooks_ran: list[str] = []
        coordinator.register_close_hook("wf", lambda: hooks_ran.append("hook"))
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            report = await coordinator.close_resources()

        # The failure does not abort shutdown: later steps still run.
        assert hooks_ran == ["hook"]
        assert "intent_store_close" in _record(report, STEP_TERMINATE_LIFECYCLES).detail
        # REQ-013: the exception text is logged, not put on the console.
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert any("intent store boom" in msg for msg in error_messages)
        assert not any(
            "intent store boom" in line for line in _warnings(coordinator._view)
        )


class TestPersistSnapshotStep:
    """REQ-007: persistence is one bounded, gate-authorized step, not a finally call."""

    @pytest.mark.asyncio
    async def test_registered_step_runs_gate_authorized(self) -> None:
        coordinator = _make_coordinator()
        seen: list[str | None] = []

        async def _persist(_window: float) -> None:
            seen.append(get_write_gate().authorized_step)

        coordinator.register_snapshot_step(_persist)

        report = await coordinator.close_resources()

        assert seen == [STEP_PERSIST_SNAPSHOT], (
            "the step writes under its own authorization"
        )
        assert (
            _record(report, STEP_PERSIST_SNAPSHOT).outcome is ShutdownOutcome.COMPLETED
        )

    @pytest.mark.asyncio
    async def test_unregistered_step_is_recorded_not_started(self) -> None:
        coordinator = _make_coordinator()
        coordinator._snapshot_step = None

        report = await coordinator.close_resources()

        record = _record(report, STEP_PERSIST_SNAPSHOT)
        assert record.outcome is ShutdownOutcome.NOT_STARTED
        assert "no snapshot step registered" in record.detail

    @pytest.mark.asyncio
    async def test_persist_timeout_records_timed_out_and_later_steps_are_not_started(
        self,
    ) -> None:
        """REQ-007, REQ-006: a persist that eats the deadline leaves the rest unstarted."""
        coordinator = _make_coordinator(budget=ShutdownBudget(0.3))

        async def _slow_persist(_window: float) -> None:
            await asyncio.sleep(5)

        coordinator.register_snapshot_step(_slow_persist)

        report = await coordinator.close_resources()

        record = _record(report, STEP_PERSIST_SNAPSHOT)
        assert record.outcome is ShutdownOutcome.TIMED_OUT
        assert re.search(r"bound of 0\.\d+s expired", record.detail), record.detail
        coordinator._wal.checkpoint_sync.assert_not_awaited()
        assert _record(report, STEP_CHECKPOINT).outcome is ShutdownOutcome.NOT_STARTED

    @pytest.mark.asyncio
    async def test_refused_writes_reach_the_report(self) -> None:
        """REQ-012: the gate's refused-write count is part of the report, not only the log."""
        coordinator = _make_coordinator()

        def _write_after_close() -> None:
            get_write_gate().check_write("late_write")

        coordinator.register_close_hook("late_writer", _write_after_close)

        report = await coordinator.close_resources()

        assert report.refused_write_count >= 1
        record = _record(report, STEP_CLOSE_HOOKS)
        assert record.outcome is ShutdownOutcome.FAILED
        assert "late_writer" in record.detail
        assert "refused_writes: 1" in _warnings(coordinator._view)[-1]


class TestWALStepsShareTheBudget:
    """REQ-008: the checkpoint and backup get the deadline and the interrupt event."""

    @staticmethod
    def _wal(
        checkpoint: tuple[bool, list[tuple[str, str]]] | None = None,
    ) -> MagicMock:
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=checkpoint or (False, []))
        wal.backup_sync = AsyncMock(return_value=("", []))
        return wal

    @pytest.mark.asyncio
    async def test_checkpoint_and_backup_receive_the_deadline_and_event(self) -> None:
        ctx = _registry_ctx()
        budget = ShutdownBudget(total_seconds=30.0)
        wal = self._wal()
        coordinator = ResourceShutdownCoordinator(ctx, MagicMock(), wal, budget=budget)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))

        before = time.monotonic()
        await coordinator.close_resources()

        for awaited in (wal.checkpoint_sync, wal.backup_sync):
            kwargs = awaited.await_args.kwargs
            # The deadline is the instant the step's window ends, not a duration.
            assert before < kwargs["deadline"] <= time.monotonic() + 30.0
            assert kwargs["stop"] is budget.interrupt_event

    @pytest.mark.asyncio
    async def test_worker_deadline_report_is_recorded_as_timed_out(self) -> None:
        """A worker that stopped at its own deadline is timed_out, not a plain failure."""
        ctx = _registry_ctx()
        wal = self._wal(
            (False, [("wal_checkpoint_deadline", "stopped at the deadline")])
        )
        coordinator = ResourceShutdownCoordinator(ctx, MagicMock(), wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))

        report = await coordinator.close_resources()

        record = _record(report, STEP_CHECKPOINT)
        assert record.outcome is ShutdownOutcome.TIMED_OUT
        assert "wal_checkpoint_deadline" in record.detail
        # REQ-006: the backup still runs when the checkpoint did not truncate.
        wal.backup_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_interrupted_checkpoint_is_recorded_as_outcome_unknown(self) -> None:
        """A statement aborted mid-flight leaves a WAL state the step cannot name."""
        ctx = _registry_ctx()
        wal = self._wal((False, [("wal_checkpoint_interrupted", "interrupt request")]))
        coordinator = ResourceShutdownCoordinator(ctx, MagicMock(), wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))

        report = await coordinator.close_resources()

        assert (
            _record(report, STEP_CHECKPOINT).outcome is ShutdownOutcome.OUTCOME_UNKNOWN
        )

    @pytest.mark.asyncio
    async def test_no_budget_still_gives_the_worker_a_deadline(self) -> None:
        """The legacy no-budget path bounds the worker with the module fallback."""
        ctx = _registry_ctx()
        wal = self._wal()
        coordinator = ResourceShutdownCoordinator(ctx, MagicMock(), wal)
        coordinator.register_snapshot_step(lambda _window: asyncio.sleep(0))

        await coordinator.close_resources()

        kwargs = wal.checkpoint_sync.await_args.kwargs
        assert kwargs["deadline"] > time.monotonic()
        assert kwargs["stop"] is None
