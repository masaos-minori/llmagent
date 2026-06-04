"""agent/llm_turn_runner.py
LLM streaming and inner tool-call loop for one agent turn.

Extracted from orchestrator.py. LLMTurnRunner.run() replaces _run_turn().
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.llm_client import LLMClient, LLMTransportError
from shared.types import LLMMessage

from agent.tool_loop_guard import ToolLoopGuard, TurnLoopState
from agent.tool_runner import execute_all_tool_calls

if TYPE_CHECKING:
    from agent.context import AgentContext

import logging

logger = logging.getLogger(__name__)


class LLMTurnRunner:
    """Manages the inner LLM streaming + tool-call loop for one agent turn.

    Accepts the same ctx/callbacks used by Orchestrator so it can be wired in
    without changing the call-site interface.
    """

    def __init__(
        self,
        ctx: AgentContext,
        guard: ToolLoopGuard,
        *,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._guard = guard
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._tracer = tracer

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, llm_url: str) -> str:
        """Send ctx.history to LLM, execute tool calls, return final answer."""
        ctx = self._ctx
        state = TurnLoopState()

        for turn in range(ctx.cfg.tool.max_tool_turns):
            if self._on_turn_start:
                self._on_turn_start()

            try:
                response = await self._stream_llm(llm_url, turn)
            except LLMTransportError as e:
                # Handle LLM transport error by delegating to error handler
                return await self._handle_llm_error(e, turn)

            message, finish_reason = LLMClient.extract_message(response)

            has_tool_calls = bool(message.get("tool_calls"))
            if (finish_reason != "tool_calls") or not has_tool_calls:
                return await self._finalize_answer(message)

            ctx.history.append(message)
            ctx.session.save(
                "assistant",
                message.get("content") or "",
                tool_calls=message.get("tool_calls"),
            )

            if msg := self._guard.check_all(
                state.seen_calls,
                state.round_fingerprints,
                state.failed_calls,
                message,
            ):
                return msg

            errors_before = ctx.stat_tool_errors
            await execute_all_tool_calls(
                ctx,
                message["tool_calls"],
                turn,
                out_failed_keys=state.failed_calls,
            )
            n_errors = ctx.stat_tool_errors - errors_before
            state.consecutive_errors = ToolLoopGuard.update_errors(
                state.consecutive_errors, n_errors, len(message["tool_calls"])
            )
            if msg := self._guard.check_error_limit(state.consecutive_errors):
                return msg

        logger.warning(f"Reached max_tool_turns={ctx.cfg.tool.max_tool_turns}")
        return "Maximum tool turns reached."

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _handle_llm_error(self, e: LLMTransportError, turn: int) -> str:
        """Handle LLM transport error by delegating to error injection service."""
        from agent.error_injection_service import ErrorInjectionService

        error_service = ErrorInjectionService(self._ctx)
        return error_service.inject_mid_turn_error(e, turn)

    def _span_ctx(self, name: str) -> Any:
        """Return a real OTel span or a no-op context manager when no tracer."""
        if self._tracer is not None:
            return self._tracer.start_as_current_span(name)

        # Return a no-op context manager
        class _NullContextManager:
            def __enter__(self) -> _NullContextManager:
                return self

            def __exit__(self, *args: object) -> None:
                pass

            def set_attribute(self, _key: str, _value: object) -> None:
                pass

        return _NullContextManager()

    async def _finalize_answer(self, message: LLMMessage) -> str:
        """Append the done-turn message to history and return the answer text."""
        ctx = self._ctx
        ctx.history.append(message)
        if self._on_turn_end:
            self._on_turn_end()
        return message.get("content") or ""

    async def _stream_llm(
        self,
        llm_url: str,
        turn: int,
    ) -> Any:
        """Stream one LLM response; raise on first-turn failure, inject on mid-turn."""
        ctx = self._ctx
        assert ctx.services.llm is not None
        try:
            response = await ctx.services.llm.stream(
                llm_url,
                ctx.history,
                ctx.cfg.tool.tool_definitions,
            )
        except LLMTransportError:
            raise  # Let the caller handle the error
        # Record latency for turn 0 only (moved to orchestrator)
        return response
