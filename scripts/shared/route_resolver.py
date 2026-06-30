#!/usr/bin/env python3
"""shared/route_resolver.py
Tool-name to server-key resolution for ToolExecutor.

Routing priority:
  1. Live-discovered tool metadata from /v1/tools (server_key field) — optional, only when discovery map is built at startup
  2. Tool registry (canonical source of truth from tool_registry.py; populated from tool_constants.py frozensets)

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


def build_discovery_map(
    server_tool_lists: dict[str, list[dict[str, object]]],
) -> dict[str, str]:
    """Build a routing map from live-discovered tool metadata.

    Each server's tool list should include a 'server_key' field per tool.
    Returns {tool_name: server_key} mapping. Duplicate tool names across servers
    log a warning and use the first occurrence.

    Example:
        >>> build_discovery_map({
        ...     "file_read": [{"name": "read_file", "server_key": "file_read"}],
        ...     "shell": [{"name": "shell_run", "server_key": "shell"}],
        ... })
        {'read_file': 'file_read', 'shell_run': 'shell'}
    """
    route_map: dict[str, str] = {}
    for server_key, tools in server_tool_lists.items():
        for tool in tools:
            name_raw = tool.get("name")
            name = name_raw if isinstance(name_raw, str) and name_raw else ""
            tk_raw = tool.get("server_key")
            tk = tk_raw if isinstance(tk_raw, str) and tk_raw else server_key
            if not name:
                continue
            if name in route_map and route_map[name] != tk:
                logger.warning(
                    "Tool %r claimed by both %r and %r; using %r first",
                    name,
                    route_map[name],
                    tk,
                    route_map[name],
                )
            else:
                route_map[name] = tk
    return route_map


class ToolRouteResolver:
    """Map tool_name → server_key.

    Routing priority:
      1. Discovery map (live /v1/tools metadata with server_key) — only when built at startup
      2. Tool registry (canonical source of truth from tool_registry.py)
    Raises ValueError when none of the above match.

    Config `tool_names` is NOT a routing input; it is validation metadata only.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        discovery_map: dict[str, str] | None = None,
        warn_on_fallback: bool = False,
        strict_mode: bool = False,
        known_tools: frozenset[str] | None = None,
    ) -> None:
        # Discovery map from live /v1/tools metadata (highest priority).
        self._discovery_map: dict[str, str] = discovery_map or {}
        # Tool registry (canonical source of truth).
        from shared.tool_registry import ToolRegistry

        self._registry: ToolRegistry | None
        try:
            from shared.tool_registry import get_registry

            self._registry = get_registry()
        except (ImportError, RuntimeError) as exc:
            logger.warning("Failed to initialize ToolRegistry: %s", exc)
            self._registry = None
        # Config tool_names is NOT used for routing — only for drift validation.
        self._warn_on_fallback = warn_on_fallback
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        # Priority 1: discovery map (live server metadata).
        if (key := self._discovery_map.get(tool_name)) is not None:
            return key
        # Priority 2: tool registry (canonical source of truth).
        if (key := self._lookup_registry(tool_name)) is not None:
            return key
        # No mapping found — raise ValueError immediately.
        if self._strict_mode:
            self._raise_strict_error(tool_name)
        if self._warn_on_fallback:
            logger.warning(
                "ToolRouteResolver: tool %r not in discovery map or ToolRegistry; "
                "add it to the appropriate frozenset in shared/tool_constants.py or register it in ToolRegistry.",
                tool_name,
            )
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def _lookup_registry(self, tool_name: str) -> str | None:
        """Look up a tool in the registry; returns server key or None."""
        if self._registry is not None:
            return self._registry.get_server_for_tool(tool_name)
        return None

    def _raise_strict_error(self, tool_name: str) -> None:
        """Raise ValueError when strict_mode is enabled and no mapping found."""
        raise ValueError(
            f"ToolRouteResolver: tool {tool_name!r} not in discovery map or ToolRegistry "
            f"and strict_mode=True; add it to the appropriate frozenset in shared/tool_constants.py"
        )

    def _log_routing_coverage(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup."""
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if tool_name in self._discovery_map:
                mapped.append(tool_name)
                continue
            if self._lookup_registry(tool_name) is not None:
                mapped.append(tool_name)
                continue
            # No mapping found — this tool is unmapped
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
