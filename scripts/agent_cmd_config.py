#!/usr/bin/env python3
"""
agent_cmd_config.py
Configuration and statistics mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _ConfigMixin with:
  _cmd_stats           — /stats: session statistics
  _print_config_values — display all config fields
  _print_rag_config    — display RAG-specific config fields
  _cmd_config          — /config dispatcher
  _apply_config_params — apply reloaded config to all components
  _cmd_set             — /set: runtime LLM parameter override
  _cmd_reload          — /reload: reload config/agent.json at runtime
"""

import logging
from typing import TYPE_CHECKING

from config_loader import ConfigLoader
from sqlite_helper import SQLiteHelper

if TYPE_CHECKING:
    from agent_context import AgentContext

logger = logging.getLogger(__name__)


class _ConfigMixin:
    """Configuration and statistics slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _cmd_stats(self) -> None:
        """Print session statistics: turns, tool calls, RAG context hits, cache hits."""
        ctx = self._ctx
        sid = str(ctx.session.session_id) if ctx.session.session_id else "none"
        cache_hits = (
            ctx.services.tools.stat_cache_hits if ctx.services.tools is not None else 0
        )
        compress_count = (
            ctx.services.hist_mgr.stat_compress_count
            if ctx.services.hist_mgr is not None
            else 0
        )
        llm_retries = (
            ctx.services.llm.stat_retries if ctx.services.llm is not None else 0
        )

        def _fmt_tokens(v: int | None) -> str:
            # None = endpoint did not return usage data this session
            return f"{v:,}" if v is not None else "N/A"

        print("Session statistics:")
        print(f"  Session ID    : {sid}")
        print(f"  Turns         : {ctx.stat_turns}")
        print(f"  Tool calls    : {ctx.stat_tool_calls}")
        print(f"  Tool errors   : {ctx.stat_tool_errors}")
        print(f"  LLM retries   : {llm_retries}")
        print(f"  Cache hits    : {cache_hits}")
        print(f"  Compress      : {compress_count}")
        print(f"  RAG hits      : {ctx.stat_rag_hits}")
        print(
            f"  Sem. cache    : {ctx.stat_semantic_cache_hits} hits"
            f"  (size={ctx.services.rag.semantic_cache.size if ctx.services.rag else 0})"
        )
        print(f"  Input tokens  : {_fmt_tokens(ctx.stat_input_tokens)}")
        print(f"  Output tokens : {_fmt_tokens(ctx.stat_output_tokens)}")
        print(f"  Debug mode    : {'ON' if ctx.debug_mode else 'OFF'}")
        if ctx.stat_latency:
            print("Latency (mean / max, N samples):")
            for step in ["rag.mqe", "rag.search", "rag.rrf", "rag.rerank", "llm"]:
                samples = ctx.stat_latency.get(step)
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
        if ctx.services.rag is not None:
            print(f"  sem_cache_size      : {ctx.services.rag.semantic_cache.size}")
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
        masked = ctx.cfg.masked_fields
        print(f"  masked_fields       : {masked if masked else '(none)'}")
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
        """Print RAG-specific settings including DB path and retrieval parameters."""
        ctx = self._ctx
        print("RAG settings:")
        SQLiteHelper._ensure_config()
        print(f"  db_path             : {SQLiteHelper.DB_PATH}")
        print(f"  top_k_search        : {ctx.cfg.top_k_search}")
        print(f"  top_k_rerank        : {ctx.cfg.top_k_rerank}")
        print(f"  rag_top_k           : {ctx.cfg.rag_top_k}")
        print(f"  rag_min_score       : {ctx.cfg.rag_min_score}")
        print(f"  max_chunks_per_doc  : {ctx.cfg.max_chunks_per_doc}")
        print(f"  use_two_stage_fetch : {ctx.cfg.use_two_stage_fetch}")
        print(f"  two_stage_max_docs  : {ctx.cfg.two_stage_max_docs}")
        print(f"  use_mqe             : {ctx.cfg.use_mqe}")
        print(f"  use_search          : {ctx.cfg.use_search}")
        print(f"  use_rrf             : {ctx.cfg.use_rrf}")
        print(f"  use_rerank          : {ctx.cfg.use_rerank}")

    def _cmd_config(self) -> None:
        """Print current configuration and source file paths."""
        from agent_config import (
            _CONFIG_DIR,  # noqa: PLC0415 — avoid module-level constant import
        )

        print("Config files:")
        print(f"  {_CONFIG_DIR / 'common.json'}")
        print(f"  {_CONFIG_DIR / 'agent.json'}")
        print()
        self._print_config_values()
        print()
        self._print_rag_config()

    def _apply_config_params(self, new_cfg: dict) -> None:
        """Update ctx.cfg from new_cfg and sync values to all components."""
        ctx = self._ctx
        ctx.cfg.context_char_limit = int(new_cfg.get("context_char_limit", 8000))
        ctx.cfg.context_compress_turns = int(new_cfg.get("context_compress_turns", 4))
        ctx.cfg.tool_cache_ttl = float(new_cfg.get("tool_cache_ttl", 300))
        ctx.cfg.top_k_search = int(new_cfg.get("top_k_search", 20))
        ctx.cfg.top_k_rerank = int(new_cfg.get("top_k_rerank", 15))
        ctx.cfg.rag_top_k = int(new_cfg.get("rag_top_k", 5))
        ctx.cfg.use_mqe = bool(new_cfg.get("use_mqe", True))
        ctx.cfg.use_search = bool(new_cfg.get("use_search", True))
        ctx.cfg.use_rrf = bool(new_cfg.get("use_rrf", True))
        ctx.cfg.use_rerank = bool(new_cfg.get("use_rerank", True))
        ctx.cfg.llm_max_retries = int(new_cfg.get("llm_max_retries", 3))
        ctx.cfg.llm_retry_base_delay = float(new_cfg.get("llm_retry_base_delay", 1.0))
        ctx.cfg.rag_min_score = float(new_cfg.get("rag_min_score", 0.0))
        ctx.cfg.max_chunks_per_doc = int(new_cfg.get("max_chunks_per_doc", 2))
        ctx.cfg.use_two_stage_fetch = bool(new_cfg.get("use_two_stage_fetch", False))
        ctx.cfg.two_stage_max_docs = int(new_cfg.get("two_stage_max_docs", 2))
        ctx.cfg.serial_tool_calls = bool(new_cfg.get("serial_tool_calls", False))
        ctx.cfg.auto_inject_notes = bool(new_cfg.get("auto_inject_notes", True))
        ctx.cfg.use_tool_summarize = bool(new_cfg.get("use_tool_summarize", False))
        ctx.cfg.tool_summarize_threshold = int(
            new_cfg.get("tool_summarize_threshold", 3000)
        )
        ctx.cfg.use_semantic_cache = bool(new_cfg.get("use_semantic_cache", False))
        ctx.cfg.semantic_cache_threshold = float(
            new_cfg.get("semantic_cache_threshold", 0.92)
        )
        ctx.cfg.semantic_cache_max_size = int(
            new_cfg.get("semantic_cache_max_size", 100)
        )
        ctx.cfg.tool_definitions_strict = bool(
            new_cfg.get("tool_definitions_strict", False)
        )
        ctx.cfg.mcp_watchdog_interval = float(new_cfg.get("mcp_watchdog_interval", 0.0))
        ctx.cfg.mcp_watchdog_max_restarts = int(
            new_cfg.get("mcp_watchdog_max_restarts", 3)
        )
        if "approval_risk_rules" in new_cfg:
            ctx.cfg.approval_risk_rules = dict(new_cfg["approval_risk_rules"])
        if "approval_protected_paths" in new_cfg:
            ctx.cfg.approval_protected_paths = list(new_cfg["approval_protected_paths"])
        if "approval_high_risk_branches" in new_cfg:
            ctx.cfg.approval_high_risk_branches = list(
                new_cfg["approval_high_risk_branches"]
            )
        if "approval_shell_safe_prefixes" in new_cfg:
            ctx.cfg.approval_shell_safe_prefixes = list(
                new_cfg["approval_shell_safe_prefixes"]
            )
        ctx.cfg.masked_fields = list(new_cfg.get("masked_fields", ["file_content"]))
        # Update URLs for HTTP-transport servers without changing transport type.
        # Transport type changes require agent restart (subprocess lifecycle).
        from agent_config import _build_mcp_servers  # noqa: PLC0415

        new_mcp = _build_mcp_servers(new_cfg)
        for key, new_srv in new_mcp.items():
            old_srv = ctx.cfg.mcp_servers.get(key)
            if old_srv and old_srv.transport == "http" and new_srv.transport == "http":
                old_srv.url = new_srv.url
                old_srv.openrc_service = new_srv.openrc_service
        ctx.cfg.plan_blocked_tools = list(
            new_cfg.get(
                "plan_blocked_tools",
                ["write_file", "create_directory", "delete_file", "delete_directory"],
            )
        )
        ctx.cfg.llm_temperature = float(new_cfg.get("llm_temperature", 0.2))
        ctx.cfg.llm_max_tokens = int(new_cfg.get("llm_max_tokens", 1024))
        ctx.cfg.use_refiner = bool(new_cfg.get("use_refiner", False))
        ctx.cfg.refiner_max_tokens = int(new_cfg.get("refiner_max_tokens", 512))
        ctx.cfg.refiner_timeout = float(new_cfg.get("refiner_timeout", 30.0))
        ctx.cfg.refiner_max_chars_per_chunk = int(
            new_cfg.get("refiner_max_chars_per_chunk", 300)
        )
        # Hot-reloadable URL and prompt config
        ctx.cfg.llm_url = new_cfg.get("llm_url", ctx.cfg.llm_url)
        ctx.cfg.github_url = new_cfg.get("github_server_url", ctx.cfg.github_url)
        ctx.cfg.web_search_url = new_cfg.get("web_search_url", ctx.cfg.web_search_url)
        ctx.cfg.embed_url = new_cfg.get("embed_url", ctx.cfg.embed_url)
        ctx.cfg.http_timeout = float(new_cfg.get("http_timeout", ctx.cfg.http_timeout))
        ctx.cfg.web_search_max_results = int(
            new_cfg.get("web_search_max_results", ctx.cfg.web_search_max_results)
        )
        ctx.cfg.max_tool_turns = int(
            new_cfg.get("max_tool_turns", ctx.cfg.max_tool_turns)
        )
        ctx.cfg.tool_result_max_llm_chars = int(
            new_cfg.get("tool_result_max_llm_chars", ctx.cfg.tool_result_max_llm_chars)
        )
        if new_cfg.get("tool_definitions"):
            ctx.cfg.tool_definitions = list(new_cfg["tool_definitions"])
        system_prompt_tool = new_cfg.get("system_prompt_tool", "")
        if system_prompt_tool:
            ctx.cfg.system_prompt_tool = system_prompt_tool
        if new_cfg.get("system_prompts"):
            ctx.cfg.system_prompts = dict(new_cfg["system_prompts"])
        if ctx.services.llm is not None:
            ctx.services.llm._max_retries = ctx.cfg.llm_max_retries
            ctx.services.llm._retry_base_delay = ctx.cfg.llm_retry_base_delay
            ctx.services.llm._temperature = ctx.cfg.llm_temperature
            ctx.services.llm._max_tokens = ctx.cfg.llm_max_tokens
        if ctx.services.hist_mgr is not None:
            ctx.services.hist_mgr._char_limit = ctx.cfg.context_char_limit
            ctx.services.hist_mgr._compress_turns = ctx.cfg.context_compress_turns
        if ctx.services.tools is not None:
            ctx.services.tools._cache_ttl = ctx.cfg.tool_cache_ttl
        if ctx.history and ctx.history[0]["role"] == "system":
            ctx.history[0]["content"] = new_cfg.get(
                "system_prompt_tool", ctx.history[0]["content"]
            )

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
                "Use: /set temperature <float> | /set max_tokens <int>"
            )
            return
        if len(parts) != 2:
            print("Usage: /set temperature <float> | /set max_tokens <int>")
            return
        param, value_str = parts
        if param == "temperature":
            try:
                val = float(value_str)
                if not 0.0 <= val <= 2.0:
                    raise ValueError
            except ValueError:
                print("temperature must be a float in [0.0, 2.0]")
                return
            ctx.cfg.llm_temperature = val
            if ctx.services.llm is not None:
                ctx.services.llm._temperature = val
            logger.info(f"llm_temperature set to {val}")
            print(f"temperature set to {val}")
        elif param == "max_tokens":
            try:
                val = int(value_str)
                if val < 1:
                    raise ValueError
            except ValueError:
                print("max_tokens must be a positive integer")
                return
            ctx.cfg.llm_max_tokens = val
            if ctx.services.llm is not None:
                ctx.services.llm._max_tokens = val
            logger.info(f"llm_max_tokens set to {val}")
            print(f"max_tokens set to {val}")
        else:
            print(f"Unknown parameter: {param!r}")
            print("Settable: temperature, max_tokens")

    def _cmd_reload(self) -> None:
        """Reload config/agent.json and apply runtime-configurable parameters.

        Updates ctx.cfg fields and syncs them to each component so changes
        take effect immediately without restarting the agent.
        """
        try:
            new_cfg = ConfigLoader().load("common.json", "agent.json")
            self._apply_config_params(new_cfg)
            logger.info("Config reloaded")
            print("Config reloaded.")
        except Exception as e:
            logger.warning(f"Config reload failed: {e}")
            print(f"Reload failed: {e}")
