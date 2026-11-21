#!/usr/bin/env python3
"""scripts/shared/tool_routing_validation.py — MCP tool routing drift validation against live responses.

This module's use of the static ToolRegistry as drift-detection input is a formalized,
current architectural decision — see ADR-003 Decision Detail #15 / INV-04
(docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry
    from shared.tool_registry import ToolRegistry


def _resolve_registry(registry: "ToolRegistry | None") -> "ToolRegistry":
    """Return `registry`, or the default singleton registry when `registry` is None."""
    if registry is None:
        from shared.tool_registry import get_registry

        return get_registry()
    return registry


def validate_routing_against_live(
    registry: "ToolRegistry | None" = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if live_tool_lists is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def check_tool_safety_tiers(
    registry: "ToolRegistry | None" = None,
    runtime_registry: "RuntimeToolRegistry | None" = None,
) -> list[str]:
    """Return drift findings for reference-seed tools with no declared safety tier.

    Compares the reference seed registry with the live `RuntimeToolRegistry`:
    every live entry carries the `agent_safety_tier` its producer declared (the
    strict builder rejects an undeclared tier), so a seed tool with no live
    entry has no declared tier and is reported as drift. The result is a drift
    finding only — no caller may use it to classify a tool (agentcfg003: tiers
    are declared values, not configuration-derived ones).

    Returns an empty list when no runtime registry is available (nothing has
    been declared yet, so there is nothing to compare).
    """
    if runtime_registry is None or not runtime_registry.all_tools():
        return []
    registry = _resolve_registry(registry)
    declared = {tool.name for tool in runtime_registry.all_tools()}
    missing = [t for t in sorted(registry.get_all_tool_names()) if t not in declared]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from declared safety tiers"
        for t in missing
    ]


def check_unknown_tool_safety_tiers(
    registry: "ToolRegistry | None" = None,
    runtime_registry: "RuntimeToolRegistry | None" = None,
) -> list[str]:
    """Return declared live tools that are absent from the reference seed registry.

    The mirror of `check_tool_safety_tiers()`: a live declared entry naming a
    tool the reference data does not seed is stale or newly added reference
    data, and is reported as a drift finding — never as a classification.
    Returns an empty list when no runtime registry is available.
    """
    if runtime_registry is None or not runtime_registry.all_tools():
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(
        tool.name for tool in runtime_registry.all_tools() if tool.name not in known
    )
