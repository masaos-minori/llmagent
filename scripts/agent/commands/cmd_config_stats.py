#!/usr/bin/env python3
"""agent/commands/cmd_config_stats.py

Stats collection and display for _ConfigMixin.

Provides:
  _collect_stats  — session statistics from ctx and services
  _cmd_stats      — /stats: print session statistics

Import from here:  from agent.commands.cmd_config_stats import _ConfigStatsMixin
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.commands.mixin_base import MixinBase
from agent.commands.models import LatencySnapshot, StatsViewModel
from agent.services.context_view import _int_safe

if TYPE_CHECKING:
    pass


def _safe[T](obj: object | None, attr: str, default: T) -> T:
    """Return getattr(obj, attr) if obj is not None, else default."""
    return getattr(obj, attr) if obj is not None else default


def _get_mem_circuit_open(ctx) -> bool:
    """Return True if the memory embedding circuit breaker is open."""
    mem = ctx.services_required.memory
    if mem is None:
        return False
    embed_client = mem.retriever.embed_client
    if embed_client is None:
        return False
    status = embed_client.get_status()
    return bool(status.circuit_open)


def _get_mem_fts_fallback(ctx) -> int:
    """Return the FTS fallback count from the memory retriever."""
    mem = ctx.services_required.memory
    if mem is None:
        return 0
    return getattr(mem.retriever, "fts_fallback_count", 0)


def _get_rag_db_configured(ctx) -> bool:
    """Return True when a RAG DB path is configured."""
    try:
        from db.config import build_db_config as _build_db_cfg  # noqa: PLC0415 — lazy

        _build_db_cfg()
        return True
    except (ValueError, RuntimeError):
        return False


class _ConfigStatsMixin(MixinBase):
    """Stats collection and display for slash commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def _collect_stats(self) -> StatsViewModel:
        """Collect session statistics from ctx and services into a typed ViewModel."""
        ctx = self._ctx
        llm = ctx.services_required.llm
        return StatsViewModel(
            session_id=str(ctx.session.session_id)
            if ctx.session.session_id
            else "none",
            turns=ctx.stats.stat_turns,
            tool_calls=ctx.stats.stat_tool_calls,
            tool_errors=ctx.stats.stat_tool_errors,
            llm_retries=_safe(llm, "stat_retries", 0),
            llm_reconnects=_safe(llm, "stat_reconnects", 0),
            llm_heartbeat_timeouts=_safe(llm, "stat_heartbeat_timeouts", 0),
            llm_partial_completions=_int_safe(ctx.stats, "stat_partial_completions", 0),
            llm_parse_errors=_safe(llm, "stat_parse_errors", 0),
            cache_hits=_safe(ctx.services_required.tools, "stat_cache_hits", 0),
            compress_count=_safe(
                ctx.services_required.hist_mgr, "stat_compress_count", 0
            ),
            fallback_truncate_count=_safe(
                ctx.services_required.hist_mgr, "stat_fallback_truncate_count", 0
            ),
            memory_consistency_failures=_safe(
                ctx.stats, "stat_memory_consistency_failures", 0
            ),
            memory_circuit_open=_get_mem_circuit_open(ctx),
            memory_fts_fallback_count=_get_mem_fts_fallback(ctx),
            semantic_cache_hits=ctx.stats.stat_semantic_cache_hits,
            input_tokens=ctx.stats.stat_input_tokens,
            output_tokens=ctx.stats.stat_output_tokens,
            debug_mode=ctx.conv.debug_mode,
            latency=LatencySnapshot(data=ctx.stats.stat_latency)
            if ctx.stats is not None
            else None,
            approval_pending=_safe(ctx.workflow, "approval_pending", False),
            rag_db_configured=_get_rag_db_configured(ctx),
        )

    def _cmd_stats(self) -> None:
        """Print session statistics: turns, tool calls, cache hits, latency."""
        stats = self._collect_stats()

        def _fmt_tokens(v: int | None) -> str:
            return f"{v:,}" if v is not None else "N/A"

        self._out.write("Session statistics:")
        self._out.write(f"  Session ID    : {stats.session_id}")
        self._out.write(f"  Turns         : {stats.turns}")
        self._out.write(f"  Tool calls    : {stats.tool_calls}")
        self._out.write(f"  Tool errors   : {stats.tool_errors}")
        self._out.write(f"  LLM retries   : {stats.llm_retries}")
        self._out.write(f"  LLM reconnects: {stats.llm_reconnects}")
        self._out.write(f"  HB timeouts   : {stats.llm_heartbeat_timeouts}")
        if stats.llm_partial_completions > 0:
            self._out.write(
                f"  Partial compl : {stats.llm_partial_completions}  (stored in session_diagnostics)"
            )
        else:
            self._out.write("  Partial compl : 0")
        self._out.write(f"  Parse errors  : {stats.llm_parse_errors}")
        self._out.write(f"  Cache hits    : {stats.cache_hits}")
        self._out.write(f"  Compress      : {stats.compress_count}")
        self._out.write(f"  Fallback trunc: {stats.fallback_truncate_count}")
        if stats.memory_consistency_failures:
            self._out.write(f"  Memory inconsist.: {stats.memory_consistency_failures}")
        if stats.memory_circuit_open:
            self._out.write("  Memory embed: CIRCUIT OPEN [DEGRADED]")
        elif stats.memory_fts_fallback_count > 0:
            self._out.write(
                f"  Memory embed: fts_only x{stats.memory_fts_fallback_count} [degraded]"
            )
        self._out.write(f"  Sem. cache    : {stats.semantic_cache_hits} hits")
        self._out.write(f"  Input tokens  : {_fmt_tokens(stats.input_tokens)}")
        self._out.write(f"  Output tokens : {_fmt_tokens(stats.output_tokens)}")
        self._out.write(f"  Debug mode    : {'ON' if stats.debug_mode else 'OFF'}")
        if stats.approval_pending:
            self._out.write("  Approval      : PENDING — use /approve or /reject")
        if stats.rag_db_configured:
            self._out.write(
                "  Hint          : Run /db rag consistency for index integrity status"
            )
        if stats.latency:
            self._out.write("Latency (mean / max, N samples):")
            for step in ["llm"]:
                samples = stats.latency.data.get(step)
                if not samples:
                    continue
                mean = sum(samples) / len(samples)
                mx = max(samples)
                self._out.write(
                    f"  {step:<12}: {mean:.2f}s / {mx:.2f}s ({len(samples)} samples)"
                )
