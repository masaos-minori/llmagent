"""tests/agent/test_signal_handler.py

Tests for ``SignalHandler.register()``: the real signal transport on the running loop
and the Windows console-control fallback.

On POSIX CI, CPython's ``ctypes`` exposes neither ``WINFUNCTYPE`` nor ``windll`` --
both are gated on ``os.name == "nt"`` (see ``ctypes/__init__.py``). The complete-failure
contract of the fallback is exercisable by injecting a raising ``WINFUNCTYPE``. The
Windows successful-registration path (``SetConsoleCtrlHandler`` through ctypes) is a
documented path that never executes on this ubuntu-latest CI matrix; it is not kept as a
permanently skipped test. ``test_signal_handler_race.py``, which used to hold the
cross-platform cases, was deleted because it asserted only on state its own tests assigned
to mocks.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import signal
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.repl_input_controller import InterruptAction
from agent.shutdown_budget import ShutdownBudget, ShutdownPhase
from agent.signal_handler import SignalHandler


def _raise_unavailable(*_args, **_kwargs) -> None:
    """Raise to simulate a missing ctypes symbol on POSIX."""
    raise RuntimeError("ctypes.WINFUNCTYPE unavailable on posix")


class TestWindowsCtypesFallback:
    """REQ-001/REQ-002/REQ-003: Windows console-control handler fallback."""

    def test_complete_failure_logs_error(self) -> None:
        """REQ-002: a failed SetConsoleCtrlHandler logs an error, never silently passes."""
        handler = SignalHandler(MagicMock(), None)
        mock_loop = MagicMock()
        with (
            patch.object(
                mock_loop, "add_signal_handler", side_effect=NotImplementedError()
            ),
            patch("sys.frozen", True, create=True),
            patch("agent.signal_handler.logger") as mock_logger,
            patch.dict(ctypes.__dict__, {"WINFUNCTYPE": _raise_unavailable}),
        ):
            handler.register(mock_loop)
        assert mock_logger.error.called


def _dispositions() -> tuple[Any, Any]:
    return signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)


def _remove_handlers(loop: asyncio.AbstractEventLoop, before: tuple[Any, Any]) -> None:
    """Remove the installed handlers and restore the captured dispositions.

    remove_signal_handler() resets a signal to its default, which would drop the
    asyncio Runner's own SIGINT handler that was in place before the test.
    """
    loop.remove_signal_handler(signal.SIGTERM)
    loop.remove_signal_handler(signal.SIGINT)
    signal.signal(signal.SIGTERM, before[0])
    signal.signal(signal.SIGINT, before[1])


class TestRealSignalTransport:
    """SignalHandler.register() on the real running loop.

    Both SIGTERM and SIGINT are installed; a real os.kill(os.getpid(), SIGTERM) is observed
    through a real asyncio.Event; and a handler built without an event still sets
    shutdown_requested. Handlers are removed in each finally and signal.getsignal
    dispositions are asserted identical afterwards.
    """

    @pytest.mark.asyncio
    async def test_register_installs_both_signals(self) -> None:
        handler = SignalHandler(MagicMock(), asyncio.Event())
        loop = asyncio.get_running_loop()
        seen: list[int] = []
        real_add = loop.add_signal_handler

        def capture(sig, callback):
            seen.append(sig)
            return real_add(sig, callback)

        before = _dispositions()
        try:
            with patch.object(loop, "add_signal_handler", side_effect=capture):
                handler.register(loop)
            assert signal.SIGTERM in seen
            assert signal.SIGINT in seen
        finally:
            _remove_handlers(loop, before)
        assert _dispositions() == before

    @pytest.mark.asyncio
    async def test_delivered_sigterm_sets_shutdown_on_real_objects(self) -> None:
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        event = asyncio.Event()
        handler = SignalHandler(ctx, event)
        loop = asyncio.get_running_loop()
        before = _dispositions()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)
            await asyncio.wait_for(event.wait(), timeout=5.0)
        finally:
            _remove_handlers(loop, before)
        assert ctx.conv.shutdown_requested is True
        assert event.is_set()
        assert _dispositions() == before

    @pytest.mark.asyncio
    async def test_none_event_still_sets_shutdown_without_raising(self) -> None:
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        handler = SignalHandler(ctx, None)
        loop = asyncio.get_running_loop()
        before = _dispositions()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)
            for _ in range(50):
                if ctx.conv.shutdown_requested is True:
                    break
                await asyncio.sleep(0.02)
        finally:
            _remove_handlers(loop, before)
        assert ctx.conv.shutdown_requested is True
        assert _dispositions() == before


class _StubController:
    """Records interrupt handling; returns a scripted action."""

    def __init__(self, action: InterruptAction = InterruptAction.DISCARD_INPUT) -> None:
        self.action = action
        self.interrupts = 0
        self.shutdowns = 0

    def handle_interrupt(self) -> InterruptAction:
        self.interrupts += 1
        return self.action

    def shutdown(self) -> None:
        self.shutdowns += 1


def _handler(
    action: InterruptAction = InterruptAction.DISCARD_INPUT,
    *,
    configured_force_exit: bool | None = None,
    **kwargs: Any,
) -> tuple[SignalHandler, _StubController, Any]:
    ctx = MagicMock()
    ctx.conv.shutdown_requested = False
    if configured_force_exit is not None:
        ctx.cfg.shutdown_force_exit_on_second_sigint = configured_force_exit
    stub = _StubController(action)
    return SignalHandler(ctx, asyncio.Event(), controller=stub, **kwargs), stub, ctx  # type: ignore[arg-type] — stub mirrors the two controller methods used


class TestInterruptByState:
    def test_sigint_acts_by_state_and_does_not_start_shutdown(self) -> None:
        for action in (
            InterruptAction.DISCARD_INPUT,
            InterruptAction.CANCEL_TURN,
            InterruptAction.CANCEL_JOB,
        ):
            handler, stub, ctx = _handler(action)
            handler._sigint_handler()
            assert stub.interrupts == 1
            assert ctx.conv.shutdown_requested is False
            assert not handler._shutdown_event.is_set()  # type: ignore[union-attr] — the event is set by _handler

    def test_sigterm_begins_graceful_shutdown_and_marks_the_controller(self) -> None:
        handler, stub, ctx = _handler()
        handler._sigterm_handler()
        assert ctx.conv.shutdown_requested is True
        assert handler._shutdown_event.is_set()  # type: ignore[union-attr] — the event is set by _handler
        assert stub.shutdowns == 1
        assert stub.interrupts == 0

    @pytest.mark.asyncio
    async def test_register_routes_each_signal_to_its_own_handler(self) -> None:
        handler, _stub, _ctx = _handler()
        loop = asyncio.get_running_loop()
        bound: dict[int, Any] = {}
        with patch.object(
            loop, "add_signal_handler", side_effect=lambda s, h: bound.update({s: h})
        ):
            handler.register(loop)
        assert bound[signal.SIGTERM] == handler._sigterm_handler
        assert bound[signal.SIGINT] == handler._sigint_handler


class TestBudgetArmingAndInterrupt:
    """REQ-002, REQ-011: the first shutdown request arms one deadline; a later Ctrl-C
    asks the step in progress to stop instead of killing the process.

    The budget is the real object, not a mock: what these cases turn on is arming being
    idempotent and the interrupt being a flag a bounded step can read.
    """

    def test_sigterm_arms_the_budget_and_moves_the_phase_to_draining(self) -> None:
        budget = ShutdownBudget(total_seconds=30.0)
        handler, _stub, _ctx = _handler(budget=budget)

        handler._sigterm_handler()

        assert budget.armed is True
        assert budget.phase is ShutdownPhase.DRAINING

    def test_repeated_sigterm_does_not_extend_the_deadline(self) -> None:
        """The first request wins: a second signal must not buy more time."""
        ticks = iter([100.0, 105.0, 110.0])
        budget = ShutdownBudget(total_seconds=30.0, clock=lambda: next(ticks))
        handler, _stub, _ctx = _handler(budget=budget)

        handler._sigterm_handler()
        after_first = budget.remaining()
        handler._sigterm_handler()
        after_second = budget.remaining()

        assert after_first == 25.0
        assert after_second == 20.0

    def test_sigint_never_arms_the_budget(self) -> None:
        """An accidental Ctrl-C still does not begin the sequence."""
        budget = ShutdownBudget(total_seconds=30.0)
        handler, _stub, ctx = _handler(budget=budget)

        handler._sigint_handler()

        assert budget.armed is False
        assert budget.interrupt_requested is False
        assert ctx.conv.shutdown_requested is False

    def test_second_sigint_interrupts_running_step_without_force_exit(self) -> None:
        """REQ-011, AC-4: the interrupt is a request the step acts on, not os._exit."""
        budget = ShutdownBudget(total_seconds=30.0)
        budget.arm()
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.SHUTDOWN_IN_PROGRESS, budget=budget, force_exit=exits.append
        )

        handler._sigint_handler()

        assert budget.interrupt_requested is True
        assert exits == []

    def test_interrupt_is_requested_when_ctrl_c_cancels_a_turn_too(self) -> None:
        """A turn cancelled after shutdown began does not leave the coordinator's step running."""
        budget = ShutdownBudget(total_seconds=30.0)
        budget.arm()
        handler, stub, _ctx = _handler(InterruptAction.CANCEL_TURN, budget=budget)

        handler._sigint_handler()

        assert stub.interrupts == 1
        assert budget.interrupt_requested is True

    def test_configured_force_exit_is_read_once_at_construction(self) -> None:
        """shutdown_force_exit_on_second_sigint is the configured opt-in, no constructor flag."""
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.SHUTDOWN_IN_PROGRESS,
            configured_force_exit=True,
            force_exit=exits.append,
        )

        handler._sigint_handler()

        assert exits == [130]

    def test_a_non_bool_configured_flag_does_not_enable_force_exit(self) -> None:
        """The configured value is read by identity, so a stand-in cfg cannot arm os._exit."""
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.SHUTDOWN_IN_PROGRESS, force_exit=exits.append
        )

        handler._sigint_handler()

        assert exits == []

    def test_windows_control_events_use_the_same_budget(self) -> None:
        """Close/logoff/shutdown arm the one budget; Ctrl-C then interrupts the step."""
        budget = ShutdownBudget(total_seconds=30.0)
        handler, _stub, _ctx = _handler(budget=budget)

        assert handler._dispatch_control_event(2) is True  # CTRL_CLOSE_EVENT
        assert budget.armed is True
        assert handler._dispatch_control_event(0) is True  # CTRL_C_EVENT
        assert budget.interrupt_requested is True


