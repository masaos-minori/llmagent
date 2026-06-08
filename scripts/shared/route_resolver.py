#!/usr/bin/env python3
"""shared/route_resolver.py
Config-driven tool-name to server-key resolution for ToolExecutor.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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

# Ordered table used by _fallback_route: each entry maps a frozenset to a server key.
# Order is preserved only for readability; no two sets overlap, so match order is irrelevant.
_SET_ROUTES: tuple[tuple[frozenset[str], str], ...] = (
    (READ_TOOLS, "file_read"),
    (WRITE_TOOLS, "file_write"),
    (DELETE_TOOLS, "file_delete"),
    (RAG_TOOLS, "rag_pipeline"),
    (CICD_TOOLS, "cicd"),
    (MDQ_TOOLS, "mdq"),
    (GIT_TOOLS, "git"),
)

# Single-name tools that cannot be identified by set membership or prefix.
_EXACT_ROUTES: dict[str, str] = {
    "shell_run": "shell",
    "search_web": "web_search",
}


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
    ) -> None:
        # Build reverse map: tool_name -> server_key from explicitly configured tool_names.
        self._config_map: dict[str, str] = {}
        for key, cfg in server_configs.items():
            for tool_name in cfg.tool_names:
                self._config_map[tool_name] = key
        self._warn_on_fallback = warn_on_fallback

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name; raises ValueError when no match."""
        key = self._config_map.get(tool_name)
        if key is not None:
            return key
        if self._warn_on_fallback:
            logger.warning(
                "ToolRouteResolver: tool %r not in config map; using static fallback. "
                "Add tool_names to mcp_servers config to suppress this warning.",
                tool_name,
            )
        return self._fallback_route(tool_name)

    def _fallback_route(self, tool_name: str) -> str:
        """Static routing preserved from the original ToolExecutor._route()."""
        if route := _EXACT_ROUTES.get(tool_name):
            return route
        if tool_name.startswith("github_"):
            return "github"
        for tool_set, server in _SET_ROUTES:
            if tool_name in tool_set:
                return server
        raise ValueError(f"Unknown tool: {tool_name!r}")
