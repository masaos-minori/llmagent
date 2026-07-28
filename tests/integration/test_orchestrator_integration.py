"""Integration tests for Orchestrator.

Tests that use real components (SQLite in-memory DB, WorkflowEngine) where
possible rather than exclusively mocking everything. These characterize
current behavior before refactoring.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.history import CompressResult
from agent.message_schema import ValidationResult
from agent.orchestrator import Orchestrator
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from shared.llm_exceptions import LLMErrorKind, LLMTransportError
from shared.llm_types import LLMMessage, LLMResponse


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
    ctx.conv.append_message = ConversationState.append_message.__get__(ctx.conv)
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
        patch("agent.orchestrator.WorkflowLoader"),
        patch("agent.orchestrator.StateStore"),
        patch("agent.orchestrator.create_task", return_value=mock_task),
        patch("agent.orchestrator.audit_workflow_start"),
        patch("agent.orchestrator.WorkflowEngine", return_value=mock_engine_instance),
    ):
        yield


def _make_orchestrator(
    ctx: MagicMock, on_error: Any = None, pause_on_critical_failure: bool = False
) -> Orchestrator:
    on_first_turn = AsyncMock()
    orch = Orchestrator(
        ctx,
        on_error=on_error,
        on_first_turn=on_first_turn,
        pause_on_critical_failure=pause_on_critical_failure,
    )
    orch._diagnostic_store = MagicMock()
    ctx.diagnostics = orch._diagnostic_store
    return orch


def _make_err(
    kind: LLMErrorKind = "CONNECT_ERROR",
    partial_text: str = "",
    retryable: bool = False,
    phase: str = "in_stream",
) -> LLMTransportError:
    return LLMTransportError(
        kind=kind,
        phase=phase,
        url="http://llm-test",
        retryable=retryable,
        partial_text=partial_text,
    )


class TestCompleteTurnExecution:
    @pytest.mark.asyncio
    async def test_handle_turn_returns_answer_on_success(self) -> None:
        """handle_turn() returns the answer string when LLM responds normally."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        captured_result: dict[str, Any] = {}

        async def _capture_and_return(*args: object, **kwargs: object) -> TurnResult:
            captured_result["url"] = args[0] if args else kwargs.get("url")
            captured_result["workflow_id"] = kwargs.get("workflow_id")
            captured_result["task_id"] = kwargs.get("task_id")
            captured_result["stage_id"] = kwargs.get("stage_id")
            captured_result["attempt_id"] = kwargs.get("attempt_id")
            return TurnResult(action="continue", answer="hello world")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=_capture_and_return),
        ):
            await orch.handle_turn("hello")

        assert captured_result.get("workflow_id") is not None
        assert captured_result.get("task_id") is not None
        assert captured_result.get("stage_id") == "execute"
        assert captured_result.get("workflow_id") is not None
        assert captured_result.get("task_id") is not None
        assert captured_result.get("stage_id") == "execute"

    @pytest.mark.asyncio
    async def test_handle_turn_saves_assistant_message_on_success(self) -> None:
        """Successful turns save assistant messages via session.save()."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="response")),
        ):
            await orch.handle_turn("question")

        ctx.session.save.assert_called_with("assistant", "response")

    @pytest.mark.asyncio
    async def test_handle_turn_appends_user_message_to_history(self) -> None:
        """User messages are appended to conversation history."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            await orch.handle_turn("user question")

        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["content"] == "user question"

    @pytest.mark.asyncio
    async def test_handle_turn_preserves_existing_messages(self) -> None:
        """Existing conversation history is preserved across turns."""
        ctx = _make_ctx()
        ctx.conv.history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "first reply"},
        ]
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(
                return_value=TurnResult(action="continue", answer="second reply")
            ),
        ):
            await orch.handle_turn("second")

        assert len(ctx.conv.history) >= 5
        assert ctx.conv.history[0]["role"] == "system"
        assert ctx.conv.history[1]["content"] == "first"
        assert ctx.conv.history[2]["content"] == "first reply"
        assert any(m.get("content") == "second" for m in ctx.conv.history)

    @pytest.mark.asyncio
    async def test_handle_turn_increments_turn_counter(self) -> None:
        """Each turn increments stat_turns."""
        ctx = _make_ctx()
        ctx.stats.stat_turns = 0
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            await orch.handle_turn("test")

        assert ctx.stats.stat_turns >= 1

    @pytest.mark.asyncio
    async def test_handle_turn_records_latency_on_success(self) -> None:
        """Successful turns record latency in stats."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            await orch.handle_turn("test")

        assert ctx.stats.stat_latency is not None

    @pytest.mark.asyncio
    async def test_handle_turn_records_latency_on_error(self) -> None:
        """Failed turns also record latency in stats."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("test")

        assert ctx.stats.stat_latency is not None

    @pytest.mark.asyncio
    async def test_handle_turn_stores_diagnostic_on_transport_error(self) -> None:
        """LLM transport errors store diagnostics via diagnostic_store.save()."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("test")

        orch._diagnostic_store.save.assert_called_once()
        call_args = orch._diagnostic_store.save.call_args[0]
        assert call_args[1] == "mid_turn_error"

    @pytest.mark.asyncio
    async def test_handle_turn_does_not_save_assistant_on_transport_error(self) -> None:
        """Transport errors must NOT save assistant messages."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("test")

        assistant_saves = [
            call
            for call in ctx.session.save.call_args_list
            if call[0][0] == "assistant"
        ]
        assert len(assistant_saves) == 0

    @pytest.mark.asyncio
    async def test_handle_turn_calls_on_error_callback_for_transport_error(
        self,
    ) -> None:
        """on_error callback is invoked for LLM transport errors."""
        on_error = MagicMock()
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx, on_error=on_error)
        err = _make_err(kind="HTTP_500", partial_text="")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("test")

        on_error.assert_called_once_with(err)

    @pytest.mark.asyncio
    async def test_handle_turn_audit_logger_written_on_success(self) -> None:
        """Audit logger writes turn_end event on successful turn completion."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="answer")),
        ):
            await orch.handle_turn("hello")

        ctx.services_required.audit_logger.info.assert_called()
        call_arg = ctx.services_required.audit_logger.info.call_args[0][0]
        event = json.loads(call_arg)
        assert event.get("event") == "turn_end"
        assert event.get("partial_completion") is False

    @pytest.mark.asyncio
    async def test_handle_turn_audit_logger_partial_completion_true(self) -> None:
        """Audit logger partial_completion=True when LLM error has partial text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("hello")

        event = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert event.get("partial_completion") is True

    @pytest.mark.asyncio
    async def test_handle_turn_audit_logger_partial_completion_false(self) -> None:
        """Audit logger partial_completion=False when LLM error has no partial text."""
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(side_effect=err),
        ):
            await orch.handle_turn("hello")

        event = json.loads(ctx.services_required.audit_logger.info.call_args[0][0])
        assert event.get("partial_completion") is False

    @pytest.mark.asyncio
    async def test_handle_turn_rejects_when_approval_pending(self) -> None:
        """handle_turn rejects immediately when approval_pending=True."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = "approval-123"
        orch = _make_orchestrator(ctx, on_error=on_error)

        with patch.object(orch._llm_runner, "run", AsyncMock()):
            await orch.handle_turn("do something")

        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert isinstance(err, RuntimeError)
        assert "approval-123" in str(err)

    @pytest.mark.asyncio
    async def test_handle_turn_allowed_tools_override_applied(self) -> None:
        """allowed_tools override replaces config value during the turn."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["write_file"]
        captured: list[list[str]] = []

        async def _capture_allowed(*_: object, **__: object) -> None:
            captured.append(list(ctx.cfg.tool.allowed_tools))

        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        orch._diagnostic_store = MagicMock()
        ctx.diagnostics = orch._diagnostic_store

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
    async def test_handle_turn_original_config_restored_after_turn(self) -> None:
        """Config values modified by allowed_tools override are restored after the turn."""
        ctx = _make_ctx()
        ctx.cfg.tool.allowed_tools = ["write_file"]
        orch = Orchestrator(ctx, allowed_tools=["search_web"])
        orch._diagnostic_store = MagicMock()
        ctx.diagnostics = orch._diagnostic_store

        with patch.object(orch, "_handle_memory_injection", AsyncMock()):
            with patch.object(
                orch._llm_runner,
                "run",
                AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
            ):
                await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == ["write_file"]

    @pytest.mark.asyncio
    async def test_handle_turn_history_compression_persists_when_needed(self) -> None:
        """History compression persists new messages to session.replace_messages()."""
        ctx = _make_ctx()
        ctx.services_required.hist_mgr.compress = AsyncMock(
            return_value=(
                [{"role": "user", "content": "compressed"}],
                CompressResult(
                    compressed_count=2, protected_count=0, summary_added=True
                ),
            )
        )
        orch = Orchestrator(ctx)
        await orch._handle_history_compression()
        ctx.session.replace_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_turn_history_compression_noop_when_unnecessary(self) -> None:
        """No-op compression does not call replace_messages."""
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


