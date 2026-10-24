"""Characterization tests for BgTaskMonitor: consecutive failure counting, threshold breach, pause state."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.bg_task_monitor import BG_FAILURE_THRESHOLD, BgTaskMonitor


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.max_tool_turns = 3
    ctx.cfg.llm.context_char_limit = 0
    ctx.cfg.llm.context_token_limit = 0
    ctx.cfg.llm.budget_warn_ratio = 0.8
    ctx.cfg.tool.tool_definitions = []
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    ctx.conv.llm_url = "http://llm-test"
    ctx.conv.history = []
    ctx.stats.stat_turns = 1
    ctx.stats.stat_latency = {}
    ctx.stats.stat_input_tokens = None
    ctx.stats.stat_output_tokens = None
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_tool_calls = 0
    ctx.turn.current_turn_id = None
    ctx.session.session_id = "test-session"
    ctx.workflow.workflow_id = None
    ctx.services_required.hist_mgr = AsyncMock()
    ctx.services_required.llm = MagicMock()
    ctx.services_required.audit_logger = None
    ctx.services_required.memory = None
    ctx.services_required.tools = None
    return ctx


async def _raising_task(message: str) -> None:
    """A task whose body raises ``RuntimeError(message)``; ``task.exception()`` returns it."""
    raise RuntimeError(message)


async def _cancellable_task() -> None:
    """A task that waits forever until cancelled."""
    await asyncio.Event().wait()


async def _await_raising(message: str, name: str = "bg_task_0") -> asyncio.Task[object]:
    """Create a raising task, let its body run to the raise, and return it.

    The exception is retained on the task (retrievable via ``task.exception()``)
    rather than propagated, so the caller can hand the finished task to the
    monitor without the raise escaping this helper.
    """
    task = asyncio.create_task(_raising_task(message), name=name)
    await asyncio.sleep(0)  # yield once so the body runs and raises
    return task


async def _make_cancelled(name: str) -> asyncio.Task[object]:
    """Create a cancellable task, cancel it, await it to completion, and return it."""
    task = asyncio.create_task(_cancellable_task(), name=name)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    return task


class TestConsecutiveFailuresIncrement:
    @pytest.mark.asyncio
    async def test_increment_on_single_failure(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        task = await _await_raising("connection refused", "first_turn")
        monitor.on_task_done(task)

        assert monitor.get_consecutive_failures("first_turn") == 1

    @pytest.mark.asyncio
    async def test_increment_continues_after_multiple_failures(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(BG_FAILURE_THRESHOLD + 2):
            task = await _await_raising(f"error {i}", "bg_task_0")
            monitor.on_task_done(task)

        assert monitor.get_consecutive_failures("bg_task_0") == BG_FAILURE_THRESHOLD + 2

    @pytest.mark.asyncio
    async def test_reset_on_cancelled_task(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(5):
            task = await _await_raising(f"fail {i}", "bg_task_0")
            monitor.on_task_done(task)
        assert monitor.get_consecutive_failures("bg_task_0") == 5

        cancelled = await _make_cancelled("cancelled_task")
        monitor.on_task_done(cancelled)

        assert monitor.get_consecutive_failures("cancelled_task") == 0
        assert monitor.get_consecutive_failures("bg_task_0") == 5


class TestThresholdReachedBehavior:
    @pytest.mark.asyncio
    async def test_logs_error_at_threshold(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        captured_log: list[str] = []

        class CapturingHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_log.append(record.getMessage())

        handler = CapturingHandler()
        handler.setLevel(logging.ERROR)
        logger = logging.getLogger("agent.bg_task_monitor")
        original_handlers = logger.handlers.copy()
        logger.addHandler(handler)

        try:
            for i in range(BG_FAILURE_THRESHOLD):
                task = await _await_raising(f"error {i}", "bg_task_0")
                monitor.on_task_done(task)

            has_error = any(
                "Consecutive background task failures" in msg for msg in captured_log
            )
            assert has_error, f"No error log found. Captured logs: {captured_log}"
        finally:
            logger.removeHandler(handler)
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_agent_continues_running_at_threshold(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(BG_FAILURE_THRESHOLD + 1):
            task = await _await_raising(f"error {i}", "bg_task_0")
            monitor.on_task_done(task)

        assert monitor.get_consecutive_failures("bg_task_0") == BG_FAILURE_THRESHOLD + 1

    @pytest.mark.asyncio
    async def test_logs_warning_below_threshold(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        captured_levels: list[int] = []

        class LevelCapturingHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_levels.append(record.levelno)

        handler = LevelCapturingHandler()
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger("agent.bg_task_monitor")
        original_handlers = logger.handlers.copy()
        logger.addHandler(handler)

        try:
            for i in range(BG_FAILURE_THRESHOLD - 1):
                task = await _await_raising(f"error {i}", "bg_task_0")
                monitor.on_task_done(task)

            has_warning = any(record == logging.WARNING for record in captured_levels)
            has_error = any(record == logging.ERROR for record in captured_levels)
            assert has_warning, "Expected WARNING level log below threshold"
            assert not has_error, "Unexpected ERROR level log below threshold"
        finally:
            logger.removeHandler(handler)
            logger.handlers = original_handlers


class TestOnErrorCallbackExceptionHandling:
    @pytest.mark.asyncio
    async def test_exception_in_on_error_logged_not_propagated(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()

        def _flaky_on_error(exc: Exception) -> None:
            raise RuntimeError("callback failed")

        monitor = BgTaskMonitor(
            ctx, tasks=tasks, on_discard=lambda t: None, on_error=_flaky_on_error
        )

        task = await _await_raising("original error", "first_turn")
        monitor.on_task_done(task)

        assert True

    @pytest.mark.asyncio
    async def test_on_error_called_with_original_exception(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        captured_exc: list[Exception | None] = [None]

        def _record_then_raise(exc: Exception) -> None:
            captured_exc[0] = exc
            raise RuntimeError("callback failed")

        monitor = BgTaskMonitor(
            ctx, tasks=tasks, on_discard=lambda t: None, on_error=_record_then_raise
        )

        original_err = RuntimeError("connection timeout")

        async def _body() -> None:
            raise original_err

        task = asyncio.create_task(_body(), name="first_turn")
        await asyncio.sleep(0)
        monitor.on_task_done(task)

        assert captured_exc[0] is original_err


class TestCancelledTaskCounterReset:
    @pytest.mark.asyncio
    async def test_cancelled_task_does_not_increment_counter(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(3):
            task = await _await_raising(f"fail {i}", "bg_task_0")
            monitor.on_task_done(task)
        assert monitor.get_consecutive_failures("bg_task_0") == 3

        cancelled = await _make_cancelled("cancelled_task")
        monitor.on_task_done(cancelled)

        assert monitor.get_consecutive_failures("cancelled_task") == 0

    @pytest.mark.asyncio
    async def test_cancelled_task_resets_counter_to_zero(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(5):
            task = await _await_raising(f"fail {i}", "bg_task_0")
            monitor.on_task_done(task)
        assert monitor.get_consecutive_failures("bg_task_0") == 5

        cancelled = await _make_cancelled("cancelled_task")
        monitor.on_task_done(cancelled)

        assert monitor.get_consecutive_failures("cancelled_task") == 0
