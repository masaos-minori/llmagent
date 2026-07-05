#!/usr/bin/env python3
"""agent/commands/cmd_config_display.py
Config display helpers for _ConfigMixin.

Provides:
  _print_llm_settings          — LLM endpoint settings
  _print_sse_settings          — SSE stream settings
  _print_execution_settings    — Execution settings
  _print_semantic_cache_settings — Semantic cache settings
  _print_mcp_settings          — MCP / security settings
  _print_approval_settings     — Approval settings
 _print_tool_safety_settings  — Tool safety settings
   _print_plugin_settings          — Plugin settings
   _print_config_values         — Combined config display
  _print_rag_config            — Retrieval/DB settings
  _cmd_config                  — /config dispatcher

Import from here:  from agent.commands.cmd_config_display import _ConfigDisplayMixin
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.commands.mixin_base import MixinBase

if TYPE_CHECKING:
    from agent.context import AgentContext


class _ConfigDisplayMixin(MixinBase):
    """Config display helpers for slash commands."""

    def _print_llm_settings(self, ctx: AgentContext) -> None:
        self._out.write("Settings:")
        self._out.write(f"  llm_url             : {ctx.cfg.llm.llm_url}")
        self._out.write(f"  web_search_url      : {ctx.cfg.rag.web_search_url}")
        self._out.write(f"  github_server_url   : {ctx.cfg.mcp.github_server_url}")
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

    def _print_sse_settings(self, ctx: AgentContext) -> None:
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

    def _print_execution_settings(self, ctx: AgentContext) -> None:
        self._out.write("Execution settings:")
        self._out.write(f"  serial_tool_calls   : {ctx.cfg.tool.serial_tool_calls}")
        self._out.write(f"  use_tool_summarize  : {ctx.cfg.tool.use_tool_summarize}")
        self._out.write(
            f"  tool_summarize_thr  : {ctx.cfg.tool.tool_summarize_threshold}"
        )

    def _print_semantic_cache_settings(self, ctx: AgentContext) -> None:
        self._out.write("Semantic cache:")
        self._out.write(f"  use_semantic_cache  : {ctx.cfg.rag.use_semantic_cache}")
        self._out.write(
            f"  sem_cache_threshold : {ctx.cfg.rag.semantic_cache_threshold}"
        )
        self._out.write(
            f"  sem_cache_max_size  : {ctx.cfg.rag.semantic_cache_max_size}"
        )

    def _print_mcp_settings(self, ctx: AgentContext) -> None:
        self._out.write("MCP / security settings:")
        self._out.write(
            f"  tool_def_strict     : {ctx.cfg.tool.tool_definitions_strict}"
        )
        self._out.write(f"  watchdog_interval   : {ctx.cfg.mcp.mcp_watchdog_interval}s")
        self._out.write(
            f"  watchdog_max_restart: {ctx.cfg.mcp.mcp_watchdog_max_restarts}"
        )

    def _print_approval_settings(self, ctx: AgentContext) -> None:
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

    def _print_tool_safety_settings(self, ctx: AgentContext) -> None:
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
                "  github_allowed_repos: (Fail-Closed — all write ops denied)",
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

    def _print_memory_settings(self, ctx: AgentContext) -> None:
        self._out.write("Memory layer settings:")
        self._out.write(f"  use_memory_layer    : {ctx.cfg.memory.use_memory_layer}")
        self._out.write(
            f"  memory_embed_enabled: {ctx.cfg.memory.memory_embed_enabled}"
        )
        self._out.write(
            f"  memory_jsonl_dir    : {ctx.cfg.memory.memory_jsonl_dir or '(not set)'}"
        )
        self._out.write(
            f"  max_inject_semantic : {ctx.cfg.memory.memory_max_inject_semantic}"
        )
        self._out.write(
            f"  max_inject_episodic : {ctx.cfg.memory.memory_max_inject_episodic}"
        )
        self._out.write(
            f"  min_importance      : {ctx.cfg.memory.memory_min_importance}"
        )

    def _print_plugin_settings(self, ctx: AgentContext) -> None:
        self._out.write("Plugin settings:")
        self._out.write(f"  plugin_strict        : {ctx.cfg.tool.plugin_strict}")
        self._out.write(f"  plugin_tool_override : {ctx.cfg.tool.plugin_tool_override}")

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
        self._out.write("")
        self._print_memory_settings(ctx)
        self._out.write("")
        self._print_plugin_settings(ctx)

    def _print_rag_config(self) -> None:
        """Print retrieval settings including DB path and search parameters."""
        ctx = self._ctx
        self._out.write("Search settings:")
        from db.config import (
            build_db_config as _build_db_cfg,  # noqa: PLC0415 — lazy
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
        from agent.config_builders import (
            _CONFIG_DIR,  # noqa: PLC0415 — lazy: avoids circular import at module level
        )

        self._out.write("Config files:")
        self._out.write(
            f"  {_CONFIG_DIR} (common.toml, llm.toml, rag.toml, security.toml, tools.toml, ...)"
        )
        self._out.write("")
        self._print_config_values()
        self._out.write("")
        self._print_rag_config()
