"""scripts/agent/services/config_reload.py

ConfigReloadService — thin orchestrator over extracted sub-modules.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)
  _classify_startup_only_fields() — identify fields requiring restart on change

Both return ConfigReloadOutcome so callers can display what changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from agent.services.config_outcome_classification import (
    classify_mcp_server_changes,
    classify_startup_only_fields,
    detect_diagnostics_live_fields,
)
from agent.services.config_section_reload import (
    reload_direct_fields,
    reload_validated_section,
)
from agent.services.config_service_sync import ServiceSyncer
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

    from agent.context import AgentContext
    from agent.history import HistoryManager
    from agent.llm_client import LLMClient


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
            changed_fields = reload_validated_section(ctx, section_path, new_cfg)
            if changed_fields:
                outcome.applied.append(section_path)
        for section_path in ("approval", "memory", "mcp"):
            changed_fields_dict = reload_direct_fields(ctx, new_cfg, section_path)
            if changed_fields_dict:
                outcome.applied.append(section_path)
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
            else:
                outcome.needs_restart.append(item)
        service_result = self._sync_services(
            new_cfg,
            ctx.services_required.llm,
            ctx.services_required.hist_mgr,
            ctx.services_required.runtime_tools,
        )
        outcome.applied.extend(service_result.applied)
        outcome.skipped.extend(service_result.skipped)
        outcome.startup_only = self._classify_startup_only_fields(new_cfg)
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
        syncer = ServiceSyncer(self._ctx)
        sync_result = syncer.sync_all(
            self._ctx.cfg.llm,
            self._ctx.cfg.rag,
            self._ctx.cfg.tool,
        )
        result = ConfigReloadOutcome()
        result.applied.extend(sync_result.applied)
        result.skipped.extend(sync_result.skipped)
        return result

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

    def _classify_mcp_server_changes(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadOutcome:
        """Classify MCP server definition changes as restart-required, field by field.

        Delegates to classify_mcp_server_changes from config_outcome_classification.
        Lifecycle cleanup for removed servers is handled locally.
        """
        result = ConfigReloadOutcome()
        for item in classify_mcp_server_changes(ctx, new_cfg):
            if item.endswith(" (removed server)"):
                server_key = item.replace("mcp_servers/", "").removesuffix(
                    " (removed server)"
                )
                lifecycle = ctx.services_required.lifecycle
                if lifecycle is not None:
                    lifecycle.cleanup_server_resources(server_key)
            result.needs_restart.append(item)
        return result

    def _classify_startup_only_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of startup-only fields that differ between new_cfg and running cfg.

        Delegates to classify_startup_only_fields from config_outcome_classification.
        """
        return classify_startup_only_fields(self._ctx, new_cfg)

    def _detect_diagnostics_live_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of diagnostics.* fields that differ between new_cfg and running cfg.

        These fields take effect immediately on every DiagnosticStore save()/fetch()
        call, independent of /reload — they are config-file-driven, not startup-only.
        """
        return detect_diagnostics_live_fields(self._ctx, new_cfg)
