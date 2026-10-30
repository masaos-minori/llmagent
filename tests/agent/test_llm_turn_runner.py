"""
tests/test_llm_turn_runner.py
Direct unit tests for LLMTurnRunner.

Tests the inner LLM streaming + tool-call loop in isolation.
"""

from __future__ import annotations

import sqlite3
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.llm_turn_runner import LLMTurnRunner
from agent.session import AgentSession
from agent.session_message_repo import SessionMessageRepository
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_persistence import ConversationPersistenceError
from shared.llm_exceptions import LLMTransportError
from shared.llm_types import LLMResponse
from shared.mcp_health import McpServerHealthState
from shared.token_estimation import RATIO_TEXT, estimate_tokens
from shared.transport_dto import DynamicAvailabilityHint, ToolCallResult
from shared.types import LLMMessage


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.tool.max_tool_turns = 5
    ctx.cfg.tool.tool_dedup_max_repeats = 3
    ctx.cfg.tool.tool_error_retry_max = 0
    ctx.cfg.tool.tool_cycle_detect_window = 0
    ctx.cfg.tool.tool_error_max_consecutive = 3
    ctx.cfg.tool.tool_definitions = []
    ctx.conv = ConversationState()
    ctx.stats.stat_tool_errors = 0
    ctx.services_required.llm = AsyncMock()
    ctx.services_required.llm.stream = AsyncMock()
    # Per-round assistant persist routes through the turn's atomic boundary (SEQ-07);
    # expose an awaitable handle so runner.run()'s tool-call path resolves it.
    ctx.turn.persistence_boundary = _persistence_boundary_mock()
    return ctx


