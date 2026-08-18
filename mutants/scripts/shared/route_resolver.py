#!/usr/bin/env python3
"""scripts/shared/route_resolver.py

Tool-name to server-key resolution for ToolExecutor.

`RuntimeToolRegistry` (populated from live `/v1/tools` discovery via
`ToolExecutor.set_runtime_registry()`) is the sole routing authority. When a tool is not
found there, `resolve()` either raises `ValueError` immediately (strict_mode) or logs a
warning and then raises. `ToolRegistry` is no longer consulted here.

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
Live /v1/tools discovery is used for startup validation only, not routing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NoReturn, TypedDict

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class ToolDescriptor(TypedDict, total=False):
    """One tool-descriptor entry from a server's /v1/tools discovery payload."""

    name: str
    server_key: str  # present in some fixtures; ignored by build_discovery_map (outer dict key is authoritative)
mutants_x_build_discovery_map__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_discovery_map__mutmut)
def build_discovery_map(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_orig(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_1(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = None
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_2(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = None

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_3(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = None
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_4(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get(None)
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_5(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("XXnameXX")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_6(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("NAME")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_7(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) and not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_8(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_9(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_10(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                break
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_11(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(None)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_12(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(None, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_13(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, None).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_14(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault([]).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_15(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, ).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_16(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_17(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = None
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_18(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    None,
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_19(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    None,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_20(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    None,
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_21(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    None,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_22(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_23(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_24(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_25(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_26(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "XXDuplicate tool ownership: %r claimed by %r and %rXX",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_27(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_28(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "DUPLICATE TOOL OWNERSHIP: %R CLAIMED BY %R AND %R",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_29(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = None
    return route_map, duplicates


def x_build_discovery_map__mutmut_30(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) >= 1}
    return route_map, duplicates


def x_build_discovery_map__mutmut_31(
    server_tool_lists: dict[str, list[ToolDescriptor]],
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Build routing map from per-server tool lists and detect duplicate ownership.

    Returns:
        route_map: {tool_name: first_claiming_server_key}
        duplicates: {tool_name: [server_key_1, server_key_2, ...]} — only tools with >1 owner
    """
    route_map: dict[str, str] = {}
    all_claims: dict[str, list[str]] = {}

    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            all_claims.setdefault(name, []).append(server_key)
            if name not in route_map:
                route_map[name] = server_key
            else:
                logger.warning(
                    "Duplicate tool ownership: %r claimed by %r and %r",
                    name,
                    route_map[name],
                    server_key,
                )

    duplicates = {n: keys for n, keys in all_claims.items() if len(keys) > 2}
    return route_map, duplicates

mutants_x_build_discovery_map__mutmut['_mutmut_orig'] = x_build_discovery_map__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_1'] = x_build_discovery_map__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_2'] = x_build_discovery_map__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_3'] = x_build_discovery_map__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_4'] = x_build_discovery_map__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_5'] = x_build_discovery_map__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_6'] = x_build_discovery_map__mutmut_6 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_7'] = x_build_discovery_map__mutmut_7 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_8'] = x_build_discovery_map__mutmut_8 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_9'] = x_build_discovery_map__mutmut_9 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_10'] = x_build_discovery_map__mutmut_10 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_11'] = x_build_discovery_map__mutmut_11 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_12'] = x_build_discovery_map__mutmut_12 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_13'] = x_build_discovery_map__mutmut_13 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_14'] = x_build_discovery_map__mutmut_14 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_15'] = x_build_discovery_map__mutmut_15 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_16'] = x_build_discovery_map__mutmut_16 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_17'] = x_build_discovery_map__mutmut_17 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_18'] = x_build_discovery_map__mutmut_18 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_19'] = x_build_discovery_map__mutmut_19 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_20'] = x_build_discovery_map__mutmut_20 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_21'] = x_build_discovery_map__mutmut_21 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_22'] = x_build_discovery_map__mutmut_22 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_23'] = x_build_discovery_map__mutmut_23 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_24'] = x_build_discovery_map__mutmut_24 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_25'] = x_build_discovery_map__mutmut_25 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_26'] = x_build_discovery_map__mutmut_26 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_27'] = x_build_discovery_map__mutmut_27 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_28'] = x_build_discovery_map__mutmut_28 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_29'] = x_build_discovery_map__mutmut_29 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_30'] = x_build_discovery_map__mutmut_30 # type: ignore # mutmut generated
mutants_x_build_discovery_map__mutmut['x_build_discovery_map__mutmut_31'] = x_build_discovery_map__mutmut_31 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRouteResolverǁresolve__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRouteResolverǁset_runtime_registry__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRouteResolverǁ_raise_strict_error__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut: MutantDict = {}  # type: ignore


class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
    when the tool is not found there.
    """

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁ__init____mutmut)
    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_orig(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_1(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = True,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_2(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = True,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_3(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = None
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_4(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map and {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_5(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = None
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_6(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = None
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_7(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = None
        if known_tools:
            self._log_routing_coverage(known_tools)

    def xǁToolRouteResolverǁ__init____mutmut_8(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            server_configs: Accepted for backward compatibility with existing callers;
                not read or stored — routing never consults per-server config.
            discovery_map: Live /v1/tools validation data; used only by the
                currently-unreachable `_log_routing_coverage()` diagnostic, never by
                `resolve()`.
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            known_tools: When provided, triggers a startup coverage log via
                `_log_routing_coverage()`. No production caller passes this today.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # Validation data from live /v1/tools (not used for routing).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(None)

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁresolve__mutmut)
    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_orig(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_1(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(None)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_2(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_3(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(None)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_4(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                None,
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_5(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                None,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_6(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_7(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_8(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "XXToolRouteResolver: tool %r not found in RuntimeToolRegistry; XX"
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_9(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "toolrouteresolver: tool %r not found in runtimetoolregistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_10(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "TOOLROUTERESOLVER: TOOL %R NOT FOUND IN RUNTIMETOOLREGISTRY; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_11(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "XXensure MCP servers are healthy and discovery completed.XX",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_12(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure mcp servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_13(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ENSURE MCP SERVERS ARE HEALTHY AND DISCOVERY COMPLETED.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def xǁToolRouteResolverǁresolve__mutmut_14(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        if (key := self._lookup_runtime_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_missing:
            logger.warning(
                "ToolRouteResolver: tool %r not found in RuntimeToolRegistry; "
                "ensure MCP servers are healthy and discovery completed.",
                tool_name,
            )
        raise ValueError(None)

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut)
    def _lookup_runtime_registry(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_orig(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_1(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_2(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(None)
        return None

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁset_runtime_registry__mutmut)
    def set_runtime_registry(self, registry: RuntimeToolRegistry | None) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place."""
        self._runtime_registry = registry

    def xǁToolRouteResolverǁset_runtime_registry__mutmut_orig(self, registry: RuntimeToolRegistry | None) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place."""
        self._runtime_registry = registry

    def xǁToolRouteResolverǁset_runtime_registry__mutmut_1(self, registry: RuntimeToolRegistry | None) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place."""
        self._runtime_registry = None

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁ_raise_strict_error__mutmut)
    def _raise_strict_error(self, tool_name: str) -> NoReturn:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not found in RuntimeToolRegistry "
            f"and strict_mode=True; ensure MCP servers are healthy and discovery completed"
        )

    def xǁToolRouteResolverǁ_raise_strict_error__mutmut_orig(self, tool_name: str) -> NoReturn:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not found in RuntimeToolRegistry "
            f"and strict_mode=True; ensure MCP servers are healthy and discovery completed"
        )

    def xǁToolRouteResolverǁ_raise_strict_error__mutmut_1(self, tool_name: str) -> NoReturn:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            None
        )

    @_mutmut_mutated(mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut)
    def _log_routing_coverage(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_orig(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_1(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = None
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_2(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = None
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_3(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(None):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_4(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(None) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_5(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_6(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(None)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_7(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(None)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_8(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = None
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_9(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                None,
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_10(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                None,
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_11(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                None,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_12(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                None,
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_13(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                None,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_14(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_15(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_16(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_17(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_18(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_19(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "XXRouting: %d/%d tools mapped; %d unmapped: %sXX",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_20(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_21(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "ROUTING: %D/%D TOOLS MAPPED; %D UNMAPPED: %S",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_22(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info(None, total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_23(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", None, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_24(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, None)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_25(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info(total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_26(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_27(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("Routing: %d/%d tools mapped", total, )

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_28(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("XXRouting: %d/%d tools mappedXX", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_29(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("routing: %d/%d tools mapped", total, total)

    def xǁToolRouteResolverǁ_log_routing_coverage__mutmut_30(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup.

        "Mapped" means resolvable via RuntimeToolRegistry — the same authority
        `resolve()` uses — not merely present in `discovery_map`. `discovery_map` is
        validation-only metadata from live /v1/tools responses and carries no routing
        authority: a tool present only in `discovery_map` but absent from
        RuntimeToolRegistry is UNMAPPED for this purpose, since `resolve()` would raise
        `ValueError` for it.

        Note: as of this writing, no production caller passes `known_tools` to
        `ToolRouteResolver.__init__()` (see `shared/tool_executor.py`'s construction
        call), so this method does not currently execute in production. It remains
        available for a future caller wanting startup coverage visibility.
        """
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if self._lookup_runtime_registry(tool_name) is not None:
                mapped.append(tool_name)
            else:
                unmapped.append(tool_name)
        total = len(known_tools)
        if unmapped:
            logger.warning(
                "Routing: %d/%d tools mapped; %d unmapped: %s",
                len(mapped),
                total,
                len(unmapped),
                unmapped,
            )
        else:
            logger.info("ROUTING: %D/%D TOOLS MAPPED", total, total)

mutants_xǁToolRouteResolverǁ__init____mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_2'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_3'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_4'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_5'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_6'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_7'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ__init____mutmut['xǁToolRouteResolverǁ__init____mutmut_8'] = ToolRouteResolver.xǁToolRouteResolverǁ__init____mutmut_8 # type: ignore # mutmut generated

mutants_xǁToolRouteResolverǁresolve__mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_2'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_3'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_4'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_5'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_6'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_7'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_8'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_9'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_10'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_11'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_12'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_13'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁresolve__mutmut['xǁToolRouteResolverǁresolve__mutmut_14'] = ToolRouteResolver.xǁToolRouteResolverǁresolve__mutmut_14 # type: ignore # mutmut generated

mutants_xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut['xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut['xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_2'] = ToolRouteResolver.xǁToolRouteResolverǁ_lookup_runtime_registry__mutmut_2 # type: ignore # mutmut generated

mutants_xǁToolRouteResolverǁset_runtime_registry__mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁset_runtime_registry__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁset_runtime_registry__mutmut['xǁToolRouteResolverǁset_runtime_registry__mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁset_runtime_registry__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolRouteResolverǁ_raise_strict_error__mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁ_raise_strict_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_raise_strict_error__mutmut['xǁToolRouteResolverǁ_raise_strict_error__mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁ_raise_strict_error__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['_mutmut_orig'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_1'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_2'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_3'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_4'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_5'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_6'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_7'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_8'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_9'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_10'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_11'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_12'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_13'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_14'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_15'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_16'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_17'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_18'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_19'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_20'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_21'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_22'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_23'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_24'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_25'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_26'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_27'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_28'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_29'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolRouteResolverǁ_log_routing_coverage__mutmut['xǁToolRouteResolverǁ_log_routing_coverage__mutmut_30'] = ToolRouteResolver.xǁToolRouteResolverǁ_log_routing_coverage__mutmut_30 # type: ignore # mutmut generated
