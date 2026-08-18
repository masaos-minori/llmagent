#!/usr/bin/env python3
"""scripts/shared/tool_registry.py

Tool ownership registry and routing seed data. RuntimeToolRegistry
(shared/runtime_tool_registry.py) is the sole runtime routing authority, populated from
live /v1/tools discovery. ToolRegistry now serves only as:
  (a) drift-detection input for McpToolDiscoveryService (per requirement 09).

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
from typing import Any

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


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
    input_schema: dict[str, Any] = field(
        default_factory=dict
    )  # reserved for future use; not populated today
mutants_x__diff_messages__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__diff_messages__mutmut)
def _diff_messages(
    subject_tools: set[str],
    other_tools: set[str],
    server_key: str,
    subject_label: str,
    other_label: str,
) -> list[str]:
    """Build mismatch messages for tools in `subject_tools` but absent from `other_tools`."""
    missing = subject_tools - other_tools
    return [
        f"[{server_key}] tool {t!r} in {subject_label} but not in {other_label}"
        for t in sorted(missing)
    ]


def x__diff_messages__mutmut_orig(
    subject_tools: set[str],
    other_tools: set[str],
    server_key: str,
    subject_label: str,
    other_label: str,
) -> list[str]:
    """Build mismatch messages for tools in `subject_tools` but absent from `other_tools`."""
    missing = subject_tools - other_tools
    return [
        f"[{server_key}] tool {t!r} in {subject_label} but not in {other_label}"
        for t in sorted(missing)
    ]


def x__diff_messages__mutmut_1(
    subject_tools: set[str],
    other_tools: set[str],
    server_key: str,
    subject_label: str,
    other_label: str,
) -> list[str]:
    """Build mismatch messages for tools in `subject_tools` but absent from `other_tools`."""
    missing = None
    return [
        f"[{server_key}] tool {t!r} in {subject_label} but not in {other_label}"
        for t in sorted(missing)
    ]


def x__diff_messages__mutmut_2(
    subject_tools: set[str],
    other_tools: set[str],
    server_key: str,
    subject_label: str,
    other_label: str,
) -> list[str]:
    """Build mismatch messages for tools in `subject_tools` but absent from `other_tools`."""
    missing = subject_tools + other_tools
    return [
        f"[{server_key}] tool {t!r} in {subject_label} but not in {other_label}"
        for t in sorted(missing)
    ]


def x__diff_messages__mutmut_3(
    subject_tools: set[str],
    other_tools: set[str],
    server_key: str,
    subject_label: str,
    other_label: str,
) -> list[str]:
    """Build mismatch messages for tools in `subject_tools` but absent from `other_tools`."""
    missing = subject_tools - other_tools
    return [
        f"[{server_key}] tool {t!r} in {subject_label} but not in {other_label}"
        for t in sorted(None)
    ]

mutants_x__diff_messages__mutmut['_mutmut_orig'] = x__diff_messages__mutmut_orig # type: ignore # mutmut generated
mutants_x__diff_messages__mutmut['x__diff_messages__mutmut_1'] = x__diff_messages__mutmut_1 # type: ignore # mutmut generated
mutants_x__diff_messages__mutmut['x__diff_messages__mutmut_2'] = x__diff_messages__mutmut_2 # type: ignore # mutmut generated
mutants_x__diff_messages__mutmut['x__diff_messages__mutmut_3'] = x__diff_messages__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁregister__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁget_server_for_tool__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁget_tool_names__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁget_all_tool_names__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁget_servers__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut: MutantDict = {}  # type: ignore
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut: MutantDict = {}  # type: ignore


class ToolRegistry:
    """Central registry of MCP tools. Single source of truth for tool ownership."""

    @_mutmut_mutated(mutants_xǁToolRegistryǁ__init____mutmut)
    def __init__(self) -> None:
        """Initialize with empty tool and server mappings."""
        self._tools: dict[str, ToolDefinition] = {}  # name → ToolDefinition
        self._by_server: dict[str, list[str]] = {}  # server_key → [tool_names]

    def xǁToolRegistryǁ__init____mutmut_orig(self) -> None:
        """Initialize with empty tool and server mappings."""
        self._tools: dict[str, ToolDefinition] = {}  # name → ToolDefinition
        self._by_server: dict[str, list[str]] = {}  # server_key → [tool_names]

    def xǁToolRegistryǁ__init____mutmut_1(self) -> None:
        """Initialize with empty tool and server mappings."""
        self._tools: dict[str, ToolDefinition] = None  # name → ToolDefinition
        self._by_server: dict[str, list[str]] = {}  # server_key → [tool_names]

    def xǁToolRegistryǁ__init____mutmut_2(self) -> None:
        """Initialize with empty tool and server mappings."""
        self._tools: dict[str, ToolDefinition] = {}  # name → ToolDefinition
        self._by_server: dict[str, list[str]] = None  # server_key → [tool_names]

    @_mutmut_mutated(mutants_xǁToolRegistryǁregister__mutmut)
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

    def xǁToolRegistryǁregister__mutmut_orig(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_1(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name not in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_2(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = None
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_3(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                None
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_4(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = None
        self._by_server.setdefault(definition.server_key, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_5(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, []).append(None)

    def xǁToolRegistryǁregister__mutmut_6(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(None, []).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_7(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, None).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_8(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault([]).append(definition.name)

    def xǁToolRegistryǁregister__mutmut_9(self, definition: ToolDefinition) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        if definition.name in self._tools:
            existing = self._tools[definition.name]
            raise ValueError(
                f"Tool {definition.name!r} already registered to server {existing.server_key!r}; "
                f"cannot reassign to {definition.server_key!r}"
            )
        self._tools[definition.name] = definition
        self._by_server.setdefault(definition.server_key, ).append(definition.name)

    @_mutmut_mutated(mutants_xǁToolRegistryǁget_server_for_tool__mutmut)
    def get_server_for_tool(self, tool_name: str) -> str | None:
        """Return the server_key that owns tool_name, or None if unknown."""
        td = self._tools.get(tool_name)
        return td.server_key if td else None

    def xǁToolRegistryǁget_server_for_tool__mutmut_orig(self, tool_name: str) -> str | None:
        """Return the server_key that owns tool_name, or None if unknown."""
        td = self._tools.get(tool_name)
        return td.server_key if td else None

    def xǁToolRegistryǁget_server_for_tool__mutmut_1(self, tool_name: str) -> str | None:
        """Return the server_key that owns tool_name, or None if unknown."""
        td = None
        return td.server_key if td else None

    def xǁToolRegistryǁget_server_for_tool__mutmut_2(self, tool_name: str) -> str | None:
        """Return the server_key that owns tool_name, or None if unknown."""
        td = self._tools.get(None)
        return td.server_key if td else None

    @_mutmut_mutated(mutants_xǁToolRegistryǁget_tool_names__mutmut)
    def get_tool_names(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get(server_key, []))

    def xǁToolRegistryǁget_tool_names__mutmut_orig(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get(server_key, []))

    def xǁToolRegistryǁget_tool_names__mutmut_1(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(None)

    def xǁToolRegistryǁget_tool_names__mutmut_2(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get(None, []))

    def xǁToolRegistryǁget_tool_names__mutmut_3(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get(server_key, None))

    def xǁToolRegistryǁget_tool_names__mutmut_4(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get([]))

    def xǁToolRegistryǁget_tool_names__mutmut_5(self, server_key: str) -> list[str]:
        """Return all tool names for a server_key, sorted alphabetically.

        Ordering is a guaranteed contract of this method (not just an artifact of
        default registration order) — callers and tests may rely on it directly
        without re-sorting.
        """
        return sorted(self._by_server.get(server_key, ))

    @_mutmut_mutated(mutants_xǁToolRegistryǁget_all_tool_names__mutmut)
    def get_all_tool_names(self) -> frozenset[str]:
        """Return all registered tool names."""
        return frozenset(self._tools.keys())

    def xǁToolRegistryǁget_all_tool_names__mutmut_orig(self) -> frozenset[str]:
        """Return all registered tool names."""
        return frozenset(self._tools.keys())

    def xǁToolRegistryǁget_all_tool_names__mutmut_1(self) -> frozenset[str]:
        """Return all registered tool names."""
        return frozenset(None)

    @_mutmut_mutated(mutants_xǁToolRegistryǁget_servers__mutmut)
    def get_servers(self) -> list[str]:
        """Return all server keys in the registry."""
        return sorted(self._by_server.keys())

    def xǁToolRegistryǁget_servers__mutmut_orig(self) -> list[str]:
        """Return all server keys in the registry."""
        return sorted(self._by_server.keys())

    def xǁToolRegistryǁget_servers__mutmut_1(self) -> list[str]:
        """Return all server keys in the registry."""
        return sorted(None)

    @_mutmut_mutated(mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut)
    def validate_tool_names_match(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_orig(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_1(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = None
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_2(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(None)
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_3(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(None))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_4(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = None

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_5(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(None)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_6(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = None
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_7(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            None
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_8(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(None, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_9(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, None, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_10(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, None, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_11(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, None, "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_12(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", None)
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_13(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_14(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_15(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_16(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_17(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", )
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_18(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "XXconfigXX", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_19(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "CONFIG", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_20(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "XXregistryXX")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_21(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "REGISTRY")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_22(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            None
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_23(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(None, config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_24(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, None, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_25(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, None, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_26(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, None, "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_27(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", None)
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_28(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(config_set, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_29(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, server_key, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_30(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, "registry", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_31(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_32(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", )
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_33(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "XXregistryXX", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_34(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "REGISTRY", "config")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_35(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "XXconfigXX")
        )
        return mismatches

    def xǁToolRegistryǁvalidate_tool_names_match__mutmut_36(
        self,
        server_key: str,
        config_tool_names: list[str],
    ) -> list[str]:
        """Validate config tool_names against registry. Returns list of mismatches."""
        registry_tools = set(self.get_tool_names(server_key))
        config_set = set(config_tool_names)

        mismatches: list[str] = []
        mismatches.extend(
            _diff_messages(config_set, registry_tools, server_key, "config", "registry")
        )
        mismatches.extend(
            _diff_messages(registry_tools, config_set, server_key, "registry", "CONFIG")
        )
        return mismatches

    @_mutmut_mutated(mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut)
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_orig(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_1(
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
        registry_tools = None
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_2(
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
        registry_tools = set(None)
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_3(
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
        registry_tools = set(self.get_tool_names(None))
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_4(
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
        live_set = None

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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_5(
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
        live_set = set(None)

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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_6(
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

        mismatches: list[str] = None
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_7(
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
        in_live_not_registry = None
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_8(
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
        in_live_not_registry = live_set + registry_tools
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_9(
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
            for t in sorted(None):
                owner = self.get_server_for_tool(t)
                if owner is None:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is unknown (not registered to any server)"
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_10(
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
                owner = None
                if owner is None:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is unknown (not registered to any server)"
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_11(
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
                owner = self.get_server_for_tool(None)
                if owner is None:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is unknown (not registered to any server)"
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_12(
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
                if owner is not None:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is unknown (not registered to any server)"
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_13(
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
                        None
                    )
                else:
                    mismatches.append(
                        f"[{server_key}] tool {t!r} is registered to server '{owner}', not '{server_key}'"
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_14(
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
                        None
                    )

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_15(
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

        mismatches.extend(
            None
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_16(
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

        mismatches.extend(
            _diff_messages(
                None, live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_17(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, None, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_18(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, None, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_19(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, None, "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_20(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", None
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_21(
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

        mismatches.extend(
            _diff_messages(
                live_set, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_22(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, server_key, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_23(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, "registry", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_24(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_25(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_26(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "XXregistryXX", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_27(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "REGISTRY", "live response"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_28(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "XXlive responseXX"
            )
        )

        return mismatches

    def xǁToolRegistryǁvalidate_live_tools_match__mutmut_29(
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

        mismatches.extend(
            _diff_messages(
                registry_tools, live_set, server_key, "registry", "LIVE RESPONSE"
            )
        )

        return mismatches

mutants_xǁToolRegistryǁ__init____mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁ__init____mutmut['xǁToolRegistryǁ__init____mutmut_1'] = ToolRegistry.xǁToolRegistryǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁ__init____mutmut['xǁToolRegistryǁ__init____mutmut_2'] = ToolRegistry.xǁToolRegistryǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁregister__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_1'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_2'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_3'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_4'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_5'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_6'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_7'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_8'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁregister__mutmut['xǁToolRegistryǁregister__mutmut_9'] = ToolRegistry.xǁToolRegistryǁregister__mutmut_9 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁget_server_for_tool__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁget_server_for_tool__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_server_for_tool__mutmut['xǁToolRegistryǁget_server_for_tool__mutmut_1'] = ToolRegistry.xǁToolRegistryǁget_server_for_tool__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_server_for_tool__mutmut['xǁToolRegistryǁget_server_for_tool__mutmut_2'] = ToolRegistry.xǁToolRegistryǁget_server_for_tool__mutmut_2 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁget_tool_names__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_tool_names__mutmut['xǁToolRegistryǁget_tool_names__mutmut_1'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_tool_names__mutmut['xǁToolRegistryǁget_tool_names__mutmut_2'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_tool_names__mutmut['xǁToolRegistryǁget_tool_names__mutmut_3'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_tool_names__mutmut['xǁToolRegistryǁget_tool_names__mutmut_4'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_tool_names__mutmut['xǁToolRegistryǁget_tool_names__mutmut_5'] = ToolRegistry.xǁToolRegistryǁget_tool_names__mutmut_5 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁget_all_tool_names__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁget_all_tool_names__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_all_tool_names__mutmut['xǁToolRegistryǁget_all_tool_names__mutmut_1'] = ToolRegistry.xǁToolRegistryǁget_all_tool_names__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁget_servers__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁget_servers__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁget_servers__mutmut['xǁToolRegistryǁget_servers__mutmut_1'] = ToolRegistry.xǁToolRegistryǁget_servers__mutmut_1 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_1'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_2'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_3'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_4'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_5'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_6'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_7'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_8'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_9'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_10'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_11'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_12'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_13'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_14'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_15'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_16'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_17'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_18'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_19'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_20'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_21'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_22'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_23'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_24'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_25'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_26'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_27'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_28'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_29'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_29 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_30'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_30 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_31'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_31 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_32'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_32 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_33'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_33 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_34'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_34 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_35'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_35 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_tool_names_match__mutmut['xǁToolRegistryǁvalidate_tool_names_match__mutmut_36'] = ToolRegistry.xǁToolRegistryǁvalidate_tool_names_match__mutmut_36 # type: ignore # mutmut generated

mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['_mutmut_orig'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_orig # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_1'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_1 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_2'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_2 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_3'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_3 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_4'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_4 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_5'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_5 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_6'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_6 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_7'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_7 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_8'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_8 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_9'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_9 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_10'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_10 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_11'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_11 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_12'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_12 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_13'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_13 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_14'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_14 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_15'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_15 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_16'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_16 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_17'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_17 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_18'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_18 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_19'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_19 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_20'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_20 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_21'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_21 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_22'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_22 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_23'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_23 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_24'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_24 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_25'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_25 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_26'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_26 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_27'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_27 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_28'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_28 # type: ignore # mutmut generated
mutants_xǁToolRegistryǁvalidate_live_tools_match__mutmut['xǁToolRegistryǁvalidate_live_tools_match__mutmut_29'] = ToolRegistry.xǁToolRegistryǁvalidate_live_tools_match__mutmut_29 # type: ignore # mutmut generated


# Global singleton registry.
_registry: ToolRegistry | None = None
mutants_x_get_registry__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_registry__mutmut)
def get_registry() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _populate_default_registry(_registry)
    return _registry


def x_get_registry__mutmut_orig() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _populate_default_registry(_registry)
    return _registry


def x_get_registry__mutmut_1() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is not None:
        _registry = ToolRegistry()
        _populate_default_registry(_registry)
    return _registry


def x_get_registry__mutmut_2() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is None:
        _registry = None
        _populate_default_registry(_registry)
    return _registry


def x_get_registry__mutmut_3() -> ToolRegistry:
    """Return the global ToolRegistry singleton, initializing it if needed."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _populate_default_registry(None)
    return _registry

