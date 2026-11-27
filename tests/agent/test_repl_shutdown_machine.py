"""tests/agent/test_repl_shutdown_machine.py — the input loop's shutdown acceptance gate.

Covers the acceptance refusal, the budget-derived graceful window, the release of a
pending approval, and the second-interrupt routing of `scripts/agent/repl_input_loop.py`.

Requirement source: issues/done/20261119-145302_cliplc004_bounded-shutdown-machine.md.
"""

import asyncio
import builtins
import re
import threading
import time
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.orchestrator import Orchestrator
from agent.repl_input_controller import InputState, reset_input_controller
from agent.repl_input_loop import ReplInputLoop, _TurnFlow
from agent.shutdown_budget import ShutdownBudget, ShutdownPhase

pytestmark = pytest.mark.contract


@pytest.fixture(autouse=True)
def _fresh_input_controller() -> Iterator[None]:
    """Give each test the process-shared controller in its initial state."""
    reset_input_controller()
    yield
    reset_input_controller()


def _make_loop(
    *,
    budget: ShutdownBudget | None = None,
    shutdown_event: asyncio.Event | None = None,
) -> tuple[MagicMock, MagicMock, ReplInputLoop]:
    """Build a bound input loop over mocked context, view, commands, and orchestrator."""
    ctx = MagicMock(spec=AgentContext)
    ctx.conv = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.conv.is_processing = False
    ctx.conv.memory_disabled = False
    ctx.conv.memory_warning_shown = False
    ctx.stats = MagicMock()
    ctx.stats.stat_partial_completions = 0
    # The turn-entry check reads the session's degraded state (cliplc010 AC-3);
    # AgentContext is a plain class, so the spec mock needs the instance attribute.
    ctx.session = MagicMock()
    ctx.session.is_degraded = False

    view = MagicMock(spec=CLIView)
    loop = ReplInputLoop(ctx, view, shutdown_event, budget=budget)
    loop._cmds = MagicMock(spec=CommandRegistry)
    loop._cmds.dispatch = AsyncMock(return_value=True)
    loop._orchestrator = MagicMock(spec=Orchestrator)
    loop._orchestrator.handle_turn = AsyncMock()
    return ctx, view, loop


def _warnings(view: MagicMock) -> list[str]:
    return [str(call.args[0]) for call in view.write_warning.call_args_list]


def _patch_lines(monkeypatch: pytest.MonkeyPatch, *lines: str) -> None:
    """Feed the prompt the given lines, then EOF."""
    remaining = list(lines)

    def _read(prompt: str = "") -> str:
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    monkeypatch.setattr(builtins, "input", _read)


async def test_command_after_draining_is_refused_before_the_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A command typed after shutdown begins never reaches the command router."""
    budget = ShutdownBudget(45.0)
    budget.arm()
    _, view, loop = _make_loop(budget=budget)
    _patch_lines(monkeypatch, "/help")

    await loop._repl_loop()

    loop._cmds.dispatch.assert_not_called()
    loop._orchestrator.handle_turn.assert_not_called()
    assert any("draining" in w and "refused" in w for w in _warnings(view))


async def test_turn_after_draining_is_refused_before_the_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A turn typed after shutdown begins never reaches the orchestrator."""
    budget = ShutdownBudget(45.0)
    budget.arm()
    budget.mark_closed()
    _, view, loop = _make_loop(budget=budget)
    _patch_lines(monkeypatch, "hello")

    await loop._repl_loop()

    loop._orchestrator.handle_turn.assert_not_called()
    assert any("closed" in w and "refused" in w for w in _warnings(view))


async def test_dispatch_gate_refuses_a_line_that_was_already_read() -> None:
    """The dispatch path is a second gate: neither the router nor the orchestrator runs."""
    budget = ShutdownBudget(45.0)
    budget.arm()
    ctx, view, loop = _make_loop(budget=budget)

    await loop._dispatch_line("/help", ctx)
    await loop._dispatch_line("hello", ctx)

    loop._cmds.dispatch.assert_not_called()
    loop._orchestrator.handle_turn.assert_not_called()
    refusals = [w for w in _warnings(view) if "refused" in w]
    assert len(refusals) == 1, "the refusal is reported once, not per line"


