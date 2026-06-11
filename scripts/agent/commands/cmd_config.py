#!/usr/bin/env python3
"""agent/commands/cmd_config.py
Configuration and statistics mixin for CommandRegistry.

Provides _ConfigMixin with:
  _cmd_stats           — /stats: session statistics
  _print_config_values — display all config fields
  _print_rag_config    — display RAG-specific config fields
  _cmd_config          — /config dispatcher
  _apply_config_params — apply reloaded config to all components
  _cmd_set             — /set: runtime LLM parameter override
  _cmd_reload          — /reload: reload split config files at runtime
"""

import logging
from typing import TYPE_CHECKING

from shared.config_loader import ConfigLoader

from agent.commands.mixin_base import MixinBase
from agent.commands.models import StatsViewModel

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _ConfigMixin(MixinBase):
    """Configuration and statistics slash-command handlers."""

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
        )

    def _cmd_stats(self) -> None:
        """Print session statistics: turns, tool calls, cache hits, latency."""
        stats = self._collect_stats()

        def _fmt_tokens(v: int | None) -> str:
            # None = endpoint did not return usage data this session
            return f"{v:,}" if v is not None else "N/A"

        self._out.write("Session statistics:")
        self._out.write(f"  Session ID    : {stats.session_id}")
        self._out.write(f"  Turns         : {stats.turns}")
        self._out.write(f"  Tool calls    : {stats.tool_calls}")
        self._out.write(f"  Tool errors   : {stats.tool_errors}")
        self._out.write(f"  LLM retries   : {stats.llm_retries}")
        self._out.write(f"  LLM reconnects: {stats.llm_reconnects}")
        self._out.write(f"  HB timeouts   : {stats.llm_heartbeat_timeouts}")
        self._out.write(f"  Partial compl : {stats.llm_partial_completions}")
        self._out.write(f"  Parse errors  : {stats.llm_parse_errors}")
        self._out.write(f"  Cache hits    : {stats.cache_hits}")
        self._out.write(f"  Compress      : {stats.compress_count}")
        self._out.write(f"  Sem. cache    : {stats.semantic_cache_hits} hits")
        self._out.write(f"  Input tokens  : {_fmt_tokens(stats.input_tokens)}")
        self._out.write(f"  Output tokens : {_fmt_tokens(stats.output_tokens)}")
        self._out.write(f"  Debug mode    : {'ON' if stats.debug_mode else 'OFF'}")
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

    def _print_llm_settings(self, ctx: "AgentContext") -> None:
        self._out.write("Settings:")
        self._out.write(f"  llm_url             : {ctx.cfg.llm.llm_url}")
        self._out.write(f"  web_search_url      : {ctx.cfg.rag.web_search_url}")
        self._out.write(f"  github_server_url   : {ctx.cfg.mcp.github_url}")
        self._out.write(f"  max_tool_turns      : {ctx.cfg.tool.max_tool_turns}")
        self._out.write(f"  http_timeout        : {ctx.cfg.llm.http_timeout}s")
        self._out.write(f"  web_search_max      : {ctx.cfg.rag.web_search_max_results}")
        self._out.write(f"  context_char_limit  : {ctx.cfg.llm.context_char_limit}")
        self._out.write(
            f"  context_compress    : {ctx.cfg.llm.context_compress_turns} turn pairs",
        )
        self._out.write(f"  tool_cache_ttl      : {ctx.cfg.tool.tool_cache_ttl}s")
        self._out.write(f"  llm_max_retries     : {ctx.cfg.llm.llm_max_retries}")
        self._out.write(f"  llm_retry_base_delay: {ctx.cfg.llm.llm_retry_base_delay}s")
        self._out.write(f"  llm_temperature     : {ctx.cfg.llm.llm_temperature}")
        self._out.write(f"  llm_max_tokens      : {ctx.cfg.llm.llm_max_tokens}")

    def _print_sse_settings(self, ctx: "AgentContext") -> None:
        self._out.write("SSE stream settings:")
        self._out.write(
            f"  sse_heartbeat_timeout              :"
            f" {ctx.cfg.llm.sse_heartbeat_timeout}s",
        )
        self._out.write(
            f"  sse_malformed_retry                : {ctx.cfg.llm.sse_malformed_retry}",
        )
        self._out.write(
            f"  sse_reconnect_max                  : {ctx.cfg.llm.sse_reconnect_max}",
        )
        self._out.write(
            f"  llm_stream_retry_on_heartbeat_timeout:"
            f" {ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout}",
        )
        self._out.write(
            f"  llm_stream_retry_on_malformed_chunk  :"
            f" {ctx.cfg.llm.llm_stream_retry_on_malformed_chunk}",
        )

    def _print_execution_settings(self, ctx: "AgentContext") -> None:
        self._out.write("Execution settings:")
        self._out.write(f"  serial_tool_calls   : {ctx.cfg.tool.serial_tool_calls}")
        self._out.write(f"  use_tool_summarize  : {ctx.cfg.tool.use_tool_summarize}")
        self._out.write(
            f"  tool_summarize_thr  : {ctx.cfg.tool.tool_summarize_threshold}"
        )
        self._out.write(f"  auto_inject_notes   : {ctx.cfg.tool.auto_inject_notes}")

    def _print_semantic_cache_settings(self, ctx: "AgentContext") -> None:
        self._out.write("Semantic cache:")
        self._out.write(f"  use_semantic_cache  : {ctx.cfg.rag.use_semantic_cache}")
        self._out.write(
            f"  sem_cache_threshold : {ctx.cfg.rag.semantic_cache_threshold}"
        )
        self._out.write(
            f"  sem_cache_max_size  : {ctx.cfg.rag.semantic_cache_max_size}"
        )

    def _print_mcp_settings(self, ctx: "AgentContext") -> None:
        self._out.write("MCP / security settings:")
        self._out.write(
            f"  tool_def_strict     : {ctx.cfg.tool.tool_definitions_strict}"
        )
        self._out.write(f"  watchdog_interval   : {ctx.cfg.mcp.mcp_watchdog_interval}s")
        self._out.write(
            f"  watchdog_max_restart: {ctx.cfg.mcp.mcp_watchdog_max_restarts}"
        )

    def _print_approval_settings(self, ctx: "AgentContext") -> None:
        self._out.write("Approval settings:")
        rules = ctx.cfg.approval.approval_risk_rules
        if rules:
            rule_str = ", ".join(f"{k}={v}" for k, v in sorted(rules.items()))
            self._out.write(f"  risk_rules          : {rule_str}")
        else:
            self._out.write("  risk_rules          : (none)")
        self._out.write(
            f"  protected_paths     : {ctx.cfg.approval.approval_protected_paths}"
        )
        self._out.write(
            f"  high_risk_branches  : {ctx.cfg.approval.approval_high_risk_branches}",
        )
        dry_run_tools = ctx.cfg.approval.approval_dry_run_tools
        self._out.write(f"  dry_run_tools       : {dry_run_tools or '(none)'}")
        masked = ctx.cfg.tool.masked_fields
        self._out.write(f"  masked_fields       : {masked or '(none)'}")

    def _print_tool_safety_settings(self, ctx: "AgentContext") -> None:
        self._out.write("Security settings (tool safety):")
        allowed_root = ctx.cfg.approval.allowed_root
        self._out.write(
            f"  allowed_root        :"
            f" {repr(allowed_root) if allowed_root else '(disabled)'}",
        )
        allowed_repos = ctx.cfg.approval.approval_github_allowed_repos
        if allowed_repos:
            self._out.write(f"  github_allowed_repos: {allowed_repos}")
        else:
            self._out.write(
                "  github_allowed_repos: (Fail-Closed \u2014 all write ops denied)",
            )
        tier_count = len(ctx.cfg.approval.tool_safety_tiers)
        self._out.write(f"  tool_safety_tiers   : {tier_count} tools classified")
        allowed_tools = ctx.cfg.tool.allowed_tools
        if allowed_tools:
            self._out.write(f"  allowed_tools       : {allowed_tools}")
        else:
            self._out.write("  allowed_tools       : (unrestricted)")
        plan_blocked = ctx.cfg.tool.plan_blocked_tools
        plan_state = "ON" if ctx.conv.plan_mode else "OFF"
        self._out.write(f"  plan_mode           : {plan_state}")
        if plan_blocked:
            self._out.write("  plan_blocked_tools  :")
            for t in plan_blocked:
                self._out.write(f"    - {t}")
        else:
            self._out.write("  plan_blocked_tools  : (none)")

    def _print_config_values(self) -> None:
        """Print static endpoint/LLM settings and execution settings."""
        ctx = self._ctx
        self._print_llm_settings(ctx)
        self._out.write("")
        self._print_sse_settings(ctx)
        self._out.write("")
        self._print_execution_settings(ctx)
        self._out.write("")
        self._print_semantic_cache_settings(ctx)
        self._out.write("")
        self._print_mcp_settings(ctx)
        self._print_approval_settings(ctx)
        self._out.write("")
        self._print_tool_safety_settings(ctx)

    def _print_rag_config(self) -> None:
        """Print retrieval settings including DB path and search parameters."""
        ctx = self._ctx
        self._out.write("Search settings:")
        from db.config import (
            build_db_config as _build_db_cfg,  # noqa: PLC0415 — lazy: only needed here
        )

        try:
            _db_cfg = _build_db_cfg()
            self._out.write(f"  rag_db_path         : {_db_cfg.rag_db_path}")
            self._out.write(f"  session_db_path     : {_db_cfg.session_db_path}")
        except (ValueError, RuntimeError) as e:
            self._out.write(f"  rag_db_path         : (config error: {e})")
            self._out.write(f"  session_db_path     : (config error: {e})")
        self._out.write(f"  top_k_search        : {ctx.cfg.rag.top_k_search}")
        self._out.write(f"  top_k_rerank        : {ctx.cfg.rag.top_k_rerank}")
        self._out.write(f"  max_chunks_per_doc  : {ctx.cfg.rag.max_chunks_per_doc}")

    def _cmd_config(self) -> None:
        """Print current configuration and source file paths."""
        from agent.config import (
            _CONFIG_DIR,
        )

        self._out.write("Config files:")
        self._out.write(f"  {_CONFIG_DIR / 'common.toml'}")
        self._out.write(f"  {_CONFIG_DIR / 'agent.toml'}")
        self._out.write("")
        self._print_config_values()
        self._out.write("")
        self._print_rag_config()

    def _set_temperature(self, ctx: "AgentContext", value_str: str) -> None:
        """Parse and apply llm_temperature from value_str."""
        try:
            val = float(value_str)
            if not 0.0 <= val <= 2.0:
                raise ValueError
        except ValueError:
            self._out.write("temperature must be a float in [0.0, 2.0]")
            return
        ctx.cfg.llm.llm_temperature = val
        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(temperature=val)
        logger.info(f"llm_temperature set to {val}")
        self._out.write(f"temperature set to {val}")

    def _set_max_tokens(self, ctx: "AgentContext", value_str: str) -> None:
        """Parse and apply llm_max_tokens from value_str."""
        try:
            val = int(value_str)
            if val < 1:
                raise ValueError
        except ValueError:
            self._out.write("max_tokens must be a positive integer")
            return
        ctx.cfg.llm.llm_max_tokens = val
        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(max_tokens=val)
        logger.info(f"llm_max_tokens set to {val}")
        self._out.write(f"max_tokens set to {val}")

    def _cmd_set(self, args: str) -> None:
        """Set a runtime LLM generation parameter.

        Usage:
          /set temperature <float>  LLM generation temperature (0.0–2.0)
          /set max_tokens <int>     Maximum tokens per LLM response (≥1)
        With no arguments, prints current values.
        """
        ctx = self._ctx
        parts = args.strip().split()
        if not parts:
            self._out.write(
                f"  temperature : {ctx.cfg.llm.llm_temperature}\n"
                f"  max_tokens  : {ctx.cfg.llm.llm_max_tokens}\n"
                "Use: /set temperature <float> | /set max_tokens <int>",
            )
            return
        if len(parts) != 2:
            self._out.write("Usage: /set temperature <float> | /set max_tokens <int>")
            return
        param, value_str = parts
        if param == "temperature":
            self._set_temperature(ctx, value_str)
        elif param == "max_tokens":
            self._set_max_tokens(ctx, value_str)
        else:
            self._out.write(f"Unknown parameter: {param!r}")
            self._out.write("Settable: temperature, max_tokens")

    def _cmd_reload(self) -> None:
        """Reload config/agent.toml and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.
        """
        from agent.services.config_reload import (
            ConfigReloadService,  # noqa: PLC0415 — lazy: deferred to avoid import cost; only needed on /reload
        )

        try:
            new_cfg = ConfigLoader().load("common.toml", "agent.toml")
            result = ConfigReloadService(self._ctx).apply_config_dict(new_cfg)
            logger.info("Config reloaded")
            if result.needs_restart:
                self._out.write(
                    f"Restart required for: {', '.join(result.needs_restart)}"
                )
            self._out.write("Config reloaded.")
        except OSError as e:
            logger.warning(f"Config reload I/O error: {e}")
            self._out.write(f"Reload failed (I/O error): {e}")
        except ValueError as e:
            logger.warning(f"Config reload failed: {e}")
            self._out.write(f"Reload failed: {e}")
