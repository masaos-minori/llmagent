#!/usr/bin/env python3
"""scripts/shared/runtime_tool_registry.py

In-memory registry of `RuntimeTool` instances, populated by
`McpToolDiscoveryService.discover_all()` at startup and wired into
`ToolRouteResolver` via `ToolExecutor.set_runtime_registry()`.
`shared.route_resolver.ToolRouteResolver.resolve()` consults this registry as
the sole routing authority — no fallback to `shared.tool_registry.ToolRegistry`
exists.

Import-layer design decisions (do not "fix" these by adding the imports back):
  - `apply_policy()` takes plain, duck-typed primitives (`allowed_tools`) instead of
    `agent.config_dataclasses.ToolConfig` / `ApprovalConfig`, for the same
    `shared-is-leaf` reason. Whichever later requirement wires this to real config
    is responsible for extracting these primitives from `ToolConfig`/`agent.toml`
    and passing them in. The safety tier is never a policy input here: each entry
    carries the tier its producer declared, and `apply_policy()` does not overwrite it.
  - The Security Posture gate arrives as `allowed_servers`, a plain set of server
    keys, for the same `shared-is-leaf` reason: `shared` cannot read the Agent's
    posture DTOs, and `agent.services.mcp_health` already reduces a posture to a
    gate decision before handing the keys here. The degraded-capability map arrives
    the same way, as plain `server_key` to capability-name entries.

Immutability (REQ-008): the registry is immutable after construction apart from
`apply_policy()`, the single rebinding of `self._tools`, so a reader sees either the
complete old mapping or the complete new one, never a mixed state. Because availability is
decided once at construction, a change in tool availability requires a restart; there is no
live swap.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

from shared.config_undo import ServiceSnapshot
from shared.resource_scope import resolve_resource_scopes
from shared.runtime_tool import RuntimeTool, _or_default
from shared.tool_spec import ToolSpec

logger = logging.getLogger(__name__)


class RuntimeToolRegistry:
    """In-memory `{name: RuntimeTool}` registry.

    Plain mutable class wrapping a `dict[str, RuntimeTool]`. No `Protocol`/`ABC`
    — single concrete implementation, no polymorphism need identified yet.

    Immutable after construction apart from `apply_policy()`'s single rebinding
    (REQ-008): every exclusion is decided during construction, so the published
    mapping never changes afterwards except through that one swap.
    """

    def __init__(
        self,
        tools: dict[str, RuntimeTool] | None = None,
        unavailable_servers: frozenset[str] | None = None,
        server_configs: dict[str, Any] | None = None,
        *,
        allowed_servers: frozenset[str],
        degraded_capabilities: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        """Register `tools`, dropping every tool whose server or capability is excluded.

        `allowed_servers` is the Security Posture gate and is mandatory: omitting it (or passing
        `None`) raises `TypeError`. A provided set is authoritative and a `server_key` absent from it
        is excluded, and an empty set registers nothing. It arrives as plain keys because `shared` is a
        leaf and cannot read the Agent's posture DTOs.

        `degraded_capabilities` is the per-server map of capability names reported `degraded` or
        `unavailable`, produced by Tool Discovery. It arrives as plain names for the same
        `shared-is-leaf` reason, and this module only applies it: the decision that a capability is
        degraded is made from the health report upstream. Only the tools that depend on one of these
        capabilities are dropped, with reason `capability` (REQ-006).
        """
        if allowed_servers is None:
            raise TypeError(
                "allowed_servers is mandatory: the Security Posture gate must be "
                "supplied explicitly; pass frozenset() to deny all servers"
            )
        self._unavailable_servers = unavailable_servers or frozenset()
        self._server_configs = server_configs or {}
        self._allowed_servers = allowed_servers
        self._degraded_capabilities = degraded_capabilities or {}
        self._posture_excluded: set[str] = set()
        self._tools: dict[str, RuntimeTool] = {}
        self._excluded_tools: dict[str, str] = {}
        if tools:
            for name, tool in tools.items():
                reason = self._exclusion_reason(tool.server_key)
                if reason is None:
                    reason = self._capability_exclusion_reason(tool)
                if reason is not None:
                    self._excluded_tools[name] = reason
                    continue
                self._tools[name] = tool
        if self._posture_excluded:
            logger.warning(
                "RuntimeToolRegistry: posture-excluded servers: %s",
                ", ".join(sorted(self._posture_excluded)),
            )

    def _exclusion_reason(self, server_key: str) -> str | None:
        """Return why tools from `server_key` are excluded, or `None` if none.

        Returns `"unavailable"` for an unreachable server, `"disabled"` for a
        `startup_mode=none` server, and `"posture"` for a server absent from the
        Security Posture gate. A posture exclusion is recorded here, during
        construction, so the reported set is exactly the set that was dropped.
        """
        if server_key in self._unavailable_servers:
            return "unavailable"
        cfg = self._server_configs.get(server_key)
        if cfg is not None and getattr(cfg, "is_disabled", False):
            return "disabled"
        if server_key not in self._allowed_servers:
            self._posture_excluded.add(server_key)
            return "posture"
        return None

    def _capability_exclusion_reason(self, tool: RuntimeTool) -> str | None:
        """Return `"capability"` when `tool` depends on a degraded capability, else `None`.

        The dependency is the capability the tool's entry declared (`tool.capabilities`). An entry
        that declares none depends on the owning server's catalog capabilities, which reach this
        module as the degraded subset of the map, so such a tool is excluded when its server has a
        degraded capability. Only the dependent tools are dropped (REQ-006): a server with a degraded
        capability that no tool depends on keeps every tool it has.

        The server-level reasons in `_exclusion_reason()` are checked first, so a tool from a
        server already excluded for availability or posture keeps that reason.
        """
        degraded = self._degraded_capabilities.get(tool.server_key)
        if not degraded:
            return None
        if tool.capabilities:
            return (
                "capability"
                if any(cap in degraded for cap in tool.capabilities)
                else None
            )
        return "capability"

    @property
    def unavailable_servers(self) -> frozenset[str]:
        """Return the set of server keys excluded due to being unavailable."""
        return self._unavailable_servers

    @property
    def posture_excluded_servers(self) -> frozenset[str]:
        """Return the server keys excluded by the posture gate, kept separate from availability.

        `` classifies the two causes differently, so a posture exclusion never appears in
        `unavailable_servers` and the "Unreachable servers" report stays truthful.
        """
        return frozenset(self._posture_excluded)

    def exclusion_reason(self, tool_name: str) -> str | None:
        """Return why `tool_name` was dropped at construction, or `None`.

        Returns one of `"unavailable"`, `"disabled"`, `"posture"`, `"capability"` for a tool the
        registry dropped, and `None` for a registered or unknown name. Lets the
        resolver distinguish posture-excluded and unavailable tools from ones
        that were never discovered.
        """
        return self._excluded_tools.get(tool_name)

    def excluded_tools(self) -> Mapping[str, str]:
        """Return the read-only `{name: exclusion reason}` map decided at construction.

        The display path needs the dropped tools listed, and `diagnostics()` has no row for
        them: an excluded tool has no row by design, so its state is only readable here and
        through `exclusion_reason()`. The map is complete at construction and never changes
        afterwards (REQ-008), so this is a read-only view rather than a copy.
        """
        return MappingProxyType(self._excluded_tools)

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
        allowed_tools: Sequence[str],
        tool_policy_mode: str = "explicit_allowlist",
        disabled_tools: Sequence[str] = (),
    ) -> None:
        """Apply an allowlist policy to all registered tools, in place.

        The tier each entry carries is the tier its producer declared; no
        configuration-derived tier is applied here (ADR-003 Decision 9,
        agentcfg003: `agent_safety_tier` is a declared value). `allowed_tools` is
        an allowlist of tool names; an empty sequence means no tool is allowed
        (fail closed, ADR-004: mirrors `tool_policy.check_preflight`).

        `tool_policy_mode` selects the visibility model: `discovered` keeps each
        tool's base visibility minus `disabled_tools`; `explicit_allowlist`
        intersects with `allowed_tools` and fails closed on an empty list.
        `disabled_tools` is a hard denylist applied in both modes.
        """
        new_tools: dict[str, RuntimeTool] = {}
        explicit = tool_policy_mode == "explicit_allowlist"
        for name, tool in list(self._tools.items()):
            resolved_llm_visibility_base = _or_default(tool.llm_visibility_base, True)
            if explicit:
                allowed_alone = name in allowed_tools
            else:  # discovered: base visibility applies to every registered tool
                allowed_alone = True
            if name in disabled_tools:
                allowed_alone = False
            if explicit and not resolved_llm_visibility_base and allowed_alone:
                logger.warning(
                    "tool %r hidden at discovery (llm_visibility_base=False);"
                    " reload's allowed_tools would otherwise have re-enabled it",
                    name,
                )
            new_enabled = resolved_llm_visibility_base and allowed_alone
            new_tools[name] = dataclasses.replace(
                tool,
                enabled_for_llm=new_enabled,
            )
        self._tools = new_tools

    def snapshot_policy(self) -> ServiceSnapshot:
        """Capture the tool mapping `apply_policy` replaces.

        The mapping object reference is captured, not a copy of each entry, so a
        restore reattaches the original `RuntimeTool` objects that `apply_policy`
        replaced with `dataclasses.replace` copies (REQ-006).  `self._tools` is the
        only attribute `apply_policy` mutates: the policy inputs are call arguments,
        not stored state.
        """
        return ServiceSnapshot(service="runtime_tools", values={"tools": self._tools})

    def restore_policy(self, snapshot: ServiceSnapshot) -> None:
        """Reattach the captured tool mapping; changes nothing else on the registry."""
        self._tools = snapshot.values["tools"]

    def diagnostics(self) -> list[dict[str, Any]]:
        """Return per-tool diagnostics rows for display in /mcp status.

        Each row contains: name, server_key, config_dependent, enabled,
        disabled_reason, enabled_for_llm. Sorted by name.

        `disabled_reason` prefers the discovery-time reason a server sent in its
        /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
        status-derived value for tools whose entry never carried that key.

        `config_dependent` is the value the producer declared on the entry (REQ-007), read from the
        explicit `RuntimeTool` field rather than derived from `status`. A tool excluded at
        construction for a degraded capability has no row here: its capability dependency is reported
        through `exclusion_reason()`, which is the excluded-or-registered state.

        `enabled` is derived from `disabled_reason` to preserve the invariant
        documented in docs/04_mcp_03_06_tool-runtime-availability-metadata.md:
        `enabled=True` iff `disabled_reason == ""`.
        """
        rows: list[dict[str, Any]] = []
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            config_dep = tool.config_dependent
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
