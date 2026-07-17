"""
tests/test_orchestrator.py
Unit tests for Orchestrator: LLMTransportError handling in handle_turn() and _run_turn().
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.history import CompressResult
from agent.orchestrator import Orchestrator
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from shared.llm_exceptions import LLMErrorKind, LLMTransportError
from shared.llm_types import LLMMessage, LLMResponse

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    # cfg values accessed by handle_turn / _run_turn
    ctx.cfg.tool.max_tool_turns = 3
    ctx.cfg.llm.context_char_limit = 0
    ctx.cfg.llm.context_token_limit = 0
    ctx.cfg.llm.budget_warn_ratio = 0.8
    ctx.cfg.tool.tool_definitions = []
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    # session / turn state
    ctx.conv.llm_url = "http://llm-test"
    ctx.conv.history = []
    ctx.stats.stat_turns = (
        1  # keep > 0 so create_task is not called in first handle_turn
    )
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
    # services
    hist_mgr = AsyncMock()
    hist_mgr.stat_compress_count = 0

    _no_op = CompressResult(compressed_count=0, protected_count=0, summary_added=False)

    async def _compress(h: list) -> tuple:
        return h, _no_op

    hist_mgr.compress = AsyncMock(side_effect=_compress)
    ctx.services_required.hist_mgr = hist_mgr
    llm_svc = MagicMock()
    llm_svc.stat_partial_completions = 0
    llm_svc.stat_parse_errors = 0
    llm_svc.stat_heartbeat_timeouts = 0
    llm_svc.stat_reconnects = 0
    ctx.services_required.llm = llm_svc
    ctx.services_required.audit_logger = None
    ctx.services_required.memory = None
    ctx.services_required.tools = None
    return ctx


@pytest.fixture(autouse=True)
def _patch_workflow_loader():
    """Patch workflow infrastructure so Orchestrator works without filesystem access."""
    mock_task = MagicMock()
    mock_task.task_id = "test-task-id"
    mock_task.workflow_id = "test-workflow-id"

    async def _engine_run(task, plan_fn, execute_fn, verify_fn):
        await plan_fn()
        await execute_fn()
        await verify_fn()

    mock_engine_instance = MagicMock()
    mock_engine_instance.run = AsyncMock(side_effect=_engine_run)

    with (
        patch("agent.orchestrator.WorkflowLoader") as mock_loader,
        patch("agent.orchestrator.StateStore"),
        patch("agent.orchestrator.create_task", return_value=mock_task),
        patch("agent.orchestrator.audit_workflow_start"),
        patch("agent.orchestrator.WorkflowEngine", return_value=mock_engine_instance),
    ):
        mock_loader.return_value.load.return_value = MagicMock(version="test-v1")
        yield mock_loader


def _make_orchestrator(ctx: MagicMock, on_error: Any = None) -> Orchestrator:
    on_first_turn = AsyncMock()
    orch = Orchestrator(
        ctx,
        on_error=on_error,
        on_first_turn=on_first_turn,
    )
    orch._diagnostic_store = MagicMock()
    ctx.diagnostics = orch._diagnostic_store  # keep ctx.diagnostics in sync with mock
    return orch


def _make_err(
    kind: LLMErrorKind = "CONNECT_ERROR",
    partial_text: str = "",
    retryable: bool = False,
    phase: str = "in_stream",
) -> LLMTransportError:
    return LLMTransportError(
        kind=kind,
        phase=phase,  # type: ignore[arg-type]
        url="http://llm-test",
        retryable=retryable,
        partial_text=partial_text,
    )


# ── handle_turn: mandatory WorkflowEngine.run() invocation ───────────────────


class TestHandleTurnInvokesWorkflowEngine:
    @pytest.mark.asyncio
    async def test_handle_turn_calls_workflow_engine_run_once(self) -> None:
        """handle_turn() always drives execution through WorkflowEngine.run() — there is
        no fallback path that bypasses the engine. This is an explicit, dedicated assertion
        independent of the autouse _patch_workflow_loader fixture's implicit exercise of
        the same call (that fixture patches WorkflowEngine but never asserts on it).
        """
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        async def _engine_run(
            task: Any, plan_fn: Any, execute_fn: Any, verify_fn: Any
        ) -> None:
            await plan_fn()
            await execute_fn()
            await verify_fn()

        mock_engine_instance = MagicMock()
        mock_engine_instance.run = AsyncMock(side_effect=_engine_run)

        with (
            patch(
                "agent.orchestrator.WorkflowEngine",
                return_value=mock_engine_instance,
            ),
            patch.object(
                orch._llm_runner,
                "run",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ),
        ):
            await orch.handle_turn("hello")

        mock_engine_instance.run.assert_called_once()


# ── handle_turn: LLMTransportError paths ─────────────────────────────────────


class TestHandleTurnLLMTransportError:
    @pytest.mark.asyncio
    async def test_partial_completion_not_in_conversation_history(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        incomplete = [
            m for m in ctx.conv.history if "[INCOMPLETE" in m.get("content", "")
        ]
        assert len(incomplete) == 0, (
            "Incomplete output must not pollute conversation history"
        )

    @pytest.mark.asyncio
    async def test_partial_completion_saved_to_diagnostic_channel(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        orch._diagnostic_store.save.assert_called_once()
        # DiagnosticStore.save(session_id, kind, content)
        saved_content = orch._diagnostic_store.save.call_args[0][2]
        assert "partial answer" in saved_content
        assert "[INCOMPLETE: PREMATURE_EOF]" in saved_content

    @pytest.mark.asyncio
    async def test_partial_completion_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="some output")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1

    @pytest.mark.asyncio
    async def test_prestream_error_stores_diagnostic_not_pop(self) -> None:
        """Pre-stream errors store a diagnostic entry; user message stays in history."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) == 1
        orch._diagnostic_store.save.assert_called()

    @pytest.mark.asyncio
    async def test_on_error_called_for_partial_completion(self) -> None:
        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        on_error.assert_called_once_with(err)

    @pytest.mark.asyncio
    async def test_on_error_called_for_prestream_failure(self) -> None:
        ctx = _make_ctx()
        on_error = MagicMock()
        orch = _make_orchestrator(ctx, on_error=on_error)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        on_error.assert_called_once_with(err)

    @pytest.mark.asyncio
    async def test_audit_logger_turn_end_written_on_success(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="answer")),
        ):
            await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_audit_logger_turn_end_written_on_partial_error(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_turn_end_event_has_partial_completion_true_on_partial_error(
        self,
    ) -> None:
        """turn_end audit event must have partial_completion=True when LLM transport error has partial_text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called
        event = ctx.services_required.audit_logger.info.call_args[0][0]
        import json

        event_dict = json.loads(event)
        assert event_dict["partial_completion"] is True

    @pytest.mark.asyncio
    async def test_turn_end_event_has_partial_completion_false_on_non_partial_error(
        self,
    ) -> None:
        """turn_end audit event must have partial_completion=False when LLM transport error has no partial_text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="HTTP_500", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.audit_logger.info.called
        event = ctx.services_required.audit_logger.info.call_args[0][0]
        import json

        event_dict = json.loads(event)
        assert event_dict["partial_completion"] is False

    @pytest.mark.asyncio
    async def test_read_timeout_with_partial_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="READ_TIMEOUT", partial_text="chunk text")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1
        call_args = orch._diagnostic_store.save.call_args_list
        assert any("llm_transport_error" in str(a) for a in call_args)

    @pytest.mark.asyncio
    async def test_http_retryable_prestream_saves_mid_turn_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="HTTP_STATUS_RETRYABLE", retryable=True, partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 0
        call_args = orch._diagnostic_store.save.call_args_list
        assert any("mid_turn_error" in str(a) for a in call_args)

    @pytest.mark.asyncio
    async def test_http_fatal_with_status_code_saves_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = LLMTransportError(
            kind="HTTP_STATUS_FATAL",
            phase="pre_stream",
            url="http://llm-test",
            status_code=503,
            partial_text="",
        )

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 0
        orch._diagnostic_store.save.assert_called()

    @pytest.mark.asyncio
    async def test_malformed_sse_with_partial_saves_llm_transport_diagnostic(
        self,
    ) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="MALFORMED_SSE_FRAME", partial_text="partial frame")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services_required.llm.stat_partial_completions == 1
        saved_content = orch._diagnostic_store.save.call_args[0][2]
        assert "[INCOMPLETE: MALFORMED_SSE_FRAME]" in saved_content

    @pytest.mark.asyncio
    async def test_prestream_error_not_saved_as_assistant_message(self) -> None:
        """Pre-stream LLM transport errors must not be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        # session.save should NOT be called with "assistant" role for transport errors
        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Transport error summary must not be saved as assistant message"
        )

    @pytest.mark.asyncio
    async def test_partial_completion_not_saved_as_assistant_message(self) -> None:
        """Partial completion LLM errors must not be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        # session.save should NOT be called with "assistant" role for partial completions
        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Partial completion must not be saved as assistant message"
        )

    @pytest.mark.asyncio
    async def test_success_still_saved_as_assistant_message(self) -> None:
        """Successful LLM responses should still be saved as assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="hello")),
        ):
            await orch.handle_turn("hello")

        ctx.session.save.assert_called_with("assistant", "hello")

    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_true_on_partial_error(self) -> None:
        """partial_completion=True when LLM transport error has partial text."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial text here")

        captured: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured.append(s)

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("test message")

        turn_end_events = [json.loads(s) for s in captured if "turn_end" in s]
        assert turn_end_events, "No turn_end event captured"
        assert turn_end_events[0]["partial_completion"] is True

    @pytest.mark.asyncio
    async def test_turn_end_partial_completion_false_on_full_error(self) -> None:
        """partial_completion=False when LLM transport error has no partial text."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        captured: list[str] = []
        ctx.services_required.audit_logger = MagicMock()
        ctx.services_required.audit_logger.info = lambda s: captured.append(s)

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("test message")

        turn_end_events = [json.loads(s) for s in captured if "turn_end" in s]
        assert turn_end_events, "No turn_end event captured"
        assert turn_end_events[0]["partial_completion"] is False

    @pytest.mark.asyncio
    async def test_fetch_messages_excludes_transport_diagnostics(self) -> None:
        """Transport errors must not be saved to the messages table."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("test message")

        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0, (
            "Transport error must not write to messages table"
        )