async def test_refusal_is_reported_once_per_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The line accepted before shutdown runs; the next iteration stops with one message."""
    budget = ShutdownBudget(45.0)
    ctx, view, loop = _make_loop(budget=budget)

    async def _handle_turn(_line: str) -> None:
        budget.arm()

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello", "second line")

    await loop._repl_loop()

    assert loop._orchestrator.handle_turn.await_count == 1
    assert len([w for w in _warnings(view) if "refused" in w]) == 1


async def test_pending_approval_is_released_with_the_shutdown_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A wait that can never be answered is ended with the shutdown outcome, not held."""
    budget = ShutdownBudget(45.0)
    _, view, loop = _make_loop(budget=budget)
    release = threading.Event()

    def _blocked_read(prompt: str = "") -> str:
        release.wait(5)
        return "never"

    monkeypatch.setattr(builtins, "input", _blocked_read)

    async def _arm_and_release() -> None:
        await asyncio.sleep(0.1)
        budget.arm()
        loop._input.shutdown()

    waiter = asyncio.ensure_future(_arm_and_release())
    try:
        await asyncio.wait_for(loop._repl_loop(), timeout=3.0)
    finally:
        release.set()
        await waiter

    assert loop._input.state is InputState.SHUTDOWN
    view.write_turn_end.assert_called_once()


async def test_graceful_window_is_the_remaining_budget() -> None:
    """The window a turn may finish in is the budget's remaining time, not a constant."""
    budget = ShutdownBudget(7.5)
    _, _, loop = _make_loop(budget=budget)

    assert loop._graceful_window() == pytest.approx(7.5, abs=0.01)
    budget.arm()
    assert 7.0 < loop._graceful_window() <= 7.5


async def test_loop_without_a_budget_keeps_the_legacy_window() -> None:
    """A loop built without a budget still uses the window it owns today."""
    _, _, loop = _make_loop()

    assert loop._graceful_window() == ReplInputLoop._GRACEFUL_TIMEOUT_S


async def test_uncooperative_turn_is_bounded_by_the_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bounded wait for a turn that ignores cancellation is the budget, not 10 s."""
    budget = ShutdownBudget(0.3)
    shutdown_event = asyncio.Event()
    _, view, loop = _make_loop(budget=budget, shutdown_event=shutdown_event)
    turn_started = asyncio.Event()

    async def _handle_turn(_line: str) -> None:
        turn_started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            await asyncio.sleep(0.8)

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello")

    async def _signal_once_turn_runs() -> None:
        await turn_started.wait()
        budget.arm()
        shutdown_event.set()

    signal_task = asyncio.ensure_future(_signal_once_turn_runs())
    start = time.monotonic()
    try:
        await asyncio.wait_for(loop._repl_loop(), timeout=3.0)
    finally:
        elapsed = time.monotonic() - start
        signal_task.cancel()

    assert elapsed < 1.5, (
        f"the turn window was not bounded by the budget: {elapsed:.2f}s"
    )
    timed_out = [w for w in _warnings(view) if "timed out after" in w]
    assert timed_out
    reported = float(re.search(r"timed out after ([0-9.]+)s", timed_out[0]).group(1))
    assert 0.0 < reported <= 0.3


async def test_second_interrupt_during_draining_ends_the_input_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An interrupt after shutdown began stops the loop and reaches the shared budget."""
    budget = ShutdownBudget(45.0)
    _, view, loop = _make_loop(budget=budget, shutdown_event=asyncio.Event())
    turn_started = asyncio.Event()

    async def _handle_turn(_line: str) -> None:
        turn_started.set()
        await asyncio.sleep(30)

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello")

    async def _interrupt_once_turn_runs() -> None:
        await turn_started.wait()
        # The first shutdown request arms the budget; the second one interrupts.
        budget.arm()
        loop._input.handle_interrupt()

    interrupter = asyncio.ensure_future(_interrupt_once_turn_runs())
    try:
        await asyncio.wait_for(loop._repl_loop(), timeout=3.0)
    finally:
        await asyncio.wait_for(interrupter, timeout=2.0)

    assert budget.interrupt_requested, "the interrupt was not routed to the budget"
    warnings = _warnings(view)
    assert any("Turn cancelled" in w for w in warnings)
    assert any("ending the input loop" in w for w in warnings)


