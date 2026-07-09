"""agent/services/config_reload.py
ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)

Both return ConfigReloadOutcome so callers can display what changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest
from shared.mcp_config import McpServerConfig

if TYPE_CHECKING:
    from agent.context import AgentContext

from agent.services.typed_validators import (
    _apply_bool,
    _apply_dict_nonempty,
    _apply_float,
    _apply_int,
    _apply_list,
    _apply_list_nonempty,
    _apply_str,
    _apply_str_nonempty,
    _get_bool,
    _get_dict,
    _get_float,
    _get_int,
    _get_list,
    _get_str,
)

_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
    "healthcheck_mode",
    "call_timeout_sec",
    "startup_timeout_sec",
    "tool_names",
    "auth_token",
    "role",
    "cmd",
    "env",
)


def _diff_mcp_server_config(old: McpServerConfig, new: McpServerConfig) -> list[str]:
    """Return names of McpServerConfig fields that differ between old and new.

    Pure comparison — never mutates either argument. Field order follows
    _MCP_SERVER_FIELDS, so output is deterministic for a given pair of inputs.
    """
    return [
        field_name
        for field_name in _MCP_SERVER_FIELDS
        if getattr(old, field_name) != getattr(new, field_name)
    ]


@dataclass
class ConfigReloadOutcome:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    """Fields intentionally ignored by /reload for reasons other than restart-
    required (e.g. unrecognized keys). MCP server definition changes are never
    reported here — see needs_restart instead."""
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)


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
        result = self._classify_mcp_server_changes(ctx, new_cfg)
        self._apply_llm_prompt_params(ctx, new_cfg)
        self._apply_sse_reload_params(ctx, new_cfg)
        service_result = self._sync_services(new_cfg)
        result.applied.extend(service_result.applied)
        result.skipped.extend(service_result.skipped)
        result.startup_only = self._detect_startup_only(new_cfg)
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

    def _sync_services(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
        """Apply new_cfg values to running service instances; return a report."""
        result = ConfigReloadOutcome()
        ctx = self._ctx

        if ctx.services_required.llm is not None:
            ctx.services_required.llm.apply_config(
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

        if ctx.services_required.hist_mgr is not None:
            ctx.services_required.hist_mgr.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if ctx.services_required.tools is not None:
            ctx.services_required.tools.apply_config(
                cache_ttl=ctx.cfg.tool.tool_cache_ttl
            )
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
        cfg = ctx.cfg
        self._apply_llm_context_params(cfg, new_cfg)
        self._apply_tool_params(cfg, new_cfg)
        self._apply_rag_params(cfg, new_cfg)
        self._apply_llm_retry_params(cfg, new_cfg)
        self._apply_mcp_watchdog_params(cfg, new_cfg)

    def _apply_llm_context_params(self, cfg: Any, new_cfg: dict[str, Any]) -> None:
        """Apply LLM context window settings."""
        _apply_int(
            new_cfg,
            "context_char_limit",
            lambda v: setattr(cfg.llm, "context_char_limit", v),
        )
        _apply_int(
            new_cfg,
            "context_compress_turns",
            lambda v: setattr(cfg.llm, "context_compress_turns", v),
        )

    def _apply_tool_params(self, cfg: Any, new_cfg: dict[str, Any]) -> None:
        """Apply tool execution settings."""
        _apply_float(
            new_cfg, "tool_cache_ttl", lambda v: setattr(cfg.tool, "tool_cache_ttl", v)
        )
        _apply_bool(
            new_cfg,
            "serial_tool_calls",
            lambda v: setattr(cfg.tool, "serial_tool_calls", v),
        )
        _apply_bool(
            new_cfg,
            "tool_definitions_strict",
            lambda v: setattr(cfg.tool, "tool_definitions_strict", v),
        )
        _apply_list(
            new_cfg,
            "plan_blocked_tools",
            lambda v: setattr(cfg.tool, "plan_blocked_tools", list(v)),
        )

    def _apply_rag_params(self, cfg: Any, new_cfg: dict[str, Any]) -> None:
        """Apply RAG (retrieval-augmented generation) settings."""
        _apply_int(
            new_cfg, "top_k_search", lambda v: setattr(cfg.rag, "top_k_search", v)
        )
        _apply_int(
            new_cfg, "top_k_rerank", lambda v: setattr(cfg.rag, "top_k_rerank", v)
        )
        _apply_int(
            new_cfg,
            "max_chunks_per_doc",
            lambda v: setattr(cfg.rag, "max_chunks_per_doc", v),
        )
        _apply_bool(
            new_cfg,
            "use_semantic_cache",
            lambda v: setattr(cfg.rag, "use_semantic_cache", v),
        )
        _apply_float(
            new_cfg,
            "semantic_cache_threshold",
            lambda v: setattr(cfg.rag, "semantic_cache_threshold", v),
        )
        _apply_int(
            new_cfg,
            "semantic_cache_max_size",
            lambda v: setattr(cfg.rag, "semantic_cache_max_size", v),
        )
        _apply_bool(
            new_cfg, "use_refiner", lambda v: setattr(cfg.rag, "use_refiner", v)
        )
        _apply_int(
            new_cfg,
            "refiner_max_tokens",
            lambda v: setattr(cfg.rag, "refiner_max_tokens", v),
        )
        _apply_float(
            new_cfg, "refiner_timeout", lambda v: setattr(cfg.rag, "refiner_timeout", v)
        )
        _apply_int(
            new_cfg,
            "refiner_max_chars_per_chunk",
            lambda v: setattr(cfg.rag, "refiner_max_chars_per_chunk", v),
        )

    def _apply_llm_retry_params(self, cfg: Any, new_cfg: dict[str, Any]) -> None:
        """Apply LLM retry settings."""
        _apply_int(
            new_cfg, "llm_max_retries", lambda v: setattr(cfg.llm, "llm_max_retries", v)
        )
        _apply_float(
            new_cfg,
            "llm_retry_base_delay",
            lambda v: setattr(cfg.llm, "llm_retry_base_delay", v),
        )

    def _apply_mcp_watchdog_params(self, cfg: Any, new_cfg: dict[str, Any]) -> None:
        """Apply MCP watchdog settings."""
        _apply_float(
            new_cfg,
            "mcp_watchdog_interval",
            lambda v: setattr(cfg.mcp, "mcp_watchdog_interval", v),
        )
        _apply_int(
            new_cfg,
            "mcp_watchdog_max_restarts",
            lambda v: setattr(cfg.mcp, "mcp_watchdog_max_restarts", v),
        )

    def _classify_mcp_server_changes(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadOutcome:
        """Classify MCP server definition changes as restart-required, field by field.

        MCP server definitions are restart-time snapshots: ToolExecutor and
        HttpTransport are built from them at startup, so mutating
        `ctx.cfg.mcp.mcp_servers` here would desync already-running instances
        from the reported config. This method only compares; it never writes.
        """
        from agent.config_builders import (
            _build_mcp_servers,  # noqa: PLC0415 — lazy: avoids circular import at module level
        )

        result = ConfigReloadOutcome()
        new_mcp = _build_mcp_servers(new_cfg)
        old_mcp = ctx.cfg.mcp.mcp_servers
        for key, new_srv in new_mcp.items():
            old_srv = old_mcp.get(key)
            if old_srv is None:
                result.needs_restart.append(f"mcp/{key} (new server)")
                continue
            for field_name in _diff_mcp_server_config(old_srv, new_srv):
                result.needs_restart.append(f"mcp/{key}.{field_name}")
        for key in old_mcp:
            if key not in new_mcp:
                result.needs_restart.append(f"mcp/{key} (removed server)")
        return result

    def _apply_llm_prompt_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Apply hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings (diff-apply)."""
        cfg = ctx.cfg
        _apply_float(
            new_cfg, "llm_temperature", lambda v: setattr(cfg.llm, "llm_temperature", v)
        )
        _apply_int(
            new_cfg, "llm_max_tokens", lambda v: setattr(cfg.llm, "llm_max_tokens", v)
        )
        _apply_str(new_cfg, "llm_url", lambda v: setattr(cfg.llm, "llm_url", v))
        _apply_str(
            new_cfg, "web_search_url", lambda v: setattr(cfg.rag, "web_search_url", v)
        )
        _apply_str(new_cfg, "embed_url", lambda v: setattr(cfg.rag, "embed_url", v))
        _apply_float(
            new_cfg, "http_timeout", lambda v: setattr(cfg.llm, "http_timeout", v)
        )
        _apply_int(
            new_cfg,
            "web_search_max_results",
            lambda v: setattr(cfg.rag, "web_search_max_results", v),
        )
        _apply_int(
            new_cfg, "max_tool_turns", lambda v: setattr(cfg.tool, "max_tool_turns", v)
        )
        _apply_int(
            new_cfg,
            "tool_result_max_llm_chars",
            lambda v: setattr(cfg.tool, "tool_result_max_llm_chars", v),
        )
        _apply_list_nonempty(
            new_cfg,
            "tool_definitions",
            lambda v: setattr(cfg.tool, "tool_definitions", list(v)),
        )
        _apply_str_nonempty(
            new_cfg,
            "system_prompt_tool",
            lambda v: setattr(cfg.tool, "system_prompt_tool", v),
        )
        _apply_dict_nonempty(
            new_cfg,
            "system_prompts",
            lambda v: setattr(cfg.tool, "system_prompts", dict(v)),
        )

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

    def _detect_startup_only(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of startup-only fields that differ between new_cfg and running cfg."""
        changed: list[str] = []
        ctx = self._ctx
        v = _get_bool(new_cfg, "use_memory_layer")
        if v is not None and v != ctx.cfg.memory.use_memory_layer:
            changed.append("use_memory_layer")
        v = _get_bool(new_cfg, "plugin_strict")
        if v is not None and v != ctx.cfg.tool.plugin_strict:
            changed.append("plugin_strict")
        v = _get_bool(new_cfg, "routing_drift_strict")
        if v is not None and v != ctx.cfg.tool.routing_drift_strict:
            changed.append("routing_drift_strict")
        return changed

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
        if (vb := _get_bool(new_cfg, "memory_local_only")) is not None:
            ctx.cfg.memory.memory_local_only = vb
        # security.toml fields — hot-reloadable
        if (vs := _get_str(new_cfg, "security_profile")) is not None:
            try:
                from shared.mcp_config import SecurityProfile

                ctx.cfg.mcp.security_profile = SecurityProfile(vs)
            except ValueError:
                pass  # invalid enum value — leave current
        if (vb := _get_bool(new_cfg, "security_lockdown_enabled")) is not None:
            ctx.cfg.mcp.security_lockdown_enabled = vb