class TestForceExit:
    def test_second_interrupt_during_shutdown_does_not_exit_by_default(self) -> None:
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.SHUTDOWN_IN_PROGRESS, force_exit=exits.append
        )
        handler._sigint_handler()
        assert exits == []

    def test_second_interrupt_during_shutdown_forces_exit_when_enabled(self) -> None:
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.SHUTDOWN_IN_PROGRESS,
            force_exit_on_second_sigint=True,
            force_exit=exits.append,
        )
        handler._sigint_handler()
        assert exits == [130]

    def test_interrupt_in_other_states_never_forces_exit(self) -> None:
        exits: list[int] = []
        handler, _stub, _ctx = _handler(
            InterruptAction.CANCEL_TURN,
            force_exit_on_second_sigint=True,
            force_exit=exits.append,
        )
        handler._sigint_handler()
        assert exits == []


class TestWindowsControlEvents:
    @pytest.mark.parametrize("event", [0, 1])
    def test_ctrl_c_and_break_act_as_interrupt(self, event: int) -> None:
        handler, stub, ctx = _handler()
        assert handler._dispatch_control_event(event) is True
        assert stub.interrupts == 1
        assert ctx.conv.shutdown_requested is False

    @pytest.mark.parametrize("event", [2, 5, 6])
    def test_close_logoff_shutdown_begin_graceful_shutdown(self, event: int) -> None:
        handler, stub, ctx = _handler()
        assert handler._dispatch_control_event(event) is True
        assert ctx.conv.shutdown_requested is True
        assert stub.shutdowns == 1

    def test_unknown_event_is_not_handled(self) -> None:
        handler, stub, _ctx = _handler()
        assert handler._dispatch_control_event(99) is False
        assert stub.interrupts == 0 and stub.shutdowns == 0

    def test_ctypes_callback_has_no_unbound_name(self) -> None:
        """The ctypes path must not reference win32con (unbound when pywin32 is missing)."""
        handler, stub, _ctx = _handler()
        registered: list[Any] = []

        def _winfunctype(*_types: Any) -> Any:
            return lambda fn: registered.append(fn) or fn

        fake_windll = MagicMock()
        mock_loop = MagicMock()
        mock_loop.call_soon_threadsafe.side_effect = lambda fn, *a: fn(*a)
        with (
            patch.object(
                mock_loop, "add_signal_handler", side_effect=NotImplementedError()
            ),
            patch("sys.frozen", True, create=True),
            patch.dict(
                ctypes.__dict__,
                {
                    "WINFUNCTYPE": _winfunctype,
                    "windll": fake_windll,
                    "wintypes": SimpleNamespace(BOOL=object, DWORD=object),
                },
            ),
        ):
            handler.register(mock_loop)
        assert len(registered) == 1
        assert registered[0](0) is True  # Ctrl-C, no NameError
        assert stub.interrupts == 1
        assert registered[0](2) is True  # close event
        assert stub.shutdowns == 1
        assert registered[0](99) is False
        fake_windll.kernel32.SetConsoleCtrlHandler.assert_called_once()
        assert handler._ctypes_callback is registered[0]
