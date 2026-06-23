"""
tests/test_llm_turn_runner.py
Direct unit tests for LLMTurnRunner.

Tests the inner LLM streaming + tool-call loop in isolation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.llm_turn_runner import LLMTurnRunner
from shared.llm_client import LLMTransportError
from shared.llm_types import LLMResponse

pytestmark = pytest.mark.asyncio


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.max_tool_turns = 5
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    ctx.cfg.tool.tool_definitions = []
    ctx.conv.history = []
    ctx.stats.stat_tool_errors = 0
    ctx.services.llm = AsyncMock()
    ctx.services.llm.stream = AsyncMock()
    return ctx


def _make_guard() -> MagicMock:
    guard = MagicMock()
    guard.check_all.return_value = None
    guard.check_error_limit.return_value = None
    guard.update_errors.return_value = 0
    return guard


@pytest.fixture
def runner() -> LLMTurnRunner:
    ctx = _make_ctx()
    guard = _make_guard()
    return LLMTurnRunner(ctx, guard)


class TestStreamLlm:
    async def test_returns_response(self, runner: LLMTurnRunner) -> None:
        expected = {"id": "resp_1"}
        runner._ctx.services.llm.stream = AsyncMock(return_value=expected)

        result = await runner._stream_llm("http://llm", 0)

        assert result == expected
        runner._ctx.services.llm.stream.assert_awaited_once()

    async def test_propagates_transport_error(self, runner: LLMTurnRunner) -> None:
        runner._ctx.services.llm.stream = AsyncMock(
            side_effect=LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm"),
        )

        with pytest.raises(LLMTransportError):
            await runner._stream_llm("http://llm", 0)


class TestFinalizeAnswer:

    @pytest.mark.asyncio(False)
    def test_appends_to_history(self, runner: LLMTurnRunner) -> None:
        message: dict[str, Any] = {"role": "assistant", "content": "Hello"}

        result = runner._finalize_answer_text(message)

        assert result == "Hello"
        assert runner._ctx.conv.history == [message]

    @pytest.mark.asyncio(False)
    def test_returns_empty_string_for_no_content(
        self, runner: LLMTurnRunner
    ) -> None:
        message: dict[str, Any] = {"role": "assistant"}

        result = runner._finalize_answer_text(message)

        assert result == ""


class TestHandleLlmError:
    async def test_stores_in_diagnostic_and_returns_fail(
        self, runner: LLMTurnRunner
    ) -> None:
        """Mid-turn LLM error is stored in diagnostic channel; returns fail TurnResult."""
        error = LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm")

        result = await runner._handle_llm_error(error, 0)

        assert result.action == "fail"
        assert "CONNECT_ERROR" in result.answer
        assert result.exception is error
        runner._ctx.diagnostics.save.assert_called_once()


class TestRun:
    async def test_returns_answer_on_stop(self, runner: LLMTurnRunner) -> None:
        stop_response = LLMResponse(
            message={"role": "assistant", "content": "Hello"},
            finish_reason="stop",
        )
        with patch.object(runner, "_stream_llm", AsyncMock(return_value=stop_response)):
            result = await runner.run("http://llm")

        assert result.answer == "Hello"

    async def test_executes_tool_calls_then_returns(
        self, runner: LLMTurnRunner
    ) -> None:
        tool_calls = [{"id": "c1", "function": {"name": "read_file"}}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )
        final_response = LLMResponse(
            message={"role": "assistant", "content": "Done"},
            finish_reason="stop",
        )

        with (
            patch.object(
                runner,
                "_stream_llm",
                AsyncMock(side_effect=[tool_response, final_response]),
            ),
            patch(
                "agent.llm_turn_runner.execute_all_tool_calls",
            ) as mock_exec,
        ):
            result = await runner.run("http://llm")

        assert result.answer == "Done"
        mock_exec.assert_awaited_once()
        assert len(runner._ctx.conv.history) == 2
        assert runner._ctx.conv.history[0]["tool_calls"] is not None

    async def test_handles_transport_error(self, runner: LLMTurnRunner) -> None:
        """LLMTransportError during run() returns fail TurnResult with error detail."""
        err = LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm")
        with patch.object(runner, "_stream_llm", AsyncMock(side_effect=err)):
            result = await runner.run("http://llm")

        assert "CONNECT_ERROR" in result.answer
        assert result.action == "fail"
        runner._ctx.diagnostics.save.assert_called_once()

    async def test_reaches_max_tool_turns(self, runner: LLMTurnRunner) -> None:
        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )

        with (
            patch.object(
                runner,
                "_stream_llm",
                AsyncMock(return_value=tool_response),
            ),
            patch(
                "agent.llm_turn_runner.execute_all_tool_calls",
            ),
        ):
            runner._ctx.cfg.tool.max_tool_turns = 2

            result = await runner.run("http://llm")

        assert "Maximum tool turns reached" in result.answer

    async def test_guard_check_all_blocks(self, runner: LLMTurnRunner) -> None:
        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )

        with patch.object(runner, "_stream_llm", AsyncMock(return_value=tool_response)):
            runner._guard.check_all.return_value = "Blocked by guard"

            result = await runner.run("http://llm")

        assert "Blocked by guard" in result.answer

    async def test_check_error_limit_triggers(self, runner: LLMTurnRunner) -> None:
        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )

        with (
            patch.object(runner, "_stream_llm", AsyncMock(return_value=tool_response)),
            patch(
                "agent.llm_turn_runner.execute_all_tool_calls",
            ),
        ):
            runner._guard.check_all.return_value = None
            runner._guard.check_error_limit.return_value = "Error limit reached"

            result = await runner.run("http://llm")

        assert "Error limit reached" in result.answer
