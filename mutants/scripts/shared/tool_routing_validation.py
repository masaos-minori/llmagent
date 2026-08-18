#!/usr/bin/env python3
"""scripts/shared/tool_routing_validation.py — MCP tool routing drift validation against config and live responses."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig
    from shared.tool_registry import ToolRegistry


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__resolve_registry__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__resolve_registry__mutmut)
def _resolve_registry(registry: "ToolRegistry | None") -> "ToolRegistry":
    """Return `registry`, or the default singleton registry when `registry` is None."""
    if registry is None:
        from shared.tool_registry import get_registry

        return get_registry()
    return registry


def x__resolve_registry__mutmut_orig(registry: "ToolRegistry | None") -> "ToolRegistry":
    """Return `registry`, or the default singleton registry when `registry` is None."""
    if registry is None:
        from shared.tool_registry import get_registry

        return get_registry()
    return registry


def x__resolve_registry__mutmut_1(registry: "ToolRegistry | None") -> "ToolRegistry":
    """Return `registry`, or the default singleton registry when `registry` is None."""
    if registry is not None:
        from shared.tool_registry import get_registry

        return get_registry()
    return registry

mutants_x__resolve_registry__mutmut['_mutmut_orig'] = x__resolve_registry__mutmut_orig # type: ignore # mutmut generated
mutants_x__resolve_registry__mutmut['x__resolve_registry__mutmut_1'] = x__resolve_registry__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_routing_against_config__mutmut)
def validate_routing_against_config(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
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


def x_validate_routing_against_config__mutmut_orig(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
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


def x_validate_routing_against_config__mutmut_1(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = None
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


def x_validate_routing_against_config__mutmut_2(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(None)
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


def x_validate_routing_against_config__mutmut_3(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is not None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_4(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = None
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_5(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_6(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            break
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_7(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = None
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_8(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(None, cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_9(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, None)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_10(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(cfg.tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_11(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, )
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_config__mutmut_12(
    registry: "ToolRegistry | None" = None,
    server_configs: dict[str, "McpServerConfig"] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if server_configs is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, cfg in server_configs.items():
        if not cfg.tool_names:
            continue
        mismatches = registry.validate_tool_names_match(server_key, cfg.tool_names)
        if mismatches:
            drift[server_key] = None

    return drift

mutants_x_validate_routing_against_config__mutmut['_mutmut_orig'] = x_validate_routing_against_config__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_1'] = x_validate_routing_against_config__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_2'] = x_validate_routing_against_config__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_3'] = x_validate_routing_against_config__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_4'] = x_validate_routing_against_config__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_5'] = x_validate_routing_against_config__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_6'] = x_validate_routing_against_config__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_7'] = x_validate_routing_against_config__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_8'] = x_validate_routing_against_config__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_9'] = x_validate_routing_against_config__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_10'] = x_validate_routing_against_config__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_11'] = x_validate_routing_against_config__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_routing_against_config__mutmut['x_validate_routing_against_config__mutmut_12'] = x_validate_routing_against_config__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_routing_against_live__mutmut)
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


def x_validate_routing_against_live__mutmut_orig(
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


def x_validate_routing_against_live__mutmut_1(
    registry: "ToolRegistry | None" = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = None
    if live_tool_lists is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_2(
    registry: "ToolRegistry | None" = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(None)
    if live_tool_lists is None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_3(
    registry: "ToolRegistry | None" = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    registry = _resolve_registry(registry)
    if live_tool_lists is not None:
        return {}

    drift: dict[str, list[str]] = {}
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_4(
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

    drift: dict[str, list[str]] = None
    for server_key, tool_names in live_tool_lists.items():
        mismatches = registry.validate_live_tools_match(server_key, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_5(
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
        mismatches = None
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_6(
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
        mismatches = registry.validate_live_tools_match(None, tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_7(
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
        mismatches = registry.validate_live_tools_match(server_key, None)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_8(
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
        mismatches = registry.validate_live_tools_match(tool_names)
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_9(
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
        mismatches = registry.validate_live_tools_match(server_key, )
        if mismatches:
            drift[server_key] = mismatches

    return drift


def x_validate_routing_against_live__mutmut_10(
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
            drift[server_key] = None

    return drift

mutants_x_validate_routing_against_live__mutmut['_mutmut_orig'] = x_validate_routing_against_live__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_1'] = x_validate_routing_against_live__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_2'] = x_validate_routing_against_live__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_3'] = x_validate_routing_against_live__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_4'] = x_validate_routing_against_live__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_5'] = x_validate_routing_against_live__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_6'] = x_validate_routing_against_live__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_7'] = x_validate_routing_against_live__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_8'] = x_validate_routing_against_live__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_9'] = x_validate_routing_against_live__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_routing_against_live__mutmut['x_validate_routing_against_live__mutmut_10'] = x_validate_routing_against_live__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_all_routing__mutmut)
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


def x_validate_all_routing__mutmut_orig(
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


def x_validate_all_routing__mutmut_1(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = None
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


def x_validate_all_routing__mutmut_2(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = None

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_3(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = None
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_4(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(None, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_5(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, None)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_6(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_7(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, )
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_8(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(None)

    live_drift = validate_routing_against_live(registry, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_9(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = None
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_10(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(None, live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_11(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, None)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_12(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(live_tool_lists)
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_13(
    server_configs: dict[str, "McpServerConfig"] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
    from shared.tool_registry import get_registry

    registry = get_registry()
    result: dict[str, list[str]] = {}

    config_drift = validate_routing_against_config(registry, server_configs)
    result.update(config_drift)

    live_drift = validate_routing_against_live(registry, )
    for server_key, messages in live_drift.items():
        if server_key in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_14(
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
        if server_key not in result:
            result[server_key].extend(messages)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_15(
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
            result[server_key].extend(None)
        else:
            result[server_key] = messages

    return result


def x_validate_all_routing__mutmut_16(
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
            result[server_key] = None

    return result

mutants_x_validate_all_routing__mutmut['_mutmut_orig'] = x_validate_all_routing__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_1'] = x_validate_all_routing__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_2'] = x_validate_all_routing__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_3'] = x_validate_all_routing__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_4'] = x_validate_all_routing__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_5'] = x_validate_all_routing__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_6'] = x_validate_all_routing__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_7'] = x_validate_all_routing__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_8'] = x_validate_all_routing__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_9'] = x_validate_all_routing__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_10'] = x_validate_all_routing__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_11'] = x_validate_all_routing__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_12'] = x_validate_all_routing__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_13'] = x_validate_all_routing__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_14'] = x_validate_all_routing__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_15'] = x_validate_all_routing__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate_all_routing__mutmut['x_validate_all_routing__mutmut_16'] = x_validate_all_routing__mutmut_16 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_check_tool_safety_tiers__mutmut)
def check_tool_safety_tiers(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_orig(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_1(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_2(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = None
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_3(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(None)
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_4(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = None
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_5(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = [
        t for t in sorted(None) if t not in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]


def x_check_tool_safety_tiers__mutmut_6(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return warning messages for registered tools missing a safety tier declaration.

    Only checks when tool_safety_tiers is non-empty (i.e., tier declarations are in use).
    Returns empty list when tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    missing = [
        t for t in sorted(registry.get_all_tool_names()) if t in tool_safety_tiers
    ]
    return [
        f"Tool {t!r} registered in ToolRegistry but missing from tool_safety_tiers"
        for t in missing
    ]

mutants_x_check_tool_safety_tiers__mutmut['_mutmut_orig'] = x_check_tool_safety_tiers__mutmut_orig # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_1'] = x_check_tool_safety_tiers__mutmut_1 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_2'] = x_check_tool_safety_tiers__mutmut_2 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_3'] = x_check_tool_safety_tiers__mutmut_3 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_4'] = x_check_tool_safety_tiers__mutmut_4 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_5'] = x_check_tool_safety_tiers__mutmut_5 # type: ignore # mutmut generated
mutants_x_check_tool_safety_tiers__mutmut['x_check_tool_safety_tiers__mutmut_6'] = x_check_tool_safety_tiers__mutmut_6 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_check_unknown_tool_safety_tiers__mutmut)
def check_unknown_tool_safety_tiers(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_orig(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_1(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_2(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = None
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_3(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(None)
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_4(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = None
    return sorted(set(tool_safety_tiers) - known)


def x_check_unknown_tool_safety_tiers__mutmut_5(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(None)


def x_check_unknown_tool_safety_tiers__mutmut_6(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(set(tool_safety_tiers) + known)


def x_check_unknown_tool_safety_tiers__mutmut_7(
    registry: "ToolRegistry | None" = None,
    tool_safety_tiers: dict[str, str] | None = None,
) -> list[str]:
    """Return the tool_safety_tiers keys that are not registered tool names.

    Detects stale or misconfigured entries (e.g. a server key like "mdq"
    used instead of its individual tool names). Returns empty list when
    tool_safety_tiers is not configured.
    """
    if not tool_safety_tiers:
        return []
    registry = _resolve_registry(registry)
    known = registry.get_all_tool_names()
    return sorted(set(None) - known)

mutants_x_check_unknown_tool_safety_tiers__mutmut['_mutmut_orig'] = x_check_unknown_tool_safety_tiers__mutmut_orig # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_1'] = x_check_unknown_tool_safety_tiers__mutmut_1 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_2'] = x_check_unknown_tool_safety_tiers__mutmut_2 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_3'] = x_check_unknown_tool_safety_tiers__mutmut_3 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_4'] = x_check_unknown_tool_safety_tiers__mutmut_4 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_5'] = x_check_unknown_tool_safety_tiers__mutmut_5 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_6'] = x_check_unknown_tool_safety_tiers__mutmut_6 # type: ignore # mutmut generated
mutants_x_check_unknown_tool_safety_tiers__mutmut['x_check_unknown_tool_safety_tiers__mutmut_7'] = x_check_unknown_tool_safety_tiers__mutmut_7 # type: ignore # mutmut generated
