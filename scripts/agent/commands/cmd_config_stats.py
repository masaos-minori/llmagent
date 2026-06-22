#!/usr/bin/env python3
"""agent/commands/cmd_config_stats.py
Stats collection and display for _ConfigMixin.

Provides:
  _collect_stats  — session statistics from ctx and services
  _cmd_stats      — /stats: print session statistics

Import from here:  from agent.commands.cmd_config_stats import _ConfigStatsMixin
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.commands.mixin_base import MixinBase
from agent.commands.models import StatsViewModel

if TYPE_CHECKING:
    pass


class _ConfigStatsMixin(MixinBase):
    """Stats collection and display for slash commands."""

    def _collect_stats(self) -> StatsViewModel:
        """Collect session statistics from ctx and services into a typed ViewModel."""
        ctx = self._ctx
        llm = ctx.services.llm
        return StatsViewModel(
            session_id=str(ctx.session.session_id)
            if ctx.session.session_id
            else "none",
            turns=ctx.stats.stat_turns,
            tool_calls=ctx.stats.stat_tool_calls,
            tool_errors=ctx.stats.stat_tool_errors,
            llm_retries=llm.stat_retries if llm is not None else 0,
            llm_reconnects=llm.stat_reconnects if llm is not None else 0,
            llm_heartbeat_timeouts=llm.stat_heartbeat_timeouts
            if llm is not None
            else 0,
            llm_partial_completions=llm.stat_partial_completions
            if llm is not None
            else 0,
            llm_parse_errors=llm.stat_parse_errors if llm is not None else 0,
            cache_hits=ctx.services.tools.stat_cache_hits
            if ctx.services.tools is not None
            else 0,
            compress_count=ctx.services.hist_mgr.stat_compress_count
            if ctx.services.hist_mgr is not None
            else 0,
            semantic_cache_hits=ctx.stats.stat_semantic_cache_hits,
            input_tokens=ctx.stats.stat_input_tokens,
            output_tokens=ctx.stats.stat_output_tokens,
            debug_mode=ctx.conv.debug_mode,
            latency=ctx.stats.stat_latency,
            workflow_mode=getattr(ctx.cfg, "workflow_mode", ""),
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
                f"  Partial compl : {stats.llm_partial_completions}"
                "  (stored as tool_result, tool_name='llm_partial_completion')"
            )
        else:
            self._out.write("  Partial compl : 0")
        self._out.write(f"  Parse errors  : {stats.llm_parse_errors}")
        self._out.write(f"  Cache hits    : {stats.cache_hits}")
        self._out.write(f"  Compress      : {stats.compress_count}")
        self._out.write(f"  Sem. cache    : {stats.semantic_cache_hits} hits")
        self._out.write(f"  Input tokens  : {_fmt_tokens(stats.input_tokens)}")
        self._out.write(f"  Output tokens : {_fmt_tokens(stats.output_tokens)}")
        self._out.write(f"  Debug mode    : {'ON' if stats.debug_mode else 'OFF'}")
        self._out.write(f"  Workflow mode : {stats.workflow_mode or '(not set)'}")
        if stats.latency:
            self._out.write("Latency (mean / max, N samples):")
            for step in ["llm"]:
                samples = stats.latency.get(step)
                if not samples:
                    continue
                mean = sum(samples) / len(samples)
                mx = max(samples)
                self._out.write(
                    f"  {step:<12}: {mean:.2f}s / {mx:.2f}s ({len(samples)} samples)"
                )