# ── _run_turn: tool-continuation LLMTransportError ───────────────────────────


class TestRunTurnLLMTransportError:
    @pytest.mark.asyncio
    async def test_transport_error_on_tool_continuation_stores_in_diagnostic(
        self,
    ) -> None:
        """Tool-continuation LLM errors go to diagnostic channel; history not modified."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=tool_calls,
            ),
            finish_reason="tool_calls",
        )
        err = _make_err(kind="CONNECT_ERROR", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services_required.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_runner.run(
                "http://llm-test",
                workflow_id="wf-test",
                task_id="task-test",
                stage_id="execute",
                attempt_id="att-test",
            )

        assert "CONNECT_ERROR" in result.answer
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 0
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_transport_error_on_first_turn_stores_in_diagnostic(self) -> None:
        """First-turn LLM errors go to diagnostic channel; no synthetic history entry."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            raise err

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_runner.run(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )
        assert "CONNECT_ERROR" in result.answer
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 0
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_continuation_fail_stores_in_diagnostic(self) -> None:
        """Tool-continuation LLM errors are stored in diagnostic channel only."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=tool_calls,
            ),
            finish_reason="tool_calls",
        )
        err = _make_err(kind="HEARTBEAT_TIMEOUT", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services_required.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_runner.run(
                "http://llm-test",
                workflow_id="wf-test",
                task_id="task-test",
                stage_id="execute",
                attempt_id="att-test",
            )

        assert result.action == "fail"
        assert "HEARTBEAT_TIMEOUT" in result.answer
        ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_timeout_on_first_turn_stores_in_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="READ_TIMEOUT", partial_text="")

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            raise err

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_runner.run(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )
        assert "READ_TIMEOUT" in result.answer
        ctx.diagnostics.save.assert_called_once()


# ── _run_turn: normal completion (is_done=True) ──────────────────────────────


class TestRunTurnNormalCompletion:
    @pytest.mark.asyncio
    async def test_run_turn_returns_content_on_stop(self) -> None:
        # finish_reason="stop" → is_done=True → _finalize_answer() → content を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content="hello world",
                tool_calls=None,
            ),
            finish_reason="stop",
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_runner.run(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.answer == "hello world"
        assistant_msgs = [m for m in ctx.conv.history if m.get("role") == "assistant"]
        assert len(assistant_msgs) == 1

    @pytest.mark.asyncio
    async def test_run_turn_returns_empty_string_on_none_content(self) -> None:
        # content が None の場合は空文字列を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=None,
                tool_calls=None,
            ),
            finish_reason="stop",
        )

        async def _mock_stream(*_args: object, **_kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_runner.run(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.answer == ""


# ── Orchestrator helper unit tests ────────────────────────────────────────────


class TestToolLoopGuardHelpers:
    """Tests for ToolLoopGuard public API (previously tested via Orchestrator delegates)."""

    def test_update_consecutive_errors_increments_when_all_fail(self) -> None:
        result = ToolLoopGuard.update_errors(0, 3, 3)
        assert result == 1

    def test_update_consecutive_errors_maintains_on_partial_failure(self) -> None:
        result = ToolLoopGuard.update_errors(2, 1, 3)
        assert result == 2

    def test_update_consecutive_errors_resets_when_no_errors(self) -> None:
        result = ToolLoopGuard.update_errors(2, 0, 3)
        assert result == 0

    def test_check_consecutive_error_limit_below_max_returns_none(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 3
        orch = _make_orchestrator(ctx)
        assert orch._guard.check_error_limit(2) is None

    def test_check_consecutive_error_limit_at_max_returns_message(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 3
        orch = _make_orchestrator(ctx)
        result = orch._guard.check_error_limit(3)
        assert result is not None
        assert "consecutive" in result

    def test_check_consecutive_error_limit_disabled_returns_none(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 0
        orch = _make_orchestrator(ctx)
        assert orch._guard.check_error_limit(999) is None

    def test_check_all_tool_guards_returns_none_when_no_guards_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 3
        ctx.cfg.tool.tool_cycle_detect_window = 0
        ctx.cfg.tool.tool_error_retry_max = 0
        orch = _make_orchestrator(ctx)
        msg = MagicMock()
        msg.__getitem__ = lambda self, k: [] if k == "tool_calls" else None
        msg.get = lambda k, d=None: [] if k == "tool_calls" else d
        result = orch._guard.check_all({}, [], set(), msg)
        assert result is None

    def test_check_all_tool_guards_returns_on_cycle_guard_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 10
        ctx.cfg.tool.tool_cycle_detect_window = 1  # detect after 1 repeat
        ctx.cfg.tool.tool_error_retry_max = 0
        orch = _make_orchestrator(ctx)
        tool_calls = [{"function": {"name": "my_tool", "arguments": "{}"}}]
        msg: dict = {"role": "assistant", "content": None, "tool_calls": tool_calls}

        fingerprints: list[str] = []
        result1 = orch._guard.check_all({}, fingerprints, set(), msg)
        assert result1 is None
        assert len(fingerprints) == 1

        # Second call with the same message → cycle guard fires
        result2 = orch._guard.check_all({}, fingerprints, set(), msg)
        assert result2 is not None
        assert "cycle" in result2.lower() or "cyclic" in result2.lower()

    def test_check_all_tool_guards_returns_on_dedup_guard_hit(self) -> None:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 1  # fire on first repeat
        ctx.cfg.tool.tool_cycle_detect_window = 0
        ctx.cfg.tool.tool_error_retry_max = 0
        orch = _make_orchestrator(ctx)
        import hashlib

        tool_calls = [{"function": {"name": "my_tool", "arguments": "{}"}}]
        msg: dict = {"role": "assistant", "content": None, "tool_calls": tool_calls}

        key = hashlib.md5(b"my_tool:{}", usedforsecurity=False).hexdigest()
        seen: dict[str, int] = {key: 1}

        result = orch._guard.check_all(seen, [], set(), msg)
        assert result is not None
        assert "repeated" in result.lower() or "duplicate" in result.lower()


# ── approval_pending guard ────────────────────────────────────────────────────


class TestApprovalPendingGuard:
    @pytest.mark.asyncio
    async def test_handle_turn_blocked_when_approval_pending(self) -> None:
        """handle_turn() must call on_error and return without LLM call when approval_pending=True."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = "approval-123"
        orch = _make_orchestrator(ctx, on_error=on_error)

        await orch.handle_turn("do something")

        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert isinstance(err, RuntimeError)
        assert "approval-123" in str(err)
        # LLM must not be called
        ctx.services_required.llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_turn_not_blocked_when_approval_not_pending(self) -> None:
        """handle_turn() must proceed normally when approval_pending=False."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = False
        orch = _make_orchestrator(ctx, on_error=on_error)

        # Patch _process_turn to return a successful result without calling LLM
        with patch.object(
            orch, "_process_turn", new=AsyncMock(return_value=("ok", None, False))
        ):
            await orch.handle_turn("do something")

        # on_error must NOT have been called due to the approval guard
        # (it may be called for other reasons, but not the guard path)
        for call in on_error.call_args_list:
            err = call[0][0]
            assert "Approval is pending" not in str(err)


# ── allowed_tools override ────────────────────────────────────────────────────


class TestAllowedToolsOverride:
    def test_allowed_tools_stored_on_init(self) -> None:
        ctx = _make_ctx()
        orch = Orchestrator(ctx, allowed_tools=["read_text_file"])
        assert orch._allowed_tools == ["read_text_file"]

    def test_allowed_tools_none_by_default(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        assert orch._allowed_tools is None

    @pytest.mark.asyncio
    async def test_allowed_tools_override_applied_during_turn(self) -> None:
        """ctx.cfg.tool.allowed_tools is overridden to the instance list during _process_turn."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        captured: list[list[str]] = []

        async def _capture_allowed(*_: object, **__: object) -> None:
            captured.append(list(ctx.cfg.tool.allowed_tools))

        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        with patch.object(
            orch, "_handle_memory_injection", side_effect=_capture_allowed
        ):
            with patch.object(
                orch._llm_runner,
                "run",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")

        assert captured == [["search_web"]]

    @pytest.mark.asyncio
    async def test_original_allowed_tools_restored_after_turn(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored to its original value after the turn."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["write_file"]
        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        with patch.object(orch, "_handle_memory_injection", AsyncMock()):
            with patch.object(
                orch._llm_runner,
                "run",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")
        assert ctx.cfg.tool.allowed_tools == ["write_file"]

    @pytest.mark.asyncio
    async def test_allowed_tools_none_leaves_config_unchanged(self) -> None:
        """When allowed_tools=None, ctx.cfg.tool.allowed_tools is not touched."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["read_text_file"]
        orch = _make_orchestrator(ctx)  # no allowed_tools override
        with patch.object(orch, "_handle_memory_injection", AsyncMock()):
            with patch.object(
                orch._llm_runner,
                "run",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")
        assert ctx.cfg.tool.allowed_tools == ["read_text_file"]

    @pytest.mark.asyncio
    async def test_original_config_restored_even_on_error(self) -> None:
        """ctx.cfg.tool.allowed_tools is restored even when an exception propagates."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = []
        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        orch._diagnostic_store = MagicMock()

        async def _raise(*_: object, **__: object) -> None:
            raise RuntimeError("unexpected error")

        with patch.object(orch, "_handle_memory_injection", side_effect=_raise):
            with pytest.raises(RuntimeError):
                await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == []


class TestHandleHistoryCompressionPersist:
    """Tests for _handle_history_compression persist behavior."""

    @pytest.mark.asyncio
    async def test_compress_persists_when_compressed(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [
                    {"role": "system", "content": "[Conversation summary]"},
                    {"role": "user", "content": "new"},
                ],
                CompressResult(
                    compressed_count=2, protected_count=0, summary_added=True
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._handle_history_compression()
        ctx.session.replace_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_no_persist_when_noop(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [{"role": "user", "content": "unchanged"}],
                CompressResult(
                    compressed_count=0, protected_count=0, summary_added=False
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._handle_history_compression()
        ctx.session.replace_messages.assert_not_called()

    @pytest.mark.asyncio
    async def test_compress_persists_on_fallback_truncation(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [{"role": "user", "content": "remaining"}],
                CompressResult(
                    compressed_count=3,
                    protected_count=0,
                    summary_added=False,
                    is_fallback=True,
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._handle_history_compression()
        ctx.session.replace_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_filters_ephemeral_and_memory_injected_from_db(
        self,
    ) -> None:
        """replace_messages() must not receive _memory_injected or _ephemeral messages."""
        ctx = _make_ctx()
        kept = {"role": "user", "content": "hello"}
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [
                    kept,
                    {"role": "system", "content": "hint", "_ephemeral": True},
                    {"role": "system", "content": "mem", "_memory_injected": True},
                ],
                CompressResult(
                    compressed_count=1, protected_count=0, summary_added=False
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._handle_history_compression()
        saved = ctx.session.replace_messages.call_args[0][0]
        assert saved == [kept]


class TestInitWorkflowTaskResumeReuse:
    """Tests for Orchestrator._init_workflow_task() resume/reuse behavior."""

    def test_resume_reuses_existing_task_not_creates_duplicate(self) -> None:
        """Resuming a workflow task must call get_task_by_id(), not create_task()."""
        from unittest.mock import MagicMock, patch

        existing_task = MagicMock()
        existing_task.task_id = "existing-task-id"
        existing_task.workflow_id = "existing-wf-id"

        ctx = _make_ctx()
        ctx.turn.pending_approval_task_id = "existing-task-id"

        with (
            patch("agent.orchestrator.get_task_by_id", return_value=existing_task),
            patch("agent.orchestrator.create_task") as mock_create,
            patch("agent.orchestrator.StateStore"),
            patch("agent.orchestrator.audit_workflow_start"),
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            workflow_id, task = orch._init_workflow_task(
                ctx, "test-session", existing_task_id="existing-task-id"
            )
            assert workflow_id == "existing-wf-id"
            assert task.task_id == "existing-task-id"
            mock_create.assert_not_called()

    def test_resume_does_not_call_audit_workflow_start_for_existing_task(self) -> None:
        """When resuming an existing task, audit_workflow_start should NOT be called again."""
        from unittest.mock import MagicMock, patch

        existing_task = MagicMock()
        existing_task.task_id = "existing-task-id"
        existing_task.workflow_id = "existing-wf-id"

        ctx = _make_ctx()

        with (
            patch("agent.orchestrator.get_task_by_id", return_value=existing_task),
            patch("agent.orchestrator.create_task"),
            patch("agent.orchestrator.StateStore"),
            patch("agent.orchestrator.audit_workflow_start") as mock_audit,
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            orch._init_workflow_task(
                ctx, "test-session", existing_task_id="existing-task-id"
            )
            mock_audit.assert_not_called()


class TestEphemeralMessageLifecycle:
    """Regression coverage for requires/20260716_15_require.md /
    plans/20260717-001758_plan.md: _ephemeral (mode-classification hint) and
    _memory_injected (memory snippet) system messages must reach the LLM call
    for the turn they were created in, and be cleared before the *next*
    turn's LLM call -- not stripped by _sync_system_prompt() before the same
    turn's LLM call ever runs.
    """

    def _wire_memory_and_mode(self, ctx: MagicMock) -> None:
        ctx.cfg.mdq_rag_mode = (
            "rag"  # deterministic hint, bypasses classifier heuristics
        )
        ctx.conv.system_prompt_content = ""  # no system-prompt sync noise in this test
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        # LLMTurnRunner.run() requires non-empty workflow context.
        ctx.workflow.workflow_id = "wf-test"
        ctx.workflow.current_task_id = "task-test"
        ctx.turn.current_turn_id = "turn-test"

    @pytest.mark.asyncio
    async def test_ephemeral_and_memory_injected_present_in_same_turn_payload(
        self,
    ) -> None:
        ctx = _make_ctx()
        self._wire_memory_and_mode(ctx)
        orch = _make_orchestrator(ctx)

        seen_payloads: list[list[dict]] = []

        async def _mock_stream(
            _url: str, history: list, _tool_defs: list
        ) -> LLMResponse:
            seen_payloads.append(list(history))
            return LLMResponse(
                message={"role": "assistant", "content": "ok"}, finish_reason="stop"
            )

        ctx.services_required.llm.stream = _mock_stream

        _answer, error_kind, _is_partial = await orch._process_turn(
            "what headings are here?", ctx, 0.0
        )

        assert error_kind is None
        assert len(seen_payloads) == 1
        payload = seen_payloads[0]
        ephemeral_msgs = [m for m in payload if m.get("_ephemeral")]
        memory_msgs = [m for m in payload if m.get("_memory_injected")]
        assert len(ephemeral_msgs) == 1
        assert len(memory_msgs) == 1
        assert "remembered fact" in memory_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_ephemeral_and_memory_injected_not_duplicated_across_turns(
        self,
    ) -> None:
        """Turn 2 gets its own fresh ephemeral/memory-injected messages (the
        memory/mode mocks fire every turn) -- the invariant under test is
        that turn 1's leftovers are cleared first, so turn 2's payload has
        exactly one of each (no accumulation), not turn 1's plus turn 2's.
        """
        ctx = _make_ctx()
        self._wire_memory_and_mode(ctx)
        orch = _make_orchestrator(ctx)

        seen_payloads: list[list[dict]] = []

        async def _mock_stream(
            _url: str, history: list, _tool_defs: list
        ) -> LLMResponse:
            seen_payloads.append(list(history))
            return LLMResponse(
                message={"role": "assistant", "content": "ok"}, finish_reason="stop"
            )

        ctx.services_required.llm.stream = _mock_stream

        await orch._process_turn("what headings are here?", ctx, 0.0)
        await orch._process_turn("second turn", ctx, 0.0)

        assert len(seen_payloads) == 2
        second_payload = seen_payloads[1]
        assert sum(1 for m in second_payload if m.get("_ephemeral")) == 1
        assert sum(1 for m in second_payload if m.get("_memory_injected")) == 1
