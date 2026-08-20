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
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)


class ToolDescriptor(TypedDict, total=False):
    """One tool-descriptor entry from a server's /v1/tools discovery payload."""

    name: str
    server_key: str  # present in some fixtures; ignored by build_discovery_map (outer dict key is authoritative)


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


class ToolRouteResolver:
    """Map tool_name → server_key using RuntimeToolRegistry as the sole routing authority.

    RuntimeToolRegistry is populated from live /v1/tools discovery. Raises ValueError
    when the tool is not found there.
    """

    def __init__(
        self,
        *,
        warn_on_missing: bool = False,
        strict_mode: bool = False,
        runtime_registry: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            warn_on_missing: When True, log a warning on unresolved tools in `resolve()`.
            strict_mode: When True, raise on unresolved tools in `resolve()` with a
                stricter error message.
            runtime_registry: Optional RuntimeToolRegistry from live /v1/tools discovery;
                the sole routing source consulted by resolve().
        """
        # RuntimeToolRegistry (sole routing authority).
        self._runtime_registry: RuntimeToolRegistry | None = runtime_registry
        self._warn_on_missing = warn_on_missing
        self._strict_mode = strict_mode

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

    def _lookup_runtime_registry(self, tool_name: str) -> str | None:
        """Look up a tool in RuntimeToolRegistry; returns server key or None."""
        if self._runtime_registry is not None:
            return self._runtime_registry.resolve(tool_name)
        return None

    def set_runtime_registry(self, registry: RuntimeToolRegistry | None) -> None:
        """Replace the RuntimeToolRegistry consulted by resolve(), in place."""
        self._runtime_registry = registry

    def _raise_strict_error(self, tool_name: str) -> NoReturn:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not found in RuntimeToolRegistry "
            f"and strict_mode=True; ensure MCP servers are healthy and discovery completed"
        )
