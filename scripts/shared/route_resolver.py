#!/usr/bin/env python3
"""shared/route_resolver.py
Config-driven tool-name to server-key resolution for ToolExecutor.

Routing priority:
  1. Live-discovered tool metadata from /v1/tools (server_key field)
  2. Config-driven tool_names from mcp_servers config
  3. Static fallback constants (compatibility/emergency use only)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NamedTuple

from shared.tool_constants import (
    CICD_TOOLS,
    DELETE_TOOLS,
    GIT_TOOLS,
    MDQ_TOOLS,
    RAG_TOOLS,
    READ_TOOLS,
    SHELL_TOOLS,
    SQLITE_TOOLS,
    WEB_SEARCH_TOOLS,
    WRITE_TOOLS,
)

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


class _SetRoute(NamedTuple):
    tool_set: frozenset[str]
    server_key: str


_SET_ROUTES: tuple[_SetRoute, ...] = (
    _SetRoute(READ_TOOLS, "file_read"),
    _SetRoute(WRITE_TOOLS, "file_write"),
    _SetRoute(DELETE_TOOLS, "file_delete"),
    _SetRoute(RAG_TOOLS, "rag_pipeline"),
    _SetRoute(CICD_TOOLS, "cicd"),
    _SetRoute(MDQ_TOOLS, "mdq"),
    _SetRoute(GIT_TOOLS, "git"),
    _SetRoute(SQLITE_TOOLS, "sqlite"),
    _SetRoute(SHELL_TOOLS, "shell"),
    _SetRoute(WEB_SEARCH_TOOLS, "web_search"),
)

_GITHUB_PREFIX = "github_"


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
      1. Discovery map (live /v1/tools metadata with server_key)
      2. Config-driven (tool_names list from mcp_servers config)
      3. Static fallback (SET_ROUTES, github prefix matching)
    Raises ValueError when none of the above match.
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
        # Build reverse map: tool_name -> server_key from explicitly configured tool_names.
        self._config_map: dict[str, str] = {}
        for key, cfg in server_configs.items():
            for tool_name in cfg.tool_names:
                self._config_map[tool_name] = key
        self._warn_on_fallback = warn_on_fallback
        self._strict_mode = strict_mode
        if known_tools:
            self._log_routing_coverage(known_tools)

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        # Priority 1: discovery map (live server metadata).
        if (key := self._discovery_map.get(tool_name)) is not None:
            return key
        if (key := self._config_map.get(tool_name)) is not None:
            return key
        if self._strict_mode:
            raise ValueError(
                f"ToolRouteResolver: tool {tool_name!r} not in config map "
                f"and strict_mode=True; add it to tool_names in mcp_servers config"
            )
        if self._warn_on_fallback:
            logger.warning(
                "ToolRouteResolver: tool %r not in config map; using static fallback. "
                "Add tool_names to mcp_servers config to suppress this warning.",
                tool_name,
            )
        return self._fallback_route(tool_name)

    def _fallback_route(self, tool_name: str) -> str:
        """Static routing preserved from the original ToolExecutor._route()."""
        if tool_name.startswith(_GITHUB_PREFIX):
            return "github"
        for entry in _SET_ROUTES:
            if tool_name in entry.tool_set:
                return entry.server_key
        raise ValueError(f"Unknown tool: {tool_name!r}")

    def _log_routing_coverage(self, known_tools: frozenset[str]) -> None:
        """Log routing coverage for all known tools at startup."""
        mapped: list[str] = []
        unmapped: list[str] = []
        for tool_name in sorted(known_tools):
            if tool_name in self._discovery_map or tool_name in self._config_map:
                mapped.append(tool_name)
                continue
            try:
                self._fallback_route(tool_name)
                mapped.append(tool_name)
            except ValueError:
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
