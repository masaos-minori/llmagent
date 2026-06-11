"""agent/services/config_reload.py
ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)

Both return ConfigReloadResult so callers can display what changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass
class ConfigReloadOutcome:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


ConfigReloadResult = ConfigReloadOutcome


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Uses public apply_config() APIs on each service — never writes private attrs.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    # ── Public entry point ────────────────────────────────────────────────────

    def apply_config(self, req: ConfigReloadRequest) -> ConfigReloadOutcome:
        """Update ctx.cfg from a typed ConfigReloadRequest, sync services, return a report.

        Raises ConfigReloadValidationError on type-level field violations.
        """
        if req.masked_fields is not None and not isinstance(req.masked_fields, list):
            raise ConfigReloadValidationError(
                f"masked_fields must be a list, got {type(req.masked_fields).__name__}"
            )
        new_cfg = self._req_to_dict(req)
        return self.apply_config_dict(new_cfg)

    def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
        """Update ctx.cfg from new_cfg, sync live services, return a report.

        Replaces _apply_config_params() + all _apply_* helpers from _ConfigMixin.
        The command handler only calls this method and renders the result.
        """
        ctx = self._ctx
        self._apply_rag_tool_params(ctx, new_cfg)
        self._reload_approval_settings(ctx, new_cfg)
        if "masked_fields" in new_cfg:
            ctx.cfg.tool.masked_fields = list(new_cfg["masked_fields"])
        result = self._apply_mcp_url_reload(ctx, new_cfg)
        self._apply_llm_prompt_params(ctx, new_cfg)
        self._apply_sse_reload_params(ctx, new_cfg)
        service_result = self._sync_services(new_cfg)
        result.applied.extend(service_result.applied)
        result.skipped.extend(service_result.skipped)
        return result

    @staticmethod
    def _req_to_dict(req: ConfigReloadRequest) -> dict[str, Any]:
        """Convert ConfigReloadRequest to the raw dict format expected by _apply_* helpers."""
        d: dict[str, Any] = {}
        if req.mcp_servers is not None:
            d["mcp_servers"] = req.mcp_servers
        if req.approval is not None:
            d["approval"] = req.approval
        if req.llm is not None:
            d.update(req.llm)
        if req.masked_fields is not None:
            d["masked_fields"] = req.masked_fields
        if req.rag_tool is not None:
            d.update(req.rag_tool)
        if req.sse is not None:
            d.update(req.sse)
        return d

    # ── Service sync ──────────────────────────────────────────────────────────

    def _sync_services(self, new_cfg: dict[str, Any]) -> ConfigReloadResult:
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
        """Apply tool cache, LLM retry, refiner, and watchdog settings (diff-apply)."""
        if "context_char_limit" in new_cfg:
            ctx.cfg.llm.context_char_limit = int(new_cfg["context_char_limit"])
        if "context_compress_turns" in new_cfg:
            ctx.cfg.llm.context_compress_turns = int(new_cfg["context_compress_turns"])
        if "tool_cache_ttl" in new_cfg:
            ctx.cfg.tool.tool_cache_ttl = float(new_cfg["tool_cache_ttl"])
        if "top_k_search" in new_cfg:
            ctx.cfg.rag.top_k_search = int(new_cfg["top_k_search"])
        if "top_k_rerank" in new_cfg:
            ctx.cfg.rag.top_k_rerank = int(new_cfg["top_k_rerank"])
        if "llm_max_retries" in new_cfg:
            ctx.cfg.llm.llm_max_retries = int(new_cfg["llm_max_retries"])
        if "llm_retry_base_delay" in new_cfg:
            ctx.cfg.llm.llm_retry_base_delay = float(new_cfg["llm_retry_base_delay"])
        if "max_chunks_per_doc" in new_cfg:
            ctx.cfg.rag.max_chunks_per_doc = int(new_cfg["max_chunks_per_doc"])
        if "serial_tool_calls" in new_cfg:
            ctx.cfg.tool.serial_tool_calls = bool(new_cfg["serial_tool_calls"])
        if "auto_inject_notes" in new_cfg:
            ctx.cfg.tool.auto_inject_notes = bool(new_cfg["auto_inject_notes"])
        if "use_tool_summarize" in new_cfg:
            ctx.cfg.tool.use_tool_summarize = bool(new_cfg["use_tool_summarize"])
        if "tool_summarize_threshold" in new_cfg:
            ctx.cfg.tool.tool_summarize_threshold = int(
                new_cfg["tool_summarize_threshold"]
            )
        if "use_semantic_cache" in new_cfg:
            ctx.cfg.rag.use_semantic_cache = bool(new_cfg["use_semantic_cache"])
        if "semantic_cache_threshold" in new_cfg:
            ctx.cfg.rag.semantic_cache_threshold = float(
                new_cfg["semantic_cache_threshold"]
            )
        if "semantic_cache_max_size" in new_cfg:
            ctx.cfg.rag.semantic_cache_max_size = int(
                new_cfg["semantic_cache_max_size"]
            )
        if "tool_definitions_strict" in new_cfg:
            ctx.cfg.tool.tool_definitions_strict = bool(
                new_cfg["tool_definitions_strict"]
            )
        if "mcp_watchdog_interval" in new_cfg:
            ctx.cfg.mcp.mcp_watchdog_interval = float(new_cfg["mcp_watchdog_interval"])
        if "mcp_watchdog_max_restarts" in new_cfg:
            ctx.cfg.mcp.mcp_watchdog_max_restarts = int(
                new_cfg["mcp_watchdog_max_restarts"]
            )
        if "plan_blocked_tools" in new_cfg:
            ctx.cfg.tool.plan_blocked_tools = list(new_cfg["plan_blocked_tools"])
        if "use_refiner" in new_cfg:
            ctx.cfg.rag.use_refiner = bool(new_cfg["use_refiner"])
        if "refiner_max_tokens" in new_cfg:
            ctx.cfg.rag.refiner_max_tokens = int(new_cfg["refiner_max_tokens"])
        if "refiner_timeout" in new_cfg:
            ctx.cfg.rag.refiner_timeout = float(new_cfg["refiner_timeout"])
        if "refiner_max_chars_per_chunk" in new_cfg:
            ctx.cfg.rag.refiner_max_chars_per_chunk = int(
                new_cfg["refiner_max_chars_per_chunk"]
            )

    def _apply_mcp_url_reload(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadResult:
        """Update HTTP MCP server URLs; classify transport changes as needs_restart."""
        from agent.config import (
            _build_mcp_servers,  # noqa: PLC0415 — lazy: avoids circular import at module level
        )

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
        """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings (diff-apply)."""
        if "llm_temperature" in new_cfg:
            ctx.cfg.llm.llm_temperature = float(new_cfg["llm_temperature"])
        if "llm_max_tokens" in new_cfg:
            ctx.cfg.llm.llm_max_tokens = int(new_cfg["llm_max_tokens"])
        if "llm_url" in new_cfg:
            ctx.cfg.llm.llm_url = new_cfg["llm_url"]
        if "github_server_url" in new_cfg:
            ctx.cfg.mcp.github_url = new_cfg["github_server_url"]
        if "web_search_url" in new_cfg:
            ctx.cfg.rag.web_search_url = new_cfg["web_search_url"]
        if "embed_url" in new_cfg:
            ctx.cfg.rag.embed_url = new_cfg["embed_url"]
        if "http_timeout" in new_cfg:
            ctx.cfg.llm.http_timeout = float(new_cfg["http_timeout"])
        if "web_search_max_results" in new_cfg:
            ctx.cfg.rag.web_search_max_results = int(new_cfg["web_search_max_results"])
        if "max_tool_turns" in new_cfg:
            ctx.cfg.tool.max_tool_turns = int(new_cfg["max_tool_turns"])
        if "tool_result_max_llm_chars" in new_cfg:
            ctx.cfg.tool.tool_result_max_llm_chars = int(
                new_cfg["tool_result_max_llm_chars"]
            )
        if new_cfg.get("tool_definitions"):
            ctx.cfg.tool.tool_definitions = list(new_cfg["tool_definitions"])
        if new_cfg.get("system_prompt_tool"):
            ctx.cfg.tool.system_prompt_tool = new_cfg["system_prompt_tool"]
        if new_cfg.get("system_prompts"):
            ctx.cfg.tool.system_prompts = dict(new_cfg["system_prompts"])

    def _apply_sse_reload_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply SSE stream resilience settings (diff-apply)."""
        if "sse_heartbeat_timeout" in new_cfg:
            ctx.cfg.llm.sse_heartbeat_timeout = float(new_cfg["sse_heartbeat_timeout"])
        if "sse_malformed_retry" in new_cfg:
            ctx.cfg.llm.sse_malformed_retry = int(new_cfg["sse_malformed_retry"])
        if "sse_reconnect_max" in new_cfg:
            ctx.cfg.llm.sse_reconnect_max = int(new_cfg["sse_reconnect_max"])
        if "llm_stream_retry_on_heartbeat_timeout" in new_cfg:
            ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = bool(
                new_cfg["llm_stream_retry_on_heartbeat_timeout"]
            )
        if "llm_stream_retry_on_malformed_chunk" in new_cfg:
            ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = bool(
                new_cfg["llm_stream_retry_on_malformed_chunk"]
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
