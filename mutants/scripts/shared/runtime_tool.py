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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__or_default__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__or_default__mutmut)
def _or_default[T](value: T | None, default: T) -> T:
    """Return *value* unless it is `None`, in which case return *default*."""
    return value if value is not None else default


def x__or_default__mutmut_orig[T](value: T | None, default: T) -> T:
    """Return *value* unless it is `None`, in which case return *default*."""
    return value if value is not None else default


def x__or_default__mutmut_1[T](value: T | None, default: T) -> T:
    """Return *value* unless it is `None`, in which case return *default*."""
    return value if value is None else default

mutants_x__or_default__mutmut['_mutmut_orig'] = x__or_default__mutmut_orig # type: ignore # mutmut generated
mutants_x__or_default__mutmut['x__or_default__mutmut_1'] = x__or_default__mutmut_1 # type: ignore # mutmut generated


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
mutants_x_build_runtime_tool__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_build_runtime_tool__mutmut)
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


def x_build_runtime_tool__mutmut_orig(
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


def x_build_runtime_tool__mutmut_1(
    name: str,
    server_key: str,
    server_url: str = "XXXX",
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


def x_build_runtime_tool__mutmut_2(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "XXXX",
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


def x_build_runtime_tool__mutmut_3(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, Any] | None = None,
    raw_definition: dict[str, Any] | None = None,
    status: str = "XXactiveXX",
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


def x_build_runtime_tool__mutmut_4(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, Any] | None = None,
    raw_definition: dict[str, Any] | None = None,
    status: str = "ACTIVE",
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


def x_build_runtime_tool__mutmut_5(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, Any] | None = None,
    raw_definition: dict[str, Any] | None = None,
    status: str = "active",
    is_write: bool | None = None,
    requires_serial: bool | None = None,
    resource_scope_kind: str = "XXXX",
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


def x_build_runtime_tool__mutmut_6(
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
    resolved_input_schema = None
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


def x_build_runtime_tool__mutmut_7(
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
    resolved_input_schema = _or_default(None, {})
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


def x_build_runtime_tool__mutmut_8(
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
    resolved_input_schema = _or_default(input_schema, None)
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


def x_build_runtime_tool__mutmut_9(
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
    resolved_input_schema = _or_default({})
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


def x_build_runtime_tool__mutmut_10(
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
    resolved_input_schema = _or_default(input_schema, )
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


def x_build_runtime_tool__mutmut_11(
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
    resolved_raw_definition = None
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


def x_build_runtime_tool__mutmut_12(
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
    resolved_raw_definition = _or_default(None, {})
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


def x_build_runtime_tool__mutmut_13(
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
    resolved_raw_definition = _or_default(raw_definition, None)
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


def x_build_runtime_tool__mutmut_14(
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
    resolved_raw_definition = _or_default({})
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


def x_build_runtime_tool__mutmut_15(
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
    resolved_raw_definition = _or_default(raw_definition, )
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


def x_build_runtime_tool__mutmut_16(
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
    resolved_is_write = None
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


def x_build_runtime_tool__mutmut_17(
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
    resolved_is_write = _or_default(None, False)
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


def x_build_runtime_tool__mutmut_18(
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
    resolved_is_write = _or_default(is_write, None)
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


def x_build_runtime_tool__mutmut_19(
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
    resolved_is_write = _or_default(False)
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


def x_build_runtime_tool__mutmut_20(
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
    resolved_is_write = _or_default(is_write, )
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


def x_build_runtime_tool__mutmut_21(
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
    resolved_is_write = _or_default(is_write, True)
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


def x_build_runtime_tool__mutmut_22(
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
    resolved_requires_serial = None
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


def x_build_runtime_tool__mutmut_23(
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
    resolved_requires_serial = _or_default(None, is_write is None)
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


def x_build_runtime_tool__mutmut_24(
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
    resolved_requires_serial = _or_default(requires_serial, None)
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


def x_build_runtime_tool__mutmut_25(
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
    resolved_requires_serial = _or_default(is_write is None)
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


def x_build_runtime_tool__mutmut_26(
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
    resolved_requires_serial = _or_default(requires_serial, )
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


def x_build_runtime_tool__mutmut_27(
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
    resolved_requires_serial = _or_default(requires_serial, is_write is not None)
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


def x_build_runtime_tool__mutmut_28(
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
    resolved_agent_safety_tier = None
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


def x_build_runtime_tool__mutmut_29(
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
        agent_safety_tier if agent_safety_tier is None else "WRITE_DANGEROUS"
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


def x_build_runtime_tool__mutmut_30(
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
        agent_safety_tier if agent_safety_tier is not None else "XXWRITE_DANGEROUSXX"
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


def x_build_runtime_tool__mutmut_31(
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
        agent_safety_tier if agent_safety_tier is not None else "write_dangerous"
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


def x_build_runtime_tool__mutmut_32(
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
    resolved_requires_approval = None
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


def x_build_runtime_tool__mutmut_33(
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
    resolved_requires_approval = _or_default(None, True)
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


def x_build_runtime_tool__mutmut_34(
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
    resolved_requires_approval = _or_default(requires_approval, None)
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


def x_build_runtime_tool__mutmut_35(
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
    resolved_requires_approval = _or_default(True)
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


def x_build_runtime_tool__mutmut_36(
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
    resolved_requires_approval = _or_default(requires_approval, )
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


def x_build_runtime_tool__mutmut_37(
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
    resolved_requires_approval = _or_default(requires_approval, False)
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


def x_build_runtime_tool__mutmut_38(
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
    resolved_enabled_for_llm = None
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


def x_build_runtime_tool__mutmut_39(
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
    resolved_enabled_for_llm = _or_default(None, False)
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


def x_build_runtime_tool__mutmut_40(
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
    resolved_enabled_for_llm = _or_default(enabled_for_llm, None)
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


def x_build_runtime_tool__mutmut_41(
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
    resolved_enabled_for_llm = _or_default(False)
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


def x_build_runtime_tool__mutmut_42(
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
    resolved_enabled_for_llm = _or_default(enabled_for_llm, )
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


def x_build_runtime_tool__mutmut_43(
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
    resolved_enabled_for_llm = _or_default(enabled_for_llm, True)
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


def x_build_runtime_tool__mutmut_44(
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
    resolved_capabilities = None
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


def x_build_runtime_tool__mutmut_45(
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
    resolved_capabilities = _or_default(None, ())
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


def x_build_runtime_tool__mutmut_46(
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
    resolved_capabilities = _or_default(capabilities, None)
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


def x_build_runtime_tool__mutmut_47(
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
    resolved_capabilities = _or_default(())
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


def x_build_runtime_tool__mutmut_48(
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
    resolved_capabilities = _or_default(capabilities, )
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


def x_build_runtime_tool__mutmut_49(
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
    resolved_resource_scope_keys = None
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


def x_build_runtime_tool__mutmut_50(
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
    resolved_resource_scope_keys = _or_default(None, ())
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


def x_build_runtime_tool__mutmut_51(
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
    resolved_resource_scope_keys = _or_default(resource_scope_keys, None)
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


def x_build_runtime_tool__mutmut_52(
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
    resolved_resource_scope_keys = _or_default(())
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


def x_build_runtime_tool__mutmut_53(
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
    resolved_resource_scope_keys = _or_default(resource_scope_keys, )
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


def x_build_runtime_tool__mutmut_54(
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
    resolved_allow_extra_fields = None

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


def x_build_runtime_tool__mutmut_55(
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
    resolved_allow_extra_fields = _or_default(None, False)

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


def x_build_runtime_tool__mutmut_56(
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
    resolved_allow_extra_fields = _or_default(allow_extra_fields, None)

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


def x_build_runtime_tool__mutmut_57(
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
    resolved_allow_extra_fields = _or_default(False)

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


def x_build_runtime_tool__mutmut_58(
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
    resolved_allow_extra_fields = _or_default(allow_extra_fields, )

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


def x_build_runtime_tool__mutmut_59(
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
    resolved_allow_extra_fields = _or_default(allow_extra_fields, True)

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


def x_build_runtime_tool__mutmut_60(
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
        name=None,
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


def x_build_runtime_tool__mutmut_61(
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
        server_key=None,
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


def x_build_runtime_tool__mutmut_62(
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
        server_url=None,
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


def x_build_runtime_tool__mutmut_63(
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
        description=None,
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


def x_build_runtime_tool__mutmut_64(
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
        input_schema=None,
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


def x_build_runtime_tool__mutmut_65(
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
        raw_definition=None,
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


def x_build_runtime_tool__mutmut_66(
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
        status=None,
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


def x_build_runtime_tool__mutmut_67(
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
        is_write=None,
        requires_serial=resolved_requires_serial,
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_68(
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
        requires_serial=None,
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_69(
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
        resource_scope_kind=None,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_70(
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
        resource_scope_keys=None,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_71(
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
        agent_safety_tier=None,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_72(
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
        requires_approval=None,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_73(
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
        enabled_for_llm=None,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_74(
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
        capabilities=None,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_75(
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
        allow_extra_fields=None,
    )


def x_build_runtime_tool__mutmut_76(
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


def x_build_runtime_tool__mutmut_77(
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


def x_build_runtime_tool__mutmut_78(
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


def x_build_runtime_tool__mutmut_79(
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


def x_build_runtime_tool__mutmut_80(
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


def x_build_runtime_tool__mutmut_81(
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


def x_build_runtime_tool__mutmut_82(
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


def x_build_runtime_tool__mutmut_83(
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
        requires_serial=resolved_requires_serial,
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_84(
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
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_85(
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
        resource_scope_keys=resolved_resource_scope_keys,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_86(
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
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_87(
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
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_88(
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
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_89(
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
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_90(
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
        allow_extra_fields=resolved_allow_extra_fields,
    )


def x_build_runtime_tool__mutmut_91(
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
        )

mutants_x_build_runtime_tool__mutmut['_mutmut_orig'] = x_build_runtime_tool__mutmut_orig # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_1'] = x_build_runtime_tool__mutmut_1 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_2'] = x_build_runtime_tool__mutmut_2 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_3'] = x_build_runtime_tool__mutmut_3 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_4'] = x_build_runtime_tool__mutmut_4 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_5'] = x_build_runtime_tool__mutmut_5 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_6'] = x_build_runtime_tool__mutmut_6 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_7'] = x_build_runtime_tool__mutmut_7 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_8'] = x_build_runtime_tool__mutmut_8 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_9'] = x_build_runtime_tool__mutmut_9 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_10'] = x_build_runtime_tool__mutmut_10 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_11'] = x_build_runtime_tool__mutmut_11 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_12'] = x_build_runtime_tool__mutmut_12 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_13'] = x_build_runtime_tool__mutmut_13 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_14'] = x_build_runtime_tool__mutmut_14 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_15'] = x_build_runtime_tool__mutmut_15 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_16'] = x_build_runtime_tool__mutmut_16 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_17'] = x_build_runtime_tool__mutmut_17 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_18'] = x_build_runtime_tool__mutmut_18 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_19'] = x_build_runtime_tool__mutmut_19 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_20'] = x_build_runtime_tool__mutmut_20 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_21'] = x_build_runtime_tool__mutmut_21 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_22'] = x_build_runtime_tool__mutmut_22 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_23'] = x_build_runtime_tool__mutmut_23 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_24'] = x_build_runtime_tool__mutmut_24 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_25'] = x_build_runtime_tool__mutmut_25 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_26'] = x_build_runtime_tool__mutmut_26 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_27'] = x_build_runtime_tool__mutmut_27 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_28'] = x_build_runtime_tool__mutmut_28 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_29'] = x_build_runtime_tool__mutmut_29 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_30'] = x_build_runtime_tool__mutmut_30 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_31'] = x_build_runtime_tool__mutmut_31 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_32'] = x_build_runtime_tool__mutmut_32 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_33'] = x_build_runtime_tool__mutmut_33 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_34'] = x_build_runtime_tool__mutmut_34 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_35'] = x_build_runtime_tool__mutmut_35 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_36'] = x_build_runtime_tool__mutmut_36 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_37'] = x_build_runtime_tool__mutmut_37 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_38'] = x_build_runtime_tool__mutmut_38 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_39'] = x_build_runtime_tool__mutmut_39 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_40'] = x_build_runtime_tool__mutmut_40 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_41'] = x_build_runtime_tool__mutmut_41 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_42'] = x_build_runtime_tool__mutmut_42 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_43'] = x_build_runtime_tool__mutmut_43 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_44'] = x_build_runtime_tool__mutmut_44 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_45'] = x_build_runtime_tool__mutmut_45 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_46'] = x_build_runtime_tool__mutmut_46 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_47'] = x_build_runtime_tool__mutmut_47 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_48'] = x_build_runtime_tool__mutmut_48 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_49'] = x_build_runtime_tool__mutmut_49 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_50'] = x_build_runtime_tool__mutmut_50 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_51'] = x_build_runtime_tool__mutmut_51 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_52'] = x_build_runtime_tool__mutmut_52 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_53'] = x_build_runtime_tool__mutmut_53 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_54'] = x_build_runtime_tool__mutmut_54 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_55'] = x_build_runtime_tool__mutmut_55 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_56'] = x_build_runtime_tool__mutmut_56 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_57'] = x_build_runtime_tool__mutmut_57 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_58'] = x_build_runtime_tool__mutmut_58 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_59'] = x_build_runtime_tool__mutmut_59 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_60'] = x_build_runtime_tool__mutmut_60 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_61'] = x_build_runtime_tool__mutmut_61 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_62'] = x_build_runtime_tool__mutmut_62 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_63'] = x_build_runtime_tool__mutmut_63 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_64'] = x_build_runtime_tool__mutmut_64 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_65'] = x_build_runtime_tool__mutmut_65 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_66'] = x_build_runtime_tool__mutmut_66 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_67'] = x_build_runtime_tool__mutmut_67 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_68'] = x_build_runtime_tool__mutmut_68 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_69'] = x_build_runtime_tool__mutmut_69 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_70'] = x_build_runtime_tool__mutmut_70 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_71'] = x_build_runtime_tool__mutmut_71 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_72'] = x_build_runtime_tool__mutmut_72 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_73'] = x_build_runtime_tool__mutmut_73 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_74'] = x_build_runtime_tool__mutmut_74 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_75'] = x_build_runtime_tool__mutmut_75 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_76'] = x_build_runtime_tool__mutmut_76 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_77'] = x_build_runtime_tool__mutmut_77 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_78'] = x_build_runtime_tool__mutmut_78 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_79'] = x_build_runtime_tool__mutmut_79 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_80'] = x_build_runtime_tool__mutmut_80 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_81'] = x_build_runtime_tool__mutmut_81 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_82'] = x_build_runtime_tool__mutmut_82 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_83'] = x_build_runtime_tool__mutmut_83 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_84'] = x_build_runtime_tool__mutmut_84 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_85'] = x_build_runtime_tool__mutmut_85 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_86'] = x_build_runtime_tool__mutmut_86 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_87'] = x_build_runtime_tool__mutmut_87 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_88'] = x_build_runtime_tool__mutmut_88 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_89'] = x_build_runtime_tool__mutmut_89 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_90'] = x_build_runtime_tool__mutmut_90 # type: ignore # mutmut generated
mutants_x_build_runtime_tool__mutmut['x_build_runtime_tool__mutmut_91'] = x_build_runtime_tool__mutmut_91 # type: ignore # mutmut generated