class TestToolCallFlow:
    @pytest.mark.asyncio
    async def test_tool_continuation_executes_tools_and_continues_loop(self) -> None:
        """A tool-calling response triggers execute_all_tool_calls and continues the loop."""
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
        second_response = LLMResponse(
            message=LLMMessage(role="assistant", content="done"),
            finish_reason="stop",
        )
        call_count = 0

        async def _mock_stream(*args: object, **kwargs: object) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            return first_response if call_count == 1 else second_response

        ctx.services_required.llm.stream = _mock_stream

        captured_tool_calls: list[list[dict]] = []

        async def _capture_execute(
            _ctx: object, tcs: list[dict], *args: object, **__kw: object
        ) -> None:
            captured_tool_calls.append(tcs)

        with patch("agent.llm_turn_runner.execute_all_tool_calls", _capture_execute):
            await orch._llm_runner.run(
                "http://llm-test",
                workflow_id="wf-test",
                task_id="task-test",
                stage_id="execute",
                attempt_id="att-test",
            )

        assert len(captured_tool_calls) >= 1
        assert any(
            tc.get("function", {}).get("name") == "test_tool"
            for tc in captured_tool_calls[0]
        )

    @pytest.mark.asyncio
    async def test_tool_call_result_saved_as_assistant_message(self) -> None:
        """Tool results are saved as assistant messages via session.save()."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(role="assistant", content="tool result"),
            finish_reason="stop",
        )

        async def _mock_stream(*args: object, **kwargs: object) -> LLMResponse:
            return stop_response

        ctx.services_required.llm.stream = _mock_stream

        result = await orch._llm_runner.run(
            "http://llm-test",
            workflow_id="wf-test",
            task_id="task-test",
            stage_id="execute",
            attempt_id="att-test",
        )

        assert result.answer == "tool result"
        assistant_msgs = [m for m in ctx.conv.history if m.get("role") == "assistant"]
        assert len(assistant_msgs) == 1

    @pytest.mark.asyncio
    async def test_tool_call_cycle_detection_fires(self) -> None:
        """Repeated identical tool calls trigger cycle detection guard."""
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 10
        ctx.cfg.tool.tool_cycle_detect_window = 1
        ctx.cfg.tool.tool_error_retry_max = 0
        orch = _make_orchestrator(ctx)

        tool_calls = [{"function": {"name": "my_tool", "arguments": "{}"}}]
        msg: dict = {"role": "assistant", "content": None, "tool_calls": tool_calls}

        fingerprints: list[str] = []
        result1 = orch._guard.check_all({}, fingerprints, set(), msg)
        assert result1 is None
        assert len(fingerprints) == 1

        result2 = orch._guard.check_all({}, fingerprints, set(), msg)
        assert result2 is not None
        assert "cycle" in result2.lower() or "cyclic" in result2.lower()

    @pytest.mark.asyncio
    async def test_tool_call_dedup_guard_fires_on_repeat(self) -> None:
        """Dedup guard fires when same tool call exceeds max_repeats."""
        ctx = _make_ctx()
        ctx.cfg.tool.tool_dedup_max_repeats = 1
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

    @pytest.mark.asyncio
    async def test_tool_call_consecutive_error_limit_fires(self) -> None:
        """Consecutive error limit fires when all tool calls fail."""
        ctx = _make_ctx()
        ctx.cfg.tool.tool_error_max_consecutive = 3
        orch = _make_orchestrator(ctx)

        result = orch._guard.check_error_limit(3)
        assert result is not None
        assert "consecutive" in result

    @pytest.mark.asyncio
    async def test_tool_call_consecutive_error_reset_on_partial_success(self) -> None:
        """Consecutive error counter resets when at least one tool succeeds."""
        result = ToolLoopGuard.update_errors(2, 1, 3)
        assert result == 2

    @pytest.mark.asyncio
    async def test_tool_call_consecutive_error_reset_on_no_errors(self) -> None:
        """Consecutive error counter resets when no errors occur."""
        result = ToolLoopGuard.update_errors(2, 0, 3)
        assert result == 0

    @pytest.mark.asyncio
    async def test_tool_call_normal_completion_returns_content(self) -> None:
        """Normal completion (is_done=True) returns content from the final response."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(role="assistant", content="hello world"),
            finish_reason="stop",
        )

        async def _mock_stream(*args: object, **kwargs: object) -> LLMResponse:
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

    @pytest.mark.asyncio
    async def test_tool_call_none_content_returns_empty_string(self) -> None:
        """When content is None on stop, empty string is returned."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = LLMResponse(
            message=LLMMessage(role="assistant", content=None),
            finish_reason="stop",
        )

        async def _mock_stream(*args: object, **kwargs: object) -> LLMResponse:
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

    @pytest.mark.asyncio
    async def test_tool_call_ephemeral_and_memory_injected_in_same_payload(
        self,
    ) -> None:
        """Ephemeral mode hint and memory-injected snippets appear together in the LLM payload."""
        ctx = _make_ctx()
        ctx.cfg.mdq_rag_mode = "rag"
        ctx.conv.system_prompt_content = ""
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        ctx.workflow.workflow_id = "wf-test"
        ctx.workflow.current_task_id = "task-test"
        ctx.turn.current_turn_id = "turn-test"
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
    async def test_tool_call_ephemeral_not_duplicated_across_turns(self) -> None:
        """Turn 2 gets fresh ephemeral/memory-injected messages; no accumulation."""
        ctx = _make_ctx()
        ctx.cfg.mdq_rag_mode = "rag"
        ctx.conv.system_prompt_content = ""
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        ctx.workflow.workflow_id = "wf-test"
        ctx.workflow.current_task_id = "task-test"
        ctx.turn.current_turn_id = "turn-test"
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

        await orch._process_turn("first turn", ctx, 0.0)
        await orch._process_turn("second turn", ctx, 0.0)

        assert len(seen_payloads) == 2
        second_payload = seen_payloads[1]
        assert sum(1 for m in second_payload if m.get("_ephemeral")) == 1
        assert sum(1 for m in second_payload if m.get("_memory_injected")) == 1


class TestApprovalWorkflowWithRealDB:
    @pytest.mark.asyncio
    async def test_handle_turn_blocked_when_approval_pending(self) -> None:
        """handle_turn must reject immediately when approval_pending=True."""
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

    @pytest.mark.asyncio
    async def test_handle_turn_not_blocked_when_approval_not_pending(self) -> None:
        """handle_turn proceeds normally when approval_pending=False."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = False
        orch = _make_orchestrator(ctx, on_error=on_error)

        with patch.object(
            orch, "_process_turn", new=AsyncMock(return_value=("ok", None, False))
        ):
            await orch.handle_turn("do something")

        for call in on_error.call_args_list:
            err = call[0][0]
            assert "Approval is pending" not in str(err)

    @pytest.mark.asyncio
    async def test_resume_reuses_existing_workflow_task(self) -> None:
        """Resuming a workflow task must call get_task_by_id(), not create_task()."""
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

    @pytest.mark.asyncio
    async def test_resume_does_not_audit_for_existing_task(self) -> None:
        """audit_workflow_start should NOT be called again for resuming tasks."""
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

    @pytest.mark.asyncio
    async def test_resume_rejects_halted_task(self) -> None:
        """A halted task must not be silently resumed."""
        halted_task = MagicMock()
        halted_task.task_id = "halted-task-id"
        halted_task.workflow_id = "halted-wf-id"
        halted_task.status = "halted"

        ctx = _make_ctx()

        with (
            patch("agent.orchestrator.get_task_by_id", return_value=halted_task),
            patch("agent.orchestrator.create_task") as mock_create,
            patch("agent.orchestrator.StateStore"),
            patch("agent.orchestrator.audit_workflow_start"),
        ):
            orch = Orchestrator(ctx)
            orch._workflow_def = MagicMock(version="test-v1")
            with pytest.raises(RuntimeError, match="halted"):
                orch._init_workflow_task(
                    ctx, "test-session", existing_task_id="halted-task-id"
                )
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_turn_invokes_workflow_engine_run(self) -> None:
        """handle_turn always drives execution through WorkflowEngine.run()."""
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        captured_calls: list[int] = []

        async def _engine_run(task, plan_fn, execute_fn, verify_fn):
            await plan_fn()
            await execute_fn()
            await verify_fn()
            captured_calls.append(len(captured_calls) + 1)

        mock_engine_instance = MagicMock()
        mock_engine_instance.run = AsyncMock(side_effect=_engine_run)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
        ):
            with patch(
                "agent.orchestrator.WorkflowEngine", return_value=mock_engine_instance
            ):
                await orch.handle_turn("hello")

        assert len(captured_calls) >= 1
        mock_engine_instance.run.assert_called()

    @pytest.mark.asyncio
    async def test_validate_message_appends_unchanged_via_append_message(self) -> None:
        """Memory injection appends via ConversationState.append_message."""
        ctx = _make_ctx()
        memory = AsyncMock()
        snippet = MagicMock()
        snippet.text = "remembered fact"
        memory.on_user_prompt = AsyncMock(return_value=[snippet])
        ctx.services_required.memory = memory
        orch = _make_orchestrator(ctx)

        await orch._handle_memory_injection("what headings are here?")

        assert len(ctx.conv.history) == 1
        msg = ctx.conv.history[0]
        assert msg["role"] == "system"
        assert msg["_memory_injected"] is True
        assert "remembered fact" in msg["content"]

    @pytest.mark.asyncio
    async def test_append_user_message_appends_unchanged_via_append_message(
        self,
    ) -> None:
        """User message appended via ConversationState.append_message."""
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = ""
        orch = _make_orchestrator(ctx)

        orch._append_user_message("hello there")

        assert ctx.conv.history == [{"role": "user", "content": "hello there"}]

    @pytest.mark.asyncio
    async def test_sync_system_prompt_insert_branch_inserts_unchanged(self) -> None:
        """System prompt insert branch inserts unchanged via append_message."""
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = "You are a helpful assistant."
        ctx.conv.history = [{"role": "user", "content": "hi"}]
        orch = _make_orchestrator(ctx)

        orch._sync_system_prompt()

        assert ctx.conv.history[0] == {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
        assert ctx.conv.history[1] == {"role": "user", "content": "hi"}

    @pytest.mark.asyncio
    async def test_sync_system_prompt_insert_branch_drops_on_validation_failure(
        self,
    ) -> None:
        """If validate_message() rejects the constructed system message, skip the insert."""
        ctx = _make_ctx()
        ctx.conv.system_prompt_content = "You are a helpful assistant."
        ctx.conv.history = [{"role": "user", "content": "hi"}]
        orch = _make_orchestrator(ctx)

        with patch(
            "agent.orchestrator.validate_message",
            return_value=ValidationResult(False, "forced failure"),
        ):
            orch._sync_system_prompt()

        assert ctx.conv.history == [{"role": "user", "content": "hi"}]
