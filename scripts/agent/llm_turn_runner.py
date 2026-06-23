"""agent/llm_turn_runner.py
LLM streaming and inner tool-call loop for one agent turn.

Extracted from orchestrator.py. LLMTurnRunner.run() replaces _run_turn().
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import orjson
from shared.llm_client import LLMTransportError
from shared.types import LLMMessage

from agent.tool_loop_guard import ToolLoopGuard, TurnLoopState
from agent.tool_runner import execute_all_tool_calls
from agent.turn_result import TurnResult

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

    async def run(self, llm_url: str) -> TurnResult:
        """Send ctx.conv.history to LLM, execute tool calls, return TurnResult."""
        ctx = self._ctx
        state = TurnLoopState()

        for turn in range(ctx.cfg.tool.max_tool_turns):
            try:
                response = await self._stream_llm(llm_url, turn)
            except LLMTransportError as e:
                return await self._handle_llm_error(e, turn)

            message, finish_reason = response.message, response.finish_reason

            has_tool_calls = bool(message.get("tool_calls"))
            if (finish_reason != "tool_calls") or not has_tool_calls:
                answer = self._finalize_answer_text(message)
                return TurnResult(action="continue", answer=answer)

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
                return TurnResult(action="fail", answer=msg, reason="tool_loop_guard")

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
                return TurnResult(action="fail", answer=msg, reason="error_limit")

        logger.warning("Reached max_tool_turns=%s", ctx.cfg.tool.max_tool_turns)
        return TurnResult(
            action="fail",
            answer="Maximum tool turns reached.",
            reason="max_tool_turns",
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _handle_llm_error(self, e: LLMTransportError, turn: int) -> TurnResult:
        """Store mid-turn LLM error in diagnostic channel and return a fail TurnResult."""
        ctx = self._ctx
        summary = e.detail or str(e)
        if ctx.diagnostics is not None:
            ctx.diagnostics.save(
                ctx.session.session_id,
                "mid_turn_error",
                orjson.dumps(
                    {
                        "error_type": type(e).__name__,
                        "detail": summary,
                        "turn": turn,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ).decode(),
            )
        logger.warning(
            "LLM transport error during tool continuation (turn=%s): %s",
            turn,
            e.kind,
        )
        return TurnResult(
            action="fail", answer=summary, reason="llm_transport_error", exception=e
        )

    def _span_ctx(
        self,
        name: str,
        task_id: str = "",
        session_id: str = "",
        model_url: str = "",
    ) -> Any:
        """Return a real OTel span or a no-op context manager when no tracer."""
        if self._tracer is not None:
            attrs: dict[str, object] = {}
            if task_id:
                attrs["workflow.task_id"] = task_id
            if session_id:
                attrs["workflow.session_id"] = session_id
            if model_url:
                attrs["llm.model_url"] = model_url
            return self._tracer.start_as_current_span(name, attributes=attrs or None)
        return nullcontext(_NoOpSpan())

    def _finalize_answer_text(self, message: LLMMessage) -> str:
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
        logger.debug("_stream_llm: turn=%d url=%s", turn, llm_url)
        if ctx.services.llm is None:
            raise RuntimeError("llm service not initialized")
        response = await ctx.services.llm.stream(
            llm_url,
            ctx.conv.history,
            ctx.cfg.tool.tool_definitions,
        )
        return response
