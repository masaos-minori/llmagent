"""Outcome classification — standalone functions for MCP server changes, startup-only fields, diagnostics."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext

from shared.mcp_config import McpServerConfig

_MCP_SERVER_FIELDS = tuple(f.name for f in dataclasses.fields(McpServerConfig))


def _diff_mcp_server_config(old: McpServerConfig, new: McpServerConfig) -> list[str]:
    """Return names of McpServerConfig fields that differ between old and new."""
    return [
        field_name
        for field_name in _MCP_SERVER_FIELDS
        if getattr(old, field_name) != getattr(new, field_name)
    ]


def classify_mcp_server_changes(
    ctx: AgentContext,
    new_cfg: dict,
) -> list[str]:
    """Classify MCP server definition changes as restart-required, field by field."""
    from agent.config_builders import _build_mcp_servers

    result: list[str] = []
    new_mcp = _build_mcp_servers(new_cfg)
    old_mcp = ctx.cfg.mcp.mcp_servers
    for key, new_srv in new_mcp.items():
        old_srv = old_mcp.get(key)
        if old_srv is None:
            result.append(f"mcp_servers/{key} (new server)")
            continue
        for field_name in _diff_mcp_server_config(old_srv, new_srv):
            result.append(f"mcp_servers/{key}.{field_name}")
    for key in old_mcp:
        if key not in new_mcp:
            result.append(f"mcp_servers/{key} (removed server)")
    return result


def classify_startup_only_fields(
    ctx: AgentContext,
    new_cfg: dict,
) -> list[str]:
    """Return names of startup-only fields that differ between new_cfg and running cfg."""
    from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY

    changed: list[str] = []
    for entry in CONFIG_FIELD_REGISTRY.values():
        if entry.hot_reloadable:
            continue
        value = new_cfg.get(entry.name)
        if value is None:
            continue
        current = getattr(getattr(ctx.cfg, entry.section_path), entry.name)
        if value != current:
            changed.append(entry.name)
    return changed


def detect_diagnostics_live_fields(
    ctx: AgentContext,
    new_cfg: dict,
) -> list[str]:
    """Return names of diagnostics.* fields that differ between new_cfg and running cfg."""
    changed: list[str] = []
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
