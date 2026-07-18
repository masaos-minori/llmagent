#!/usr/bin/env python3
"""shared/runtime_tool.py

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
from typing import Literal

AgentSafetyTier = Literal["READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"]


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
        resource_scope:    Resource path/branch string for conflict detection ("" if none).
        agent_safety_tier: Safety tier used for approval-risk classification.
        requires_approval: True when the tool requires explicit user approval before execution.
        enabled_for_llm:   True when the tool is exposed to the LLM's tool-calling surface.
    """

    name: str
    server_key: str
    server_url: str
    description: str
    input_schema: dict[str, object]
    raw_definition: dict[str, object]
    status: str
    is_write: bool
    requires_serial: bool
    resource_scope: str
    agent_safety_tier: AgentSafetyTier
    requires_approval: bool
    enabled_for_llm: bool


def build_runtime_tool(
    name: str,
    server_key: str,
    server_url: str = "",
    description: str = "",
    input_schema: dict[str, object] | None = None,
    raw_definition: dict[str, object] | None = None,
    status: str = "active",
    is_write: bool | None = None,
    requires_serial: bool | None = None,
    resource_scope: str = "",
    agent_safety_tier: AgentSafetyTier | None = None,
    requires_approval: bool | None = None,
    enabled_for_llm: bool | None = None,
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
    """
    resolved_input_schema = input_schema if input_schema is not None else {}
    resolved_raw_definition = raw_definition if raw_definition is not None else {}
    resolved_is_write = is_write if is_write is not None else False
    resolved_requires_serial = (
        requires_serial if requires_serial is not None else is_write is None
    )
    resolved_agent_safety_tier = (
        agent_safety_tier if agent_safety_tier is not None else "WRITE_DANGEROUS"
    )
    resolved_requires_approval = (
        requires_approval if requires_approval is not None else True
    )
    resolved_enabled_for_llm = enabled_for_llm if enabled_for_llm is not None else False

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
        resource_scope=resource_scope,
        agent_safety_tier=resolved_agent_safety_tier,
        requires_approval=resolved_requires_approval,
        enabled_for_llm=resolved_enabled_for_llm,
    )
