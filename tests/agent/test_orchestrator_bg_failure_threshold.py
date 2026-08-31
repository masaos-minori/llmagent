"""Characterization tests for orchestrator background task failure threshold."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.orchestrator import BG_FAILURE_THRESHOLD, Orchestrator


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
    """Verify _consecutive_bg_failures increments correctly."""

    @pytest.mark.asyncio
    async def test_increment_on_single_failure(self) -> None:
        """A single bg task failure increments _consecutive_bg_failures by 1."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        # Simulate a non-cancelled exception via _discard_and_log
        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        mock_task.exception.return_value = RuntimeError("connection refused")

        orch._discard_and_log(mock_task)

        assert orch._consecutive_bg_failures == 1

    @pytest.mark.asyncio
    async def test_increment_continues_after_multiple_failures(self) -> None:
        """_consecutive_bg_failures continues incrementing across multiple failures."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        for i in range(BG_FAILURE_THRESHOLD + 2):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"error {i}")
            orch._discard_and_log(mock_task)

        assert orch._consecutive_bg_failures == BG_FAILURE_THRESHOLD + 2

    @pytest.mark.asyncio
    async def test_reset_on_cancelled_task(self) -> None:
        """Cancelled tasks reset _consecutive_bg_failures to 0."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        # Cause some failures first
        for i in range(5):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            orch._discard_and_log(mock_task)
        assert orch._consecutive_bg_failures == 5

        # Now simulate cancellation
        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        orch._discard_and_log(cancelled_task)

        assert orch._consecutive_bg_failures == 0


class TestThresholdReachedBehavior:
    """Verify error log output and agent continues at threshold."""

    @pytest.mark.asyncio
    async def test_logs_error_at_threshold(self) -> None:
        """At exactly BG_FAILURE_THRESHOLD, an error-level log is emitted."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

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
                orch._discard_and_log(mock_task)

            has_error = any(
                "Consecutive background task failures" in msg for msg in captured_log
            )
            assert has_error, f"No error log found. Captured logs: {captured_log}"
        finally:
            logger.removeHandler(handler)
            logger.handlers = original_handlers

    @pytest.mark.asyncio
    async def test_agent_continues_running_at_threshold(self) -> None:
        """Agent does NOT crash when threshold is reached; it continues running."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        # Drive past threshold
        for i in range(BG_FAILURE_THRESHOLD + 1):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"error {i}")
            orch._discard_and_log(mock_task)

        # Agent continues running but health check may be paused after threshold breach
        assert orch._consecutive_bg_failures == BG_FAILURE_THRESHOLD + 1

    @pytest.mark.asyncio
    async def test_logs_warning_below_threshold(self) -> None:
        """Below threshold, only warning-level log is emitted, not error."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

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
            # Failures below threshold
            for i in range(BG_FAILURE_THRESHOLD - 1):
                mock_task = MagicMock(spec=asyncio.Task)
                mock_task.get_name.return_value = f"bg_task_{i}"
                mock_task.exception.return_value = RuntimeError(f"error {i}")
                orch._discard_and_log(mock_task)

            has_warning = any(record == logging.WARNING for record in captured_levels)
            has_error = any(record == logging.ERROR for record in captured_levels)
            assert has_warning, "Expected WARNING level log below threshold"
            assert not has_error, "Unexpected ERROR level log below threshold"
        finally:
            logger.removeHandler(handler)
            logger.handlers = original_handlers


class TestOnErrorCallbackExceptionHandling:
    """Verify exception logged but not notified to user."""

    @pytest.mark.asyncio
    async def test_exception_in_on_error_logged_not_propagated(self) -> None:
        """If _on_error raises, the exception is caught and logged, not propagated."""
        ctx = _make_ctx()

        def _flaky_on_error(exc: Exception) -> None:
            raise RuntimeError("callback failed")

        orch = Orchestrator(ctx, on_error=_flaky_on_error)
        orch._bg_pause_state = {"health": False}

        # This should NOT propagate the callback exception
        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        mock_task.exception.return_value = RuntimeError("original error")
        orch._discard_and_log(mock_task)

        # No exception should have been raised from this call
        assert True  # If we get here, the exception was caught

    @pytest.mark.asyncio
    async def test_on_error_called_with_original_exception(self) -> None:
        """The original bg task exception is passed to _on_error even if callback fails."""
        ctx = _make_ctx()
        captured_exc: list[Exception | None] = [None]

        def _record_then_raise(exc: Exception) -> None:
            captured_exc[0] = exc
            raise RuntimeError("callback failed")

        orch = Orchestrator(ctx, on_error=_record_then_raise)
        orch._bg_pause_state = {"health": False}

        mock_task = MagicMock(spec=asyncio.Task)
        mock_task.get_name.return_value = "first_turn"
        original_err = RuntimeError("connection timeout")
        mock_task.exception.return_value = original_err
        orch._discard_and_log(mock_task)

        assert captured_exc[0] is original_err


class TestCancelledTaskCounterReset:
    """Verify cancelled tasks do NOT increment _consecutive_bg_failures."""

    @pytest.mark.asyncio
    async def test_cancelled_task_does_not_increment_counter(self) -> None:
        """A cancelled task does NOT increment _consecutive_bg_failures."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        # First, cause some real failures
        for i in range(3):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            orch._discard_and_log(mock_task)
        assert orch._consecutive_bg_failures == 3

        # Cancelled task resets counter to 0
        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        orch._discard_and_log(cancelled_task)

        assert orch._consecutive_bg_failures == 0

    @pytest.mark.asyncio
    async def test_cancelled_task_resets_counter_to_zero(self) -> None:
        """A cancelled task resets _consecutive_bg_failures to 0."""
        ctx = _make_ctx()
        orch = Orchestrator(ctx)
        orch._bg_pause_state = {"health": False}

        # Cause several failures
        for i in range(5):
            mock_task = MagicMock(spec=asyncio.Task)
            mock_task.get_name.return_value = f"bg_task_{i}"
            mock_task.exception.return_value = RuntimeError(f"fail {i}")
            orch._discard_and_log(mock_task)
        assert orch._consecutive_bg_failures == 5

        # Cancelled task should reset to zero
        cancelled_task = MagicMock(spec=asyncio.Task)
        cancelled_task.get_name.return_value = "cancelled_task"
        cancelled_task.exception.return_value = asyncio.CancelledError()
        orch._discard_and_log(cancelled_task)

        assert orch._consecutive_bg_failures == 0