async def test_second_interrupt_without_a_shutdown_event_ends_the_input_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same routing holds when shutdown was requested without a shutdown event."""
    budget = ShutdownBudget(45.0)
    _, view, loop = _make_loop(budget=budget)
    turn_started = asyncio.Event()

    async def _handle_turn(_line: str) -> None:
        turn_started.set()
        await asyncio.sleep(30)

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello")

    async def _interrupt_once_turn_runs() -> None:
        await turn_started.wait()
        budget.arm()
        loop._input.handle_interrupt()

    interrupter = asyncio.ensure_future(_interrupt_once_turn_runs())
    try:
        await asyncio.wait_for(loop._repl_loop(), timeout=3.0)
    finally:
        await asyncio.wait_for(interrupter, timeout=2.0)

    assert budget.interrupt_requested, "the interrupt was not routed to the budget"
    warnings = _warnings(view)
    assert any("Turn cancelled" in w for w in warnings)
    assert any("ending the input loop" in w for w in warnings)


async def test_interrupt_while_accepting_keeps_the_loop_prompting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ctrl-C before shutdown still cancels only the turn and keeps the session open."""
    budget = ShutdownBudget(45.0)
    _, view, loop = _make_loop(budget=budget, shutdown_event=asyncio.Event())
    turn_started = asyncio.Event()

    async def _handle_turn(_line: str) -> None:
        turn_started.set()
        await asyncio.sleep(30)

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello")

    async def _interrupt_once_turn_runs() -> None:
        await turn_started.wait()
        loop._input.handle_interrupt()

    interrupter = asyncio.ensure_future(_interrupt_once_turn_runs())
    try:
        await asyncio.wait_for(loop._repl_loop(), timeout=3.0)
    finally:
        await asyncio.wait_for(interrupter, timeout=2.0)

    assert budget.interrupt_requested is False
    assert not any("ending the input loop" in w for w in _warnings(view))
    assert loop._orchestrator.handle_turn.await_count == 1


async def test_phase_check_does_not_refuse_work_while_accepting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unarmed budget leaves the loop accepting, so existing behavior is unchanged."""
    budget = ShutdownBudget(45.0)
    ctx, view, loop = _make_loop(budget=budget)
    _patch_lines(monkeypatch, "/help", "hello")

    await loop._repl_loop()

    assert budget.phase is ShutdownPhase.ACCEPTING
    loop._cmds.dispatch.assert_awaited_once_with("/help")
    loop._orchestrator.handle_turn.assert_awaited_once_with("hello")
    assert not any("refused" in w for w in _warnings(view))


async def test_a_requested_shutdown_bounds_the_running_turn_by_the_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A turn that times out while shutdown was requested ends the loop with the window."""
    monkeypatch.setattr(ReplInputLoop, "_GRACEFUL_TIMEOUT_S", 0.3)
    shutdown_event = asyncio.Event()
    shutdown_event.set()
    ctx, view, loop = _make_loop(shutdown_event=shutdown_event)
    ctx.conv.shutdown_requested = True

    loop._orchestrator.handle_turn = AsyncMock(side_effect=TimeoutError)
    dispatch_task = asyncio.ensure_future(loop._dispatch_line("hello", ctx))

    flow = await loop._await_turn(dispatch_task, ctx)

    assert flow is _TurnFlow.BREAK
    timed_out = [w for w in _warnings(view) if "timed out after" in w]
    assert timed_out
    reported = float(re.search(r"timed out after ([0-9.]+)s", timed_out[0]).group(1))
    assert 0.0 < reported <= 0.3


async def test_a_turn_that_times_out_after_shutdown_started_reports_the_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A turn that reports its own timeout during shutdown ends the loop with the window."""
    budget = ShutdownBudget(0.4)
    ctx, view, loop = _make_loop(budget=budget)

    async def _handle_turn(_line: str) -> None:
        ctx.conv.shutdown_requested = True
        budget.arm()
        raise TimeoutError

    loop._orchestrator.handle_turn = AsyncMock(side_effect=_handle_turn)
    _patch_lines(monkeypatch, "hello")

    await asyncio.wait_for(loop._repl_loop(), timeout=3.0)

    timed_out = [w for w in _warnings(view) if "timed out after" in w]
    assert timed_out
    reported = float(re.search(r"timed out after ([0-9.]+)s", timed_out[0]).group(1))
    assert 0.0 < reported <= 0.4
    loop._orchestrator.handle_turn.assert_awaited_once_with("hello")
