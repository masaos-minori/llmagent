#!/usr/bin/env python3
"""agent/orchestrator.py
Turn-level orchestration facade.

Delegates LLM streaming and tool-loop guarding to:
  llm_turn_runner.py  — LLMTurnRunner (streaming + inner tool-call loop)
  tool_loop_guard.py  — ToolLoopGuard + TurnLoopState (dedup/cycle/retry/error guards)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable
from typing import Any

import orjson
from shared.llm_client import LLMTransportError
from shared.logger import Logger
from shared.types import LLMMessage

from agent.context import AgentContext
from agent.llm_turn_runner import LLMTurnRunner
from agent.tool_loop_guard import ToolLoopGuard

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class TurnResult:
    """Represents the result of a turn execution."""

    def __init__(self, success: bool, answer: str = "", error_kind: str | None = None):
        self.success = success
        self.answer = answer
        self.error_kind = error_kind


class Orchestrator:
    """Turn-level coordinator: compression -> LLM loop -> tool dispatch.

    Receives AgentContext (shared state) at construction. All terminal output
    and side effects are routed via optional callbacks so this class has no
    direct I/O dependency.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        allowed_tools: list[str] | None = None,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_first_turn: Callable[[str], Any] | None = None,
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._allowed_tools: list[str] | None = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._tracer = tracer
        self._guard = ToolLoopGuard(ctx)
        self._llm_runner = LLMTurnRunner(
            ctx,
            self._guard,
            on_turn_start=on_turn_start,
            on_turn_end=on_turn_end,
            tracer=tracer,
        )

    # ── Public entry point ────────────────────────────────────────────────────

    async def handle_turn(self, line: str) -> None:
        """Call LLM with the user message and persist to DB."""
        ctx = self._ctx
        turn_started_at = time.perf_counter()

        # Start turn processing
        await self._handle_turn_start(line)

        # Process the turn and handle errors
        answer, error_kind = await self._process_turn(line, ctx, turn_started_at)

        # End turn processing
        await self._handle_turn_end(line, answer, turn_started_at, error_kind)

    # ── Turn lifecycle ────────────────────────────────────────────────────────

    async def _handle_turn_start(self, line: str) -> None:
        ctx = self._ctx
        assert ctx.services.hist_mgr is not None
        ctx.turn.current_turn_id = str(uuid.uuid4())
        session_id = str(ctx.session.session_id) if ctx.session.session_id else "none"
        if ctx.services.audit_logger is not None:
            ctx.services.audit_logger.info(
                orjson.dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.turn.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ).decode(),
            )

    async def _handle_memory_injection(self, line: str) -> None:
        ctx = self._ctx
        if ctx.services.memory is not None:
            memory_snippets = await ctx.services.memory.on_user_prompt(
                query=line,
                session_id=ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "[Relevant memories]\n" + "\n".join(
                    f"- {s}" for s in memory_snippets
                )
                ctx.conv.history.append(
                    {
                        "role": "system",
                        "content": memory_block,
                        "_memory_injected": True,  # type: ignore[typeddict-unknown-key]
                    }
                )

    async def _handle_history_compression(self) -> None:
        ctx = self._ctx
        assert ctx.services.hist_mgr is not None
        with self._llm_runner._span_ctx("compress"):
            ctx.conv.history, _ = await ctx.services.hist_mgr.compress(ctx.conv.history)

    async def _handle_llm_turn(self, llm_url: str) -> TurnResult:
        ctx = self._ctx
        try:
            with self._llm_runner._span_ctx("llm") as llm_span:
                llm_span.set_attribute("model_url", llm_url)
                answer = await self._llm_runner.run(llm_url)
                logger.info(f"LLM response: {answer}")
                ctx.session.save("assistant", answer)
                return TurnResult(success=True, answer=answer)
        except LLMTransportError as e:
            self._handle_llm_transport_error(e, ctx)
            if self._on_error:
                self._on_error(e)
            # Return error result instead of raising to make error handling explicit
            return TurnResult(success=False, answer="", error_kind=str(e))
        except Exception as e:
            self._handle_general_llm_error(e, ctx)
            if self._on_error:
                self._on_error(e)
            # Return error result instead of raising to make error handling explicit
            return TurnResult(success=False, answer="", error_kind=str(e))

    async def _process_turn(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None]:
        """Process a turn and return (answer, error_kind)."""
        answer = ""
        error_kind = None

        # Snapshot original and apply override for this turn
        original_allowed = ctx.cfg.tool.allowed_tools
        if self._allowed_tools is not None:
            ctx.cfg.tool.allowed_tools = self._allowed_tools
        try:
            await self._handle_memory_injection(line)
            self._append_user_message(line)
            await self._handle_history_compression()

            result = await self._handle_llm_turn(ctx.conv.llm_url)
            answer = result.answer
            if not result.success:
                error_kind = result.error_kind

        except LLMTransportError as e:
            # Handle LLMTransportError explicitly to avoid ambiguity
            error_kind = str(e)
            # Log the error but don't re-raise to make the error explicit to the caller
            logger.error(f"LLM transport error: {e}")
        finally:
            ctx.cfg.tool.allowed_tools = original_allowed  # always restore

        return answer, error_kind

    async def _handle_turn_end(
        self, line: str, answer: str, turn_started_at: float, error_kind: str | None
    ) -> None:
        ctx = self._ctx
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services.audit_logger is not None:
            llm = ctx.services.llm
            ctx.services.audit_logger.info(
                orjson.dumps(
                    {
                        "event": "turn_end",
                        "task_id": ctx.turn.current_turn_id,
                        "elapsed_ms": elapsed_ms,
                        "input_tokens": ctx.stats.stat_input_tokens,
                        "output_tokens": ctx.stats.stat_output_tokens,
                        "parse_error_count": (
                            llm.stat_parse_errors if llm is not None else 0
                        ),
                        "heartbeat_timeout_count": (
                            llm.stat_heartbeat_timeouts if llm is not None else 0
                        ),
                        "reconnect_count": (
                            llm.stat_reconnects if llm is not None else 0
                        ),
                        "partial_completion": False,
                        "error_kind": error_kind,
                    },
                ).decode(),
            )
        ctx.turn.current_turn_id = None

    # ── User message helpers ──────────────────────────────────────────────────

    def _sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        ctx = self._ctx
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            ctx.conv.history.insert(
                0, {"role": "system", "content": ctx.conv.system_prompt_content}
            )

    def _append_user_message(self, line: str) -> None:
        ctx = self._ctx
        self._sync_system_prompt()
        ctx.conv.history.append({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            asyncio.create_task(self._on_first_turn(line))
        ctx.session.save("user", line)

    def _handle_llm_transport_error(
        self,
        e: LLMTransportError,
        ctx: AgentContext,
    ) -> bool:
        if e.partial_text:
            incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
            ctx.conv.history.append(
                LLMMessage(role="assistant", content=incomplete_msg)
            )
            ctx.session.save("assistant", incomplete_msg)
            ctx.tool_result_store.store(
                session_id=ctx.session.session_id,
                turn=ctx.stats.stat_turns,
                tool_name="llm_partial_completion",
                args_json="{}",
                full_text=e.detail or f"partial={len(e.partial_text)} chars",
                summary=f"[INCOMPLETE: {e.kind}]",
                is_error=True,
            )
            if ctx.services.llm is not None:
                ctx.services.llm.stat_partial_completions += 1
            logger.warning(f"Partial LLM completion saved: {e.kind}")
            return True
        if ctx.conv.history and ctx.conv.history[-1]["role"] == "user":
            ctx.conv.history.pop()
        logger.error(
            f"LLM transport error (pre-stream): {e.kind} status={e.status_code}",
        )
        return False

    def _handle_general_llm_error(self, e: Exception, ctx: AgentContext) -> None:
        logger.error(f"LLM request failed: {e}")
        if ctx.conv.history and ctx.conv.history[-1]["role"] == "user":
            ctx.conv.history.pop()
