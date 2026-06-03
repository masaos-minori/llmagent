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

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


class _ConfigMixin:
    """Configuration and statistics slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _collect_stats(self) -> dict[str, Any]:
        """Collect session statistics from ctx and services into a plain dict."""
        ctx = self._ctx
        llm = ctx.services.llm
        return {
            "session_id": str(ctx.session.session_id) if ctx.session.session_id else "none",
            "turns": ctx.stat_turns,
            "tool_calls": ctx.stat_tool_calls,
            "tool_errors": ctx.stat_tool_errors,
            "llm_retries": llm.stat_retries if llm is not None else 0,
            "llm_reconnects": llm.stat_reconnects if llm is not None else 0,
            "llm_heartbeat_timeouts": llm.stat_heartbeat_timeouts if llm is not None else 0,
            "llm_partial_completions": llm.stat_partial_completions if llm is not None else 0,
            "llm_parse_errors": llm.stat_parse_errors if llm is not None else 0,
            "cache_hits": ctx.services.tools.stat_cache_hits if ctx.services.tools is not None else 0,
            "compress_count": ctx.services.hist_mgr.stat_compress_count if ctx.services.hist_mgr is not None else 0,
            "semantic_cache_hits": ctx.stat_semantic_cache_hits,
            "input_tokens": ctx.stat_input_tokens,
            "output_tokens": ctx.stat_output_tokens,
            "debug_mode": ctx.debug_mode,
            "latency": ctx.stat_latency,
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
        print(f"  llm_url             : {ctx.cfg.llm_url}")
        print(f"  web_search_url      : {ctx.cfg.web_search_url}")
        print(f"  github_server_url   : {ctx.cfg.github_url}")
        print(f"  max_tool_turns      : {ctx.cfg.max_tool_turns}")
        print(f"  http_timeout        : {ctx.cfg.http_timeout}s")
        print(f"  web_search_max      : {ctx.cfg.web_search_max_results}")
        print(f"  context_char_limit  : {ctx.cfg.context_char_limit}")
        print(f"  context_compress    : {ctx.cfg.context_compress_turns} turn pairs")
        print(f"  tool_cache_ttl      : {ctx.cfg.tool_cache_ttl}s")
        print(f"  llm_max_retries     : {ctx.cfg.llm_max_retries}")
        print(f"  llm_retry_base_delay: {ctx.cfg.llm_retry_base_delay}s")
        print(f"  llm_temperature     : {ctx.cfg.llm_temperature}")
        print(f"  llm_max_tokens      : {ctx.cfg.llm_max_tokens}")
        print()
        print("SSE stream settings:")
        print(
            f"  sse_heartbeat_timeout              : {ctx.cfg.sse_heartbeat_timeout}s",
        )
        print(f"  sse_malformed_retry                : {ctx.cfg.sse_malformed_retry}")
        print(f"  sse_reconnect_max                  : {ctx.cfg.sse_reconnect_max}")
        print(
            f"  llm_stream_retry_on_heartbeat_timeout:"
            f" {ctx.cfg.llm_stream_retry_on_heartbeat_timeout}",
        )
        print(
            f"  llm_stream_retry_on_malformed_chunk  :"
            f" {ctx.cfg.llm_stream_retry_on_malformed_chunk}",
        )
        print()
        print("Execution settings:")
        print(f"  serial_tool_calls   : {ctx.cfg.serial_tool_calls}")
        print(f"  use_tool_summarize  : {ctx.cfg.use_tool_summarize}")
        print(f"  tool_summarize_thr  : {ctx.cfg.tool_summarize_threshold}")
        print(f"  auto_inject_notes   : {ctx.cfg.auto_inject_notes}")
        print()
        print("Semantic cache:")
        print(f"  use_semantic_cache  : {ctx.cfg.use_semantic_cache}")
        print(f"  sem_cache_threshold : {ctx.cfg.semantic_cache_threshold}")
        print(f"  sem_cache_max_size  : {ctx.cfg.semantic_cache_max_size}")
        print()
        print("MCP / security settings:")
        print(f"  tool_def_strict     : {ctx.cfg.tool_definitions_strict}")
        print(f"  watchdog_interval   : {ctx.cfg.mcp_watchdog_interval}s")
        print(f"  watchdog_max_restart: {ctx.cfg.mcp_watchdog_max_restarts}")
        print("Approval settings:")
        rules = ctx.cfg.approval_risk_rules
        if rules:
            rule_str = ", ".join(f"{k}={v}" for k, v in sorted(rules.items()))
            print(f"  risk_rules          : {rule_str}")
        else:
            print("  risk_rules          : (none)")
        print(f"  protected_paths     : {ctx.cfg.approval_protected_paths}")
        print(f"  high_risk_branches  : {ctx.cfg.approval_high_risk_branches}")
        dry_run_tools = ctx.cfg.approval_dry_run_tools
        print(f"  dry_run_tools       : {dry_run_tools or '(none)'}")
        masked = ctx.cfg.masked_fields
        print(f"  masked_fields       : {masked or '(none)'}")
        print()
        print("Security settings (tool safety):")
        allowed_root = ctx.cfg.allowed_root
        print(
            f"  allowed_root        : {repr(allowed_root) if allowed_root else '(disabled)'}",
        )
        allowed_repos = ctx.cfg.approval_github_allowed_repos
        if allowed_repos:
            print(f"  github_allowed_repos: {allowed_repos}")
        else:
            print("  github_allowed_repos: (Fail-Closed — all write ops denied)")
        tier_count = len(ctx.cfg.tool_safety_tiers)
        print(f"  tool_safety_tiers   : {tier_count} tools classified")
        allowed_tools = ctx.cfg.allowed_tools
        if allowed_tools:
            print(f"  allowed_tools       : {allowed_tools}")
        else:
            print("  allowed_tools       : (unrestricted)")
        plan_blocked = ctx.cfg.plan_blocked_tools
        plan_state = "ON" if ctx.plan_mode else "OFF"
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
        print(f"  top_k_search        : {ctx.cfg.top_k_search}")
        print(f"  top_k_rerank        : {ctx.cfg.top_k_rerank}")
        print(f"  max_chunks_per_doc  : {ctx.cfg.max_chunks_per_doc}")

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

    def _apply_config_params(self, new_cfg: dict[str, Any]) -> None:
        """Update ctx.cfg from new_cfg and sync values to all components."""
        ctx = self._ctx
        self._apply_rag_tool_params(ctx, new_cfg)
        self._reload_approval_settings(ctx, new_cfg)
        ctx.cfg.masked_fields = list(new_cfg.get("masked_fields", ["file_content"]))
        self._apply_mcp_url_reload(ctx, new_cfg)
        self._apply_llm_prompt_params(ctx, new_cfg)
        self._apply_sse_reload_params(ctx, new_cfg)
        self._sync_services_to_cfg(ctx, new_cfg)

    def _apply_rag_tool_params(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply tool cache, LLM retry, refiner, and watchdog settings."""
        ctx.cfg.context_char_limit = int(new_cfg.get("context_char_limit", 8000))
        ctx.cfg.context_compress_turns = int(new_cfg.get("context_compress_turns", 4))
        ctx.cfg.tool_cache_ttl = float(new_cfg.get("tool_cache_ttl", 300))
        ctx.cfg.top_k_search = int(new_cfg.get("top_k_search", 20))
        ctx.cfg.top_k_rerank = int(new_cfg.get("top_k_rerank", 15))
        ctx.cfg.llm_max_retries = int(new_cfg.get("llm_max_retries", 3))
        ctx.cfg.llm_retry_base_delay = float(new_cfg.get("llm_retry_base_delay", 1.0))
        ctx.cfg.max_chunks_per_doc = int(new_cfg.get("max_chunks_per_doc", 2))
        ctx.cfg.serial_tool_calls = bool(new_cfg.get("serial_tool_calls", False))
        ctx.cfg.auto_inject_notes = bool(new_cfg.get("auto_inject_notes", True))
        ctx.cfg.use_tool_summarize = bool(new_cfg.get("use_tool_summarize", False))
        ctx.cfg.tool_summarize_threshold = int(
            new_cfg.get("tool_summarize_threshold", 3000),
        )
        ctx.cfg.use_semantic_cache = bool(new_cfg.get("use_semantic_cache", False))
        ctx.cfg.semantic_cache_threshold = float(
            new_cfg.get("semantic_cache_threshold", 0.92),
        )
        ctx.cfg.semantic_cache_max_size = int(
            new_cfg.get("semantic_cache_max_size", 100),
        )
        ctx.cfg.tool_definitions_strict = bool(
            new_cfg.get("tool_definitions_strict", False),
        )
        ctx.cfg.mcp_watchdog_interval = float(new_cfg.get("mcp_watchdog_interval", 0.0))
        ctx.cfg.mcp_watchdog_max_restarts = int(
            new_cfg.get("mcp_watchdog_max_restarts", 3),
        )
        ctx.cfg.plan_blocked_tools = list(
            new_cfg.get(
                "plan_blocked_tools",
                ["write_file", "create_directory", "delete_file", "delete_directory"],
            ),
        )
        ctx.cfg.use_refiner = bool(new_cfg.get("use_refiner", False))
        ctx.cfg.refiner_max_tokens = int(new_cfg.get("refiner_max_tokens", 512))
        ctx.cfg.refiner_timeout = float(new_cfg.get("refiner_timeout", 30.0))
        ctx.cfg.refiner_max_chars_per_chunk = int(
            new_cfg.get("refiner_max_chars_per_chunk", 300),
        )

    def _apply_mcp_url_reload(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Update HTTP MCP server URLs from reloaded config; transport type changes require restart."""
        from agent.config import _build_mcp_servers  # noqa: PLC0415

        new_mcp = _build_mcp_servers(new_cfg)
        for key, new_srv in new_mcp.items():
            old_srv = ctx.cfg.mcp_servers.get(key)
            if old_srv and old_srv.transport == "http" and new_srv.transport == "http":
                old_srv.url = new_srv.url
                old_srv.openrc_service = new_srv.openrc_service

    def _apply_llm_prompt_params(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings."""
        ctx.cfg.llm_temperature = float(new_cfg.get("llm_temperature", 0.2))
        ctx.cfg.llm_max_tokens = int(new_cfg.get("llm_max_tokens", 1024))
        ctx.cfg.llm_url = new_cfg.get("llm_url", ctx.cfg.llm_url)
        ctx.cfg.github_url = new_cfg.get("github_server_url", ctx.cfg.github_url)
        ctx.cfg.web_search_url = new_cfg.get("web_search_url", ctx.cfg.web_search_url)
        ctx.cfg.embed_url = new_cfg.get("embed_url", ctx.cfg.embed_url)
        ctx.cfg.http_timeout = float(new_cfg.get("http_timeout", ctx.cfg.http_timeout))
        ctx.cfg.web_search_max_results = int(
            new_cfg.get("web_search_max_results", ctx.cfg.web_search_max_results),
        )
        ctx.cfg.max_tool_turns = int(
            new_cfg.get("max_tool_turns", ctx.cfg.max_tool_turns),
        )
        ctx.cfg.tool_result_max_llm_chars = int(
            new_cfg.get("tool_result_max_llm_chars", ctx.cfg.tool_result_max_llm_chars),
        )
        if new_cfg.get("tool_definitions"):
            ctx.cfg.tool_definitions = list(new_cfg["tool_definitions"])
        system_prompt_tool = new_cfg.get("system_prompt_tool", "")
        if system_prompt_tool:
            ctx.cfg.system_prompt_tool = system_prompt_tool
        if new_cfg.get("system_prompts"):
            ctx.cfg.system_prompts = dict(new_cfg["system_prompts"])

    def _apply_sse_reload_params(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply SSE stream resilience settings."""
        ctx.cfg.sse_heartbeat_timeout = float(
            new_cfg.get("sse_heartbeat_timeout", ctx.cfg.sse_heartbeat_timeout),
        )
        ctx.cfg.sse_malformed_retry = int(
            new_cfg.get("sse_malformed_retry", ctx.cfg.sse_malformed_retry),
        )
        ctx.cfg.sse_reconnect_max = int(
            new_cfg.get("sse_reconnect_max", ctx.cfg.sse_reconnect_max),
        )
        ctx.cfg.llm_stream_retry_on_heartbeat_timeout = bool(
            new_cfg.get(
                "llm_stream_retry_on_heartbeat_timeout",
                ctx.cfg.llm_stream_retry_on_heartbeat_timeout,
            ),
        )
        ctx.cfg.llm_stream_retry_on_malformed_chunk = bool(
            new_cfg.get(
                "llm_stream_retry_on_malformed_chunk",
                ctx.cfg.llm_stream_retry_on_malformed_chunk,
            ),
        )

    def _reload_approval_settings(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Update approval-related list/dict fields in ctx.cfg when present in new_cfg."""
        if "approval_risk_rules" in new_cfg:
            ctx.cfg.approval_risk_rules = dict(new_cfg["approval_risk_rules"])
        if "approval_protected_paths" in new_cfg:
            ctx.cfg.approval_protected_paths = list(new_cfg["approval_protected_paths"])
        if "approval_high_risk_branches" in new_cfg:
            ctx.cfg.approval_high_risk_branches = list(
                new_cfg["approval_high_risk_branches"],
            )
        if "approval_shell_safe_prefixes" in new_cfg:
            ctx.cfg.approval_shell_safe_prefixes = list(
                new_cfg["approval_shell_safe_prefixes"],
            )
        if "approval_resource_keys" in new_cfg:
            ctx.cfg.approval_resource_keys = dict(new_cfg["approval_resource_keys"])
        if "approval_dry_run_tools" in new_cfg:
            ctx.cfg.approval_dry_run_tools = list(new_cfg["approval_dry_run_tools"])
        if "tool_safety_tiers" in new_cfg:
            ctx.cfg.tool_safety_tiers = dict(new_cfg["tool_safety_tiers"])
        ctx.cfg.allowed_root = new_cfg.get("allowed_root", ctx.cfg.allowed_root)
        if "approval_github_allowed_repos" in new_cfg:
            ctx.cfg.approval_github_allowed_repos = list(
                new_cfg["approval_github_allowed_repos"],
            )
        if "allowed_tools" in new_cfg:
            ctx.cfg.allowed_tools = list(new_cfg["allowed_tools"])
        if "memory_retention_days" in new_cfg:
            ctx.cfg.memory_retention_days = int(new_cfg["memory_retention_days"])

    def _sync_services_to_cfg(
        self,
        ctx: "AgentContext",
        new_cfg: dict[str, Any],
    ) -> None:
        """Propagate updated cfg fields to live service instances via public apply_config() APIs."""
        from agent.services.config_reload import ConfigReloadService  # noqa: PLC0415

        ConfigReloadService(ctx).sync_services(new_cfg)

    def _set_temperature(self, ctx: "AgentContext", value_str: str) -> None:
        """Parse and apply llm_temperature from value_str."""
        try:
            val = float(value_str)
            if not 0.0 <= val <= 2.0:
                raise ValueError
        except ValueError:
            print("temperature must be a float in [0.0, 2.0]")
            return
        ctx.cfg.llm_temperature = val
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
        ctx.cfg.llm_max_tokens = val
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
                f"  temperature : {ctx.cfg.llm_temperature}\n"
                f"  max_tokens  : {ctx.cfg.llm_max_tokens}\n"
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
        try:
            new_cfg = ConfigLoader().load("common.toml", "agent.toml")
            self._apply_config_params(new_cfg)
            logger.info("Config reloaded")
            print("Config reloaded.")
        except Exception as e:
            logger.warning(f"Config reload failed: {e}")
            print(f"Reload failed: {e}")
