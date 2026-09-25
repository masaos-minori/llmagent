#!/usr/bin/env python3
"""scripts/agent/commands/cmd_config_display.py

Config display helpers for _ConfigMixin.

Provides:
  _print_llm_settings          — LLM endpoint settings
  _print_sse_settings          — SSE stream settings
  _print_execution_settings    — Execution settings
  _print_mcp_settings          — MCP / security settings
  _print_approval_settings     — Approval settings
 _print_tool_safety_settings  — Tool safety settings
   _print_config_values         — Combined config display
  _print_rag_config            — Retrieval/DB settings
  _cmd_config                  — /config dispatcher

Import from here:  from agent.commands.cmd_config_display import _ConfigDisplayMixin
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.commands.mixin_base import MixinBase

if TYPE_CHECKING:
    from agent.context import AgentContext


class _ConfigDisplayMixin(MixinBase):
    """Config display helpers for slash commands."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the config display mixin via MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _print_llm_settings(self, ctx: AgentContext) -> None:
        """Print LLM endpoint and core settings."""
        self._out.write("Settings:")
        pairs = [
            ("llm_url", str(ctx.cfg.llm.llm_url)),
            ("max_tool_turns", str(ctx.cfg.tool.max_tool_turns)),
            ("http_timeout", f"{ctx.cfg.llm.http_timeout}s"),
            ("context_char_limit", str(ctx.cfg.llm.context_char_limit)),
            ("context_compress", f"{ctx.cfg.llm.context_compress_turns} turn pairs"),
            ("llm_max_retries", str(ctx.cfg.llm.llm_max_retries)),
            ("llm_retry_base_delay", f"{ctx.cfg.llm.llm_retry_base_delay}s"),
            ("llm_temperature", str(ctx.cfg.llm.llm_temperature)),
            ("llm_max_tokens", str(ctx.cfg.llm.llm_max_tokens)),
        ]
        self._out.write_kv(pairs, key_width=20)

    def _print_sse_settings(self, ctx: AgentContext) -> None:
        """Print SSE streaming settings."""
        self._out.write("SSE stream settings:")
        pairs = [
            ("sse_heartbeat_timeout", f"{ctx.cfg.llm.sse_heartbeat_timeout}s"),
            ("sse_malformed_retry", str(ctx.cfg.llm.sse_malformed_retry)),
            ("sse_reconnect_max", str(ctx.cfg.llm.sse_reconnect_max)),
            (
                "llm_stream_retry_on_heartbeat_timeout",
                str(ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout),
            ),
            (
                "llm_stream_retry_on_malformed_chunk",
                str(ctx.cfg.llm.llm_stream_retry_on_malformed_chunk),
            ),
        ]
        self._out.write_kv(pairs, key_width=35)

    def _print_execution_settings(self, ctx: AgentContext) -> None:
        """Print execution settings."""
        self._out.write("Execution settings:")
        self._out.write_kv(
            [("serial_tool_calls", str(ctx.cfg.tool.serial_tool_calls))], key_width=20
        )

    def _print_mcp_settings(self, ctx: AgentContext) -> None:
        """Print MCP and security settings."""
        self._out.write("MCP / security settings:")
        self._out.write_kv(
            [("tool_def_strict", str(ctx.cfg.tool.tool_definitions_strict))],
            key_width=20,
        )

    def _print_approval_settings(self, ctx: AgentContext) -> None:
        """Print approval and risk rule settings."""
        self._out.write("Approval settings:")
        rules = ctx.cfg.approval.approval_risk_rules
        if rules:
            rule_str = ", ".join(f"{k}={v}" for k, v in sorted(rules.items()))
            pairs = [("risk_rules", rule_str)]
        else:
            pairs = [("risk_rules", "(none)")]
        pairs.extend(
            [
                (
                    "protected_paths",
                    ", ".join(ctx.cfg.approval.approval_protected_paths),
                ),
                (
                    "high_risk_branches",
                    ", ".join(ctx.cfg.approval.approval_high_risk_branches),
                ),
            ]
        )
        dry_run_tools = ctx.cfg.approval.approval_dry_run_tools
        masked = ctx.cfg.tool.masked_fields
        pairs.append(
            ("dry_run_tools", ", ".join(dry_run_tools) if dry_run_tools else "(none)")
        )
        pairs.append(("masked_fields", ", ".join(masked) if masked else "(none)"))
        self._out.write_kv(pairs, key_width=20)

    def _print_tool_safety_settings(self, ctx: AgentContext) -> None:
        """Print tool safety and allowed-tools settings."""
        self._out.write("Security settings (tool safety):")
        allowed_root = ctx.cfg.approval.allowed_root
        allowed_root_str = repr(allowed_root) if allowed_root else "(disabled)"
        pairs = [("allowed_root", allowed_root_str)]
        allowed_repos = ctx.cfg.approval.approval_github_allowed_repos
        if allowed_repos:
            pairs.append(("github_allowed_repos", ", ".join(allowed_repos)))
        else:
            pairs.append(
                ("github_allowed_repos", "(Fail-Closed — all write ops denied)")
            )
        tier_count = len(ctx.cfg.approval.tool_safety_tiers)
        pairs.append(("tool_safety_tiers", f"{tier_count} tools classified"))
        allowed_tools = ctx.cfg.tool.allowed_tools
        if allowed_tools:
            pairs.append(("allowed_tools", ", ".join(allowed_tools)))
        else:
            pairs.append(("allowed_tools", "(unrestricted)"))
        plan_blocked = ctx.cfg.tool.plan_blocked_tools
        plan_state = "ON" if ctx.conv.plan_mode else "OFF"
        pairs.append(("plan_mode", plan_state))
        self._out.write_kv(pairs, key_width=20)
        if plan_blocked:
            self._out.write("  plan_blocked_tools  :")
            for t in plan_blocked:
                self._out.write(f"    - {t}")
        else:
            self._out.write("  plan_blocked_tools  : (none)")

    def _print_memory_settings(self, ctx: AgentContext) -> None:
        """Print memory layer configuration settings."""
        self._out.write("Memory layer settings:")
        pairs = [
            ("use_memory_layer", str(ctx.cfg.memory.use_memory_layer)),
            ("memory_embed_enabled", str(ctx.cfg.memory.memory_embed_enabled)),
            ("memory_jsonl_dir", ctx.cfg.memory.memory_jsonl_dir or "(not set)"),
            ("max_inject_semantic", str(ctx.cfg.memory.memory_max_inject_semantic)),
            ("max_inject_episodic", str(ctx.cfg.memory.memory_max_inject_episodic)),
            ("min_importance", str(ctx.cfg.memory.memory_min_importance)),
        ]
        self._out.write_kv(pairs, key_width=20)

    def _print_config_values(self) -> None:
        """Print static endpoint/LLM settings and execution settings."""
        ctx = self._ctx
        self._print_llm_settings(ctx)
        self._out.write("")
        self._print_sse_settings(ctx)
        self._out.write("")
        self._print_execution_settings(ctx)
        self._out.write("")
        self._print_mcp_settings(ctx)
        self._print_approval_settings(ctx)
        self._out.write("")
        self._print_tool_safety_settings(ctx)
        self._out.write("")
        self._print_memory_settings(ctx)

    def _print_rag_config(self) -> None:
        """Print retrieval settings including DB path and search parameters."""
        self._out.write("Search settings:")
        from db.config import (
            build_db_config as _build_db_cfg,  # lazy
        )

        try:
            _db_cfg = _build_db_cfg()
            pairs = [
                ("rag_db_path", _db_cfg.rag_db_path),
                ("session_db_path", _db_cfg.session_db_path),
            ]
            self._out.write_kv(pairs, key_width=20)
        except (ValueError, RuntimeError) as e:
            pairs = [
                ("rag_db_path", f"(config error: {e})"),
                ("session_db_path", f"(config error: {e})"),
            ]
            self._out.write_kv(pairs, key_width=20)

    def _cmd_config(self) -> None:
        """Print current configuration and source file paths."""
        from agent.config_builders import (
            _CONFIG_DIR,  # lazy: avoids circular import at module level
        )

        self._out.write("Config files:")
        self._out.write(
            f"  {_CONFIG_DIR} (common.toml, llm.toml, rag.toml, security.toml, tools.toml, ...)"
        )
        self._out.write("")
        self._print_config_values()
        self._out.write("")
        self._print_rag_config()
