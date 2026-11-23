"""Characterization tests for BgTaskMonitor: consecutive failure counting, threshold breach, pause state."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.bg_task_monitor import (
    BG_FAILURE_THRESHOLD,
    BgTaskMonitor,
    TaskIdentity,
    bind_task_identity,
    current_task_identity,
    current_task_target,
    new_task_identity,
)
from agent.session import SessionTarget


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


async def _ok_task() -> None:
    """A task body that returns normally; ``task.exception()`` is ``None``."""


async def _await_ok(name: str = "bg_task_0") -> asyncio.Task[object]:
    """Create a task whose body completes cleanly and return the finished task.

    Mirrors ``_await_raising`` for the clean-completion case: the body returns
    normally, one yield lets it finish, and the finished task is returned so the
    caller can hand it to the monitor without the completion escaping this helper.
    """
    task = asyncio.create_task(_ok_task(), name=name)
    await asyncio.sleep(0)  # yield once so the body runs to completion
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


class TestPauseResumePath:
    @pytest.mark.asyncio
    async def test_clean_completion_after_breach_clears_pause(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(
            ctx, tasks=tasks, on_discard=lambda t: None, pause_on_critical_failure=True
        )

        for i in range(BG_FAILURE_THRESHOLD):
            monitor.on_task_done(await _await_raising(f"error {i}", "bg_task_0"))
        assert monitor.bg_pause_state == {"bg_task_0": True}  # precondition

        monitor.on_task_done(await _await_ok("bg_task_0"))

        assert monitor.bg_pause_state == {}
        assert monitor.check_pause_state() == (False, [])

    @pytest.mark.asyncio
    async def test_cancelled_task_after_breach_keeps_pause(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(
            ctx, tasks=tasks, on_discard=lambda t: None, pause_on_critical_failure=True
        )

        for i in range(BG_FAILURE_THRESHOLD):
            monitor.on_task_done(await _await_raising(f"error {i}", "bg_task_0"))
        assert monitor.bg_pause_state == {"bg_task_0": True}  # precondition

        monitor.on_task_done(await _make_cancelled("bg_task_0"))

        assert monitor.bg_pause_state == {"bg_task_0": True}

    @pytest.mark.asyncio
    async def test_other_task_success_after_breach_keeps_pause(self) -> None:
        ctx = _make_ctx()
        tasks: set[asyncio.Task[object]] = set()
        monitor = BgTaskMonitor(
            ctx, tasks=tasks, on_discard=lambda t: None, pause_on_critical_failure=True
        )

        for i in range(BG_FAILURE_THRESHOLD):
            monitor.on_task_done(await _await_raising(f"error {i}", "bg_task_0"))
        assert monitor.bg_pause_state == {"bg_task_0": True}  # precondition

        monitor.on_task_done(await _await_ok("other_task"))

        assert monitor.bg_pause_state == {"bg_task_0": True}
        assert monitor.check_pause_state() == (True, ["bg_task_0"])


async def _await_raising_with_identity(
    message: str, identity: TaskIdentity, name: str = "ignored_name"
) -> asyncio.Task[object]:
    """Create a raising task under ``bind_task_identity`` and let it fail."""
    with bind_task_identity(identity):
        task = asyncio.create_task(_raising_task(message), name=name)
    await asyncio.sleep(0)
    return task


class TestTypedRegistration:
    @pytest.mark.asyncio
    async def test_register_records_type_instance_session_and_generation(self) -> None:
        monitor = BgTaskMonitor(_make_ctx(), tasks=set(), on_discard=lambda t: None)
        task = asyncio.create_task(_ok_task(), name="whatever")

        identity = monitor.register(task, "session_title", 7, 3, instance_id="inst-1")
        await task

        assert identity == TaskIdentity("session_title", "inst-1", 7, 3)

    @pytest.mark.asyncio
    async def test_failures_group_by_type_across_task_names(self) -> None:
        monitor = BgTaskMonitor(_make_ctx(), tasks=set(), on_discard=lambda t: None)

        for i, name in enumerate(["alpha", "beta", "gamma"]):
            task = await _await_raising(f"boom {i}", name)
            monitor.register(task, "session_title", 1, 1)
            monitor.on_task_done(task)

        assert monitor.get_consecutive_failures("session_title") == 3
        assert monitor.get_consecutive_failures("alpha") == 0

    @pytest.mark.asyncio
    async def test_untyped_tasks_keep_name_based_keys(self) -> None:
        monitor = BgTaskMonitor(_make_ctx(), tasks=set(), on_discard=lambda t: None)
        for i in range(2):
            monitor.on_task_done(await _await_raising(f"e{i}", "legacy_name"))

        assert monitor.get_consecutive_failures("legacy_name") == 2

    @pytest.mark.asyncio
    async def test_identity_bound_at_creation_is_found_through_the_task_context(
        self,
    ) -> None:
        monitor = BgTaskMonitor(_make_ctx(), tasks=set(), on_discard=lambda t: None)
        identity = new_task_identity("session_title", 9, 4)

        task = await _await_raising_with_identity("boom", identity)
        monitor.on_task_done(task)

        assert monitor.get_consecutive_failures("session_title") == 1

    @pytest.mark.asyncio
    async def test_identity_is_visible_inside_the_task_and_target_is_derived(
        self,
    ) -> None:
        seen: list[object] = []

        async def _body() -> None:
            seen.append(current_task_identity())
            seen.append(current_task_target())

        identity = TaskIdentity("session_title", "i-1", 5, 2)
        with bind_task_identity(identity):
            task = asyncio.create_task(_body())
        await task

        assert seen == [identity, SessionTarget(5, 2)]
        assert current_task_identity() is None  # reset after the with block
        assert current_task_target() is None

    @pytest.mark.asyncio
    async def test_typed_pause_state_is_keyed_by_type(self) -> None:
        monitor = BgTaskMonitor(
            _make_ctx(),
            tasks=set(),
            on_discard=lambda t: None,
            on_error=lambda e: None,
            pause_on_critical_failure=True,
        )
        for i in range(BG_FAILURE_THRESHOLD):
            task = await _await_raising(f"e{i}", f"name{i}")
            monitor.register(task, "session_title", 1, 1)
            monitor.on_task_done(task)

        assert monitor.check_pause_state() == (True, ["session_title"])


class _CaptureMonitorLog:
    """Capture formatted records of the monitor logger (it does not propagate to root)."""

    def __enter__(self) -> list[str]:
        self.messages: list[str] = []
        messages = self.messages

        class _Handler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                messages.append(record.getMessage())

        self._handler = _Handler(logging.DEBUG)
        self._logger = logging.getLogger("agent.bg_task_monitor")
        self._level = self._logger.level
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(self._handler)
        return self.messages

    def __exit__(self, *_: object) -> None:
        self._logger.removeHandler(self._handler)
        self._logger.setLevel(self._level)


class TestFailureRedaction:
    SECRET = "sk-title-text-and-secret-reason"

    @pytest.mark.asyncio
    async def test_no_log_line_carries_the_raw_reason(self) -> None:
        monitor = BgTaskMonitor(
            _make_ctx(), tasks=set(), on_discard=lambda t: None, on_error=lambda e: None
        )
        identity = new_task_identity("session_title", 11, 6)

        with _CaptureMonitorLog() as logged:
            for _ in range(BG_FAILURE_THRESHOLD + 5):
                monitor.on_task_done(
                    await _await_raising_with_identity(self.SECRET, identity)
                )

        text = "\n".join(logged)
        assert logged, "expected failure log records"
        assert self.SECRET not in text
        assert "RuntimeError" in text
        assert "session=11" in text
        assert "generation=6" in text

    @pytest.mark.asyncio
    async def test_notification_callback_failure_logs_class_name_only(self) -> None:
        def _flaky(exc: Exception) -> None:
            raise ValueError(self.SECRET)

        monitor = BgTaskMonitor(
            _make_ctx(), tasks=set(), on_discard=lambda t: None, on_error=_flaky
        )

        with _CaptureMonitorLog() as logged:
            monitor.on_task_done(await _await_raising("boom", "first_turn"))

        text = "\n".join(logged)
        assert self.SECRET not in text
        assert "ValueError" in text
