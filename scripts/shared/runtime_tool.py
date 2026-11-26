#!/usr/bin/env python3
"""scripts/shared/runtime_tool.py — Normalized runtime tool-metadata shape.

Normalized runtime tool-metadata shape.

`RuntimeTool` is the shape stored by `RuntimeToolRegistry` and built by MCP tool
discovery. `build_runtime_tool()` is the single construction point and enforces
the required execution metadata (field set `TOOL_FIELD_SET_VERSION`): `is_write`,
`requires_serial`, `resource_scope_kind`, `resource_scope_keys`, `side_effect_class`,
`retry_policy`, `reconciliation_policy`, `idempotency_required`, `preview_capability`,
`policy_version` and `agent_safety_tier` are required arguments with no defaults;
omission fails closed with `TypeError` and an explicit `None` with `ValueError`.
The vocabulary values come from `shared.tool_metadata`; the remaining annotation
fields keep conservative defaults.

`AgentSafetyTier`'s literal values intentionally duplicate (not import)
`agent.tool_policy`'s tier vocabulary (`_TIER_TO_RISK` dict keys) to respect the
`shared`-is-leaf import-layer contract (`shared` must not import from `agent`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from shared.tool_metadata import (
    PreviewCapability,
    ReconciliationPolicy,
    ResourceKeyKind,
    RetryPolicy,
    SideEffectClass,
)

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
        resource_scope_keys: Mapping of argument-dict key name to its declared
                            ResourceKeyKind; empty mapping if none. Keys typed
                            "non_escalating" still resolve a scope string but are
                            never used by an escalation rule.
        agent_safety_tier: Safety tier declared by the tool (no default; required).
        side_effect_class: Declared side-effect class from the closed vocabulary.
        retry_policy:      Declared retry policy from the closed vocabulary.
        reconciliation_policy: Declared reconciliation policy from the closed vocabulary.
        idempotency_required: True when the tool must be idempotent to be safely retried.
        preview_capability: Declared preview capability flag from the closed vocabulary;
                            the Agent does not infer execution mode.
        policy_version:    Field-set version the declaration was written against.
        enabled_for_llm:   True when the tool is exposed to the LLM's tool-calling surface.
        capabilities:      Capability strings declared by the MCP server (empty tuple if absent).
        allow_extra_fields: True when unexpected/unschemad argument fields should be
                            tolerated instead of rejected by validate_tool_arguments().
        llm_visibility_base: Immutable base visibility flag set once at discovery time.
                             Defaults to mirroring ``enabled_for_llm`` when unset.
        config_dependent:    True when the tool's operation depends on configuration declared by
                             the producer. Carried from the declaration, never inferred (REQ-007);
                             diagnostic-only, so it defaults to False outside the discovery path.
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
    resource_scope_keys: Mapping[str, ResourceKeyKind]
    agent_safety_tier: AgentSafetyTier
    side_effect_class: SideEffectClass
    retry_policy: RetryPolicy
    reconciliation_policy: ReconciliationPolicy
    idempotency_required: bool
    preview_capability: PreviewCapability
    policy_version: str
    enabled_for_llm: bool
    capabilities: tuple[str, ...]
    allow_extra_fields: bool = False
    llm_visibility_base: bool | None = None
    config_dependent: bool = False

    def __post_init__(self) -> None:
        """Resolve the immutable base visibility when not explicitly provided."""
        if object.__getattribute__(self, "llm_visibility_base") is None:
            object.__setattr__(self, "llm_visibility_base", self.enabled_for_llm)


def build_runtime_tool(
    name: str,
    server_key: str,
    *,
    is_write: bool,
    requires_serial: bool,
    resource_scope_kind: str,
    resource_scope_keys: Mapping[str, ResourceKeyKind],
    agent_safety_tier: AgentSafetyTier,
    side_effect_class: SideEffectClass,
    retry_policy: RetryPolicy,
    reconciliation_policy: ReconciliationPolicy,
    idempotency_required: bool,
    preview_capability: PreviewCapability,
    policy_version: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, Any] | None = None,
    raw_definition: dict[str, Any] | None = None,
    status: str = "active",
    enabled_for_llm: bool | None = None,
    capabilities: tuple[str, ...] | None = None,
    allow_extra_fields: bool | None = None,
    llm_visibility_base: bool | None = None,
    config_dependent: bool | None = None,
) -> RuntimeTool:
    """Build a `RuntimeTool`, requiring the full execution-metadata field set.

    Required fields (fail-closed): `is_write`, `requires_serial`,
    `resource_scope_kind`, `resource_scope_keys`, `agent_safety_tier`,
    `side_effect_class`, `retry_policy`, `reconciliation_policy`,
    `idempotency_required`, `preview_capability`, `policy_version`. Omitting one
    raises `TypeError` via the keyword-only signature; passing `None` explicitly
    raises `ValueError`. No default value is added for any required field: a tool
    that cannot declare a value is rejected.

    Safe-default rules for the remaining annotation fields:
        - `enabled_for_llm` defaults to `False`.
        - `capabilities` defaults to an empty tuple when not explicitly supplied.
        - `allow_extra_fields` defaults to False — extra/unschemad fields are rejected
          unless a tool explicitly opts in.
        - `llm_visibility_base` defaults to mirroring ``enabled_for_llm`` when not
          explicitly supplied.
        - `config_dependent` defaults to `False`. The default serves non-discovery
          construction only (D-7): the discovery path passes the producer-declared
          value, and the field is diagnostic-only.
    """
    for field, value in (
        ("is_write", is_write),
        ("requires_serial", requires_serial),
        ("resource_scope_kind", resource_scope_kind),
        ("resource_scope_keys", resource_scope_keys),
        ("agent_safety_tier", agent_safety_tier),
        ("side_effect_class", side_effect_class),
        ("retry_policy", retry_policy),
        ("reconciliation_policy", reconciliation_policy),
        ("idempotency_required", idempotency_required),
        ("preview_capability", preview_capability),
        ("policy_version", policy_version),
    ):
        if value is None:
            raise ValueError(f"{field} is required")
    resolved_input_schema = _or_default(input_schema, {})
    resolved_raw_definition = _or_default(raw_definition, {})
    resolved_enabled_for_llm = _or_default(enabled_for_llm, False)
    resolved_capabilities = _or_default(capabilities, ())
    resolved_allow_extra_fields = _or_default(allow_extra_fields, False)
    resolved_llm_visibility_base = _or_default(
        llm_visibility_base, resolved_enabled_for_llm
    )
    resolved_config_dependent = _or_default(config_dependent, False)

    return RuntimeTool(
        name=name,
        server_key=server_key,
        server_url=server_url,
        description=description,
        input_schema=resolved_input_schema,
        raw_definition=resolved_raw_definition,
        status=status,
        is_write=is_write,
        requires_serial=requires_serial,
        resource_scope_kind=resource_scope_kind,
        resource_scope_keys=resource_scope_keys,
        agent_safety_tier=agent_safety_tier,
        side_effect_class=side_effect_class,
        retry_policy=retry_policy,
        reconciliation_policy=reconciliation_policy,
        idempotency_required=idempotency_required,
        preview_capability=preview_capability,
        policy_version=policy_version,
        enabled_for_llm=resolved_enabled_for_llm,
        capabilities=resolved_capabilities,
        allow_extra_fields=resolved_allow_extra_fields,
        llm_visibility_base=resolved_llm_visibility_base,
        config_dependent=resolved_config_dependent,
    )
