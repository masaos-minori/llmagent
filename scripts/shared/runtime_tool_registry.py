#!/usr/bin/env python3
"""scripts/shared/runtime_tool_registry.py

In-memory registry of `RuntimeTool` instances, populated by
`McpToolDiscoveryService.discover_all()` at startup and wired into
`ToolRouteResolver` via `ToolExecutor.set_runtime_registry()`.
`shared.route_resolver.ToolRouteResolver.resolve()` consults this registry as
the sole routing authority — no fallback to `shared.tool_registry.ToolRegistry`
exists.

Import-layer design decisions (do not "fix" these by adding the imports back):
  - `apply_policy()` takes plain, duck-typed primitives (`tier_map`,
    `allowed_tools`) instead of `agent.config_dataclasses.ToolConfig` /
    `ApprovalConfig`, for the same `shared-is-leaf` reason. Whichever later
    requirement wires this to real config is responsible for extracting these
    primitives from `ToolConfig`/`agent.toml` and passing them in.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

from shared.resource_scope import resolve_resource_scopes
from shared.runtime_tool import AgentSafetyTier, RuntimeTool
from shared.tool_spec import ToolSpec


class RuntimeToolRegistry:
    """In-memory `{name: RuntimeTool}` registry.

    Plain mutable class wrapping a `dict[str, RuntimeTool]`. No `Protocol`/`ABC`
    — single concrete implementation, no polymorphism need identified yet.
    """

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

    def _is_excluded_server(self, server_key: str) -> bool:
        """Return whether tools from `server_key` should be excluded.

        A server is excluded if it is unavailable, or degraded (conservative
        default: exclude degraded server tools too).
        """
        return (
            server_key in self._unavailable_servers
            or server_key in self._degraded_servers
        )

    @property
    def unavailable_servers(self) -> frozenset[str]:
        """Return the set of server keys excluded due to being unavailable."""
        return self._unavailable_servers

    @property
    def degraded_servers(self) -> frozenset[str]:
        """Return the set of server keys excluded due to being degraded."""
        return self._degraded_servers

    def resolve(self, tool_name: str) -> str | None:
        """Return the `server_key` that owns `tool_name`, or `None` if unknown.

        Mirrors `shared.tool_registry.ToolRegistry.get_server_for_tool()`'s
        unknown-name handling: unregistered names return `None` rather than
        raising.
        """
        entry = self._tools.get(tool_name)
        return entry.server_key if entry else None

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

    def all_tools(self) -> list[RuntimeTool]:
        """Return all registered tools."""
        return list(self._tools.values())

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

    @staticmethod
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

    def tool_spec_map(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: RuntimeToolRegistry._build_tool_spec("", name, tool)
            for name, tool in self._tools.items()
        }

    def tool_spec_for_call(
        self, call_id: str, name: str, args: dict[str, Any]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)

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