def _persistence_boundary_mock() -> MagicMock:
    """A stand-in TurnPersistence with awaitable write methods.

    Lets LLMTurnRunner route its per-round assistant persist (SEQ-07) and
    complete_round its round persist (SEQ-08) through
    ``ctx.turn.persistence_boundary`` without a real session/DB.
    """
    boundary = MagicMock()
    boundary.save = AsyncMock(return_value=None)
    boundary.save_many = AsyncMock(return_value=None)
    boundary.save_phase_grouped = AsyncMock(return_value=None)
    boundary.replace_messages = AsyncMock(return_value=None)
    return boundary


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
        runner.llm_url = "http://llm"

        response = await runner._stream_llm_final_answer()

        assert response == expected
        runner._ctx.services_required.llm.stream.assert_awaited_once_with(
            runner.llm_url,
            runner._ctx.conv.history,
            [],
        )

    @pytest.mark.asyncio
    async def test_streams_final_answer_to_configured_url(
        self,
        runner: LLMTurnRunner,
    ) -> None:
        runner.llm_url = "http://llm"
        expected = LLMResponse(
            message={"role": "assistant", "content": "Final answer"},
            finish_reason="stop",
        )
        runner._ctx.services_required.llm.stream = AsyncMock(return_value=expected)

        response = await runner._stream_llm_final_answer()

        assert response == expected
        runner._ctx.services_required.llm.stream.assert_awaited_once_with(
            "http://llm",
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

        with patch(  # mock-patch-ok: _finalize_after_guard imports validate_message inside the function
            "agent.message_schema.validate_message", side_effect=_mock_validate
        ):
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
    @pytest.mark.asyncio
    async def test_appends_to_history(self, runner: LLMTurnRunner) -> None:
        message: dict[str, Any] = {"role": "assistant", "content": "Hello"}

        result = await runner._finalize_answer_text(message)

        assert result == "Hello"
        assert runner._ctx.conv.history == [message]

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_no_content(
        self, runner: LLMTurnRunner
    ) -> None:
        message: dict[str, Any] = {"role": "assistant"}

        result = await runner._finalize_answer_text(message)

        assert result == ""


class TestStreamLlmToolDefs:
    """REQ-008: _filter_disabled_tool_definitions() (a confirmed self-referential
    no-op second-stage filter) was removed; _stream_llm() now inlines the one part
    of it that was actually live — the registry-is-None fallback to
    ctx.cfg.tool.tool_definitions. These cases assert on the tool_defs argument
    _stream_llm() passes to llm.stream(), rather than calling the removed method
    directly."""

    @pytest.mark.asyncio
    async def test_registry_not_none_returns_from_registry(
        self, runner: LLMTurnRunner
    ) -> None:
        """When registry exists, _stream_llm uses registry.llm_tool_definitions()."""
        mock_registry = MagicMock()
        mock_registry.llm_tool_definitions.return_value = [
            {"name": "tool_a", "description": "desc_a", "parameters": {}},
            {"name": "tool_b", "description": "desc_b", "parameters": {}},
        ]
        runner._ctx.services_required.runtime_tools = mock_registry

        await runner._stream_llm("http://llm", 0)

        tool_defs = runner._ctx.services_required.llm.stream.call_args.args[2]
        assert len(tool_defs) == 2
        assert tool_defs[0]["name"] == "tool_a"
        assert tool_defs[1]["name"] == "tool_b"
        mock_registry.llm_tool_definitions.assert_called_once()

    @pytest.mark.asyncio
    async def test_registry_not_none_includes_live_registered_tool_absent_from_static_config(
        self, runner: LLMTurnRunner
    ) -> None:
        """Regression: tool present in RuntimeToolRegistry but absent from
        ctx.cfg.tool.tool_definitions is still offered to the LLM."""
        mock_registry = MagicMock()
        live_tool_def = {
            "name": "live_tool",
            "description": "discovered at runtime",
            "parameters": {},
        }
        mock_registry.llm_tool_definitions.return_value = [live_tool_def]
        runner._ctx.services_required.runtime_tools = mock_registry
        # Explicitly ensure the static config does NOT contain the live tool
        runner._ctx.cfg.tool.tool_definitions = []

        await runner._stream_llm("http://llm", 0)

        tool_defs = runner._ctx.services_required.llm.stream.call_args.args[2]
        assert len(tool_defs) == 1
        assert tool_defs[0]["name"] == "live_tool"

    @pytest.mark.asyncio
    async def test_registry_is_none_falls_back_to_static_config(
        self, runner: LLMTurnRunner
    ) -> None:
        """When registry is None, _stream_llm falls back to ctx.cfg.tool.tool_definitions."""
        runner._ctx.services_required.runtime_tools = None
        static_tools = [{"name": "static_tool", "function": {"name": "static_tool"}}]
        runner._ctx.cfg.tool.tool_definitions = static_tools

        await runner._stream_llm("http://llm", 0)

        tool_defs = runner._ctx.services_required.llm.stream.call_args.args[2]
        assert len(tool_defs) == 1
        assert tool_defs[0]["name"] == "static_tool"

    @pytest.mark.asyncio
    async def test_registry_not_none_correct_shape(self, runner: LLMTurnRunner) -> None:
        """tool_defs entries carry name/description/parameters keys, unmodified
        from registry.llm_tool_definitions()'s own shape."""
        mock_registry = MagicMock()
        mock_registry.llm_tool_definitions.return_value = [
            {"name": "t1", "description": "d1", "parameters": {"type": "object"}},
        ]
        runner._ctx.services_required.runtime_tools = mock_registry

        await runner._stream_llm("http://llm", 0)

        tool_defs = runner._ctx.services_required.llm.stream.call_args.args[2]
        assert isinstance(tool_defs, list)
        assert len(tool_defs) == 1
        assert "name" in tool_defs[0]
        assert "description" in tool_defs[0]
        assert "parameters" in tool_defs[0]


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
            runner._guard.check_all.return_value = None
            runner._guard.check_empty_result_repeat.return_value = None
            runner._guard.check_unavailable_repeat.return_value = None
            result = await runner.run("http://llm", **WF_CTX)

        assert result.answer == "Done"
        mock_exec.assert_awaited_once()
        assert len(runner._ctx.conv.history) == 2
        assert runner._ctx.conv.history[0]["tool_calls"] is not None
        # SEQ-07: assistant tool-call row persists through the turn boundary,
        # not a standalone session.save.
        runner._ctx.turn.persistence_boundary.save.assert_awaited_once_with(
            "assistant",
            "",
            tool_calls=tool_calls,
        )

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
            runner._guard.check_all.return_value = None
            runner._guard.check_empty_result_repeat.return_value = None
            runner._guard.check_unavailable_repeat.return_value = None
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
            runner._guard.check_empty_result_repeat.return_value = None
            runner._guard.check_unavailable_repeat.return_value = None
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
            runner._guard.check_all.return_value = None
            runner._guard.check_empty_result_repeat.return_value = None
            runner._guard.check_unavailable_repeat.return_value = None
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

    @pytest.mark.asyncio
    async def test_finalize_answer_text_appends_unchanged_via_append_message(
        self, runner: LLMTurnRunner
    ) -> None:
        message: LLMMessage = {"role": "assistant", "content": "Done"}

        result = await runner._finalize_answer_text(message)

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
            runner._guard.check_all.return_value = None
            runner._guard.check_empty_result_repeat.return_value = None
            runner._guard.check_unavailable_repeat.return_value = None
            await runner.run("http://llm", **WF_CTX)

        assert runner._ctx.conv.history[0] == {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }


class TestAllFailingRoundGuardReachable:
    """Pin the real ToolLoopGuard consecutive-error counting path (REQ-009 / AC-7).

    The shared `runner` fixture uses a MagicMock guard, so these cases build a
    runner with a real ToolLoopGuard(ctx) and drive run() through multiple
    tool-call rounds. execute_all_tool_calls is replaced with an AsyncMock whose
    side_effect advances ctx.stats.stat_tool_errors, so update_errors and
    check_error_limit run for real while the preparation/registry path stays
    out of the way.
    """

    def _guarded_runner(self) -> tuple[LLMTurnRunner, MagicMock]:
        ctx = _make_ctx()
        # The guard compares several thresholds with `<= 0`; an unset MagicMock
        # attribute raises TypeError on comparison, so pin the ones this test
        # does not otherwise configure.
        ctx.cfg.tool.progress_stagnation_window = 0
        ctx.cfg.tool.tool_empty_result_max_repeats = 0
        guard = ToolLoopGuard(ctx)
        return LLMTurnRunner(ctx, guard), ctx

    @pytest.mark.asyncio
    async def test_full_failure_stops_turn_at_error_limit(self) -> None:
        runner, ctx = self._guarded_runner()
        # Distinct tool name per round so the real dedup guard never fires
        # before the consecutive-error limit is reached.
        rounds = [
            [{"id": "c1", "function": {"name": "read_file"}}],
            [{"id": "c2", "function": {"name": "write_file"}}],
            [{"id": "c3", "function": {"name": "delete_file"}}],
        ]
        responses = [
            LLMResponse(
                message={"role": "assistant", "content": "", "tool_calls": calls},
                finish_reason="tool_calls",
            )
            for calls in rounds
        ]

        async def _record_all_fail(_ctx, calls, *_a, **_k) -> None:
            # Every call failed: record one error per call in the round.
            _ctx.stats.stat_tool_errors += len(calls)

        with (
            patch.object(
                runner,
                "_stream_llm",
                AsyncMock(side_effect=responses),
            ),
            patch(
                "agent.llm_turn_runner.execute_all_tool_calls",
                AsyncMock(side_effect=_record_all_fail),
            ),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "fail"
        assert result.reason == "error_limit"

    @pytest.mark.asyncio
    async def test_partial_failure_maintains_consecutive_count(self) -> None:
        runner, ctx = self._guarded_runner()
        # Dedup raised so the two tools can repeat across the three partial
        # rounds below (progress stagnation is disabled in the helper).
        ctx.cfg.tool.tool_dedup_max_repeats = 100

        partial = LLMResponse(
            message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "c1", "function": {"name": "read_file"}},
                    {"id": "c2", "function": {"name": "write_file"}},
                ],
            },
            finish_reason="tool_calls",
        )
        stop_response = LLMResponse(
            message={"role": "assistant", "content": "done"},
            finish_reason="stop",
        )

        async def _record_one_fail(_ctx, calls, *_a, **_k) -> None:
            # Only one of the two calls in the round failed.
            _ctx.stats.stat_tool_errors += 1

        with (
            patch.object(
                runner,
                "_stream_llm",
                AsyncMock(side_effect=[partial, partial, partial, stop_response]),
            ),
            patch(
                "agent.llm_turn_runner.execute_all_tool_calls",
                AsyncMock(side_effect=_record_one_fail),
            ),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        # Three partial rounds keep consecutive_errors below the limit, so the
        # turn continues. Had update_errors incremented on partial failure, the
        # third round would have hit error_limit instead.
        assert result.action == "continue"


# ── Round atomicity (AC-002) ────────────────────────────────────────────────

_ROUND_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    title TEXT,
    undo_floor_message_id INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    tool_calls TEXT,
    tool_call_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class _FakeSQLiteHelper:
    """Minimal SQLiteHelper stand-in bound to an in-memory connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def open(
        self, *, write_mode: bool = False, row_factory: bool = False
    ) -> _FakeSQLiteHelper:
        self._conn.row_factory = sqlite3.Row if row_factory else None
        return self

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: list) -> sqlite3.Cursor:
        return self._conn.executemany(sql, params_seq)

    def fetchall(self, sql: str, params: tuple | dict = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        pass

    def __enter__(self) -> _FakeSQLiteHelper:
        return self

    def __exit__(self, *_: object) -> None:
        pass


class TestRunRoundAtomicity:
    """A persistence failure in a later tool round rolls back every earlier
    round's assistant row through the turn boundary (AC-002)."""

    @pytest.mark.asyncio
    async def test_failed_later_round_leaves_no_partial_rows(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.executescript(_ROUND_SCHEMA_SQL)
        conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
        conn.commit()
        fake = _FakeSQLiteHelper(conn)
        with (
            patch("agent.session.SQLiteHelper", return_value=fake),
            patch("agent.session_message_repo.SQLiteHelper", return_value=fake),
        ):
            session = AgentSession()
            session.session_id = 1
            session._message_repo = SessionMessageRepository(session_id=1)

            # Pre-turn user row (id 1); the boundary marker is captured after it.
            user_msg: LLMMessage = {"role": "user", "content": "q"}
            session.save(user_msg["role"], user_msg["content"])
            conv = ConversationState()
            conv.history = [user_msg]
            boundary = await session.turn_boundary(conv)

            guard = MagicMock()
            guard.check_all.return_value = None
            guard.check_error_limit.return_value = None
            guard.check_empty_result_repeat.return_value = None
            guard.check_unavailable_repeat.return_value = None
            guard.update_errors.return_value = 0
            ctx = MagicMock()
            ctx.conv = conv
            ctx.turn.persistence_boundary = boundary
            ctx.stats.stat_tool_errors = 0
            ctx.cfg.tool.max_tool_turns = 5
            runner = LLMTurnRunner(ctx, guard)

            tool_calls = [{"id": "c1", "function": {"name": "read_file"}}]
            tool_response = LLMResponse(
                message={
                    "role": "assistant",
                    "content": "",
                    "tool_calls": tool_calls,
                },
                finish_reason="tool_calls",
            )

            real_save = session._message_repo.save  # bound to the repo instance
            calls = {"n": 0}

            def _counting_save(
                role: str,
                content: str,
                tool_calls: list[dict] | None = None,
                tool_call_id: str | None = None,
            ) -> None:
                # 1st call = round-1 assistant row (persists); the 2nd
                # (round-2 assistant) fails and the boundary compensates every
                # row after the turn-start marker.
                calls["n"] += 1
                if calls["n"] >= 2:
                    raise sqlite3.OperationalError("injected disk failure")
                return real_save(role, content, tool_calls, tool_call_id)

            with (
                patch.object(
                    runner,
                    "_stream_llm",
                    AsyncMock(side_effect=[tool_response, tool_response]),
                ),
                patch("agent.llm_turn_runner.execute_all_tool_calls", AsyncMock()),
            ):
                with patch.object(
                    SessionMessageRepository, "save", side_effect=_counting_save
                ):
                    with pytest.raises(ConversationPersistenceError):
                        await runner.run("http://llm", **WF_CTX)

            # Round 2's failure compensated round 1's assistant row; only the
            # pre-turn user row remains. No partial round rows survive (AC-002).
            rows = conn.execute(
                "SELECT role FROM messages WHERE session_id = 1 ORDER BY message_id"
            ).fetchall()
            assert [r[0] for r in rows] == ["user"]


# ── Unavailable-repeat bound integration (toolhint001 AC-2 / AC-1 / AC-5) ────

_UNAVAILABLE_OUTPUT = "MCP server 'srv' is currently unavailable (health check failed)"
_BOUND_SUMMARY = "Repeated unavailability from server 'srv' detected."


def _hinted_unavailable_result() -> ToolCallResult:
    return ToolCallResult(
        output=_UNAVAILABLE_OUTPUT,
        is_error=True,
        request_id="",
        server_key="srv",
        source="mcp",
        error_type="tool",
        availability_hint=DynamicAvailabilityHint(
            reason="server_unavailable",
            circuit_state=McpServerHealthState.UNAVAILABLE,
            retry_after_seconds=7,
        ),
    )


class TestUnavailableRepeatBoundIntegration:
    """End-to-end runner bound: hinted results observed through the real
    ToolLoopGuard stop the turn before max_tool_turns, and the tool-definitions
    block at the LLM request boundary is identical across every round (AC-1/AC-2)."""

    _TOOL_DEFS = [
        {"name": "mcp_read", "description": "read", "parameters": {"type": "object"}},
        {"name": "mcp_write", "description": "write", "parameters": {"type": "object"}},
    ]

    def _real_guard_runner(
        self, limit: int, responses: list[LLMResponse]
    ) -> tuple[LLMTurnRunner, MagicMock, MagicMock]:
        ctx = _make_ctx()
        ctx.cfg.tool.tool_empty_result_max_repeats = limit
        # Distinct tool names per round already avoid dedup; raise the window so
        # only the unavailable-repeat bound can end this turn. Pin the stagnation
        # dial the real guard compares with `<= 0`.
        ctx.cfg.tool.tool_dedup_max_repeats = 100
        ctx.cfg.tool.progress_stagnation_window = 0
        guard = ToolLoopGuard(ctx)
        registry = MagicMock()
        registry.llm_tool_definitions.return_value = [dict(d) for d in self._TOOL_DEFS]
        ctx.services_required.runtime_tools = registry
        ctx.services_required.llm.stream = AsyncMock(side_effect=responses)
        return LLMTurnRunner(ctx, guard), ctx, guard

    @staticmethod
    def _tool_response(round_idx: int) -> LLMResponse:
        return LLMResponse(
            message={
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": f"c{round_idx}",
                        "function": {"name": f"mcp_read_{round_idx}"},
                    }
                ],
            },
            finish_reason="tool_calls",
        )

    @pytest.mark.asyncio
    async def test_bound_terminates_turn_before_max_tool_turns(self) -> None:
        responses = [
            self._tool_response(1),
            self._tool_response(2),
            self._tool_response(3),
        ]
        runner, ctx, guard = self._real_guard_runner(2, responses)

        async def _observe_hook(*_a: object, **_k: object) -> None:
            # Mirrors scripts/agent/tool_runner.py: every executed result is
            # offered to the guard's availability observer.
            guard.observe_availability(_hinted_unavailable_result())

        with patch(
            "agent.llm_turn_runner.execute_all_tool_calls",
            AsyncMock(side_effect=_observe_hook),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "fail"
        assert result.reason == "unavailable_repeat"
        # Fixed guard summary, not server free text (security boundary).
        assert result.answer == _BOUND_SUMMARY
        # Bounded at 2 rounds, strictly before max_tool_turns=5 exhaustion.
        assert ctx.services_required.llm.stream.await_count == 2
        assert guard.scan_unavailable_repeat() == ("srv", 2)

    @pytest.mark.asyncio
    async def test_llm_tool_definitions_identical_across_turns(self) -> None:
        responses = [
            self._tool_response(1),
            self._tool_response(2),
            self._tool_response(3),
        ]
        runner, ctx, guard = self._real_guard_runner(2, responses)

        async def _observe_hook(*_a: object, **_k: object) -> None:
            guard.observe_availability(_hinted_unavailable_result())

        with patch(
            "agent.llm_turn_runner.execute_all_tool_calls",
            AsyncMock(side_effect=_observe_hook),
        ):
            await runner.run("http://llm", **WF_CTX)

        captured = [
            call.args[2] for call in ctx.services_required.llm.stream.await_args_list
        ]
        assert len(captured) == 2
        assert all(defs == self._TOOL_DEFS for defs in captured)

    @pytest.mark.asyncio
    async def test_default_off_runs_unbounded_scenario_as_today(self) -> None:
        # tool_empty_result_max_repeats=0 (repo default): identical hinted
        # results never end the turn (characterization of default-off).
        stop = LLMResponse(
            message={"role": "assistant", "content": "Done"}, finish_reason="stop"
        )
        responses = [self._tool_response(1), self._tool_response(2), stop]
        runner, ctx, guard = self._real_guard_runner(0, responses)

        async def _observe_hook(*_a: object, **_k: object) -> None:
            guard.observe_availability(_hinted_unavailable_result())

        with patch(
            "agent.llm_turn_runner.execute_all_tool_calls",
            AsyncMock(side_effect=_observe_hook),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "continue"
        assert result.answer == "Done"
        assert guard.scan_unavailable_repeat() is None


class TestAvailabilityHintTokenImpact:
    """REQ-006 / AC-5 measurement: hint-carrying vs unhinted histories.

    The availability hint travels as structured DTO metadata; the tool-result
    text is byte-identical to the legacy rejection text. The only turn-level
    token addition is the fixed guard bound summary. Cached regions (system
    prompt + assistant tool-call serialization) must measure identically.
    """

    _SYSTEM = (
        "You are an agent. Use the available tools to answer user requests. "
        "Prefer short, verified answers and cite tool output. "
    ) * 6
    _TOOL_CALLS = [
        {
            "id": "c1",
            "function": {"name": "mcp_read", "arguments": '{"path": "notes.txt"}'},
        }
    ]

    def _histories(self) -> tuple[list[LLMMessage], list[LLMMessage]]:
        base: list[LLMMessage] = [
            {"role": "system", "content": self._SYSTEM},
            {"role": "user", "content": "Read the notes file."},
            {"role": "assistant", "content": "", "tool_calls": self._TOOL_CALLS},
            {"role": "tool", "tool_call_id": "c1", "content": _UNAVAILABLE_OUTPUT},
            {"role": "assistant", "content": "", "tool_calls": self._TOOL_CALLS},
            {"role": "tool", "tool_call_id": "c2", "content": _UNAVAILABLE_OUTPUT},
        ]
        hinted = list(base)
        # At the bound the runner ends the turn with the fixed guard summary;
        # this is the only conversation-visible hint artifact.
        hinted.append({"role": "assistant", "content": _BOUND_SUMMARY})
        return base, hinted

    def _tool_region_tokens(self, history: list[LLMMessage]) -> int:
        return sum(
            int(len(msg["content"]) / RATIO_TEXT)
            for msg in history
            if msg.get("role") == "tool"
        )

    def test_cached_regions_measure_identically(self) -> None:
        unhinted, hinted = self._histories()
        _, base_breakdown = estimate_tokens(unhinted)
        _, hinted_breakdown = estimate_tokens(hinted)
        # Prompt-cached regions: system prompt and tool-call serialization.
        assert hinted_breakdown["system"] == base_breakdown["system"]
        assert hinted_breakdown["tool_calls"] == base_breakdown["tool_calls"]

    def test_tool_result_region_delta_is_zero_and_summary_cost_recorded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        unhinted, hinted = self._histories()
        base_total, _ = estimate_tokens(unhinted)
        hinted_total, _ = estimate_tokens(hinted)
        tool_region_base = self._tool_region_tokens(unhinted)
        tool_region_hinted = self._tool_region_tokens(hinted)
        total_delta = hinted_total - base_total

        # Tool-result text region: unchanged (hint is structured DTO metadata).
        assert tool_region_hinted == tool_region_base
        # The only added cost is the once-per-turn fixed bound summary.
        assert total_delta == int(len(_BOUND_SUMMARY) / RATIO_TEXT)

        # Recorded value for the plan Execution Status note (AC-5 gate).
        print(
            "REQ-006 measurement: tool-result-region delta="
            f"{tool_region_hinted - tool_region_base} tokens, "
            f"bound-summary cost={total_delta} tokens, "
            f"totals unhinted={base_total} hinted={hinted_total}"
        )