mutants_x_get_registry__mutmut['_mutmut_orig'] = x_get_registry__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_registry__mutmut['x_get_registry__mutmut_1'] = x_get_registry__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_registry__mutmut['x_get_registry__mutmut_2'] = x_get_registry__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_registry__mutmut['x_get_registry__mutmut_3'] = x_get_registry__mutmut_3 # type: ignore # mutmut generated
mutants_x__reset_registry_for_testing__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__reset_registry_for_testing__mutmut)
def _reset_registry_for_testing() -> None:
    """Reset the global ToolRegistry singleton. FOR TESTING ONLY."""
    global _registry
    _registry = None


def x__reset_registry_for_testing__mutmut_orig() -> None:
    """Reset the global ToolRegistry singleton. FOR TESTING ONLY."""
    global _registry
    _registry = None


def x__reset_registry_for_testing__mutmut_1() -> None:
    """Reset the global ToolRegistry singleton. FOR TESTING ONLY."""
    global _registry
    _registry = ""

mutants_x__reset_registry_for_testing__mutmut['_mutmut_orig'] = x__reset_registry_for_testing__mutmut_orig # type: ignore # mutmut generated
mutants_x__reset_registry_for_testing__mutmut['x__reset_registry_for_testing__mutmut_1'] = x__reset_registry_for_testing__mutmut_1 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__populate_default_registry__mutmut)
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_orig(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_1(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = None
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_2(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "XXfile_readXX"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_3(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "FILE_READ"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_4(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "XXfile_writeXX"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_5(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "FILE_WRITE"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_6(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "XXfile_deleteXX"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_7(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "FILE_DELETE"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_8(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "XXrag_pipelineXX"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_9(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "RAG_PIPELINE"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_10(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "XXcicdXX"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_11(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "CICD"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_12(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "XXmdqXX"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_13(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "MDQ"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_14(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "XXgitXX"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_15(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "GIT"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_16(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "XXshellXX"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_17(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "SHELL"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_18(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "XXgithubXX"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_19(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "GITHUB"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_20(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "XXweb_searchXX"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_21(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "WEB_SEARCH"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, server_key)


def x__populate_default_registry__mutmut_22(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(None, tool_names, server_key)


def x__populate_default_registry__mutmut_23(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, None, server_key)


def x__populate_default_registry__mutmut_24(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, None)


def x__populate_default_registry__mutmut_25(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(tool_names, server_key)


def x__populate_default_registry__mutmut_26(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, server_key)


def x__populate_default_registry__mutmut_27(registry: ToolRegistry) -> None:
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

    # Register each tool set with its server key, in the same order as before.
    tool_sets_by_server: tuple[tuple[frozenset[str], str], ...] = (
        (READ_TOOLS, "file_read"),
        (WRITE_TOOLS, "file_write"),
        (DELETE_TOOLS, "file_delete"),
        (RAG_TOOLS, "rag_pipeline"),
        (CICD_TOOLS, "cicd"),
        (MDQ_TOOLS, "mdq"),
        (GIT_TOOLS, "git"),
        (SHELL_TOOLS, "shell"),
        (GITHUB_TOOLS, "github"),
        (WEB_SEARCH_TOOLS, "web_search"),
    )
    for tool_names, server_key in tool_sets_by_server:
        _register_set(registry, tool_names, )

mutants_x__populate_default_registry__mutmut['_mutmut_orig'] = x__populate_default_registry__mutmut_orig # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_1'] = x__populate_default_registry__mutmut_1 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_2'] = x__populate_default_registry__mutmut_2 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_3'] = x__populate_default_registry__mutmut_3 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_4'] = x__populate_default_registry__mutmut_4 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_5'] = x__populate_default_registry__mutmut_5 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_6'] = x__populate_default_registry__mutmut_6 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_7'] = x__populate_default_registry__mutmut_7 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_8'] = x__populate_default_registry__mutmut_8 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_9'] = x__populate_default_registry__mutmut_9 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_10'] = x__populate_default_registry__mutmut_10 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_11'] = x__populate_default_registry__mutmut_11 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_12'] = x__populate_default_registry__mutmut_12 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_13'] = x__populate_default_registry__mutmut_13 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_14'] = x__populate_default_registry__mutmut_14 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_15'] = x__populate_default_registry__mutmut_15 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_16'] = x__populate_default_registry__mutmut_16 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_17'] = x__populate_default_registry__mutmut_17 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_18'] = x__populate_default_registry__mutmut_18 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_19'] = x__populate_default_registry__mutmut_19 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_20'] = x__populate_default_registry__mutmut_20 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_21'] = x__populate_default_registry__mutmut_21 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_22'] = x__populate_default_registry__mutmut_22 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_23'] = x__populate_default_registry__mutmut_23 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_24'] = x__populate_default_registry__mutmut_24 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_25'] = x__populate_default_registry__mutmut_25 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_26'] = x__populate_default_registry__mutmut_26 # type: ignore # mutmut generated
mutants_x__populate_default_registry__mutmut['x__populate_default_registry__mutmut_27'] = x__populate_default_registry__mutmut_27 # type: ignore # mutmut generated
mutants_x__register_set__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__register_set__mutmut)
def _register_set(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, server_key=server_key))


def x__register_set__mutmut_orig(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, server_key=server_key))


def x__register_set__mutmut_1(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(None):
        registry.register(ToolDefinition(name=name, server_key=server_key))


def x__register_set__mutmut_2(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(None)


def x__register_set__mutmut_3(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=None, server_key=server_key))


def x__register_set__mutmut_4(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, server_key=None))


def x__register_set__mutmut_5(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(server_key=server_key))


def x__register_set__mutmut_6(
    registry: ToolRegistry, tool_names: frozenset[str], server_key: str
) -> None:
    """Register a set of tools with a server key."""
    for name in sorted(tool_names):
        registry.register(ToolDefinition(name=name, ))

mutants_x__register_set__mutmut['_mutmut_orig'] = x__register_set__mutmut_orig # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_1'] = x__register_set__mutmut_1 # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_2'] = x__register_set__mutmut_2 # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_3'] = x__register_set__mutmut_3 # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_4'] = x__register_set__mutmut_4 # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_5'] = x__register_set__mutmut_5 # type: ignore # mutmut generated
mutants_x__register_set__mutmut['x__register_set__mutmut_6'] = x__register_set__mutmut_6 # type: ignore # mutmut generated
