#!/usr/bin/env python3
"""scripts/shared/runtime_tool.py

Normalized runtime tool-metadata shape.

`RuntimeTool` is the foundational data type that a future `RuntimeToolRegistry`
(separate module) will store and operate on. This module defines the shape and
its safe-default construction logic only; it has no consumer yet — MCP tool
discovery, registry storage, and dispatch-side wiring are handled by later
implementation steps.

`AgentSafetyTier`'s literal values intentionally duplicate (not import)
`agent.tool_policy`'s tier vocabulary (`_TIER_TO_RISK` dict keys) to respect the
`shared`-is-leaf import-layer contract (`shared` must not import from `agent`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AgentSafetyTier = Literal["READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"]


def _or_default[T](value: T | None, default: T) -> T:
    """Return *value* unless it is `None`, in which case return *default*."""
    return value if value is not None else default


@dataclass(frozen=True)
class RuntimeTool:
    """Normalized runtime metadata for a single tool.

    Fields:
        name:              Tool function name.
        server_key:        MCP server key the tool is routed to.
        server_url:        Base URL of the owning MCP server ("" if none).
        description:       Human/LLM-facing tool description.
        input_schema:      JSON schema for the tool's input arguments.
        raw_definition:    Verbatim raw tool definition as received from the MCP server.
        status:            Server-reported tool status (e.g. "active").
        is_write:          True when the tool has write/delete side effects.
        requires_serial:   True when the tool must not run concurrently with others.
        resource_scope_kind: Scope-kind prefix used by resolve_resource_scopes() (e.g.
                            "filesystem", "git_repo"; "" if unscoped).
        resource_scope_keys: Argument-dict keys whose values feed the resolved scope
                            string(s); empty tuple if none.
        agent_safety_tier: Safety tier used for approval-risk classification.
        requires_approval: True when the tool requires explicit user approval before execution.
        enabled_for_llm:   True when the tool is exposed to the LLM's tool-calling surface.
        capabilities:      Capability strings declared by the MCP server (empty tuple if absent).
        allow_extra_fields: True when unexpected/unschemad argument fields should be
                            tolerated instead of rejected by validate_tool_arguments().
    """

    name: str
    server_key: str
    server_url: str
    description: str
    input_schema: dict[str, Any]
    raw_definition: dict[str, Any]
    status: str
    is_write: bool
    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: tuple[str, ...]
    agent_safety_tier: AgentSafetyTier
    requires_approval: bool
    enabled_for_llm: bool
    capabilities: tuple[str, ...]
    allow_extra_fields: bool = False


def build_runtime_tool(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, Any] | None = None,
    raw_definition: dict[str, Any] | None = None,
    status: str = "active",
    is_write: bool | None = None,
    requires_serial: bool | None = None,
    resource_scope_kind: str = "",
    resource_scope_keys: tuple[str, ...] | None = None,
    agent_safety_tier: AgentSafetyTier | None = None,
    requires_approval: bool | None = None,
    enabled_for_llm: bool | None = None,
    capabilities: tuple[str, ...] | None = None,
    allow_extra_fields: bool | None = None,
) -> RuntimeTool:
    """Build a `RuntimeTool`, applying safe defaults for omitted annotation fields.

    Safe-default rules:
        - `is_write` defaults to `False` when not explicitly supplied.
        - `requires_serial` defaults to `True` whenever `is_write` was not explicitly
          supplied (unannotated write status is treated as unsafe to parallelize),
          otherwise `False`.
        - `agent_safety_tier` defaults to `"WRITE_DANGEROUS"` (most conservative tier).
        - `requires_approval` defaults to `True`.
        - `enabled_for_llm` defaults to `False`.
        - `capabilities` defaults to an empty tuple when not explicitly supplied.
        - `resource_scope_keys` defaults to an empty tuple when not explicitly supplied.
        - `allow_extra_fields` defaults to False — extra/unschemad fields are rejected
          unless a tool explicitly opts in.
    """
    resolved_input_schema = _or_default(input_schema, {})
    resolved_raw_definition = _or_default(raw_definition, {})
    resolved_is_write = _or_default(is_write, False)
    resolved_requires_serial = _or_default(requires_serial, is_write is None)
    # Kept as an explicit ternary (not routed through `_or_default`): pyright widens a
    # `Literal[...]`-typed TypeVar argument to `str`, which would break the
    # `AgentSafetyTier` return type below even though mypy accepts it.
    resolved_agent_safety_tier = (
        agent_safety_tier if agent_safety_tier is not None else "WRITE_DANGEROUS"
    )
    resolved_requires_approval = _or_default(requires_approval, True)
    resolved_enabled_for_llm = _or_default(enabled_for_llm, False)
    resolved_capabilities = _or_default(capabilities, ())
    resolved_resource_scope_keys = _or_default(resource_scope_keys, ())
    resolved_allow_extra_fields = _or_default(allow_extra_fields, False)

    return RuntimeTool(
        name=name,
        server_key=server_key,
        server_url=server_url,
        description=description,
        input_schema=resolved_input_schema,
        raw_definition=resolved_raw_definition,
        status=status,
        is_write=resolved_is_write,
        requires_serial=resolved_requires_serial,
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )
