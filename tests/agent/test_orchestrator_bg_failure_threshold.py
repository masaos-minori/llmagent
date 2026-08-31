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
    ctx.turn.pending_approval_task_id = None
    ctx.session.session_id = "test-session"
    ctx.workflow.workflow_id = None
    ctx.workflow.approval_pending = False
    ctx.services_required.hist_mgr = AsyncMock()
    ctx.services_required.llm = MagicMock()
    ctx.services_required.audit_logger = None
    ctx.services_required.memory = None
    ctx.services_required.tools = None
    return ctx


class TestConsecutiveFailuresIncrement:
    @pytest.mark.asyncio
    async def test_increment_on_single_failure(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        mock_task.exception.return_value = RuntimeError("connection refused")

        monitor.on_task_done(mock_task)

        assert monitor.get_consecutive_failures("first_turn") == 1

    @pytest.mark.asyncio
    async def test_increment_continues_after_multiple_failures(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(BG_FAILURE_THRESHOLD + 2):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"error {i}")
            monitor.on_task_done(mock_task)

        assert monitor.get_consecutive_failures("bg_task_0") == BG_FAILURE_THRESHOLD + 2

    @pytest.mark.asyncio
    async def test_reset_on_cancelled_task(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(5):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            monitor.on_task_done(mock_task)
        assert monitor.get_consecutive_failures("bg_task_0") == 5

        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        monitor.on_task_done(cancelled_task)

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
                mock_task = MagicMock(spec=asyncio.Task)
                mock_task.get_name.return_value = f"bg_task_{i}"
                mock_task.exception.return_value = RuntimeError(f"error {i}")
                monitor.on_task_done(mock_task)

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
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"error {i}")
            monitor.on_task_done(mock_task)

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
                mock_task = MagicMock(spec=asyncio.Task)
                mock_task.get_name.return_value = f"bg_task_{i}"
                mock_task.exception.return_value = RuntimeError(f"error {i}")
                monitor.on_task_done(mock_task)

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

        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        mock_task.exception.return_value = RuntimeError("original error")
        monitor.on_task_done(mock_task)

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

        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        original_err = RuntimeError("connection timeout")
        mock_task.exception.return_value = original_err
        monitor.on_task_done(mock_task)

        assert captured_exc[0] is original_err


class TestCancelledTaskCounterReset:
    @pytest.mark.asyncio
    async def test_cancelled_task_does_not_increment_counter(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(3):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            monitor.on_task_done(mock_task)
        assert monitor.get_consecutive_failures("bg_task_0") == 3

        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        monitor.on_task_done(cancelled_task)

        assert monitor.get_consecutive_failures("cancelled_task") == 0

    @pytest.mark.asyncio
    async def test_cancelled_task_resets_counter_to_zero(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(ctx, tasks=tasks, on_discard=lambda t: None)

        for i in range(5):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            monitor.on_task_done(mock_task)
        assert monitor.get_consecutive_failures("bg_task_0") == 5

        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        monitor.on_task_done(cancelled_task)

        assert monitor.get_consecutive_failures("cancelled_task") == 0
