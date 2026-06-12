"""agent/llm_turn_runner.py
LLM streaming and inner tool-call loop for one agent turn.

Extracted from orchestrator.py. LLMTurnRunner.run() replaces _run_turn().
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any

from shared.llm_client import LLMTransportError
from shared.types import LLMMessage

from agent.tool_loop_guard import ToolLoopGuard, TurnLoopState
from agent.tool_runner import execute_all_tool_calls

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _NoOpSpan:
    """No-op OTel span returned by _span_ctx when no tracer is configured."""

    def set_attribute(self, key: str, value: object) -> None:
        pass

    def record_exception(self, exc: BaseException) -> None:
        pass


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
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._guard = guard
        self._tracer = tracer

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, llm_url: str) -> str:
        """Send ctx.conv.history to LLM, execute tool calls, return final answer."""
        ctx = self._ctx
        state = TurnLoopState()

        for turn in range(ctx.cfg.tool.max_tool_turns):
            try:
                response = await self._stream_llm(llm_url, turn)
            except LLMTransportError as e:
                # Handle LLM transport error by delegating to error handler
                return await self._handle_llm_error(e, turn)

            message, finish_reason = response.message, response.finish_reason

            has_tool_calls = bool(message.get("tool_calls"))
            if (finish_reason != "tool_calls") or not has_tool_calls:
                return await self._finalize_answer(message)

            ctx.conv.history.append(message)
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

            errors_before = ctx.stats.stat_tool_errors
            await execute_all_tool_calls(
                ctx,
                message["tool_calls"],
                turn,
                out_failed_keys=state.failed_calls,
            )
            n_errors = ctx.stats.stat_tool_errors - errors_before
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
        return nullcontext(_NoOpSpan())

    async def _finalize_answer(self, message: LLMMessage) -> str:
        """Append the done-turn message to history and return the answer text."""
        ctx = self._ctx
        ctx.conv.history.append(message)
        return message.get("content") or ""

    async def _stream_llm(
        self,
        llm_url: str,
        turn: int,
    ) -> Any:
        """Stream one LLM response; raise on first-turn failure, inject on mid-turn."""
        ctx = self._ctx
        if ctx.services.llm is None:
            raise RuntimeError("llm service not initialized")
        response = await ctx.services.llm.stream(
            llm_url,
            ctx.conv.history,
            ctx.cfg.tool.tool_definitions,
        )
        return response
