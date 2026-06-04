#!/usr/bin/env python3
"""cmd_config.py
Configuration and statistics mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _ConfigMixin with:
  _cmd_stats           — /stats: session statistics
  _print_config_values — display all config fields
  _print_rag_config    — display RAG-specific config fields
  _cmd_config          — /config dispatcher
  _apply_config_params — apply reloaded config to all components
  _cmd_set             — /set: runtime LLM parameter override
  _cmd_reload          — /reload: reload split config files at runtime
"""

import logging
from typing import TYPE_CHECKING, Any

from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader

from agent.commands.mixin_base import MixinBase

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _ConfigMixin(MixinBase):
    """Configuration and statistics slash-command handlers."""

    def _collect_stats(self) -> dict[str, Any]:
        """Collect session statistics from ctx and services into a plain dict."""
        ctx = self._ctx
        llm = ctx.services.llm
        return {
            "session_id": str(ctx.session.session_id)
            if ctx.session.session_id
            else "none",
            "turns": ctx.stats.stat_turns,
            "tool_calls": ctx.stats.stat_tool_calls,
            "tool_errors": ctx.stats.stat_tool_errors,
            "llm_retries": llm.stat_retries if llm is not None else 0,
            "llm_reconnects": llm.stat_reconnects if llm is not None else 0,
            "llm_heartbeat_timeouts": llm.stat_heartbeat_timeouts
            if llm is not None
            else 0,
            "llm_partial_completions": llm.stat_partial_completions
            if llm is not None
            else 0,
            "llm_parse_errors": llm.stat_parse_errors if llm is not None else 0,
            "cache_hits": ctx.services.tools.stat_cache_hits
            if ctx.services.tools is not None
            else 0,
            "compress_count": ctx.services.hist_mgr.stat_compress_count
            if ctx.services.hist_mgr is not None
            else 0,
            "semantic_cache_hits": ctx.stats.stat_semantic_cache_hits,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            "debug_mode": ctx.conv.debug_mode,
            "latency": ctx.stats.stat_latency,
        }

    def _cmd_stats(self) -> None:
        """Print session statistics: turns, tool calls, cache hits, latency."""
        stats = self._collect_stats()

        def _fmt_tokens(v: int | None) -> str:
            # None = endpoint did not return usage data this session
            return f"{v:,}" if v is not None else "N/A"

        print("Session statistics:")
        print(f"  Session ID    : {stats['session_id']}")
        print(f"  Turns         : {stats['turns']}")
        print(f"  Tool calls    : {stats['tool_calls']}")
        print(f"  Tool errors   : {stats['tool_errors']}")
        print(f"  LLM retries   : {stats['llm_retries']}")
        print(f"  LLM reconnects: {stats['llm_reconnects']}")
        print(f"  HB timeouts   : {stats['llm_heartbeat_timeouts']}")
        print(f"  Partial compl : {stats['llm_partial_completions']}")
        print(f"  Parse errors  : {stats['llm_parse_errors']}")
        print(f"  Cache hits    : {stats['cache_hits']}")
        print(f"  Compress      : {stats['compress_count']}")
        print(f"  Sem. cache    : {stats['semantic_cache_hits']} hits")
        print(f"  Input tokens  : {_fmt_tokens(stats['input_tokens'])}")
        print(f"  Output tokens : {_fmt_tokens(stats['output_tokens'])}")
        print(f"  Debug mode    : {'ON' if stats['debug_mode'] else 'OFF'}")
        if stats["latency"]:
            print("Latency (mean / max, N samples):")
            for step in ["llm"]:
                samples = stats["latency"].get(step)
                if not samples:
                    continue
                mean = sum(samples) / len(samples)
                mx = max(samples)
                print(f"  {step:<12}: {mean:.2f}s / {mx:.2f}s ({len(samples)} samples)")

    def _print_config_values(self) -> None:
        """Print static endpoint/LLM settings and execution settings."""
        ctx = self._ctx
        print("Settings:")
        print(f"  llm_url             : {ctx.cfg.llm.llm_url}")
        print(f"  web_search_url      : {ctx.cfg.rag.web_search_url}")
        print(f"  github_server_url   : {ctx.cfg.mcp.github_url}")
        print(f"  max_tool_turns      : {ctx.cfg.tool.max_tool_turns}")
        print(f"  http_timeout        : {ctx.cfg.llm.http_timeout}s")
        print(f"  web_search_max      : {ctx.cfg.rag.web_search_max_results}")
        print(f"  context_char_limit  : {ctx.cfg.llm.context_char_limit}")
        print(
            f"  context_compress    : {ctx.cfg.llm.context_compress_turns} turn pairs"
        )
        print(f"  tool_cache_ttl      : {ctx.cfg.tool.tool_cache_ttl}s")
        print(f"  llm_max_retries     : {ctx.cfg.llm.llm_max_retries}")
        print(f"  llm_retry_base_delay: {ctx.cfg.llm.llm_retry_base_delay}s")
        print(f"  llm_temperature     : {ctx.cfg.llm.llm_temperature}")
        print(f"  llm_max_tokens      : {ctx.cfg.llm.llm_max_tokens}")
        print()
        print("SSE stream settings:")
        print(
            f"  sse_heartbeat_timeout              : {ctx.cfg.llm.sse_heartbeat_timeout}s",
        )
        print(
            f"  sse_malformed_retry                : {ctx.cfg.llm.sse_malformed_retry}"
        )
        print(f"  sse_reconnect_max                  : {ctx.cfg.llm.sse_reconnect_max}")
        print(
            f"  llm_stream_retry_on_heartbeat_timeout:"
            f" {ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout}",
        )
        print(
            f"  llm_stream_retry_on_malformed_chunk  :"
            f" {ctx.cfg.llm.llm_stream_retry_on_malformed_chunk}",
        )
        print()
        print("Execution settings:")
        print(f"  serial_tool_calls   : {ctx.cfg.tool.serial_tool_calls}")
        print(f"  use_tool_summarize  : {ctx.cfg.tool.use_tool_summarize}")
        print(f"  tool_summarize_thr  : {ctx.cfg.tool.tool_summarize_threshold}")
        print(f"  auto_inject_notes   : {ctx.cfg.tool.auto_inject_notes}")
        print()
        print("Semantic cache:")
        print(f"  use_semantic_cache  : {ctx.cfg.rag.use_semantic_cache}")
        print(f"  sem_cache_threshold : {ctx.cfg.rag.semantic_cache_threshold}")
        print(f"  sem_cache_max_size  : {ctx.cfg.rag.semantic_cache_max_size}")
        print()
        print("MCP / security settings:")
        print(f"  tool_def_strict     : {ctx.cfg.tool.tool_definitions_strict}")
        print(f"  watchdog_interval   : {ctx.cfg.mcp.mcp_watchdog_interval}s")
        print(f"  watchdog_max_restart: {ctx.cfg.mcp.mcp_watchdog_max_restarts}")
        print("Approval settings:")
        rules = ctx.cfg.approval.approval_risk_rules
        if rules:
            rule_str = ", ".join(f"{k}={v}" for k, v in sorted(rules.items()))
            print(f"  risk_rules          : {rule_str}")
        else:
            print("  risk_rules          : (none)")
        print(f"  protected_paths     : {ctx.cfg.approval.approval_protected_paths}")
        print(f"  high_risk_branches  : {ctx.cfg.approval.approval_high_risk_branches}")
        dry_run_tools = ctx.cfg.approval.approval_dry_run_tools
        print(f"  dry_run_tools       : {dry_run_tools or '(none)'}")
        masked = ctx.cfg.tool.masked_fields
        print(f"  masked_fields       : {masked or '(none)'}")
        print()
        print("Security settings (tool safety):")
        allowed_root = ctx.cfg.approval.allowed_root
        print(
            f"  allowed_root        : {repr(allowed_root) if allowed_root else '(disabled)'}",
        )
        allowed_repos = ctx.cfg.approval.approval_github_allowed_repos
        if allowed_repos:
            print(f"  github_allowed_repos: {allowed_repos}")
        else:
            print("  github_allowed_repos: (Fail-Closed — all write ops denied)")
        tier_count = len(ctx.cfg.approval.tool_safety_tiers)
        print(f"  tool_safety_tiers   : {tier_count} tools classified")
        allowed_tools = ctx.cfg.tool.allowed_tools
        if allowed_tools:
            print(f"  allowed_tools       : {allowed_tools}")
        else:
            print("  allowed_tools       : (unrestricted)")
        plan_blocked = ctx.cfg.tool.plan_blocked_tools
        plan_state = "ON" if ctx.conv.plan_mode else "OFF"
        print(f"  plan_mode           : {plan_state}")
        if plan_blocked:
            print("  plan_blocked_tools  :")
            for t in plan_blocked:
                print(f"    - {t}")
        else:
            print("  plan_blocked_tools  : (none)")

    def _print_rag_config(self) -> None:
        """Print retrieval settings including DB path and search parameters."""
        ctx = self._ctx
        print("Search settings:")
        SQLiteHelper._ensure_config()
        print(f"  rag_db_path         : {SQLiteHelper._RAG_PATH}")
        print(f"  session_db_path     : {SQLiteHelper._SESSION_PATH}")
        print(f"  top_k_search        : {ctx.cfg.rag.top_k_search}")
        print(f"  top_k_rerank        : {ctx.cfg.rag.top_k_rerank}")
        print(f"  max_chunks_per_doc  : {ctx.cfg.rag.max_chunks_per_doc}")

    def _cmd_config(self) -> None:
        """Print current configuration and source file paths."""
        from agent.config import (
            _CONFIG_DIR,
        )

        print("Config files:")
        print(f"  {_CONFIG_DIR / 'common.toml'}")
        print(f"  {_CONFIG_DIR / 'agent.toml'}")
        print()
        self._print_config_values()
        print()
        self._print_rag_config()

    def _set_temperature(self, ctx: "AgentContext", value_str: str) -> None:
        """Parse and apply llm_temperature from value_str."""
        try:
            val = float(value_str)
            if not 0.0 <= val <= 2.0:
                raise ValueError
        except ValueError:
            print("temperature must be a float in [0.0, 2.0]")
            return
        ctx.cfg.llm.llm_temperature = val
        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(temperature=val)
        logger.info(f"llm_temperature set to {val}")
        print(f"temperature set to {val}")

    def _set_max_tokens(self, ctx: "AgentContext", value_str: str) -> None:
        """Parse and apply llm_max_tokens from value_str."""
        try:
            val = int(value_str)
            if val < 1:
                raise ValueError
        except ValueError:
            print("max_tokens must be a positive integer")
            return
        ctx.cfg.llm.llm_max_tokens = val
        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(max_tokens=val)
        logger.info(f"llm_max_tokens set to {val}")
        print(f"max_tokens set to {val}")

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
            print(
                f"  temperature : {ctx.cfg.llm.llm_temperature}\n"
                f"  max_tokens  : {ctx.cfg.llm.llm_max_tokens}\n"
                "Use: /set temperature <float> | /set max_tokens <int>",
            )
            return
        if len(parts) != 2:
            print("Usage: /set temperature <float> | /set max_tokens <int>")
            return
        param, value_str = parts
        if param == "temperature":
            self._set_temperature(ctx, value_str)
        elif param == "max_tokens":
            self._set_max_tokens(ctx, value_str)
        else:
            print(f"Unknown parameter: {param!r}")
            print("Settable: temperature, max_tokens")

    def _cmd_reload(self) -> None:
        """Reload config/agent.toml and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.
        """
        from agent.services.config_reload import ConfigReloadService  # noqa: PLC0415

        try:
            new_cfg = ConfigLoader().load("common.toml", "agent.toml")
            result = ConfigReloadService(self._ctx).apply_config_dict(new_cfg)
            logger.info("Config reloaded")
            if result.needs_restart:
                print(f"Restart required for: {', '.join(result.needs_restart)}")
            print("Config reloaded.")
        except Exception as e:
            logger.warning(f"Config reload failed: {e}")
            print(f"Reload failed: {e}")
