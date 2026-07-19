#!/usr/bin/env python3
"""shared/runtime_tool_registry.py

In-memory registry of `RuntimeTool` instances.

This module is additive and unused until a later implementation step (MCP
discovery) populates it, and until subsequent steps wire existing call sites
(`route_resolver.py`, `tool_executor_helpers.py`, `tool_policy.py`,
`tool_runner.py`) to actually consult it. `shared.tool_registry.ToolRegistry`
remains the sole routing authority for now, per that module's own docstring.

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
from typing import Literal

from shared.runtime_tool import AgentSafetyTier, RuntimeTool
from shared.tool_spec import ToolSpec


class RuntimeToolRegistry:
    """In-memory `{name: RuntimeTool}` registry.

    Plain mutable class wrapping a `dict[str, RuntimeTool]`. No `Protocol`/`ABC`
    — single concrete implementation, no polymorphism need identified yet.
    """

    def __init__(self, tools: dict[str, RuntimeTool] | None = None) -> None:
        self._tools: dict[str, RuntimeTool] = dict(tools) if tools else {}

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

    def llm_tool_definitions(self) -> list[dict[str, object]]:
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

    def tool_spec_map(self) -> dict[str, ToolSpec]:
        """Return a `{name: ToolSpec}` map built from all registered tools.

        Each `ToolSpec` is built with an empty `call_id`/`args` — this method
        is for shape/config inspection, not for representing an actual call.
        """
        return {
            name: ToolSpec(
                call_id="",
                name=name,
                resource_scope=tool.resource_scope,
                requires_serial=tool.requires_serial,
                is_write=tool.is_write,
            )
            for name, tool in self._tools.items()
        }

    def tool_spec_for_call(
        self, call_id: str, name: str, args: dict[str, object]
    ) -> ToolSpec:
        """Return a `ToolSpec` representing an actual tool call.

        Raises `KeyError` (via `get()`) if `name` has no registry entry.
        """
        tool = self.get(name)
        return ToolSpec(
            call_id=call_id,
            name=name,
            args=args,
            resource_scope=tool.resource_scope,
            requires_serial=tool.requires_serial,
            is_write=tool.is_write,
        )

    def is_side_effect(self, tool_name: str) -> bool:
        """Return whether `tool_name` has write/delete side effects.

        Raises `KeyError` (via `get()`) if `tool_name` has no registry entry.
        """
        return self.get(tool_name).is_write

    def classify_operation_type(self, tool_name: str) -> Literal["read", "write"]:
        """Return a coarse read/write classification for `tool_name`.

        NOTE: cannot distinguish DELETE/EXECUTE/API_WRITE from `RuntimeTool`'s
        fields alone — see module docstring.
        """
        return "write" if self.get(tool_name).is_write else "read"

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

    def diagnostics(self) -> list[dict[str, object]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.
        """
        rows: list[dict[str, object]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.status != "active"
            disabled_reason = "" if tool.status == "active" else tool.status
            rows.append(
                {
                    "name": tool.name,
                    "server_key": tool.server_key,
                    "config_dependent": config_dep,
                    "enabled": True,
                    "disabled_reason": disabled_reason,
                    "enabled_for_llm": tool.enabled_for_llm,
                }
            )
        return rows
