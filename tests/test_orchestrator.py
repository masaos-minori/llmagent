"""
tests/test_orchestrator.py
Unit tests for Orchestrator: LLMTransportError handling in handle_turn() and _run_turn().
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.orchestrator import Orchestrator
from agent.tool_loop_guard import ToolLoopGuard
from shared.llm_client import LLMErrorKind, LLMTransportError

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
    # services
    hist_mgr = AsyncMock()
    hist_mgr.stat_compress_count = 0

    async def _compress(h: list) -> list:
        return h

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
    return Orchestrator(ctx, on_error=on_error, on_first_turn=on_first_turn)


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
    async def test_partial_completion_saves_incomplete_message(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        incomplete = [
            m for m in ctx.conv.history if "[INCOMPLETE" in m.get("content", "")
        ]
        assert len(incomplete) == 1
        assert "partial answer" in incomplete[0]["content"]

    @pytest.mark.asyncio
    async def test_partial_completion_increments_stat(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="some output")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        assert ctx.services.llm.stat_partial_completions == 1

    @pytest.mark.asyncio
    async def test_prestream_error_pops_user_message(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        user_msgs = [m for m in ctx.conv.history if m.get("role") == "user"]
        assert len(user_msgs) == 0

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

        with patch.object(orch._llm_runner, "run", AsyncMock(return_value="answer")):
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


# ── _run_turn: tool-continuation LLMTransportError ───────────────────────────


class TestRunTurnLLMTransportError:
    @pytest.mark.asyncio
    async def test_transport_error_on_tool_continuation_injects_synthetic_error(
        self,
    ) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls,
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
        err = _make_err(kind="CONNECT_ERROR", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            result = await orch._llm_runner.run("http://llm-test")

        assert "CONNECT_ERROR" in result
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 1

    @pytest.mark.asyncio
    async def test_transport_error_on_first_turn_injects_synthetic_error(self) -> None:
        # LLMTurnRunner.run() now catches LLMTransportError at turn=0 and injects
        # a synthetic tool-error message instead of re-raising.
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            raise err

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")
        assert "CONNECT_ERROR" in result
        synthetic = [
            m for m in ctx.conv.history if m.get("name") == "llm_transport_error"
        ]
        assert len(synthetic) == 1

    @pytest.mark.asyncio
    async def test_tool_continuation_fail_saves_to_tool_result_store(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        tool_calls = [
            {"id": "tc1", "function": {"name": "test_tool", "arguments": "{}"}}
        ]
        first_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls,
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
        err = _make_err(kind="HEARTBEAT_TIMEOUT", partial_text="")
        call_count = 0

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            raise err

        ctx.services.llm.stream = _mock_stream

        with patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()):
            await orch._llm_runner.run("http://llm-test")

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args.kwargs
        assert call_kwargs["tool_name"] == "llm_transport_error"
        assert call_kwargs["is_error"] is True


# ── _run_turn: normal completion (is_done=True) ──────────────────────────────


class TestRunTurnNormalCompletion:
    @pytest.mark.asyncio
    async def test_run_turn_returns_content_on_stop(self) -> None:
        # finish_reason="stop" → is_done=True → _finalize_answer() → content を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "hello world",
                        "tool_calls": None,
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            return stop_response

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")

        assert result == "hello world"
        assistant_msgs = [m for m in ctx.conv.history if m.get("role") == "assistant"]
        assert len(assistant_msgs) == 1

    @pytest.mark.asyncio
    async def test_run_turn_returns_empty_string_on_none_content(self) -> None:
        # content が None の場合は空文字列を返す
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)

        stop_response = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": None,
                    },
                    "finish_reason": "stop",
                }
            ]
        }

        async def _mock_stream(*_args: object, **_kwargs: object) -> dict:
            return stop_response

        ctx.services.llm.stream = _mock_stream

        result = await orch._llm_runner.run("http://llm-test")

        assert result == ""


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

    def test_update_consecutive_errors_resets_when_any_succeeds(self) -> None:
        result = ToolLoopGuard.update_errors(2, 1, 3)
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
