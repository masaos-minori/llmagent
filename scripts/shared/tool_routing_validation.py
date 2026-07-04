#!/usr/bin/env python3
"""shared/tool_routing_validation.py — MCP tool routing drift validation against config and live responses."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig
    from shared.tool_registry import ToolRegistry


def validate_routing_against_config(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    if registry is None:
        from shared.tool_registry import get_registry

        registry = get_registry()
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def validate_routing_against_live(
    registry: "ToolRegistry | None" = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    if registry is None:
        from shared.tool_registry import get_registry

        registry = get_registry()
    if live_tool_lists is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def validate_all_routing(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result
