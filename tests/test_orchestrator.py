"""
tests/test_orchestrator.py
Unit tests for Orchestrator: LLMTransportError handling in handle_turn() and _run_turn().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.history import CompressResult
from agent.orchestrator import Orchestrator
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from shared.llm_client import LLMErrorKind, LLMTransportError
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
    ctx.services.hist_mgr = hist_mgr
    llm_svc = MagicMock()
    llm_svc.stat_partial_completions = 0
    llm_svc.stat_parse_errors = 0
    llm_svc.stat_heartbeat_timeouts = 0
    llm_svc.stat_reconnects = 0
    ctx.services.llm = llm_svc
    ctx.services.audit_logger = None
    ctx.services.memory = None
    ctx.services.tools = None
    return ctx


def _make_orchestrator(ctx: MagicMock, on_error: Any = None) -> Orchestrator:
    on_first_turn = AsyncMock()
    orch = Orchestrator(
        ctx,
        on_error=on_error,
        on_first_turn=on_first_turn,
        workflow_mode="disabled",
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

        assert ctx.services.llm.stat_partial_completions == 1

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
        ctx.services.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)

        with patch.object(
            orch._llm_runner,
            "run",
            AsyncMock(return_value=TurnResult(action="continue", answer="answer")),
        ):
            await orch.handle_turn("hello")

        assert ctx.services.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_audit_logger_turn_end_written_on_partial_error(self) -> None:
        ctx = _make_ctx()
        ctx.services.audit_logger = MagicMock()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services.audit_logger.info.called

    @pytest.mark.asyncio
    async def test_read_timeout_with_partial_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="READ_TIMEOUT", partial_text="chunk text")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services.llm.stat_partial_completions == 1
        call_args = orch._diagnostic_store.save.call_args_list
        assert any("llm_transport_error" in str(a) for a in call_args)

    @pytest.mark.asyncio
    async def test_http_retryable_prestream_saves_mid_turn_diagnostic(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="HTTP_STATUS_RETRYABLE", retryable=True, partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services.llm.stat_partial_completions == 0
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

        assert ctx.services.llm.stat_partial_completions == 0
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

        assert ctx.services.llm.stat_partial_completions == 1
        saved_content = orch._diagnostic_store.save.call_args[0][2]
        assert "[INCOMPLETE: MALFORMED_SSE_FRAME]" in saved_content


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

        ctx.services.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_runner.run("http://llm-test")

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

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")
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

        ctx.services.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_runner.run("http://llm-test")

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

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")
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

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")

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

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")

        assert result.answer == ""


# ── handle_turn: tool_result_store ───────────────────────────────────────────


class TestHandleTurnToolResultStore:
    @pytest.mark.asyncio
    async def test_partial_completion_saves_to_tool_result_store(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args.kwargs
        assert call_kwargs["tool_name"] == "llm_partial_completion"
        assert call_kwargs["is_error"] is True
        assert "INCOMPLETE" in call_kwargs["summary"]

    @pytest.mark.asyncio
    async def test_prestream_error_does_not_save_to_tool_result_store(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        # Pre-stream fail: no partial output, so tool_result_store should NOT be called
        ctx.tool_result_store.store.assert_not_called()


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
        orch = _make_orchestrator(ctx, on_error=on_error)

        await orch.handle_turn("do something")

        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert isinstance(err, RuntimeError)
        assert "/approve" in str(err) or "/reject" in str(err)
        # LLM must not be called
        ctx.services.llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_turn_not_blocked_when_approval_not_pending(self) -> None:
        """handle_turn() must proceed normally when approval_pending=False."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = False
        orch = _make_orchestrator(ctx, on_error=on_error)

        # Patch _process_turn to return a successful result without calling LLM
        with patch.object(
            orch, "_process_turn", new=AsyncMock(return_value=("ok", None))
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

        orch = Orchestrator(ctx, allowed_tools=["search_web"], workflow_mode="disabled")
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
        orch = Orchestrator(ctx, allowed_tools=["search_web"], workflow_mode="disabled")
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
        orch = Orchestrator(ctx, allowed_tools=["search_web"], workflow_mode="disabled")
        orch._diagnostic_store = MagicMock()

        async def _raise(*_: object, **__: object) -> None:
            raise RuntimeError("unexpected error")

        with patch.object(orch, "_handle_memory_injection", side_effect=_raise):
            with pytest.raises(RuntimeError):
                await orch.handle_turn("test")

        assert ctx.cfg.tool.allowed_tools == []


# ── workflow_mode ─────────────────────────────────────────────────────────────


class TestWorkflowMode:
    """Tests for explicit workflow_mode parameter on Orchestrator and AgentConfig."""

    def _ok_run(self) -> AsyncMock:
        return AsyncMock(return_value=TurnResult(action="continue", answer="ok"))

    # -- disabled mode -------------------------------------------------------

    def test_disabled_mode_does_not_load_workflow(self) -> None:
        ctx = _make_ctx()
        with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
            Orchestrator(ctx, workflow_mode="disabled")
        mock_loader.assert_not_called()

    @pytest.mark.asyncio
    async def test_disabled_mode_handle_turn_skips_state_store(self) -> None:
        ctx = _make_ctx()
        orch = Orchestrator(ctx, workflow_mode="disabled")
        with (
            patch("agent.orchestrator.StateStore") as mock_store,
            patch.object(orch._llm_runner, "run", self._ok_run()),
        ):
            await orch.handle_turn("hello")
        mock_store.assert_not_called()

    # -- auto mode (no workflow def) -----------------------------------------

    @pytest.mark.asyncio
    async def test_auto_mode_no_workflow_def_runs_direct(self) -> None:
        ctx = _make_ctx()
        with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("not found")
            orch = Orchestrator(ctx, workflow_mode="auto")
        assert orch._workflow_def is None
        with patch.object(orch._llm_runner, "run", self._ok_run()):
            await orch.handle_turn("hello")  # must not raise

    @pytest.mark.asyncio
    async def test_auto_mode_state_store_failure_raises(self) -> None:
        ctx = _make_ctx()
        mock_wf = MagicMock()
        with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
            mock_loader.return_value.load.return_value = mock_wf
            orch = Orchestrator(ctx, workflow_mode="auto")
        assert orch._workflow_def is mock_wf
        with (
            patch("agent.orchestrator.StateStore", side_effect=RuntimeError("db gone")),
            pytest.raises(RuntimeError, match="db gone"),
        ):
            await orch.handle_turn("hello")

    # -- required mode -------------------------------------------------------

    def test_required_mode_raises_at_construction_when_loader_fails(self) -> None:
        ctx = _make_ctx()
        with (
            patch("agent.orchestrator.WorkflowLoader") as mock_loader,
            pytest.raises(RuntimeError, match="mode=required"),
        ):
            mock_loader.return_value.load.side_effect = Exception("not found")
            Orchestrator(ctx, workflow_mode="required")

    def test_required_mode_raises_on_workflow_load_error(self) -> None:
        from agent.workflow.workflow_loader import WorkflowLoadError

        ctx = _make_ctx()
        with (
            patch("agent.orchestrator.WorkflowLoader") as mock_loader,
            pytest.raises(RuntimeError, match="mode=required"),
        ):
            mock_loader.return_value.load.side_effect = WorkflowLoadError("bad yaml")
            Orchestrator(ctx, workflow_mode="required")

    @pytest.mark.asyncio
    async def test_required_mode_state_store_failure_raises(self) -> None:
        ctx = _make_ctx()
        mock_wf = MagicMock()
        with patch("agent.orchestrator.WorkflowLoader") as mock_loader:
            mock_loader.return_value.load.return_value = mock_wf
            orch = Orchestrator(ctx, workflow_mode="required")
        assert orch._workflow_def is mock_wf
        with (
            patch("agent.orchestrator.StateStore", side_effect=RuntimeError("db gone")),
            pytest.raises(RuntimeError, match="db gone"),
        ):
            await orch.handle_turn("hello")

    # -- AgentConfig validation ----------------------------------------------

    def test_agent_config_accepts_valid_modes(self) -> None:
        from agent.config_dataclasses import AgentConfig

        for mode in ("auto", "required", "disabled"):
            cfg = AgentConfig(workflow_mode=mode)
            assert cfg.workflow_mode == mode

    def test_agent_config_rejects_invalid_mode(self) -> None:
        from agent.config_dataclasses import AgentConfig

        with pytest.raises(ValueError, match="workflow_mode must be one of"):
            AgentConfig(workflow_mode="on")
