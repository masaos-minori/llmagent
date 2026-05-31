#!/usr/bin/env python3
"""
shared/route_resolver.py
Config-driven tool-name to server-key resolution for ToolExecutor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.tool_constants import (
    CICD_TOOLS,
    DELETE_TOOLS,
    MDQ_TOOLS,
    RAG_TOOLS,
    READ_TOOLS,
    WRITE_TOOLS,
)

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig


class ToolRouteResolver:
    """Maps tool_name to server_key: config-driven (tool_names list) first, then static prefix fallback; raises ValueError when no match."""

    def __init__(self, server_configs: dict[str, McpServerConfig]) -> None:
        # Build reverse map: tool_name -> server_key from explicitly configured tool_names.
        self._config_map: dict[str, str] = {}
        for key, cfg in server_configs.items():
            for tool_name in cfg.tool_names:
                self._config_map[tool_name] = key

    def resolve(self, tool_name: str) -> str:
        """Return the server key for tool_name via config-driven mapping then static fallback; raises ValueError when neither path matches."""
        key = self._config_map.get(tool_name)
        if key is not None:
            return key
        return self._fallback_route(tool_name)

    def _fallback_route(self, tool_name: str) -> str:
        """Static routing preserved from the original ToolExecutor._route()."""
        if tool_name in READ_TOOLS:
            return "file_read"
        if tool_name in WRITE_TOOLS:
            return "file_write"
        if tool_name in DELETE_TOOLS:
            return "file_delete"
        if tool_name == "shell_run":
            return "shell"
        if tool_name == "search_web":
            return "web_search"
        if tool_name.startswith("github_"):
            return "github"
        if tool_name in RAG_TOOLS:
            return "rag_pipeline"
        if tool_name in CICD_TOOLS:
            return "cicd"
        if tool_name in MDQ_TOOLS:
            return "mdq"
        raise ValueError(f"Unknown tool: {tool_name!r}")
