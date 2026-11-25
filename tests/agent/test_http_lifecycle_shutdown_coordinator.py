import asyncio
import signal
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.http_lifecycle_errors import TerminationOutcome
from agent.http_lifecycle_shutdown_coordinator import (
    _SHUTDOWN_TIMEOUT_SEC,
    ShutdownCoordinator,
)
from agent.shutdown_budget import ShutdownBudget


class TestShutdownCoordinatorFailureScenarios:
    """Tests for REQ-003, REQ-004: Verify tracking entry handling on shutdown failure."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "outcome",
        [
            TerminationOutcome.EXIT_UNCONFIRMED,
            TerminationOutcome.SIGNAL_NOT_DELIVERED,
        ],
    )
    async def test_unconfirmed_exit_removes_process_entry_but_keeps_other_tracking(
        self, outcome, caplog
    ):
        """The process entry goes before the attempt; the rest survives a failure."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"
        mock_manager = _multi_manager([server_key], AsyncMock(return_value=outcome))

        failures = await coordinator.shutdown_all(mock_manager)

        mock_manager.remove_process_entry.assert_called_once_with(server_key)
        mock_manager.cleanup_server_key.assert_not_called()
        assert failures == [(server_key, outcome)]
        assert "kill -TERM -" in caplog.text
        assert "pgid and stderr-log tracking retained" in caplog.text
        assert "tracking entry" not in caplog.text

    @pytest.mark.asyncio
    async def test_termination_exception_is_reported_as_unconfirmed(self):
        """An OSError out of the terminator is an unconfirmed exit, not a success."""
        coordinator = ShutdownCoordinator()
        mock_manager = _multi_manager(
            ["srv"], AsyncMock(side_effect=OSError("Connection refused"))
        )

        failures = await coordinator.shutdown_all(mock_manager)

        mock_manager.cleanup_server_key.assert_not_called()
        assert failures == [("srv", TerminationOutcome.EXIT_UNCONFIRMED)]

    @pytest.mark.asyncio
    async def test_tracking_entry_removed_on_success(self):
        """REQ-001: Tracking entry is removed after confirmed termination."""
        coordinator = ShutdownCoordinator()
        server_key = "test-server-key"

        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.process_terminator = MagicMock()
        mock_manager.process_terminator.terminate_with_timeout = AsyncMock(
            return_value=TerminationOutcome.EXITED
        )
        mock_manager.cleanup_server_key = MagicMock()
        mock_manager.remove_process_entry = MagicMock()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Process still running
        mock_manager.iter_processes = MagicMock(return_value=[(server_key, mock_proc)])
        mock_manager.clear_all_health_checks = MagicMock()

        # Attempt shutdown
        failures = await coordinator.shutdown_all(mock_manager)

        # Verify cleanup_server_key WAS called and nothing is reported as failed
        mock_manager.cleanup_server_key.assert_called_once_with(server_key)
        assert failures == []


def _multi_manager(keys, terminate):
    """Build a mock manager with one running mock process per key."""
    manager = MagicMock()
    manager.process_terminator = MagicMock()
    manager.process_terminator.terminate_with_timeout = terminate
    manager.cleanup_server_key = MagicMock()
    manager.remove_process_entry = MagicMock()
    procs = []
    for key in keys:
        proc = MagicMock()
        proc.poll.return_value = None  # Process still running
        procs.append((key, proc))
    manager.iter_processes = MagicMock(return_value=procs)
    manager.clear_all_health_checks = MagicMock()
    return manager


