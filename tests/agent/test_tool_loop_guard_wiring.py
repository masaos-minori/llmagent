"""tests/agent/test_tool_loop_guard_wiring.py

The per-turn ToolLoopGuard reaches the tool-execution path: every non-error tool
result is recorded on the guard that LLMTurnRunner later consults, at the moment
the result is produced, for sequential and gathered groups alike.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.llm_turn_runner import LLMTurnRunner
from agent.tool_loop_guard import ToolLoopGuard
from agent.tool_runner import execute_all_tool_calls
from shared.llm_types import LLMResponse
from shared.transport_dto import ToolCallResult

from tests.agent.test_tool_runner import _cfg, _make_ctx

WF_CTX = dict(
    workflow_id="wf-1", task_id="task-1", stage_id="execute", attempt_id="attempt-1"
)
TOOL = "read_text_file"


def _ctx(max_repeats: int, *, serial: bool = False):
    ctx = _make_ctx(_cfg(serial_tool_calls=serial))
    ctx.cfg.tool.tool_empty_result_max_repeats = max_repeats
    ctx.cfg.tool.max_tool_turns = 3
    ctx.diagnostics = None
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


def _batch(n: int) -> list[dict]:
    """n distinct calls of one tool (distinct args avoid the dedup guard)."""
    return [
        {
            "id": f"call_{i}",
            "function": {"name": TOOL, "arguments": f'{{"path": "/tmp/f{i}"}}'},
        }
        for i in range(n)
    ]


def _empty() -> ToolCallResult:
    return ToolCallResult(output="", is_error=False, request_id="r", server_key="")


def _approve_all():
    return patch(
        "agent.tool_approval.run_approval_checks",
        new_callable=AsyncMock,
        side_effect=lambda ctx, prepared: (prepared, []),
    )


class TestRecordedWhileBatchIsStillRunning:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("serial", [True, False])
    async def test_earlier_empty_results_are_visible_to_a_later_call(
        self, serial: bool
    ) -> None:
        ctx = _ctx(max_repeats=5, serial=serial)
        guard = ToolLoopGuard(ctx)
        seen_by_third_call: list[int] = []
        calls = 0

        async def execute(name: str, args: dict) -> ToolCallResult:
            nonlocal calls
            calls += 1
            if calls == 3:
                # Let the calls that started before this one finish and record.
                await asyncio.sleep(0.01)
                seen_by_third_call.append(guard._empty_result_counts.get(TOOL, 0))
            return _empty()

        ctx.services_required.tools.execute = execute

        with _approve_all():
            await execute_all_tool_calls(ctx, _batch(3), 0, guard=guard)

        # Both earlier results were already on the guard while the third call ran.
        assert seen_by_third_call == [2]
        assert guard._empty_result_counts[TOOL] == 3


class TestTurnLevelAcceptance:
    @pytest.mark.asyncio
    async def test_three_empty_results_fail_the_turn_with_empty_result_repeat(
        self,
    ) -> None:
        ctx = _ctx(max_repeats=2)
        ctx.services_required.tools.execute = AsyncMock(return_value=_empty())
        guard = ToolLoopGuard(ctx)
        runner = LLMTurnRunner(ctx, guard)
        tool_turn = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": _batch(3)},
            finish_reason="tool_calls",
        )

        with (
            _approve_all(),
            patch.object(runner, "_stream_llm", AsyncMock(return_value=tool_turn)),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.action == "fail"
        assert result.reason == "empty_result_repeat"
        assert TOOL in result.answer

    @pytest.mark.asyncio
    async def test_option_off_never_fires_and_records_nothing(self) -> None:
        ctx = _ctx(max_repeats=0)
        ctx.services_required.tools.execute = AsyncMock(return_value=_empty())
        guard = ToolLoopGuard(ctx)
        runner = LLMTurnRunner(ctx, guard)
        tool_turn = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": _batch(3)},
            finish_reason="tool_calls",
        )
        final = LLMResponse(
            message={"role": "assistant", "content": "done"}, finish_reason="stop"
        )

        with (
            _approve_all(),
            patch.object(
                runner, "_stream_llm", AsyncMock(side_effect=[tool_turn, final])
            ),
        ):
            result = await runner.run("http://llm", **WF_CTX)

        assert result.reason != "empty_result_repeat"
        assert guard._empty_result_counts == {}

    @pytest.mark.asyncio
    async def test_counts_do_not_leak_into_the_next_turn(self) -> None:
        ctx = _ctx(max_repeats=3)
        ctx.services_required.tools.execute = AsyncMock(return_value=_empty())

        with _approve_all():
            first = ToolLoopGuard(ctx)
            await execute_all_tool_calls(ctx, _batch(2), 0, guard=first)
            second = ToolLoopGuard(ctx)  # a new turn builds a new guard

        assert first._empty_result_counts[TOOL] == 2
        assert second._empty_result_counts == {}

    @pytest.mark.asyncio
    async def test_runner_passes_its_own_guard_to_the_tool_runner(self) -> None:
        ctx = _ctx(max_repeats=2)
        guard = ToolLoopGuard(ctx)
        runner = LLMTurnRunner(ctx, guard)
        tool_turn = LLMResponse(
            message={"role": "assistant", "content": "", "tool_calls": _batch(1)},
            finish_reason="tool_calls",
        )
        final = LLMResponse(
            message={"role": "assistant", "content": "done"}, finish_reason="stop"
        )

        with (
            patch.object(
                runner, "_stream_llm", AsyncMock(side_effect=[tool_turn, final])
            ),
            patch("agent.llm_turn_runner.execute_all_tool_calls") as mock_exec,
        ):
            await runner.run("http://llm", **WF_CTX)

        assert mock_exec.call_args.kwargs["guard"] is guard
