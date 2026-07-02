#!/usr/bin/env python3
"""shared/tool_registry.py
Primary source of truth for MCP tool definitions and drift validation.

Ownership model:
  - This module is the primary registry of all MCP tools.
  - Each tool belongs to exactly one server (server_key).
  - tool_constants.py frozensets populate this registry at import time.
  - Config mcp_servers.toml tool_names lists are optional; they are validated
    against the registry but not required as a source of truth.
  - Server /v1/tools responses are validated against the registry at startup.

Routing priority:
  1. Live discovery map (/v1/tools with server_key) — runtime override, highest priority
  2. Registry (this module) — primary routing layer, populated from frozensets at import time

Config `tool_names` is NOT a routing input; it is drift validation metadata only.

Drift detection:
  - compare_registry_vs_config(): validates config tool_names against registry
  - compare_registry_vs_live(): validates live /v1/tools responses against registry
  - compare_config_vs_live(): validates config tool_names against live responses
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolDefinition:
    """Immutable tool definition owned by a single server."""

    name: str
    server_key: str
    description: str = ""
    input_schema: dict[str, object] = field(default_factory=dict)


class ToolRegistry:
    """Central registry of MCP tools. Single source of truth for tool ownership."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}  # name → ToolDefinition
        self._by_server: dict[str, list[str]] = {}  # server_key → [tool_names]

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def get_server_for_tool(self, tool_name: str) -> str | None:
        """Return the server_key that owns tool_name, or None if unknown."""
        td = self._tools.get(tool_name)
        return td.server_key if td else None

    def get_tool_names(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key."""
        return list(self._by_server.get(server_key, []))

    def get_all_tool_names(self) -> frozenset[str]:
        """Return all registered tool names."""
        return frozenset(self._tools.keys())

    def get_servers(self) -> list[str]:
        """Return all server keys in the registry."""
        return sorted(self._by_server.keys())

    def validate_tool_names_match(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        in_config_not_registry = config_set - registry_tools
        if in_config_not_registry:
            mismatches.extend(
                f"[{server_key}] tool {t!r} in config but not in registry"
                for t in sorted(in_config_not_registry)
            )

        in_registry_not_config = registry_tools - config_set
        if in_registry_not_config:
            mismatches.extend(
                f"[{server_key}] tool {t!r} in registry but not in config"
                for t in sorted(in_registry_not_config)
            )

        return mismatches

    def validate_live_tools_match(
        self,
        server_key: str,
        live_tool_names: list[str],
    ) -> list[str]:
        """Validate live /v1/tools response against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        live_set = set(live_tool_names)

        mismatches: list[str] = []
        in_live_not_registry = live_set - registry_tools
        if in_live_not_registry:
            mismatches.extend(
                f"[{server_key}] tool {t!r} in live response but not in registry"
                for t in sorted(in_live_not_registry)
            )

        in_registry_not_live = registry_tools - live_set
        if in_registry_not_live:
            mismatches.extend(
                f"[{server_key}] tool {t!r} in registry but not in live response"
                for t in sorted(in_registry_not_live)
            )

        return mismatches


# Global singleton registry.
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _populate_default_registry(_registry)
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None


def _populate_default_registry(registry: ToolRegistry) -> None:
    """Populate the registry with default tool definitions from tool_constants."""
    from shared.tool_constants import (
        CICD_TOOLS,
        DELETE_TOOLS,
        GIT_TOOLS,
        GITHUB_TOOLS,
        MDQ_TOOLS,
        RAG_TOOLS,
        READ_TOOLS,
        SHELL_TOOLS,
        SQLITE_TOOLS,
        WEB_SEARCH_TOOLS,
        WRITE_TOOLS,
    )

    # Register each tool set with its server key.
    _register_set(registry, READ_TOOLS, "file_read")
    _register_set(registry, WRITE_TOOLS, "file_write")
    _register_set(registry, DELETE_TOOLS, "file_delete")
    _register_set(registry, RAG_TOOLS, "rag_pipeline")
    _register_set(registry, CICD_TOOLS, "cicd")
    _register_set(registry, MDQ_TOOLS, "mdq")
    _register_set(registry, GIT_TOOLS, "git")
    _register_set(registry, SQLITE_TOOLS, "sqlite")
    _register_set(registry, SHELL_TOOLS, "shell")
    _register_set(registry, GITHUB_TOOLS, "github")
    _register_set(registry, WEB_SEARCH_TOOLS, "web_search")


def _register_set(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, server_key=server_key))


def validate_routing_against_config(
    registry: ToolRegistry | None = None,
    server_configs: dict[str, McpServerConfig] | None = None,
) -> dict[str, list[str]]:
    """Validate that config tool_names match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    if registry is None:
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
    registry: ToolRegistry | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Validate that live /v1/tools responses match the registry.

    Returns {server_key: [mismatch_messages]} for servers with mismatches.
    Empty dict means no drift detected.
    """
    if registry is None:
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
    server_configs: dict[str, McpServerConfig] | None = None,
    live_tool_lists: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    """Run all routing validations. Returns combined drift report."""
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