class TestShutdownCoordinatorBudget:
    """REQ-010, REQ-011: one armed budget bounds every server, and a SIGINT delivered
    during cleanup reaches that budget instead of being absorbed.

    The budget is the real object, not a mock: what these cases turn on is
    ``remaining()`` being read once for the whole gather and the interrupt being a
    flag the terminator can read.
    """

    @staticmethod
    def _armed_budget(*, elapsed: float, total: float = 45.0) -> ShutdownBudget:
        """Return a budget armed at 100.0 whose remaining() reads total - elapsed."""
        ticks = iter([100.0, 100.0 + elapsed]).__next__
        budget = ShutdownBudget(total_seconds=total, clock=ticks)
        budget.arm()
        return budget

    @pytest.mark.asyncio
    async def test_remaining_deadline_shared_across_servers(self) -> None:
        """REQ-010, AC-1: three servers get the same clamped window from one budget."""
        budget = self._armed_budget(elapsed=30.0)
        windows: list[float] = []
        forwarded: list[ShutdownBudget | None] = []

        async def terminate(proc, key, timeout, budget=None, **kwargs):
            windows.append(timeout)
            forwarded.append(budget)
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b", "c"], terminate)

        await ShutdownCoordinator().shutdown_all(manager, budget=budget)

        # 45 s total, 30 s already spent: the 30 s module window cannot be used up.
        assert windows == [15.0, 15.0, 15.0]
        assert forwarded == [budget, budget, budget]

    @pytest.mark.asyncio
    async def test_no_budget_keeps_the_module_fallback_window(self) -> None:
        """A caller without a budget (a restart, a health check) keeps today's window."""
        windows: list[float] = []
        forwarded: list[ShutdownBudget | None] = []

        async def terminate(proc, key, timeout, budget=None, **kwargs):
            windows.append(timeout)
            forwarded.append(budget)
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b"], terminate)

        await ShutdownCoordinator().shutdown_all(manager)

        assert windows == [_SHUTDOWN_TIMEOUT_SEC, _SHUTDOWN_TIMEOUT_SEC]
        assert forwarded == [None, None]

    @pytest.mark.asyncio
    async def test_spent_deadline_still_signals_every_server(self) -> None:
        """OD-05: a spent deadline shortens the waiting, it does not skip a signal."""
        budget = self._armed_budget(elapsed=45.0)
        windows: list[float] = []

        async def terminate(proc, key, timeout, budget=None, **kwargs):
            windows.append(timeout)
            return TerminationOutcome.EXIT_UNCONFIRMED

        manager = _multi_manager(["a", "b", "c"], terminate)

        failures = await ShutdownCoordinator().shutdown_all(manager, budget=budget)

        assert windows == [0.0, 0.0, 0.0]
        assert [key for key, _ in failures] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_sigint_during_cleanup_requests_the_budget_interrupt(self) -> None:
        """REQ-011, AC-4: a Ctrl-C mid-cleanup is forwarded, and the handler is restored."""
        shutdown_budget = self._armed_budget(elapsed=5.0)
        original_handler = signal.getsignal(signal.SIGINT)
        interrupt_seen: list[bool] = []

        async def terminate(proc, key, timeout, budget=None, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            assert callable(handler)
            handler(signal.SIGINT, None)  # a second Ctrl-C arriving mid-cleanup
            interrupt_seen.append(shutdown_budget.interrupt_requested)
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b"], terminate)

        await ShutdownCoordinator().shutdown_all(manager, budget=shutdown_budget)

        assert interrupt_seen == [True, True]
        assert signal.getsignal(signal.SIGINT) is original_handler

    @pytest.mark.asyncio
    async def test_sigint_is_absorbed_only_when_no_budget_is_supplied(self) -> None:
        """The absorbing guard survives only on the paths that have no interrupt channel."""
        shutdown_budget = self._armed_budget(elapsed=5.0)

        async def terminate(proc, key, timeout, budget=None, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            assert callable(handler)
            handler(signal.SIGINT, None)
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a"], terminate)

        await ShutdownCoordinator().shutdown_all(manager)

        assert shutdown_budget.interrupt_requested is False


class TestShutdownCoordinatorConcurrency:
    """REQ-005: tests for REQ-002, REQ-003, REQ-004 with several servers."""

    @pytest.mark.asyncio
    async def test_total_time_is_bounded_by_one_termination_delay(self):
        """REQ-002: servers terminate together, not one after another."""

        async def terminate(proc, key, **kwargs):
            await asyncio.sleep(0.2)
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b", "c"], terminate)

        start = time.monotonic()
        await ShutdownCoordinator().shutdown_all(manager)
        elapsed = time.monotonic() - start

        assert elapsed < 0.5  # sequential termination would take about 0.6
        assert manager.cleanup_server_key.call_count == 3

    @pytest.mark.asyncio
    async def test_every_server_is_signalled_before_any_wait_finishes(self):
        """REQ-003: all servers receive the termination call before the first ends."""
        events: list[tuple[str, str]] = []

        async def terminate(proc, key, **kwargs):
            events.append(("signalled", key))
            await asyncio.sleep(0.05)
            events.append(("finished", key))
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b", "c"], terminate)

        await ShutdownCoordinator().shutdown_all(manager)

        first_finished = next(i for i, e in enumerate(events) if e[0] == "finished")
        signalled_before = [e for e in events[:first_finished] if e[0] == "signalled"]
        assert len(signalled_before) == 3

    @pytest.mark.asyncio
    async def test_cancellation_during_shutdown_still_leaves_all_signalled(self):
        """REQ-003: an interrupted shutdown has already signalled every server."""
        signalled: list[str] = []

        async def terminate(proc, key, **kwargs):
            signalled.append(key)
            await asyncio.sleep(5)

        manager = _multi_manager(["a", "b", "c"], terminate)

        task = asyncio.create_task(ShutdownCoordinator().shutdown_all(manager))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert sorted(signalled) == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_one_failing_server_keeps_only_its_own_entry(self):
        """REQ-004: a termination failure does not affect the other servers."""

        async def terminate(proc, key, **kwargs):
            if key == "b":
                return TerminationOutcome.EXIT_UNCONFIRMED
            return TerminationOutcome.EXITED

        manager = _multi_manager(["a", "b", "c"], terminate)

        failures = await ShutdownCoordinator().shutdown_all(manager)

        cleaned = sorted(c.args[0] for c in manager.cleanup_server_key.call_args_list)
        assert cleaned == ["a", "c"]
        assert failures == [("b", TerminationOutcome.EXIT_UNCONFIRMED)]
        removed = sorted(c.args[0] for c in manager.remove_process_entry.call_args_list)
        assert removed == ["a", "b", "c"]
