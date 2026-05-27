#!/usr/bin/env python3
"""
orchestrator.py
Turn-level orchestration: RAG augmentation -> history compression -> LLM streaming
-> tool dispatch with duplicate call detection and consecutive error guard.
Extracted from AgentREPL to separate UI loop from task control logic.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from agent_commands import _budget_breakdown
from agent_config import BUDGET_WARN_RATIO
from agent_context import AgentContext
from agent_repl_debug import (
    _extract_history_context,
    _make_debug_fn,
    _needs_more_context,
)
from agent_repl_tool_exec import execute_all_tool_calls
from llm_client import LLMClient
from logger import Logger
from rag_llm import get_embedding
from rag_repository import fetch_full_document
from sqlite_helper import SQLiteHelper
from tool_executor import tool_call_key

if TYPE_CHECKING:
    from agent_commands import CommandRegistry

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


class Orchestrator:
    """Turn-level coordinator: RAG -> compression -> LLM loop -> tool dispatch.

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
    ) -> None:
        self._ctx = ctx
        self._cmds = cmds
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error

    # ── Public entry point ────────────────────────────────────────────────────

    async def handle_turn(self, line: str) -> None:
        """Augment line with RAG context, call LLM, and persist to DB.

        Compresses conversation history before the LLM call when total chars
        exceed context_char_limit.
        """
        ctx = self._ctx
        assert ctx.services.hist_mgr is not None

        context, cache_hit = await self._augment_with_rag(line)

        if context:
            ctx.stat_rag_hits += 1
            augmented = f"[Reference documents]\n{context}\n\nQuestion: {line}"
            # Accumulate per-step RAG latency samples (only on real pipeline runs)
            if ctx.services.rag is not None and not cache_hit:
                for step, secs in ctx.services.rag.last_timings.items():
                    ctx.stat_latency.setdefault(step, []).append(secs)
        else:
            augmented = line
        ctx.history.append({"role": "user", "content": augmented})
        ctx.stat_turns += 1

        # Generate session title asynchronously from the first user input
        if ctx.stat_turns == 1:
            asyncio.create_task(self._cmds._generate_session_title(line))
        ctx.session.save("user", augmented)

        # Compress history before sending to LLM when it exceeds the char limit
        ctx.history = await ctx.services.hist_mgr.compress(ctx.history)

        try:
            answer = await self._run_turn(ctx.llm_url)
            logger.info(f"LLM response: {answer}")
            ctx.session.save("assistant", answer)
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            if self._on_error:
                self._on_error(e)
            # Remove failed user message to keep history consistent
            if ctx.history and ctx.history[-1]["role"] == "user":
                ctx.history.pop()

    # ── LLM interaction ───────────────────────────────────────────────────────

    async def _run_turn(self, llm_url: str) -> str:
        """Send ctx.history to LLM; execute tool calls; return final answer.

        All turns use SSE streaming so tokens arrive incrementally.
        Applies duplicate tool call detection and consecutive all-error guard.
        """
        ctx = self._ctx
        assert ctx.services.llm is not None
        tool_defs = ctx.cfg.tool_definitions
        # Guard: two-stage fetch runs at most once per user turn
        two_stage_done = False
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

            # Warn when total input chars exceed BUDGET_WARN_RATIO of context_char_limit
            if turn == 0 and ctx.cfg.context_char_limit > 0:
                bd = _budget_breakdown(ctx.history)
                total_bd = sum(bd.values())
                if total_bd > ctx.cfg.context_char_limit * BUDGET_WARN_RATIO:
                    pct = int(total_bd * 100 / ctx.cfg.context_char_limit)
                    logger.warning(
                        f"Context budget {pct}% used"
                        f" (total={total_bd:,}"
                        f" limit={ctx.cfg.context_char_limit:,})"
                        f" sys={bd['system']:,} rag={bd['rag']:,}"
                        f" hist={bd['history']:,}"
                        f" tool={bd['tool_results']:,}"
                    )

            t0_llm = time.perf_counter()
            response = await ctx.services.llm.stream(llm_url, ctx.history, tool_defs)
            # Record LLM wall-clock time for the first (main) generation turn only
            if turn == 0:
                ctx.stat_latency.setdefault("llm", []).append(
                    time.perf_counter() - t0_llm
                )

            message, finish_reason = LLMClient.extract_message(response)

            has_tool_calls = bool(message.get("tool_calls"))
            is_done = (finish_reason != "tool_calls") or not has_tool_calls
            if is_done:
                ctx.history.append(message)
                if self._on_turn_end:
                    self._on_turn_end()
                answer = message.get("content") or ""
                # Two-stage: expand full document context when LLM signals need
                if not two_stage_done:
                    extra = await self._maybe_two_stage_fetch(answer)
                    if extra is not None:
                        two_stage_done = True
                        ctx.history.append(
                            {
                                "role": "user",
                                "content": (
                                    "[Additional context]\n"
                                    + extra
                                    + "\n\n(Please revise your answer using"
                                    " the above additional context.)"
                                ),
                            }
                        )
                        continue
                return answer

            ctx.history.append(message)
            ctx.session.save(
                "assistant",
                message.get("content") or "",
                tool_calls=message.get("tool_calls"),
            )

            # Cycle detection: abort when the same round-level tool fingerprint repeats
            if ctx.cfg.tool_cycle_detect_window > 0:
                round_key = hashlib.md5(
                    "|".join(
                        sorted(
                            f"{tc.get('function', {}).get('name', '')}:"
                            f"{tc.get('function', {}).get('arguments', '{}')}"
                            for tc in message["tool_calls"]
                        )
                    ).encode()
                ).hexdigest()
                if (
                    round_fingerprints.count(round_key)
                    >= ctx.cfg.tool_cycle_detect_window
                ):
                    logger.warning(
                        f"Cyclic planning detected: round fingerprint {round_key!r}"
                        f" repeated {round_fingerprints.count(round_key)} times"
                    )
                    ctx.history.append({"role": "user", "content": _CYCLE_HINT})
                    return "Cyclic tool call pattern detected."
                round_fingerprints.append(round_key)

            # Dedup: block re-execution of identical (tool, args) within this turn sequence
            dedup_name: str | None = None
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                key = hashlib.md5(
                    f"{func.get('name', '')}:{func.get('arguments', '{}')}".encode()
                ).hexdigest()
                seen_calls[key] = seen_calls.get(key, 0) + 1
                if seen_calls[key] >= ctx.cfg.tool_dedup_max_repeats:
                    dedup_name = func.get("name", "<unknown>")
                    break

            if dedup_name is not None:
                logger.warning(f"Duplicate tool call blocked: {dedup_name!r}")
                ctx.history.append({"role": "user", "content": _DEDUP_HINT})
                return "Repeated tool call detected."

            # Recursive retry suppression: block re-execution of calls that already errored.
            if ctx.cfg.tool_error_retry_max > 0:
                retry_blocked: str | None = None
                for tc in message["tool_calls"]:
                    func = tc.get("function", {})
                    try:
                        tc_args = json.loads(func.get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
                        tc_args = {}
                    if tool_call_key(func.get("name", ""), tc_args) in failed_calls:
                        retry_blocked = func.get("name", "<unknown>")
                        break
                if retry_blocked is not None:
                    logger.warning(
                        f"Retry of failed tool call blocked: {retry_blocked!r}"
                    )
                    ctx.history.append({"role": "user", "content": _DEDUP_HINT})
                    return "Repeated failed tool call detected."

            errors_before = ctx.stat_tool_errors
            await execute_all_tool_calls(
                ctx, message["tool_calls"], turn, out_failed_keys=failed_calls
            )
            n_errors = ctx.stat_tool_errors - errors_before

            # Consecutive error tracking: reset count when any tool succeeds this turn
            if n_errors == len(message["tool_calls"]):
                consecutive_errors += 1
            else:
                consecutive_errors = 0

            if (
                ctx.cfg.tool_error_max_consecutive > 0
                and consecutive_errors >= ctx.cfg.tool_error_max_consecutive
            ):
                logger.warning(
                    f"Aborting turn: {consecutive_errors} consecutive all-error"
                    f" tool turns (max={ctx.cfg.tool_error_max_consecutive})"
                )
                return "Too many consecutive tool errors."

        logger.warning(f"Reached max_tool_turns={ctx.cfg.max_tool_turns}")
        return "Maximum tool turns reached."

    # ── RAG augmentation ──────────────────────────────────────────────────────

    async def _augment_with_rag(self, line: str) -> tuple[str, bool]:
        """Run the RAG pipeline (or semantic cache) and return (context, cache_hit).

        Returns an empty string when use_search is False or no relevant chunks found.
        """
        ctx = self._ctx
        if not ctx.cfg.use_search or ctx.services.rag is None:
            return "", False

        history_context = _extract_history_context(ctx.history, n=2)
        debug_fn = _make_debug_fn() if ctx.debug_mode else None

        # Try semantic cache before running the full RAG pipeline
        _cached_emb: list[float] | None = None
        if ctx.cfg.use_semantic_cache and ctx.services.http is not None:
            try:
                _cached_emb = await get_embedding("query: " + line, ctx.services.http)
                _cached_ctx = ctx.services.rag.semantic_cache.lookup(_cached_emb)
                if _cached_ctx is not None:
                    ctx.stat_semantic_cache_hits += 1
                    logger.info("Semantic cache hit; skipping RAG pipeline")
                    return _cached_ctx, True
            except Exception as _e:
                logger.warning(f"Semantic cache lookup failed: {_e}")
                _cached_emb = None

        context = await ctx.services.rag.augment(
            line, debug_fn, history_context=history_context
        )
        # Store result in semantic cache for future reuse
        if ctx.cfg.use_semantic_cache and context and ctx.services.http is not None:
            try:
                emb_for_store = _cached_emb or await get_embedding(
                    "query: " + line, ctx.services.http
                )
                ctx.services.rag.semantic_cache.put(emb_for_store, context)
            except Exception as _e:
                logger.warning(f"Semantic cache put failed: {_e}")

        return context, False

    # ── Two-stage context fetch ───────────────────────────────────────────────

    async def _fetch_two_stage_context(self) -> str:
        """Fetch full document context for the top reranked hits (second stage).

        Opens its own DB connection, expands up to two_stage_max_docs unique
        documents, and returns a formatted context block for the second LLM call.
        """
        ctx = self._ctx
        hits = ctx.services.rag.last_reranked if ctx.services.rag is not None else []
        if not hits:
            return ""
        max_docs = ctx.cfg.two_stage_max_docs
        try:
            db = SQLiteHelper().open(row_factory=True)
        except Exception as e:
            logger.warning(f"Two-stage fetch DB open failed: {e}")
            return ""
        blocks: list[str] = []
        seen_urls: set[str] = set()
        with db:
            for hit in hits:
                if len(seen_urls) >= max_docs:
                    break
                url = hit.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                chunk_id = hit.get("chunk_id")
                if chunk_id is None:
                    continue
                # Expand +-2 surrounding chunks for focused context
                full_hits = fetch_full_document(chunk_id, db, window=2)
                if full_hits:
                    content = "\n".join(h["content"] for h in full_hits)
                    blocks.append(f"[Source: {url}]\n{content}")
        result = "\n\n---\n\n".join(blocks)
        logger.info(f"Two-stage fetch: {len(blocks)} docs, {len(result)} chars")
        return result

    async def _maybe_two_stage_fetch(self, answer: str) -> str | None:
        """Inject full-document context when the LLM signals it needs more.

        Returns the extra context string when triggered, None otherwise.
        Called at most once per handle_turn() invocation.
        """
        ctx = self._ctx
        if not (
            ctx.cfg.use_two_stage_fetch
            and ctx.services.rag is not None
            and ctx.services.rag.last_reranked
            and _needs_more_context(answer)
        ):
            return None
        extra = await self._fetch_two_stage_context()
        if not extra:
            return None
        logger.info("Two-stage fetch: injecting full doc context")
        return extra
