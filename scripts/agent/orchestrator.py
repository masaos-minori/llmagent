#!/usr/bin/env python3
"""agent/orchestrator.py
Turn-level orchestration: history compression -> LLM streaming
-> tool dispatch with duplicate call detection and consecutive error guard.
Extracted from AgentREPL to separate UI loop from task control logic.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import orjson
from shared.llm_client import LLMClient, LLMTransportError
from shared.logger import Logger
from shared.tool_executor import format_transport_error, tool_call_key
from shared.types import LLMMessage

from agent.commands.registry import _budget_breakdown
from agent.context import AgentContext
from agent.repl_tool_exec import execute_all_tool_calls

if TYPE_CHECKING:
    from agent.commands.registry import CommandRegistry

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# Injected into LLM history when a duplicate tool call is blocked
_DEDUP_HINT = (
    "[System] The same tool was called with identical arguments multiple times."
    " Stop retrying and provide your best answer with the information already available."
)

# Injected into LLM history when a cyclic round-level planning pattern is detected
_CYCLE_HINT = (
    "[System] A cyclic planning pattern was detected: the same set of tool calls"
    " is being requested repeatedly across multiple rounds. Stop and provide your"
    " best answer with the information already available."
)


class _NullContextManager:
    """No-op context manager used when no tracer is configured.

    Allows `with _NullContextManager():` syntax without conditional branching
    throughout handle_turn(), keeping the OTel integration transparent.
    """

    def __enter__(self) -> _NullContextManager:
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def set_attribute(self, _key: str, _value: object) -> None:
        """Accept attribute calls without recording anything."""


class Orchestrator:
    """Turn-level coordinator: compression -> LLM loop -> tool dispatch.

    Receives AgentContext (shared state) and CommandRegistry (for session title
    generation) at construction. All terminal output is routed via optional
    callbacks so this class has no direct I/O dependency.
    """

    def __init__(
        self,
        ctx: AgentContext,
        cmds: CommandRegistry,
        *,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        tracer: Any = None,
    ) -> None:
        self._ctx = ctx
        self._cmds = cmds
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        # OTel tracer (or NoOp stand-in when otel_enabled=False)
        self._tracer = tracer

    # ── Public entry point ────────────────────────────────────────────────────

    async def _handle_turn_start(self, line: str) -> None:
        """Handle turn start operations."""
        ctx = self._ctx
        assert ctx.services.hist_mgr is not None

        # Assign a UUID to this turn; held in ctx for the duration, then cleared
        ctx.current_turn_id = str(uuid.uuid4())
        session_id = str(ctx.session.session_id) if ctx.session.session_id else "none"

        if ctx.services.audit_logger is not None:
            ctx.services.audit_logger.info(
                orjson.dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ).decode(),
            )

    async def _handle_memory_injection(self, line: str) -> None:
        """Handle memory injection before user message append."""
        ctx = self._ctx
        # UserPromptSubmit: inject relevant memories before RAG augmentation
        if ctx.services.memory is not None:
            memory_snippets = await ctx.services.memory.on_user_prompt(
                query=line,
                session_id=ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "[Relevant memories]\n" + "\n".join(
                    f"- {s}" for s in memory_snippets
                )
                ctx.history.append({"role": "system", "content": memory_block})

    async def _handle_history_compression(self) -> None:
        """Handle history compression."""
        ctx = self._ctx
        assert ctx.services.hist_mgr is not None
        # ── History compression span ──────────────────────────────────────
        with self._span_ctx("compress"):
            ctx.history = await ctx.services.hist_mgr.compress(ctx.history)

    async def _handle_llm_turn(self, llm_url: str) -> str:
        """Handle LLM turn."""
        ctx = self._ctx
        try:
            with self._span_ctx("llm") as llm_span:
                llm_span.set_attribute("model_url", llm_url)
                answer = await self._run_turn(llm_url)
                logger.info(f"LLM response: {answer}")
                ctx.session.save("assistant", answer)
                return answer
        except LLMTransportError as e:
            self._handle_llm_transport_error(e, ctx)
            if self._on_error:
                self._on_error(e)
            raise
        except Exception as e:
            self._handle_general_llm_error(e, ctx)
            if self._on_error:
                self._on_error(e)
            raise

    async def _handle_turn_end(self, line: str, answer: str) -> None:
        """Handle turn end operations."""
        ctx = self._ctx
        # NOTE: t0_turn is reset here, so elapsed_ms is always ~0ms.
        # To measure actual turn latency, t0_turn must be set in _handle_turn_start
        # and stored on self (e.g. self._t0_turn); deferred to avoid behavior change.
        t0_turn = time.perf_counter()
        elapsed_ms = round((time.perf_counter() - t0_turn) * 1000, 1)
        if ctx.services.audit_logger is not None:
            llm = ctx.services.llm
            ctx.services.audit_logger.info(
                orjson.dumps(
                    {
                        "event": "turn_end",
                        "task_id": ctx.current_turn_id,
                        "elapsed_ms": elapsed_ms,
                        "input_tokens": ctx.stat_input_tokens,
                        "output_tokens": ctx.stat_output_tokens,
                        "parse_error_count": (
                            llm.stat_parse_errors if llm is not None else 0
                        ),
                        "heartbeat_timeout_count": (
                            llm.stat_heartbeat_timeouts if llm is not None else 0
                        ),
                        "reconnect_count": (
                            llm.stat_reconnects if llm is not None else 0
                        ),
                        "partial_completion": False,  # This would be set in _handle_llm_turn
                    },
                ).decode(),
            )
        ctx.current_turn_id = None

    async def handle_turn(self, line: str) -> None:
        """Call LLM with the user message and persist to DB.

        Compresses conversation history before the LLM call when total chars
        exceed context_char_limit.
        """
        ctx = self._ctx
        await self._handle_turn_start(line)
        answer = ""

        try:
            await self._handle_memory_injection(line)
            self._append_user_message(line)
            await self._handle_history_compression()

            answer = await self._handle_llm_turn(ctx.llm_url)

        except LLMTransportError:
            # Error already handled (incomplete message / on_error) in _handle_llm_turn
            pass
        finally:
            await self._handle_turn_end(line, answer)

    # ── LLM interaction ───────────────────────────────────────────────────────

    async def _finalize_answer(self, message: LLMMessage) -> str:
        """Append the done-turn message to history and return the answer text."""
        ctx = self._ctx
        ctx.history.append(message)
        if self._on_turn_end:
            self._on_turn_end()
        return message.get("content") or ""

    def _span_ctx(self, name: str) -> Any:
        """Return a real OTel span context or a _NullContextManager when no tracer is set."""
        if self._tracer is not None:
            return self._tracer.start_as_current_span(name)
        return _NullContextManager()

    def _append_user_message(self, line: str) -> None:
        """Append user message to history and persist to session."""
        ctx = self._ctx
        ctx.history.append({"role": "user", "content": line})
        ctx.stat_turns += 1
        if ctx.stat_turns == 1:
            asyncio.create_task(self._cmds._generate_session_title(line))
        ctx.session.save("user", line)

    def _handle_llm_transport_error(
        self,
        e: LLMTransportError,
        ctx: AgentContext,
    ) -> bool:
        """Handle LLMTransportError from _run_turn(); return True when partial completion saved."""
        if e.partial_text:
            incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
            ctx.history.append(LLMMessage(role="assistant", content=incomplete_msg))
            ctx.session.save("assistant", incomplete_msg)
            ctx.tool_result_store.store(
                session_id=ctx.session.session_id,
                turn=ctx.stat_turns,
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
        # Pre-stream failure: pop the user message to keep history clean
        if ctx.history and ctx.history[-1]["role"] == "user":
            ctx.history.pop()
        logger.error(
            f"LLM transport error (pre-stream): {e.kind} status={e.status_code}",
        )
        return False

    def _handle_general_llm_error(self, e: Exception, ctx: AgentContext) -> None:
        """Handle unexpected exception from _run_turn(); remove last user message from history."""
        logger.error(f"LLM request failed: {e}")
        if ctx.history and ctx.history[-1]["role"] == "user":
            ctx.history.pop()

    async def _warn_budget(self) -> None:
        """Log warnings when conversation history approaches context limits.

        Called at turn=0 only; skips when both limits are disabled (=0).
        """
        ctx = self._ctx
        if ctx.cfg.context_char_limit > 0:
            bd = _budget_breakdown(ctx.history)
            total_bd = sum(bd.values())
            if total_bd > ctx.cfg.context_char_limit * ctx.cfg.budget_warn_ratio:
                pct = int(total_bd * 100 / ctx.cfg.context_char_limit)
                logger.warning(
                    f"Context budget {pct}% used"
                    f" (total={total_bd:,}"
                    f" limit={ctx.cfg.context_char_limit:,})"
                    f" sys={bd['system']:,} rag={bd['rag']:,}"
                    f" hist={bd['history']:,}"
                    f" tool={bd['tool_results']:,}",
                )
        if ctx.cfg.context_token_limit > 0:
            assert ctx.services.hist_mgr is not None
            token_bd, _ = await ctx.services.hist_mgr.count_tokens_async(
                ctx.history,
                ctx.stat_input_tokens,
            )
            if token_bd > ctx.cfg.context_token_limit * ctx.cfg.budget_warn_ratio:
                pct = int(token_bd * 100 / ctx.cfg.context_token_limit)
                logger.warning(
                    f"Token budget {pct}% used"
                    f" (tokens={token_bd:,}"
                    f" limit={ctx.cfg.context_token_limit:,})",
                )

    def _check_cycle_guard(
        self,
        round_fingerprints: list[str],
        message: LLMMessage,
    ) -> str | None:
        """Detect repeating round-level tool fingerprints; inject _CYCLE_HINT and return exit msg.

        Returns None when window is disabled or no cycle detected.
        Appends round_key to round_fingerprints on each call regardless of detection result.
        """
        ctx = self._ctx
        if ctx.cfg.tool_cycle_detect_window <= 0:
            return None
        round_key = hashlib.md5(  # dedup key only, not for security
            "|".join(
                sorted(
                    f"{tc.get('function', {}).get('name', '')}:"
                    f"{tc.get('function', {}).get('arguments', '{}')}"
                    for tc in message["tool_calls"]
                ),
            ).encode(),
            usedforsecurity=False,
        ).hexdigest()
        if round_fingerprints.count(round_key) >= ctx.cfg.tool_cycle_detect_window:
            logger.warning(
                f"Cyclic planning detected: round fingerprint {round_key!r}"
                f" repeated {round_fingerprints.count(round_key)} times",
            )
            ctx.history.append({"role": "user", "content": _CYCLE_HINT})
            return "Cyclic tool call pattern detected."
        round_fingerprints.append(round_key)
        return None

    def _check_dedup_guard(
        self,
        seen_calls: dict[str, int],
        message: LLMMessage,
    ) -> str | None:
        """Block re-execution of identical (tool, args); inject _DEDUP_HINT and return exit msg.

        Returns None when no dedup threshold is reached.
        Increments seen_calls counters for every tool call in message.
        """
        ctx = self._ctx
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            key = hashlib.md5(  # dedup key only, not for security
                f"{func.get('name', '')}:{func.get('arguments', '{}')}".encode(),
                usedforsecurity=False,
            ).hexdigest()
            seen_calls[key] = seen_calls.get(key, 0) + 1
            if seen_calls[key] >= ctx.cfg.tool_dedup_max_repeats:
                name = func.get("name", "<unknown>")
                logger.warning(f"Duplicate tool call blocked: {name!r}")
                ctx.history.append({"role": "user", "content": _DEDUP_HINT})
                return "Repeated tool call detected."
        return None

    def _check_retry_guard(
        self,
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Block retry of already-failed (tool, args); inject _DEDUP_HINT and return exit msg.

        Returns None when tool_error_retry_max is 0 or no failed key matches.
        """
        ctx = self._ctx
        if ctx.cfg.tool_error_retry_max <= 0:
            return None
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            try:
                tc_args = orjson.loads(func.get("arguments", "{}"))
            except (orjson.JSONDecodeError, TypeError):
                tc_args = {}
            if tool_call_key(func.get("name", ""), tc_args) in failed_calls:
                name = func.get("name", "<unknown>")
                logger.warning(f"Retry of failed tool call blocked: {name!r}")
                ctx.history.append({"role": "user", "content": _DEDUP_HINT})
                return "Repeated failed tool call detected."
        return None

    def _check_all_tool_guards(
        self,
        seen_calls: dict[str, int],
        round_fingerprints: list[str],
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Run cycle, dedup, and retry guards in order; return first hit or None."""
        if msg := self._check_cycle_guard(round_fingerprints, message):
            return msg
        if msg := self._check_dedup_guard(seen_calls, message):
            return msg
        return self._check_retry_guard(failed_calls, message)

    def _update_consecutive_errors(
        self,
        consecutive_errors: int,
        n_errors: int,
        n_tool_calls: int,
    ) -> int:
        """Increment consecutive-all-error counter; reset to 0 when any tool succeeds."""
        return consecutive_errors + 1 if n_errors == n_tool_calls else 0

    def _check_consecutive_error_limit(self, consecutive_errors: int) -> str | None:
        """Return exit message when consecutive all-error turns exceed the configured max."""
        ctx = self._ctx
        if (
            ctx.cfg.tool_error_max_consecutive <= 0
            or consecutive_errors < ctx.cfg.tool_error_max_consecutive
        ):
            return None
        logger.warning(
            f"Aborting turn: {consecutive_errors} consecutive all-error"
            f" tool turns (max={ctx.cfg.tool_error_max_consecutive})",
        )
        return "Too many consecutive tool errors."

    def _record_llm_latency(self, t0_llm: float, turn: int) -> None:
        """Append wall-clock time to stat_latency['llm'] for the first inner turn only."""
        if turn == 0:
            self._ctx.stat_latency.setdefault("llm", []).append(
                time.perf_counter() - t0_llm,
            )

    def _inject_mid_turn_error(self, e: LLMTransportError, turn: int) -> str:
        """Inject a synthetic tool-error message for a mid-turn LLM failure and return its summary."""
        ctx = self._ctx
        err = format_transport_error(
            source="llm",
            phase=e.phase,
            kind=e.kind,
            url=e.url,
            status_code=e.status_code,
            retryable=e.retryable,
            partial=bool(e.partial_text),
        )
        ctx.history.append(
            {
                "role": "tool",
                "content": err["detail"],
                "name": "llm_transport_error",
                "tool_call_id": f"synthetic_{uuid.uuid4().hex[:8]}",
            },
        )
        ctx.tool_result_store.store(
            session_id=ctx.session.session_id,
            turn=turn,
            tool_name="llm_transport_error",
            args_json="{}",
            full_text=err["detail"],
            summary=err["summary"],
            is_error=True,
        )
        logger.warning(
            f"LLM transport error during tool continuation (turn={turn}): {e.kind}",
        )
        return err["summary"]

    async def _run_turn(self, llm_url: str) -> str:
        """Send ctx.history to LLM; execute tool calls; return final answer.

        All turns use SSE streaming so tokens arrive incrementally.
        Applies duplicate tool call detection and consecutive all-error guard.
        """
        ctx = self._ctx
        assert ctx.services.llm is not None
        tool_defs = ctx.cfg.tool_definitions
        # Dedup: track (tool_name:args_json) md5 -> call count across all inner turns
        seen_calls: dict[str, int] = {}
        # Retry suppression: (name, args) keys that errored in this turn sequence
        failed_calls: set[str] = set()
        consecutive_errors: int = 0
        # Cycle detection: fingerprints of each round's tool call set (sorted, md5)
        round_fingerprints: list[str] = []

        for turn in range(ctx.cfg.max_tool_turns):
            if self._on_turn_start:
                self._on_turn_start()
            if turn == 0:
                await self._warn_budget()

            t0_llm = time.perf_counter()
            try:
                response = await ctx.services.llm.stream(
                    llm_url,
                    ctx.history,
                    tool_defs,
                )
            except LLMTransportError as e:
                if turn > 0:
                    return self._inject_mid_turn_error(e, turn)
                raise  # first turn: propagate to handle_turn()
            self._record_llm_latency(t0_llm, turn)

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

            if msg := self._check_all_tool_guards(
                seen_calls, round_fingerprints, failed_calls, message
            ):
                return msg

            errors_before = ctx.stat_tool_errors
            await execute_all_tool_calls(
                ctx,
                message["tool_calls"],
                turn,
                out_failed_keys=failed_calls,
            )
            n_errors = ctx.stat_tool_errors - errors_before
            consecutive_errors = self._update_consecutive_errors(
                consecutive_errors, n_errors, len(message["tool_calls"])
            )
            if msg := self._check_consecutive_error_limit(consecutive_errors):
                return msg

        logger.warning(f"Reached max_tool_turns={ctx.cfg.max_tool_turns}")
        return "Maximum tool turns reached."
