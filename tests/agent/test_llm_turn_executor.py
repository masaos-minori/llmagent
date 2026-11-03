"""tests/agent/test_llm_turn_executor.py

Tests for scripts/agent/llm_turn_executor.py callback invocation.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.llm_turn_executor import LlmTurnExecutor
from agent.turn_result import TurnResult


def _make_executor(
    on_llm_wait_start: Callable[[str], Any] | None = None,
) -> LlmTurnExecutor:
    return LlmTurnExecutor(MagicMock(), on_llm_wait_start=on_llm_wait_start)


async def _run_turn(executor: LlmTurnExecutor) -> TurnResult:
    runner = AsyncMock()
    runner.run.return_value = TurnResult(action="continue", answer="ok")
    with (
        patch("agent.llm_turn_executor.LLMTurnRunner", return_value=runner),
        patch("agent.llm_turn_executor.ToolLoopGuard"),
    ):
        return await executor.handle_llm_turn("http://llm.invalid")


class TestWaitStartCallback:
    @pytest.mark.asyncio
    async def test_async_callback_body_runs_before_turn(self) -> None:
        calls: list[str] = []

        async def on_llm_wait_start(msg: str) -> None:
            calls.append(msg)

        await _run_turn(_make_executor(on_llm_wait_start=on_llm_wait_start))

        assert calls == ["Thinking"]

    @pytest.mark.asyncio
    async def test_sync_callback_still_invoked(self) -> None:
        on_llm_wait_start = MagicMock()

        await _run_turn(_make_executor(on_llm_wait_start=on_llm_wait_start))

        on_llm_wait_start.assert_called_once_with("Thinking")


class TestGuardDeferralWiring:
    """blockio001 AC-2: handle_llm_turn must build the guard with deferral on."""

    @pytest.mark.asyncio
    async def test_handle_llm_turn_builds_guard_with_defer_hints(self) -> None:
        executor = _make_executor()
        runner = AsyncMock()
        runner.run.return_value = TurnResult(action="continue", answer="ok")
        guard_cls = MagicMock()
        with (
            patch("agent.llm_turn_executor.LLMTurnRunner", return_value=runner),
            patch("agent.llm_turn_executor.ToolLoopGuard", guard_cls),
        ):
            await executor.handle_llm_turn("http://llm.invalid")

        guard_cls.assert_called_once()
        assert guard_cls.call_args.kwargs.get("defer_hints") is True
