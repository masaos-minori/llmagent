#!/usr/bin/env python3
"""shared/route_resolver.py
Config-driven tool-name to server-key resolution for ToolExecutor.
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
)

_EXACT_ROUTES: dict[str, str] = {
    "shell_run": "shell",
    "search_web": "web_search",
}

_GITHUB_PREFIX = "github_"


class ToolRouteResolver:
    """Map tool_name → server_key.

    Config-driven (tool_names list) first; static prefix fallback second.
    Raises ValueError when neither path matches.
    """

    def __init__(
        self,
        server_configs: dict[str, McpServerConfig],
        *,
        warn_on_fallback: bool = False,
        strict_mode: bool = False,
    ) -> None:
        # Build reverse map: tool_name -> server_key from explicitly configured tool_names.
        self._config_map: dict[str, str] = {}
        for key, cfg in server_configs.items():
            for tool_name in cfg.tool_names:
                self._config_map[tool_name] = key
        self._warn_on_fallback = warn_on_fallback
        self._strict_mode = strict_mode

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
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
        if (route := _EXACT_ROUTES.get(tool_name)) is not None:
            return route
        if tool_name.startswith(_GITHUB_PREFIX):
            return "github"
        for entry in _SET_ROUTES:
            if tool_name in entry.tool_set:
                return entry.server_key
        raise ValueError(f"Unknown tool: {tool_name!r}")
