#!/usr/bin/env python3
"""scripts/shared/runtime_tool_registry.py

In-memory registry of `RuntimeTool` instances, populated by
`McpToolDiscoveryService.discover_all()` at startup and wired into
`ToolRouteResolver` via `ToolExecutor.set_runtime_registry()`.
`shared.route_resolver.ToolRouteResolver.resolve()` consults this registry as
the sole routing authority — no fallback to `shared.tool_registry.ToolRegistry`
exists.

Import-layer design decisions (do not "fix" these by adding the imports back):
  - `classify_operation_type()` returns a plain `Literal["read", "write"]`
    string, not `agent.tool_enums.OperationType`. `OperationType` lives in the
    agent layer, and per `.importlinter`'s `shared-is-leaf` contract this
    module must not import from `agent`. A `RuntimeTool` only carries a single
    `is_write: bool` field today, so `DELETE`/`API_WRITE`/`EXECUTE` granularity
    cannot be derived here — that is a documented gap, not silently collapsed.
    Any agent-layer caller wanting a real `OperationType` member wraps the
    returned string itself (`OperationType(result)`).
  - `apply_policy()` takes plain, duck-typed primitives (`tier_map`,
    `allowed_tools`) instead of `agent.config_dataclasses.ToolConfig` /
    `ApprovalConfig`, for the same `shared-is-leaf` reason. Whichever later
    requirement wires this to real config is responsible for extracting these
    primitives from `ToolConfig`/`agent.toml` and passing them in.

`is_side_effect()` intentionally duplicates (does not replace)
`shared.tool_executor_helpers.is_side_effect()`'s frozenset-based contract,
sourcing its answer from the registered `RuntimeTool.is_write` field instead.
Both live in `shared/`, so there is no layer-contract concern; this is
temporary, parallel duplication pending a future unification decision.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from shared.resource_scope import resolve_resource_scopes
from shared.runtime_tool import AgentSafetyTier, RuntimeTool
from shared.tool_spec import ToolSpec


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁRuntimeToolRegistryǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁresolve__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁget__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁall_tools__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁis_side_effect__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut: MutantDict = {}  # type: ignore


class RuntimeToolRegistry:
    """In-memory `{name: RuntimeTool}` registry.

    Plain mutable class wrapping a `dict[str, RuntimeTool]`. No `Protocol`/`ABC`
    — single concrete implementation, no polymorphism need identified yet.
    """

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁ__init____mutmut)
    def __init__(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_orig(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_1(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = None
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_2(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers and frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_3(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = None
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_4(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers and frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_5(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = None
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_6(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(None):
                    continue
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_7(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    break
                self._tools[name] = tool

    def xǁRuntimeToolRegistryǁ__init____mutmut_8(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        degraded_servers: frozenset[str] | None = None,
    ) -> None:
        self._unavailable_servers = unavailable_servers or frozenset()
        self._degraded_servers = degraded_servers or frozenset()
        self._tools: dict[str, RuntimeTool] = {}
        if tools:
            for name, tool in tools.items():
                if self._is_excluded_server(tool.server_key):
                    continue
                self._tools[name] = None

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut)
    def _is_excluded_server(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key in self._unavailable_servers
            or server_key in self._degraded_servers
        )

    def xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_orig(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key in self._unavailable_servers
            or server_key in self._degraded_servers
        )

    def xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_1(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key in self._unavailable_servers and server_key in self._degraded_servers
        )

    def xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_2(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key not in self._unavailable_servers
            or server_key in self._degraded_servers
        )

    def xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_3(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key in self._unavailable_servers
            or server_key not in self._degraded_servers
        )

    @property
    def unavailable_servers(self) -> frozenset[str]:
        """Return the set of server keys excluded due to being unavailable."""
        return self._unavailable_servers

    @property
    def degraded_servers(self) -> frozenset[str]:
        """Return the set of server keys excluded due to being degraded."""
        return self._degraded_servers

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁresolve__mutmut)
    def resolve(self, tool_name: str) -> str | None:
        """Return the `server_key` that owns `tool_name`, or `None` if unknown.

        Mirrors `shared.tool_registry.ToolRegistry.get_server_for_tool()`'s
        unknown-name handling: unregistered names return `None` rather than
        raising.
        """
        entry = self._tools.get(tool_name)
        return entry.server_key if entry else None

    def xǁRuntimeToolRegistryǁresolve__mutmut_orig(self, tool_name: str) -> str | None:
        """Return the `server_key` that owns `tool_name`, or `None` if unknown.

        Mirrors `shared.tool_registry.ToolRegistry.get_server_for_tool()`'s
        unknown-name handling: unregistered names return `None` rather than
        raising.
        """
        entry = self._tools.get(tool_name)
        return entry.server_key if entry else None

    def xǁRuntimeToolRegistryǁresolve__mutmut_1(self, tool_name: str) -> str | None:
        """Return the `server_key` that owns `tool_name`, or `None` if unknown.

        Mirrors `shared.tool_registry.ToolRegistry.get_server_for_tool()`'s
        unknown-name handling: unregistered names return `None` rather than
        raising.
        """
        entry = None
        return entry.server_key if entry else None

    def xǁRuntimeToolRegistryǁresolve__mutmut_2(self, tool_name: str) -> str | None:
        """Return the `server_key` that owns `tool_name`, or `None` if unknown.

        Mirrors `shared.tool_registry.ToolRegistry.get_server_for_tool()`'s
        unknown-name handling: unregistered names return `None` rather than
        raising.
        """
        entry = self._tools.get(None)
        return entry.server_key if entry else None

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁget__mutmut)
    def get(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = self._tools.get(tool_name)
        if entry is None:
            raise KeyError(f"unregistered tool: {tool_name}")
        return entry

    def xǁRuntimeToolRegistryǁget__mutmut_orig(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = self._tools.get(tool_name)
        if entry is None:
            raise KeyError(f"unregistered tool: {tool_name}")
        return entry

    def xǁRuntimeToolRegistryǁget__mutmut_1(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = None
        if entry is None:
            raise KeyError(f"unregistered tool: {tool_name}")
        return entry

    def xǁRuntimeToolRegistryǁget__mutmut_2(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = self._tools.get(None)
        if entry is None:
            raise KeyError(f"unregistered tool: {tool_name}")
        return entry

    def xǁRuntimeToolRegistryǁget__mutmut_3(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = self._tools.get(tool_name)
        if entry is not None:
            raise KeyError(f"unregistered tool: {tool_name}")
        return entry

    def xǁRuntimeToolRegistryǁget__mutmut_4(self, tool_name: str) -> RuntimeTool:
        """Return the registered `RuntimeTool` for `tool_name`.

        Raises `KeyError` if `tool_name` has no registry entry at all —
        distinct from "registered-but-under-annotated", where safe defaults
        already apply at construction time and no raise occurs.
        """
        entry = self._tools.get(tool_name)
        if entry is None:
            raise KeyError(None)
        return entry

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁall_tools__mutmut)
    def all_tools(self) -> list[RuntimeTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def xǁRuntimeToolRegistryǁall_tools__mutmut_orig(self) -> list[RuntimeTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def xǁRuntimeToolRegistryǁall_tools__mutmut_1(self) -> list[RuntimeTool]:
        """Return all registered tools."""
        return list(None)

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut)
    def llm_tool_definitions(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_orig(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_1(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "XXnameXX": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_2(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "NAME": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_3(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "XXdescriptionXX": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_4(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "DESCRIPTION": tool.description,
                "parameters": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_5(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "XXparametersXX": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    def xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_6(self) -> list[dict[str, Any]]:
        """Return LLM-facing tool definitions for tools enabled for LLM use.

        Re-keys `RuntimeTool.input_schema` to `parameters` to match the shape
        LLM clients expect (`{"name", "description", "parameters"}`).
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "PARAMETERS": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.enabled_for_llm
        ]

    @staticmethod
    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut)
    def _build_tool_spec(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_orig(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_1(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=None,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_2(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=None,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_3(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=None,
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_4(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=None,
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_5(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=None,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_6(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=None,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_7(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_8(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_9(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_10(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_11(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_12(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_13(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args and {},
            resource_scopes=resolve_resource_scopes(tool, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_14(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(None, args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_15(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, None),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_16(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(args or {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_17(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, ),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @staticmethod
    def xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_18(
        call_id: str,
        name: str,
        tool: RuntimeTool,
        args: dict[str, Any] | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec from a RuntimeTool, resolving its resource scopes against
        *args* via resolve_resource_scopes()."""
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args or {},
            resource_scopes=resolve_resource_scopes(tool, args and {}),
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut)
    def tool_spec_map(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", name, tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_orig(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", name, tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_1(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec(None, name, tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_2(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", None, tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_3(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", name, None)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_4(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec(name, tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_5(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", tool)
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_6(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", name, )
            for name, tool in self._tools.items()
        }

    def xǁRuntimeToolRegistryǁtool_spec_map__mutmut_7(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("XXXX", name, tool)
            for name, tool in self._tools.items()
        }

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut)
    def tool_spec_for_call(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_orig(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_1(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = None
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_2(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(None)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_3(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(None, name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_4(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, None, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_5(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, None, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_6(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, None)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_7(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(name, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_8(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, tool, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_9(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, args)

    def xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_10(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, )

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁis_side_effect__mutmut)
    def is_side_effect(self, tool_name: str) -> bool:
        """Return whether `tool_name` has write/delete side effects.

        Raises `KeyError` (via `get()`) if `tool_name` has no registry entry.
        """
        return self.get(tool_name).is_write

    def xǁRuntimeToolRegistryǁis_side_effect__mutmut_orig(self, tool_name: str) -> bool:
        """Return whether `tool_name` has write/delete side effects.

        Raises `KeyError` (via `get()`) if `tool_name` has no registry entry.
        """
        return self.get(tool_name).is_write

    def xǁRuntimeToolRegistryǁis_side_effect__mutmut_1(self, tool_name: str) -> bool:
        """Return whether `tool_name` has write/delete side effects.

        Raises `KeyError` (via `get()`) if `tool_name` has no registry entry.
        """
        return self.get(None).is_write

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut)
    def classify_operation_type(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(tool_name).is_write else "read"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_orig(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(tool_name).is_write else "read"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_1(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "XXwriteXX" if self.get(tool_name).is_write else "read"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_2(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "WRITE" if self.get(tool_name).is_write else "read"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_3(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(None).is_write else "read"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_4(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(tool_name).is_write else "XXreadXX"

    def xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_5(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(tool_name).is_write else "READ"

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut)
    def apply_policy(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_orig(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_1(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(None):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_2(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = None
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_3(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(None, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_4(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, None)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_5(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_6(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, )
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_7(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = None
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_8(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) and (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_9(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = allowed_tools or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_10(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name not in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_11(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = None
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_12(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier not in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_13(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("XXWRITE_DANGEROUSXX", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_14(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("write_dangerous", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_15(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "XXADMINXX")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_16(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "admin")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_17(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = None

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_18(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                None,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_19(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=None,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_20(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=None,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_21(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=None,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_22(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_23(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                requires_approval=requires_approval,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_24(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                enabled_for_llm=enabled and tool.enabled_for_llm,
            )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_25(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                )

    def xǁRuntimeToolRegistryǁapply_policy__mutmut_26(
        self,
        tier_map: Mapping[str, AgentSafetyTier],
        allowed_tools: Sequence[str] = (),
    ) -> None:
        """Apply a tier/allowlist policy to all registered tools, in place.

        `tier_map` maps tool name to `AgentSafetyTier`; tools absent from
        `tier_map` keep their current tier. `allowed_tools` is an allowlist of
        tool names; an empty sequence means all tools remain allowed (mirrors
        `agent.config_dataclasses.ToolConfig.allowed_tools`'s own documented
        convention).

        The `requires_approval`/`enabled_for_llm` re-derivation rule below is
        a reasonable default (dangerous/admin tiers require approval) but is
        explicitly provisional — a later requirement's `/reload` consumer may
        refine it.
        """
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            enabled = (not allowed_tools) or (name in allowed_tools)
            requires_approval = tier in ("WRITE_DANGEROUS", "ADMIN")
            self._tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                requires_approval=requires_approval,
                enabled_for_llm=enabled or tool.enabled_for_llm,
            )

    @_mutmut_mutated(mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut)
    def diagnostics(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_orig(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_1(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = None
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_2(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(None, key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_3(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=None):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_4(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_5(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), ):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_6(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: None):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_7(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = None
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_8(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status == "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_9(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "XXactiveXX"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_10(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "ACTIVE"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_11(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = None
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_12(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get(None)
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_13(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("XXdisabled_reasonXX")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_14(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("DISABLED_REASON")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_15(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = None
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_16(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(None)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_17(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) or raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_18(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("XXXX" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_19(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status != "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_20(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "XXactiveXX" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_21(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "ACTIVE" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_22(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                None
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_23(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "XXnameXX": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_24(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "NAME": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_25(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "XXserver_keyXX": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_26(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "SERVER_KEY": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_27(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "XXconfig_dependentXX": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_28(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "CONFIG_DEPENDENT": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_29(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "XXenabledXX": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_30(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "ENABLED": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_31(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": disabled_reason,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_32(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "XXdisabled_reasonXX": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_33(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "DISABLED_REASON": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_34(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "XXenabled_for_llmXX": tool.enabled_for_llm,
                }
            )
        return rows

    def xǁRuntimeToolRegistryǁdiagnostics__mutmut_35(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            raw_reason = tool.raw_definition.get("disabled_reason")
            disabled_reason = (
                str(raw_reason)
                if isinstance(raw_reason, str) and raw_reason
                else ("" if tool.status == "active" else tool.status)
            )
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": not disabled_reason,
                    "disabled_reason": disabled_reason,
                    "ENABLED_FOR_LLM": tool.enabled_for_llm,
                }
            )
        return rows

mutants_xǁRuntimeToolRegistryǁ__init____mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ__init____mutmut['xǁRuntimeToolRegistryǁ__init____mutmut_8'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ__init____mutmut_8 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut['xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut['xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut['xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_is_excluded_server__mutmut_3 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁresolve__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁresolve__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁresolve__mutmut['xǁRuntimeToolRegistryǁresolve__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁresolve__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁresolve__mutmut['xǁRuntimeToolRegistryǁresolve__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁresolve__mutmut_2 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁget__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁget__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁget__mutmut['xǁRuntimeToolRegistryǁget__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁget__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁget__mutmut['xǁRuntimeToolRegistryǁget__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁget__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁget__mutmut['xǁRuntimeToolRegistryǁget__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁget__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁget__mutmut['xǁRuntimeToolRegistryǁget__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁget__mutmut_4 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁall_tools__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁall_tools__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁall_tools__mutmut['xǁRuntimeToolRegistryǁall_tools__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁall_tools__mutmut_1 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut['xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁllm_tool_definitions__mutmut_6 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_8'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_9'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_10'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_11'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_12'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_13'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_14'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_15'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_16'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_17'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut['xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_18'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁ_build_tool_spec__mutmut_18 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_map__mutmut['xǁRuntimeToolRegistryǁtool_spec_map__mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_map__mutmut_7 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_8'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_9'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut['xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_10'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁtool_spec_for_call__mutmut_10 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁis_side_effect__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁis_side_effect__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁis_side_effect__mutmut['xǁRuntimeToolRegistryǁis_side_effect__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁis_side_effect__mutmut_1 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁclassify_operation_type__mutmut['xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁclassify_operation_type__mutmut_5 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_8'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_9'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_10'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_11'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_12'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_13'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_14'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_15'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_16'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_17'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_18'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_19'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_20'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_21'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_22'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_23'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_24'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_25'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁapply_policy__mutmut['xǁRuntimeToolRegistryǁapply_policy__mutmut_26'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁapply_policy__mutmut_26 # type: ignore # mutmut generated

mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['_mutmut_orig'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_1'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_2'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_3'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_4'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_5'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_6'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_7'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_8'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_9'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_10'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_11'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_12'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_13'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_14'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_15'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_16'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_17'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_18'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_19'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_20'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_21'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_22'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_23'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_24'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_25'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_26'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_27'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_28'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_29'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_30'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_31'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_32'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_33'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_34'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRuntimeToolRegistryǁdiagnostics__mutmut['xǁRuntimeToolRegistryǁdiagnostics__mutmut_35'] = RuntimeToolRegistry.xǁRuntimeToolRegistryǁdiagnostics__mutmut_35 # type: ignore # mutmut generated
