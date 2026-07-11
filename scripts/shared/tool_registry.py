#!/usr/bin/env python3
"""shared/tool_registry.py
Primary source of truth for MCP tool ownership and routing.

Ownership model:
  - This module is the primary registry of all MCP tools.
  - Each tool belongs to exactly one server (server_key).
  - tool_constants.py frozensets populate this registry at import time.
  - Config mcp_servers.toml tool_names lists are optional; they are validated
    against the registry but not required as a source of truth.
  - Server /v1/tools responses are validated against the registry at startup.
  - This module owns tool-to-server ownership and routing only; it is not a
    schema/description registry. LLM-visible tool schemas come from each
    server's own `tools.py` `TOOL_LIST` (see
    `docs/04_mcp_07_tool_schema_export_policy.md`).

Routing authority:
  ToolRegistry is the sole routing authority. Live /v1/tools is used only for startup
  validation (drift detection), not for routing decisions.

Config `tool_names` is NOT a routing input; it is drift validation metadata only.

Drift detection:
  Canonical validation module: `shared.tool_routing_validation`.
  - validate_routing_against_config(): validates config tool_names against registry
  - validate_routing_against_live(): validates live /v1/tools responses against registry
  - validate_all_routing(): runs both config and live validation together
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolDefinition:
    """Immutable tool definition owned by a single server.

    `description` and `input_schema` are reserved for future use: they are never
    populated by `_populate_default_registry()` and are not read by any caller today.
    LLM-visible tool schemas are sourced from each server's own `tools.py` `TOOL_LIST`,
    not from this registry.
    """

    name: str
    server_key: str
    description: str = ""  # reserved for future use; not populated today
    input_schema: dict[str, object] = field(
        default_factory=dict
    )  # reserved for future use; not populated today


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
        """Validate live /v1/tools response against registry. Returns list of mismatches.

        For tools found in the live response but not in this server's registry,
        distinguishes between:
        - Unknown tool: not registered to any server (get_server_for_tool returns None).
        - Wrong-owner tool: registered to a different server than the one being validated.
        """
        registry_tools = set(self.get_tool_names(server_key))
        live_set = set(live_tool_names)

        mismatches: list[str] = []
        in_live_not_registry = live_set - registry_tools
        if in_live_not_registry:
            for t in sorted(in_live_not_registry):
                owner = self.get_server_for_tool(t)
                if owner is None:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is unknown (not registered to any server)"
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
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


def _reset_registry_for_testing() -> None:
    """Reset the global ToolRegistry singleton. FOR TESTING ONLY."""
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
    _register_set(registry, SHELL_TOOLS, "shell")
    _register_set(registry, GITHUB_TOOLS, "github")
    _register_set(registry, WEB_SEARCH_TOOLS, "web_search")


def _register_set(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, server_key=server_key))
