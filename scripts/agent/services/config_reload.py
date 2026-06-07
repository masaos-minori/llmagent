"""agent/services/config_reload.py
ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  sync_services()      — propagate already-updated cfg to live service instances

Both return ConfigReloadResult so callers can display what changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass
class ConfigReloadResult:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Uses public apply_config() APIs on each service — never writes private attrs.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    # ── Public entry point ────────────────────────────────────────────────────

    def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadResult:
        """Update ctx.cfg from new_cfg, sync live services, return a report.

        Replaces _apply_config_params() + all _apply_* helpers from _ConfigMixin.
        The command handler only calls this method and renders the result.
        """
        ctx = self._ctx
        self._apply_rag_tool_params(ctx, new_cfg)
        self._reload_approval_settings(ctx, new_cfg)
        ctx.cfg.tool.masked_fields = list(
            new_cfg.get("masked_fields", ["file_content"])
        )
        result = self._apply_mcp_url_reload(ctx, new_cfg)
        self._apply_llm_prompt_params(ctx, new_cfg)
        self._apply_sse_reload_params(ctx, new_cfg)
        service_result = self.sync_services(new_cfg)
        result.applied.extend(service_result.applied)
        result.skipped.extend(service_result.skipped)
        return result

    # ── Service sync (called by apply_config_dict and directly by legacy code) ─

    def sync_services(self, new_cfg: dict[str, Any]) -> ConfigReloadResult:
        """Apply new_cfg values to running service instances; return a report."""
        result = ConfigReloadResult()
        ctx = self._ctx

        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(
                temperature=ctx.cfg.llm.llm_temperature,
                max_tokens=ctx.cfg.llm.llm_max_tokens,
                max_retries=ctx.cfg.llm.llm_max_retries,
                retry_base_delay=ctx.cfg.llm.llm_retry_base_delay,
                sse_heartbeat_timeout=ctx.cfg.llm.sse_heartbeat_timeout,
                sse_malformed_retry=ctx.cfg.llm.sse_malformed_retry,
                sse_reconnect_max=ctx.cfg.llm.sse_reconnect_max,
                stream_retry_on_heartbeat_timeout=ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
                stream_retry_on_malformed_chunk=ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
            )
            result.applied.append("llm")

        if ctx.services.hist_mgr is not None:
            ctx.services.hist_mgr.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if ctx.services.tools is not None:
            ctx.services.tools.apply_config(cache_ttl=ctx.cfg.tool.tool_cache_ttl)
            result.applied.append("tools")

        # system_prompt update: write to the canonical field; Orchestrator syncs history[0].
        if "system_prompt_tool" in new_cfg:
            ctx.conv.system_prompt_content = new_cfg["system_prompt_tool"]

        return result

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

    def _apply_rag_tool_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply tool cache, LLM retry, refiner, and watchdog settings."""
        ctx.cfg.llm.context_char_limit = int(new_cfg.get("context_char_limit", 8000))
        ctx.cfg.llm.context_compress_turns = int(
            new_cfg.get("context_compress_turns", 4)
        )
        ctx.cfg.tool.tool_cache_ttl = float(new_cfg.get("tool_cache_ttl", 300))
        ctx.cfg.rag.top_k_search = int(new_cfg.get("top_k_search", 20))
        ctx.cfg.rag.top_k_rerank = int(new_cfg.get("top_k_rerank", 15))
        ctx.cfg.llm.llm_max_retries = int(new_cfg.get("llm_max_retries", 3))
        ctx.cfg.llm.llm_retry_base_delay = float(
            new_cfg.get("llm_retry_base_delay", 1.0)
        )
        ctx.cfg.rag.max_chunks_per_doc = int(new_cfg.get("max_chunks_per_doc", 2))
        ctx.cfg.tool.serial_tool_calls = bool(new_cfg.get("serial_tool_calls", False))
        ctx.cfg.tool.auto_inject_notes = bool(new_cfg.get("auto_inject_notes", True))
        ctx.cfg.tool.use_tool_summarize = bool(new_cfg.get("use_tool_summarize", False))
        ctx.cfg.tool.tool_summarize_threshold = int(
            new_cfg.get("tool_summarize_threshold", 3000),
        )
        ctx.cfg.rag.use_semantic_cache = bool(new_cfg.get("use_semantic_cache", False))
        ctx.cfg.rag.semantic_cache_threshold = float(
            new_cfg.get("semantic_cache_threshold", 0.92),
        )
        ctx.cfg.rag.semantic_cache_max_size = int(
            new_cfg.get("semantic_cache_max_size", 100)
        )
        ctx.cfg.tool.tool_definitions_strict = bool(
            new_cfg.get("tool_definitions_strict", False),
        )
        ctx.cfg.mcp.mcp_watchdog_interval = float(
            new_cfg.get("mcp_watchdog_interval", 0.0)
        )
        ctx.cfg.mcp.mcp_watchdog_max_restarts = int(
            new_cfg.get("mcp_watchdog_max_restarts", 3)
        )
        ctx.cfg.tool.plan_blocked_tools = list(
            new_cfg.get(
                "plan_blocked_tools",
                ["write_file", "create_directory", "delete_file", "delete_directory"],
            ),
        )
        ctx.cfg.rag.use_refiner = bool(new_cfg.get("use_refiner", False))
        ctx.cfg.rag.refiner_max_tokens = int(new_cfg.get("refiner_max_tokens", 512))
        ctx.cfg.rag.refiner_timeout = float(new_cfg.get("refiner_timeout", 30.0))
        ctx.cfg.rag.refiner_max_chars_per_chunk = int(
            new_cfg.get("refiner_max_chars_per_chunk", 300),
        )

    def _apply_mcp_url_reload(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadResult:
        """Update HTTP MCP server URLs; classify transport changes as needs_restart."""
        from agent.config import _build_mcp_servers  # noqa: PLC0415

        result = ConfigReloadResult()
        new_mcp = _build_mcp_servers(new_cfg)
        for key, new_srv in new_mcp.items():
            old_srv = ctx.cfg.mcp.mcp_servers.get(key)
            if old_srv is None:
                result.skipped.append(f"mcp/{key} (new server — restart required)")
                result.needs_restart.append(key)
            elif old_srv.transport != new_srv.transport:
                # Transport type change cannot be applied at runtime
                result.needs_restart.append(key)
            elif old_srv.transport == "http" and new_srv.transport == "http":
                old_srv.url = new_srv.url
                old_srv.openrc_service = new_srv.openrc_service
                result.applied.append(f"mcp/{key}")
        return result

    def _apply_llm_prompt_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings."""
        ctx.cfg.llm.llm_temperature = float(new_cfg.get("llm_temperature", 0.2))
        ctx.cfg.llm.llm_max_tokens = int(new_cfg.get("llm_max_tokens", 1024))
        ctx.cfg.llm.llm_url = new_cfg.get("llm_url", ctx.cfg.llm.llm_url)
        ctx.cfg.mcp.github_url = new_cfg.get(
            "github_server_url", ctx.cfg.mcp.github_url
        )
        ctx.cfg.rag.web_search_url = new_cfg.get(
            "web_search_url", ctx.cfg.rag.web_search_url
        )
        ctx.cfg.rag.embed_url = new_cfg.get("embed_url", ctx.cfg.rag.embed_url)
        ctx.cfg.llm.http_timeout = float(
            new_cfg.get("http_timeout", ctx.cfg.llm.http_timeout)
        )
        ctx.cfg.rag.web_search_max_results = int(
            new_cfg.get("web_search_max_results", ctx.cfg.rag.web_search_max_results),
        )
        ctx.cfg.tool.max_tool_turns = int(
            new_cfg.get("max_tool_turns", ctx.cfg.tool.max_tool_turns),
        )
        ctx.cfg.tool.tool_result_max_llm_chars = int(
            new_cfg.get(
                "tool_result_max_llm_chars", ctx.cfg.tool.tool_result_max_llm_chars
            ),
        )
        if new_cfg.get("tool_definitions"):
            ctx.cfg.tool.tool_definitions = list(new_cfg["tool_definitions"])
        system_prompt_tool = new_cfg.get("system_prompt_tool", "")
        if system_prompt_tool:
            ctx.cfg.tool.system_prompt_tool = system_prompt_tool
        if new_cfg.get("system_prompts"):
            ctx.cfg.tool.system_prompts = dict(new_cfg["system_prompts"])

    def _apply_sse_reload_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply SSE stream resilience settings."""
        ctx.cfg.llm.sse_heartbeat_timeout = float(
            new_cfg.get("sse_heartbeat_timeout", ctx.cfg.llm.sse_heartbeat_timeout),
        )
        ctx.cfg.llm.sse_malformed_retry = int(
            new_cfg.get("sse_malformed_retry", ctx.cfg.llm.sse_malformed_retry),
        )
        ctx.cfg.llm.sse_reconnect_max = int(
            new_cfg.get("sse_reconnect_max", ctx.cfg.llm.sse_reconnect_max),
        )
        ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = bool(
            new_cfg.get(
                "llm_stream_retry_on_heartbeat_timeout",
                ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
            ),
        )
        ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = bool(
            new_cfg.get(
                "llm_stream_retry_on_malformed_chunk",
                ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
            ),
        )

    def _reload_approval_config(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update ApprovalConfig fields in ctx.cfg when present in new_cfg."""
        approval = ctx.cfg.approval
        if "approval_risk_rules" in new_cfg:
            approval.approval_risk_rules = dict(new_cfg["approval_risk_rules"])
        if "approval_protected_paths" in new_cfg:
            approval.approval_protected_paths = list(
                new_cfg["approval_protected_paths"]
            )
        if "approval_high_risk_branches" in new_cfg:
            approval.approval_high_risk_branches = list(
                new_cfg["approval_high_risk_branches"]
            )
        if "approval_shell_safe_prefixes" in new_cfg:
            approval.approval_shell_safe_prefixes = list(
                new_cfg["approval_shell_safe_prefixes"]
            )
        if "approval_resource_keys" in new_cfg:
            approval.approval_resource_keys = dict(new_cfg["approval_resource_keys"])
        if "approval_dry_run_tools" in new_cfg:
            approval.approval_dry_run_tools = list(new_cfg["approval_dry_run_tools"])
        if "tool_safety_tiers" in new_cfg:
            approval.tool_safety_tiers = dict(new_cfg["tool_safety_tiers"])
        approval.allowed_root = new_cfg.get("allowed_root", approval.allowed_root)
        if "approval_github_allowed_repos" in new_cfg:
            approval.approval_github_allowed_repos = list(
                new_cfg["approval_github_allowed_repos"]
            )

    def _reload_approval_settings(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update approval, tool, and memory config fields when present in new_cfg."""
        self._reload_approval_config(ctx, new_cfg)
        if "allowed_tools" in new_cfg:
            ctx.cfg.tool.allowed_tools = list(new_cfg["allowed_tools"])
        if "memory_retention_days" in new_cfg:
            ctx.cfg.memory.memory_retention_days = int(new_cfg["memory_retention_days"])
