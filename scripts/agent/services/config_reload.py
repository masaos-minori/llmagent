"""scripts/agent/services/config_reload.py

ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)
  _update_section()    — registry-driven validation helper for dataclass replacement

Both return ConfigReloadOutcome so callers can display what changed.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from shared.mcp_config import McpServerConfig

from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from shared.runtime_tool import AgentSafetyTier
    from shared.runtime_tool_registry import RuntimeToolRegistry

    from agent.context import AgentContext
    from agent.history import HistoryManager
    from agent.llm_client import LLMClient

from collections.abc import Callable

from agent.services.config_validators import (
    validate_llm_context_char_limit,
    validate_llm_context_token_limit,
    validate_llm_http_timeout,
    validate_llm_max_retries,
    validate_llm_max_tokens,
    validate_llm_retry_base_delay,
    validate_llm_sse_heartbeat_timeout,
    validate_llm_sse_malformed_retry,
    validate_llm_sse_reconnect_max,
    validate_llm_temperature,
    validate_rag_refiner_max_chars_per_chunk,
    validate_rag_refiner_max_tokens,
    validate_rag_refiner_timeout,
    validate_tool_max_tool_turns,
    validate_tool_result_max_llm_chars,
)
from agent.services.typed_validators import _get_bool


@dataclass(frozen=True)
class ConfigFieldRegistry:
    name: str
    section_path: str
    hot_reloadable: bool
    validator_fn: Callable[[Any], None] | None = None

    @property
    def field_name(self) -> str:
        return self.name


CONFIG_FIELD_REGISTRY: Mapping[str, ConfigFieldRegistry] = {
    entry.field_name: entry
    for entry in [
        # LLM section
        ConfigFieldRegistry("http_timeout", "llm", True, validate_llm_http_timeout),
        ConfigFieldRegistry(
            "context_token_limit", "llm", False, validate_llm_context_token_limit
        ),
        ConfigFieldRegistry(
            "context_char_limit", "llm", False, validate_llm_context_char_limit
        ),
        ConfigFieldRegistry("context_compress_turns", "llm", False),
        ConfigFieldRegistry("llm_temperature", "llm", True, validate_llm_temperature),
        ConfigFieldRegistry("llm_max_tokens", "llm", True, validate_llm_max_tokens),
        ConfigFieldRegistry("llm_url", "llm", True),
        ConfigFieldRegistry("llm_max_retries", "llm", True, validate_llm_max_retries),
        ConfigFieldRegistry(
            "llm_retry_base_delay", "llm", True, validate_llm_retry_base_delay
        ),
        ConfigFieldRegistry(
            "sse_heartbeat_timeout", "llm", True, validate_llm_sse_heartbeat_timeout
        ),
        ConfigFieldRegistry(
            "sse_malformed_retry", "llm", True, validate_llm_sse_malformed_retry
        ),
        ConfigFieldRegistry(
            "sse_reconnect_max", "llm", True, validate_llm_sse_reconnect_max
        ),
        ConfigFieldRegistry("llm_stream_retry_on_heartbeat_timeout", "llm", True),
        ConfigFieldRegistry("llm_stream_retry_on_malformed_chunk", "llm", True),
        # RAG section
        ConfigFieldRegistry("embed_url", "rag", True),
        ConfigFieldRegistry("web_search_url", "rag", True),
        ConfigFieldRegistry("use_refiner", "rag", True),
        ConfigFieldRegistry(
            "refiner_max_tokens", "rag", True, validate_rag_refiner_max_tokens
        ),
        ConfigFieldRegistry(
            "refiner_timeout", "rag", True, validate_rag_refiner_timeout
        ),
        ConfigFieldRegistry(
            "refiner_max_chars_per_chunk",
            "rag",
            True,
            validate_rag_refiner_max_chars_per_chunk,
        ),
        # Tool section
        ConfigFieldRegistry(
            "max_tool_turns", "tool", True, validate_tool_max_tool_turns
        ),
        ConfigFieldRegistry(
            "tool_result_max_llm_chars",
            "tool",
            True,
            validate_tool_result_max_llm_chars,
        ),
        ConfigFieldRegistry("serial_tool_calls", "tool", True),
        ConfigFieldRegistry("tool_definitions_strict", "tool", True),
        ConfigFieldRegistry("plan_blocked_tools", "tool", True),
        ConfigFieldRegistry("system_prompt_tool", "tool", True),
        ConfigFieldRegistry("system_prompts", "tool", True),
        ConfigFieldRegistry("tool_definitions", "tool", True),
        ConfigFieldRegistry("allowed_tools", "tool", True),
        ConfigFieldRegistry("routing_drift_strict", "tool", False),
        # Approval section
        ConfigFieldRegistry("approval_risk_rules", "approval", True),
        ConfigFieldRegistry("approval_protected_paths", "approval", True),
        ConfigFieldRegistry("approval_high_risk_branches", "approval", True),
        ConfigFieldRegistry("approval_shell_safe_prefixes", "approval", True),
        ConfigFieldRegistry("approval_resource_keys", "approval", True),
        ConfigFieldRegistry("approval_dry_run_tools", "approval", True),
        ConfigFieldRegistry("tool_safety_tiers", "approval", True),
        ConfigFieldRegistry("allowed_root", "approval", True),
        ConfigFieldRegistry("approval_github_allowed_repos", "approval", True),
        ConfigFieldRegistry("gitops_push_blocked", "approval", False),
        # Memory section
        ConfigFieldRegistry("memory_retention_days", "memory", True),
        ConfigFieldRegistry("memory_local_only", "memory", True),
        ConfigFieldRegistry("use_memory_layer", "memory", False),
        ConfigFieldRegistry("memory_embed_enabled", "memory", False),
        # MCP section
        ConfigFieldRegistry("security_profile", "mcp", True),
        ConfigFieldRegistry("security_lockdown_enabled", "mcp", True),
    ]
}

_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
    "call_timeout_sec",
    "startup_timeout_sec",
    "tool_names",
    "auth_token",  # restart-only, intentional: a live credential change must not apply mid-session
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
        outcome = ConfigReloadOutcome()
        for section_path in ("llm", "rag", "tool"):
            cfg = getattr(ctx.cfg, section_path)
            changed_fields: dict[str, Any] = {}
            for field_entry in CONFIG_FIELD_REGISTRY.values():
                if field_entry.section_path != section_path:
                    continue
                value = new_cfg.get(field_entry.field_name)
                if value is None or value == getattr(cfg, field_entry.field_name):
                    continue
                changed_fields[field_entry.field_name] = value
            if changed_fields:
                try:
                    replaced = dataclasses.replace(cfg, **changed_fields)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e
                for field_entry in CONFIG_FIELD_REGISTRY.values():
                    if (
                        field_entry.section_path == section_path
                        and field_entry.validator_fn
                    ):
                        try:
                            field_entry.validator_fn(replaced)
                        except ValueError as e:
                            raise ConfigReloadValidationError(
                                f"{section_path}.{field_entry.field_name}: {e}"
                            ) from e
                setattr(ctx.cfg, section_path, replaced)
        # web_search_url handled by registry-driven loop above
        self._reload_approval_config(ctx, new_cfg)
        self._reload_memory_runtime(ctx, new_cfg)
        self._reload_security_profile(ctx, new_cfg)
        if "system_prompt_tool" in new_cfg:
            ctx.conv.system_prompt_content = new_cfg["system_prompt_tool"]
        if "allowed_tools" in new_cfg:
            ctx.cfg.tool.allowed_tools = list(new_cfg["allowed_tools"])
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
        service_result = self._sync_services(
            new_cfg,
            ctx.services_required.llm,
            ctx.services_required.hist_mgr,
            ctx.services_required.runtime_tools,
        )
        outcome.applied.extend(service_result.applied)
        outcome.skipped.extend(service_result.skipped)
        outcome.startup_only = self._detect_startup_only(new_cfg)
        outcome.always_live = self._detect_diagnostics_live_fields(new_cfg)
        return outcome

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

    def _sync_services(
        self,
        new_cfg: dict[str, Any],
        llm_service: LLMClient | None,
        hist_mgr_service: HistoryManager | None,
        runtime_tools_service: RuntimeToolRegistry | None,
    ) -> ConfigReloadOutcome:
        """Apply new_cfg values to running service instances; return a report."""
        result = ConfigReloadOutcome()
        ctx = self._ctx

        if llm_service is not None:
            llm_service.apply_config(
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

        if hist_mgr_service is not None:
            hist_mgr_service.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if runtime_tools_service is not None:
            runtime_tools_service.apply_policy(
                tier_map=cast(
                    Mapping[str, "AgentSafetyTier"], ctx.cfg.approval.tool_safety_tiers
                ),
                allowed_tools=ctx.cfg.tool.allowed_tools,
            )
            result.applied.append("runtime_tools")

        return result

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

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

        auth_token in particular is restart-only by design: a live /reload must
        never apply a changed credential to an already-running HttpTransport
        instance mid-session.
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

    def _reload_section(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        section_path: str,
        field_mappings: list[tuple[str, str]],
    ) -> None:
        """Apply a batch of field updates to a config section.

        Args:
            ctx: AgentContext for accessing cfg
            new_cfg: New configuration dict
            section_path: Dot-separated path to the target section (e.g., "approval")
            field_mappings: List of (new_cfg_key, target_field) tuples where
                target_field is the attribute name within the section
        """
        parts = section_path.split(".")
        obj = ctx.cfg
        for part in parts:
            obj = getattr(obj, part)
        for new_key, target_field in field_mappings:
            if new_key not in new_cfg:
                continue
            value = new_cfg[new_key]
            if isinstance(value, dict):
                setattr(obj, target_field, dict(value))
            elif isinstance(value, list):
                setattr(obj, target_field, list(value))
            else:
                setattr(obj, target_field, value)

    def _reload_approval_config(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update ApprovalConfig fields in ctx.cfg when present in new_cfg."""
        field_mappings = [
            (entry.field_name, entry.field_name)
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "approval"
        ]
        self._reload_section(ctx, new_cfg, "approval", field_mappings)

    def _reload_tool_allowlist(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload allowed_tools from new_cfg if present."""
        field_mappings = [
            (entry.field_name, entry.field_name)
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "tool" and entry.field_name == "allowed_tools"
        ]
        self._reload_section(ctx, new_cfg, "tool", field_mappings)

    def _reload_memory_runtime(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload memory runtime fields from new_cfg if present."""
        field_mappings = [
            (entry.field_name, entry.field_name)
            for entry in CONFIG_FIELD_REGISTRY.values()
            if entry.section_path == "memory"
        ]
        self._reload_section(ctx, new_cfg, "memory", field_mappings)

    def _reload_security_profile(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload the security-profile and security-lockdown fields from new_cfg."""
        for field_entry in CONFIG_FIELD_REGISTRY.values():
            if field_entry.section_path != "mcp":
                continue
            value = new_cfg.get(field_entry.field_name)
            if value is None:
                continue
            if field_entry.field_name == "security_profile":
                try:
                    from shared.mcp_config import SecurityProfile

                    ctx.cfg.mcp.security_profile = SecurityProfile(value)
                except ValueError:
                    pass
            elif field_entry.field_name == "security_lockdown_enabled":
                ctx.cfg.mcp.security_lockdown_enabled = bool(value)

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
