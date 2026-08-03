"""
tests/test_llm_turn_runner.py
Direct unit tests for LLMTurnRunner.

Tests the inner LLM streaming + tool-call loop in isolation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.llm_turn_runner import LLMTurnRunner
from shared.llm_exceptions import LLMTransportError
from shared.llm_types import LLMResponse
from shared.types import LLMMessage


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.max_tool_turns = 5
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    ctx.cfg.tool.tool_definitions = []
    ctx.conv.history = []
    # Bind the real ConversationState.append_message so calls made through
    # ctx.conv.append_message(...) actually mutate ctx.conv.history (with the
    # same validation/sanitization behavior as production), instead of being
    # swallowed as a no-op MagicMock call.
    ctx.conv.append_message = ConversationState.append_message.__get__(ctx.conv)
    ctx.stats.stat_tool_errors = 0
    ctx.services_required.llm = AsyncMock()
    ctx.services_required.llm.stream = AsyncMock()
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
    @pytest.mark.asyncio
    async def test_returns_response(self, runner: LLMTurnRunner) -> None:
        expected = {"id": "resp_1"}
        runner._ctx.services_required.llm.stream = AsyncMock(return_value=expected)

        result = await runner._stream_llm("http://llm", 0)

        assert result == expected
        runner._ctx.services_required.llm.stream.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_propagates_transport_error(self, runner: LLMTurnRunner) -> None:
        runner._ctx.services_required.llm.stream = AsyncMock(
            side_effect=LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm"),
        )

        with pytest.raises(LLMTransportError):
            await runner._stream_llm("http://llm", 0)


class TestStreamLlmFinalAnswer:
    @pytest.mark.asyncio
    async def test_streams_without_tool_defs(self, runner: LLMTurnRunner) -> None:
        expected = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )
        runner._ctx.services_required.llm.stream = AsyncMock(return_value=expected)

        response = await runner._stream_llm_final_answer()

        assert response == expected
        runner._ctx.services_required.llm.stream.assert_awaited_once_with(
            runner.llm_url,
            runner._ctx.conv.history,
            [],
        )

    @pytest.mark.asyncio
    async def test_propagates_transport_error(self, runner: LLMTurnRunner) -> None:
        err = LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm")
        runner._ctx.services_required.llm.stream = AsyncMock(side_effect=err)

        with pytest.raises(LLMTransportError):
            await runner._stream_llm_final_answer()


class TestFinalizeAfterGuard:
    @pytest.mark.asyncio
    async def test_success_returns_continue_with_answer(
        self, runner: LLMTurnRunner
    ) -> None:
        final_response = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )
        runner._guard.check_all.return_value = "Blocked by guard"

        with patch.object(
            runner, "_stream_llm_final_answer", AsyncMock(return_value=final_response)
        ):
            result = await runner._finalize_after_guard()

        assert result.action == "continue"
        assert result.answer == "Final answer"
        assert result.reason != "tool_loop_guard"

    @pytest.mark.asyncio
    async def test_fails_when_llm_returns_tool_calls(
        self, runner: LLMTurnRunner
    ) -> None:
        final_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
            finish_reason="tool_calls",
        )
        runner.llm_url = "http://llm"

        with patch.object(
            runner, "_stream_llm_final_answer", AsyncMock(return_value=final_response)
        ):
            result = await runner._finalize_after_guard()

        assert result.action == "fail"
        assert result.reason == "tool_loop_guard"

    @pytest.mark.asyncio
    async def test_fails_when_validation_fails(self, runner: LLMTurnRunner) -> None:
        def _mock_validate(msg: dict) -> MagicMock:
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.reason = "Validation failed"
            return mock_result

        runner.llm_url = "http://llm"

        with patch("agent.message_schema.validate_message", side_effect=_mock_validate):
            result = await runner._finalize_after_guard()

        assert result.action == "fail"
        assert result.reason == "tool_loop_guard"

    @pytest.mark.asyncio
    async def test_ephemeral_message_injected_on_success(
        self, runner: LLMTurnRunner
    ) -> None:
        final_response = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )
        runner.llm_url = "http://llm"

        with patch.object(
            runner, "_stream_llm_final_answer", AsyncMock(return_value=final_response)
        ):
            await runner._finalize_after_guard()

        ephemeral_msgs = [
            m for m in runner._ctx.conv.history if m.get("_ephemeral") is True
        ]
        assert len(ephemeral_msgs) == 1
        assert ephemeral_msgs[0]["source"] == "loop_guard"

    @pytest.mark.asyncio
    async def test_history_not_modified_before_guard_check(
        self, runner: LLMTurnRunner
    ) -> None:
        """History must not be modified before the guard check in run()."""
        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )
        final_response = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )

        history_len_before = len(runner._ctx.conv.history)

        with (
            patch.object(runner, "_stream_llm", AsyncMock(return_value=tool_response)),
            patch.object(
                runner,
                "_stream_llm_final_answer",
                AsyncMock(return_value=final_response),
            ),
        ):
            runner._guard.check_all.return_value = "Blocked by guard"
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "continue"
        assert "Final answer" in result.answer
        assert (
            len(runner._ctx.conv.history) == history_len_before + 2
        )  # ephemeral msg + final answer message added


class TestFinalizeAnswer:
    def test_appends_to_history(self, runner: LLMTurnRunner) -> None:
        message: dict[str, Any] = {"role": "assistant", "content": "Hello"}

        result = runner._finalize_answer_text(message)

        assert result == "Hello"
        assert runner._ctx.conv.history == [message]

    def test_returns_empty_string_for_no_content(self, runner: LLMTurnRunner) -> None:
        message: dict[str, Any] = {"role": "assistant"}

        result = runner._finalize_answer_text(message)

        assert result == ""


class TestHandleLlmError:
    @pytest.mark.asyncio
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


WF_CTX = dict(
    workflow_id="wf-test-1",
    task_id="task-test-1",
    stage_id="execute",
    attempt_id="att-test-1",
)


class TestRun:
    @pytest.mark.asyncio
    async def test_returns_answer_on_stop(self, runner: LLMTurnRunner) -> None:
        stop_response = LLMResponse(
            message={"role": "assistant", "content": "Hello"},
            finish_reason="stop",
        )
        with patch.object(runner, "_stream_llm", AsyncMock(return_value=stop_response)):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.answer == "Hello"

    @pytest.mark.asyncio
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
            result = await runner.run("http://llm", **WF_CTX)

        assert result.answer == "Done"
        mock_exec.assert_awaited_once()
        assert len(runner._ctx.conv.history) == 2
        assert runner._ctx.conv.history[0]["tool_calls"] is not None

    @pytest.mark.asyncio
    async def test_handles_transport_error(self, runner: LLMTurnRunner) -> None:
        """LLMTransportError during run() returns fail TurnResult with error detail."""
        err = LLMTransportError("CONNECT_ERROR", "pre_stream", "http://llm")
        with patch.object(runner, "_stream_llm", AsyncMock(side_effect=err)):
            result = await runner.run("http://llm", **WF_CTX)

        assert "CONNECT_ERROR" in result.answer
        assert result.action == "fail"
        runner._ctx.diagnostics.save.assert_called_once()
        assert result.persist_as_assistant is False

    @pytest.mark.asyncio
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

            result = await runner.run("http://llm", **WF_CTX)

        assert "Maximum tool turns reached" in result.answer

    @pytest.mark.asyncio
    async def test_guard_check_all_blocks(self, runner: LLMTurnRunner) -> None:
        tool_calls = [{"id": "c1"}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )
        final_response = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )

        with (
            patch.object(runner, "_stream_llm", AsyncMock(return_value=tool_response)),
            patch.object(
                runner,
                "_stream_llm_final_answer",
                AsyncMock(return_value=final_response),
            ),
        ):
            runner._guard.check_all.return_value = "Blocked by guard"

            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "continue"
        assert "Final answer" in result.answer

    @pytest.mark.asyncio
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

            result = await runner.run("http://llm", **WF_CTX)

        assert "Error limit reached" in result.answer

    @pytest.mark.asyncio
    async def test_mid_turn_transport_error_not_persisted_as_assistant(
        self, runner: LLMTurnRunner
    ) -> None:
        """Mid-turn LLM transport error must not be persisted as assistant message."""
        tool_calls = [{"id": "c1", "function": {"name": "read_file"}}]
        tool_response = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": tool_calls},
            finish_reason="tool_calls",
        )

        with (
            patch.object(
                runner,
                "_stream_llm",
                AsyncMock(
                    side_effect=[
                        tool_response,
                        LLMTransportError("CONNECT_ERROR", "in_stream", "http://llm"),
                    ]
                ),
            ),
            patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "fail"
        assert result.persist_as_assistant is False
        runner._ctx.diagnostics.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_raises_without_workflow_context(
        self, runner: LLMTurnRunner
    ) -> None:
        """run() must raise RuntimeError when workflow context params are empty."""
        with pytest.raises(RuntimeError, match="requires non-empty workflow context"):
            await runner.run(
                "http://llm",
                workflow_id="",
                task_id="task-test-1",
                stage_id="execute",
                attempt_id="att-test-1",
            )


class TestHistoryConstructionRoutedThroughAppendMessage:
    """Regression coverage for plans/20260726-093008_plan.md: the two
    history-construction call sites in llm_turn_runner.py -- the tool-call
    branch in run()'s main loop and _finalize_answer_text() -- route through
    ConversationState.append_message() instead of raw
    ctx.conv.history.append() calls, and produce the same message content as
    before for well-formed input.
    """

    def test_finalize_answer_text_appends_unchanged_via_append_message(
        self, runner: LLMTurnRunner
    ) -> None:
        message: LLMMessage = {"role": "assistant", "content": "Done"}

        result = runner._finalize_answer_text(message)

        assert result == "Done"
        assert runner._ctx.conv.history == [message]

    @pytest.mark.asyncio
    async def test_tool_call_branch_appends_unchanged_via_append_message(
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
            patch("agent.llm_turn_runner.execute_all_tool_calls"),
        ):
            await runner.run("http://llm", **WF_CTX)

        assert runner._ctx.conv.history[0] == {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }
