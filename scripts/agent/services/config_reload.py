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


# ── Typed boundary extraction helpers ────────────────────────────────────────


def _get_int(d: dict[str, Any], key: str) -> int | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v


def _get_float(d: dict[str, Any], key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be float, got {type(v).__name__}"
        )
    return float(v)


def _get_bool(d: dict[str, Any], key: str) -> bool | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be bool, got {type(v).__name__}"
        )
    return v


def _get_str(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, str):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be str, got {type(v).__name__}"
        )
    return v


def _get_list(d: dict[str, Any], key: str) -> list[Any] | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, list):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be list, got {type(v).__name__}"
        )
    return v


def _get_dict(d: dict[str, Any], key: str) -> dict[str, Any] | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, dict):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be dict, got {type(v).__name__}"
        )
    return v


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
        if (vi := _get_int(new_cfg, "context_char_limit")) is not None:
            ctx.cfg.llm.context_char_limit = vi
        if (vi := _get_int(new_cfg, "context_compress_turns")) is not None:
            ctx.cfg.llm.context_compress_turns = vi
        if (vf := _get_float(new_cfg, "tool_cache_ttl")) is not None:
            ctx.cfg.tool.tool_cache_ttl = vf
        if (vi := _get_int(new_cfg, "top_k_search")) is not None:
            ctx.cfg.rag.top_k_search = vi
        if (vi := _get_int(new_cfg, "top_k_rerank")) is not None:
            ctx.cfg.rag.top_k_rerank = vi
        if (vi := _get_int(new_cfg, "llm_max_retries")) is not None:
            ctx.cfg.llm.llm_max_retries = vi
        if (vf := _get_float(new_cfg, "llm_retry_base_delay")) is not None:
            ctx.cfg.llm.llm_retry_base_delay = vf
        if (vi := _get_int(new_cfg, "max_chunks_per_doc")) is not None:
            ctx.cfg.rag.max_chunks_per_doc = vi
        if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
            ctx.cfg.tool.serial_tool_calls = vb
        if (vb := _get_bool(new_cfg, "auto_inject_notes")) is not None:
            ctx.cfg.tool.auto_inject_notes = vb
        if (vb := _get_bool(new_cfg, "use_tool_summarize")) is not None:
            ctx.cfg.tool.use_tool_summarize = vb
        if (vi := _get_int(new_cfg, "tool_summarize_threshold")) is not None:
            ctx.cfg.tool.tool_summarize_threshold = vi
        if (vb := _get_bool(new_cfg, "use_semantic_cache")) is not None:
            ctx.cfg.rag.use_semantic_cache = vb
        if (vf := _get_float(new_cfg, "semantic_cache_threshold")) is not None:
            ctx.cfg.rag.semantic_cache_threshold = vf
        if (vi := _get_int(new_cfg, "semantic_cache_max_size")) is not None:
            ctx.cfg.rag.semantic_cache_max_size = vi
        if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
            ctx.cfg.tool.tool_definitions_strict = vb
        if (vf := _get_float(new_cfg, "mcp_watchdog_interval")) is not None:
            ctx.cfg.mcp.mcp_watchdog_interval = vf
        if (vi := _get_int(new_cfg, "mcp_watchdog_max_restarts")) is not None:
            ctx.cfg.mcp.mcp_watchdog_max_restarts = vi
        if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
            ctx.cfg.tool.plan_blocked_tools = list(lst)
        if (vb := _get_bool(new_cfg, "use_refiner")) is not None:
            ctx.cfg.rag.use_refiner = vb
        if (vi := _get_int(new_cfg, "refiner_max_tokens")) is not None:
            ctx.cfg.rag.refiner_max_tokens = vi
        if (vf := _get_float(new_cfg, "refiner_timeout")) is not None:
            ctx.cfg.rag.refiner_timeout = vf
        if (vi := _get_int(new_cfg, "refiner_max_chars_per_chunk")) is not None:
            ctx.cfg.rag.refiner_max_chars_per_chunk = vi

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
        if (vf := _get_float(new_cfg, "llm_temperature")) is not None:
            ctx.cfg.llm.llm_temperature = vf
        if (vi := _get_int(new_cfg, "llm_max_tokens")) is not None:
            ctx.cfg.llm.llm_max_tokens = vi
        if (vs := _get_str(new_cfg, "llm_url")) is not None:
            ctx.cfg.llm.llm_url = vs
        if (vs := _get_str(new_cfg, "github_server_url")) is not None:
            ctx.cfg.mcp.github_url = vs
        if (vs := _get_str(new_cfg, "web_search_url")) is not None:
            ctx.cfg.rag.web_search_url = vs
        if (vs := _get_str(new_cfg, "embed_url")) is not None:
            ctx.cfg.rag.embed_url = vs
        if (vf := _get_float(new_cfg, "http_timeout")) is not None:
            ctx.cfg.llm.http_timeout = vf
        if (vi := _get_int(new_cfg, "web_search_max_results")) is not None:
            ctx.cfg.rag.web_search_max_results = vi
        if (vi := _get_int(new_cfg, "max_tool_turns")) is not None:
            ctx.cfg.tool.max_tool_turns = vi
        if (vi := _get_int(new_cfg, "tool_result_max_llm_chars")) is not None:
            ctx.cfg.tool.tool_result_max_llm_chars = vi
        if (lst := _get_list(new_cfg, "tool_definitions")) is not None and lst:
            ctx.cfg.tool.tool_definitions = list(lst)
        if (vs := _get_str(new_cfg, "system_prompt_tool")) is not None and vs:
            ctx.cfg.tool.system_prompt_tool = vs
        if (d := _get_dict(new_cfg, "system_prompts")) is not None and d:
            ctx.cfg.tool.system_prompts = dict(d)

    def _apply_sse_reload_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply SSE stream resilience settings (diff-apply)."""
        if (vf := _get_float(new_cfg, "sse_heartbeat_timeout")) is not None:
            ctx.cfg.llm.sse_heartbeat_timeout = vf
        if (vi := _get_int(new_cfg, "sse_malformed_retry")) is not None:
            ctx.cfg.llm.sse_malformed_retry = vi
        if (vi := _get_int(new_cfg, "sse_reconnect_max")) is not None:
            ctx.cfg.llm.sse_reconnect_max = vi
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_heartbeat_timeout")
        ) is not None:
            ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout = vb
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_malformed_chunk")
        ) is not None:
            ctx.cfg.llm.llm_stream_retry_on_malformed_chunk = vb

    def _reload_approval_config(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update ApprovalConfig fields in ctx.cfg when present in new_cfg."""
        approval = ctx.cfg.approval
        if (d := _get_dict(new_cfg, "approval_risk_rules")) is not None:
            approval.approval_risk_rules = dict(d)
        if (lst := _get_list(new_cfg, "approval_protected_paths")) is not None:
            approval.approval_protected_paths = list(lst)
        if (lst := _get_list(new_cfg, "approval_high_risk_branches")) is not None:
            approval.approval_high_risk_branches = list(lst)
        if (lst := _get_list(new_cfg, "approval_shell_safe_prefixes")) is not None:
            approval.approval_shell_safe_prefixes = list(lst)
        if (d := _get_dict(new_cfg, "approval_resource_keys")) is not None:
            approval.approval_resource_keys = dict(d)
        if (lst := _get_list(new_cfg, "approval_dry_run_tools")) is not None:
            approval.approval_dry_run_tools = list(lst)
        if (d := _get_dict(new_cfg, "tool_safety_tiers")) is not None:
            approval.tool_safety_tiers = dict(d)
        if (v := _get_str(new_cfg, "allowed_root")) is not None:
            approval.allowed_root = v
        if (lst := _get_list(new_cfg, "approval_github_allowed_repos")) is not None:
            approval.approval_github_allowed_repos = list(lst)

    def _reload_approval_settings(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update approval, tool, and memory config fields when present in new_cfg."""
        self._reload_approval_config(ctx, new_cfg)
        if (lst := _get_list(new_cfg, "allowed_tools")) is not None:
            ctx.cfg.tool.allowed_tools = list(lst)
        if (v := _get_int(new_cfg, "memory_retention_days")) is not None:
            ctx.cfg.memory.memory_retention_days = v
