"""scripts/agent/services/config_reload.py

ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)

Both return ConfigReloadOutcome so callers can display what changed.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from shared.mcp_config import McpServerConfig

from agent.config_dataclasses import AgentConfig
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from shared.runtime_tool import AgentSafetyTier

    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext

from agent.services.typed_validators import (
    _get_bool,
    _get_dict,
    _get_dict_nonempty,
    _get_float,
    _get_int,
    _get_list,
    _get_list_nonempty,
    _get_str,
    _get_str_nonempty,
)

_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
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
    """Fields present in the reload payload and differing from the running
    value but requiring a restart to take effect. Distinct from `skipped`,
    which ignores fields for reasons unrelated to restart requirement, and
    `needs_restart`, which is reserved exclusively for MCP server definition
    changes."""
    always_live: list[str] = field(default_factory=list)
    """Fields that take effect independently of /reload — they are read from
    disk on every DiagnosticStore save()/fetch() call, so any change to them
    is immediately effective without a restart or special handling."""


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Updates ctx.cfg via typed validators, syncs services via their public APIs,
    and writes certain fields (e.g. system_prompt) directly to ctx.conv.
    """

    def __init__(self, ctx: AgentContext) -> None:
        """Initialize the config reload handler with the agent context for service updates."""
        self._ctx = ctx

    # ── Public entry point ────────────────────────────────────────────────────

    def apply_config(self, req: ConfigReloadRequest) -> ConfigReloadOutcome:
        """Convert a typed ConfigReloadRequest to a dict and delegate to apply_config_dict().

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
        self._validate_request(new_cfg)
        self._apply_rag_tool_params(ctx, new_cfg)
        self._reload_approval_config(ctx, new_cfg)
        self._reload_tool_allowlist(ctx, new_cfg)
        self._reload_memory_runtime(ctx, new_cfg)
        self._reload_security_profile(ctx, new_cfg)
        if "masked_fields" in new_cfg:
            ctx.cfg.tool.masked_fields = list(new_cfg["masked_fields"])
        result = self._classify_mcp_server_changes(ctx, new_cfg)
        for item in result.needs_restart:
            if item.endswith(" (removed server)"):
                server_key = item.replace("mcp_servers/", "").removesuffix(
                    " (removed server)"
                )
                lifecycle = ctx.services_required.lifecycle
                if lifecycle is not None:
                    lifecycle.cleanup_server_resources(server_key)
        service_result = self._sync_services(new_cfg)
        result.applied.extend(service_result.applied)
        result.skipped.extend(service_result.skipped)
        result.startup_only = self._detect_startup_only(new_cfg)
        result.always_live = self._detect_diagnostics_live_fields(new_cfg)
        return result

    def _validate_request(self, new_cfg: dict[str, Any]) -> None:
        """Validate request values BEFORE applying any changes.

        Creates fresh dataclass instances from defaults + request values,
        then runs validators. Raises ConfigReloadValidationError on failure.
        This ensures validation runs independently of mocked apply_config_dict.
        """
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}

        self._collect_request_values(new_cfg, llm_changes, rag_changes, tool_changes)

        if llm_changes:
            try:
                new_llm = dataclasses.replace(self._ctx.cfg.llm, **llm_changes)
                from agent.services.config_validators import (
                    validate_llm_context_token_limit,
                    validate_llm_http_timeout,
                )

                validate_llm_http_timeout(new_llm)
                validate_llm_context_token_limit(new_llm)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e

        if rag_changes:
            # Remove undeclared fields that cannot go through dataclasses.replace()
            rag_changes = {
                k: v for k, v in rag_changes.items() if k != "web_search_url"
            }
            if rag_changes:
                try:
                    new_rag = dataclasses.replace(self._ctx.cfg.rag, **rag_changes)
                    from agent.services.config_validators import (
                        validate_rag_refiner_max_chars_per_chunk,
                        validate_rag_refiner_max_tokens,
                        validate_rag_refiner_timeout,
                    )

                    validate_rag_refiner_max_tokens(new_rag)
                    validate_rag_refiner_timeout(new_rag)
                    validate_rag_refiner_max_chars_per_chunk(new_rag)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e

        if tool_changes:
            try:
                new_tool = dataclasses.replace(self._ctx.cfg.tool, **tool_changes)
                from agent.services.config_validators import (
                    validate_progress_stagnation_window,
                    validate_tool_cycle_detect_window,
                    validate_tool_dedup_max_repeats,
                    validate_tool_error_max_consecutive,
                    validate_tool_error_retry_max,
                    validate_tool_max_tool_turns,
                    validate_tool_result_max_llm_chars,
                )

                validate_tool_dedup_max_repeats(new_tool)
                validate_tool_cycle_detect_window(new_tool)
                validate_tool_error_max_consecutive(new_tool)
                validate_tool_error_retry_max(new_tool)
                validate_progress_stagnation_window(new_tool)
                validate_tool_max_tool_turns(new_tool)
                validate_tool_result_max_llm_chars(new_tool)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e

    @staticmethod
    def _collect_request_values(
        new_cfg: dict[str, Any],
        llm_changes: dict[str, Any],
        rag_changes: dict[str, Any],
        tool_changes: dict[str, Any],
    ) -> None:
        """Collect field values from new_cfg into change dicts for validation."""
        if (v := _get_float(new_cfg, "http_timeout")) is not None:
            llm_changes["http_timeout"] = v
        if (v := _get_int(new_cfg, "context_token_limit")) is not None:
            llm_changes["context_token_limit"] = v
        if (embed_url := _get_str(new_cfg, "embed_url")) is not None:
            rag_changes["embed_url"] = embed_url
        if (vb := _get_bool(new_cfg, "use_semantic_cache")) is not None:
            rag_changes["use_semantic_cache"] = vb
        if (v := _get_int(new_cfg, "max_tool_turns")) is not None:
            tool_changes["max_tool_turns"] = v
        if (
            tool_result_max_chars := _get_int(new_cfg, "tool_result_max_llm_chars")
        ) is not None:
            tool_changes["tool_result_max_llm_chars"] = tool_result_max_chars

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

        if ctx.services_required.runtime_tools is not None:
            ctx.services_required.runtime_tools.apply_policy(
                tier_map=cast(
                    Mapping[str, "AgentSafetyTier"], ctx.cfg.approval.tool_safety_tiers
                ),
                allowed_tools=ctx.cfg.tool.allowed_tools,
            )
            result.applied.append("runtime_tools")

        # system_prompt update: write to the canonical field; Orchestrator syncs history[0].
        if "system_prompt_tool" in new_cfg:
            ctx.conv.system_prompt_content = new_cfg["system_prompt_tool"]

        return result

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

    def _apply_rag_tool_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadOutcome:
        """Apply LLM/RAG/Tool settings with validation re-execution."""
        result = ConfigReloadOutcome()
        cfg = ctx.cfg

        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}

        self._apply_llm_context_params(cfg, new_cfg, llm_changes)
        self._apply_tool_params(cfg, new_cfg, tool_changes)
        self._apply_rag_params(cfg, new_cfg, rag_changes)
        self._apply_llm_retry_params(cfg, new_cfg, llm_changes)
        self._apply_llm_prompt_params(
            ctx, new_cfg, llm_changes, rag_changes, tool_changes
        )
        self._apply_sse_reload_params(ctx, new_cfg, llm_changes)

        if llm_changes:
            try:
                new_llm = dataclasses.replace(cfg.llm, **llm_changes)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e
            # Re-validate after replacement
            from agent.services.config_validators import (
                validate_llm_context_char_limit,
                validate_llm_max_retries,
                validate_llm_max_tokens,
                validate_llm_retry_base_delay,
                validate_llm_sse_heartbeat_timeout,
                validate_llm_sse_malformed_retry,
                validate_llm_sse_reconnect_max,
                validate_llm_temperature,
            )

            validate_llm_temperature(new_llm)
            validate_llm_max_tokens(new_llm)
            validate_llm_context_char_limit(new_llm)
            validate_llm_max_retries(new_llm)
            validate_llm_retry_base_delay(new_llm)
            validate_llm_sse_heartbeat_timeout(new_llm)
            validate_llm_sse_malformed_retry(new_llm)
            validate_llm_sse_reconnect_max(new_llm)
            cfg.llm = new_llm

        if rag_changes:
            # Remove undeclared fields that cannot go through dataclasses.replace()
            rag_changes = {
                k: v for k, v in rag_changes.items() if k != "web_search_url"
            }
            if rag_changes:
                try:
                    new_rag = dataclasses.replace(cfg.rag, **rag_changes)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e
                from agent.services.config_validators import (
                    validate_rag_refiner_max_chars_per_chunk,
                    validate_rag_refiner_max_tokens,
                    validate_rag_refiner_timeout,
                )

                validate_rag_refiner_max_tokens(new_rag)
                validate_rag_refiner_timeout(new_rag)
                validate_rag_refiner_max_chars_per_chunk(new_rag)
                cfg.rag = new_rag

        if tool_changes:
            try:
                new_tool = dataclasses.replace(cfg.tool, **tool_changes)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e
            from agent.services.config_validators import (
                validate_progress_stagnation_window,
                validate_tool_cycle_detect_window,
                validate_tool_dedup_max_repeats,
                validate_tool_error_max_consecutive,
                validate_tool_error_retry_max,
            )

            validate_tool_dedup_max_repeats(new_tool)
            validate_tool_cycle_detect_window(new_tool)
            validate_tool_error_max_consecutive(new_tool)
            validate_tool_error_retry_max(new_tool)
            validate_progress_stagnation_window(new_tool)
            cfg.tool = new_tool

        return result

    def _apply_llm_context_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect LLM context window setting changes."""
        if (v := _get_int(new_cfg, "context_char_limit")) is not None:
            changes["context_char_limit"] = v
        if (v := _get_int(new_cfg, "context_compress_turns")) is not None:
            changes["context_compress_turns"] = v

    def _apply_tool_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect tool execution setting changes."""
        if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
            changes["serial_tool_calls"] = vb
        if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
            changes["tool_definitions_strict"] = vb
        if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
            changes["plan_blocked_tools"] = list(lst)

    def _apply_rag_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect RAG setting changes."""
        if (vb := _get_bool(new_cfg, "use_semantic_cache")) is not None:
            changes["use_semantic_cache"] = vb
        if (v := _get_float(new_cfg, "semantic_cache_threshold")) is not None:
            changes["semantic_cache_threshold"] = v
        if (v := _get_int(new_cfg, "semantic_cache_max_size")) is not None:
            changes["semantic_cache_max_size"] = v
        if (vb := _get_bool(new_cfg, "use_refiner")) is not None:
            changes["use_refiner"] = vb
        if (v := _get_int(new_cfg, "refiner_max_tokens")) is not None:
            changes["refiner_max_tokens"] = v
        if (v := _get_float(new_cfg, "refiner_timeout")) is not None:
            changes["refiner_timeout"] = v
        if (v := _get_int(new_cfg, "refiner_max_chars_per_chunk")) is not None:
            changes["refiner_max_chars_per_chunk"] = v

    def _apply_llm_retry_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect LLM retry setting changes."""
        if (max_retries := _get_int(new_cfg, "llm_max_retries")) is not None:
            changes["llm_max_retries"] = max_retries
        if (base_delay := _get_float(new_cfg, "llm_retry_base_delay")) is not None:
            changes["llm_retry_base_delay"] = base_delay

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
            _build_mcp_servers,  # lazy: avoids circular import at module level
        )

        result = ConfigReloadOutcome()
        new_mcp = _build_mcp_servers(new_cfg)
        old_mcp = ctx.cfg.mcp.mcp_servers
        for key, new_srv in new_mcp.items():
            old_srv = old_mcp.get(key)
            if old_srv is None:
                result.needs_restart.append(f"mcp_servers/{key} (new server)")
                continue
            for field_name in _diff_mcp_server_config(old_srv, new_srv):
                result.needs_restart.append(f"mcp_servers/{key}.{field_name}")
        for key in old_mcp:
            if key not in new_mcp:
                result.needs_restart.append(f"mcp_servers/{key} (removed server)")
        return result

    def _apply_llm_prompt_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        llm_changes: dict[str, Any],
        rag_changes: dict[str, Any],
        tool_changes: dict[str, Any],
    ) -> None:
        """Collect hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings."""
        if (temperature := _get_float(new_cfg, "llm_temperature")) is not None:
            llm_changes["llm_temperature"] = temperature
        if (max_tokens := _get_int(new_cfg, "llm_max_tokens")) is not None:
            llm_changes["llm_max_tokens"] = max_tokens
        if (llm_url := _get_str(new_cfg, "llm_url")) is not None:
            llm_changes["llm_url"] = llm_url
        if (web_search_url := _get_str(new_cfg, "web_search_url")) is not None:
            rag_changes["web_search_url"] = web_search_url
        if (embed_url := _get_str(new_cfg, "embed_url")) is not None:
            rag_changes["embed_url"] = embed_url
        if (http_timeout := _get_float(new_cfg, "http_timeout")) is not None:
            llm_changes["http_timeout"] = http_timeout
        if (max_tool_turns := _get_int(new_cfg, "max_tool_turns")) is not None:
            tool_changes["max_tool_turns"] = max_tool_turns
        if (
            tool_result_max_chars := _get_int(new_cfg, "tool_result_max_llm_chars")
        ) is not None:
            tool_changes["tool_result_max_llm_chars"] = tool_result_max_chars
        if (lst := _get_list_nonempty(new_cfg, "tool_definitions")) is not None:
            tool_changes["tool_definitions"] = list(lst)
        if (
            prompt_tool := _get_str_nonempty(new_cfg, "system_prompt_tool")
        ) is not None:
            tool_changes["system_prompt_tool"] = prompt_tool
        if (sys_prompts := _get_dict_nonempty(new_cfg, "system_prompts")) is not None:
            tool_changes["system_prompts"] = dict(sys_prompts)

    def _apply_sse_reload_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        changes: dict[str, Any],
    ) -> None:
        """Collect SSE stream resilience settings."""
        if (vf := _get_float(new_cfg, "sse_heartbeat_timeout")) is not None:
            changes["sse_heartbeat_timeout"] = vf
        if (vi := _get_int(new_cfg, "sse_malformed_retry")) is not None:
            changes["sse_malformed_retry"] = vi
        if (vi := _get_int(new_cfg, "sse_reconnect_max")) is not None:
            changes["sse_reconnect_max"] = vi
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_heartbeat_timeout")
        ) is not None:
            changes["llm_stream_retry_on_heartbeat_timeout"] = vb
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_malformed_chunk")
        ) is not None:
            changes["llm_stream_retry_on_malformed_chunk"] = vb

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
        if (vb := _get_bool(new_cfg, "gitops_push_blocked")) is not None:
            approval.gitops_push_blocked = vb

    def _reload_tool_allowlist(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload allowed_tools from new_cfg if present."""
        if (lst := _get_list(new_cfg, "allowed_tools")) is not None:
            ctx.cfg.tool.allowed_tools = list(lst)

    def _reload_memory_runtime(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload memory runtime fields from new_cfg if present."""
        if (v := _get_int(new_cfg, "memory_retention_days")) is not None:
            ctx.cfg.memory.memory_retention_days = v
        if (vb := _get_bool(new_cfg, "memory_local_only")) is not None:
            ctx.cfg.memory.memory_local_only = vb

    def _reload_security_profile(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload security profile fields from new_cfg if present."""
        if (vs := _get_str(new_cfg, "security_profile")) is not None:
            try:
                from shared.mcp_config import SecurityProfile

                ctx.cfg.mcp.security_profile = SecurityProfile(vs)
            except ValueError:
                pass  # invalid enum value — leave current
        if (vb := _get_bool(new_cfg, "security_lockdown_enabled")) is not None:
            ctx.cfg.mcp.security_lockdown_enabled = vb

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

        v = _get_bool(new_cfg, "routing_drift_strict")
        if v is not None and v != ctx.cfg.tool.routing_drift_strict:
            changed.append("routing_drift_strict")

        v = _get_bool(new_cfg, "memory_embed_enabled")
        if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
            changed.append("memory_embed_enabled")
        return changed

    def _detect_diagnostics_live_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of diagnostics.* fields that differ between new_cfg and running cfg.

        These fields take effect immediately on every DiagnosticStore save()/fetch()
        call, independent of /reload — they are config-file-driven, not startup-only.
        """
        changed: list[str] = []
        ctx = self._ctx
        diag_new = new_cfg.get("diagnostics")
        if diag_new is None:
            return changed
        diag_running = getattr(ctx.cfg, "diagnostics", None)
        if diag_running is None:
            return changed
        for key in ("encryption_key", "retention_days", "sensitive_fields"):
            v = diag_new.get(key)
            if v is None:
                continue
            current = getattr(diag_running, key, None)
            if v != current:
                changed.append(f"diagnostics.{key}")
        return changed
