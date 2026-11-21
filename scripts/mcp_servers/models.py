#!/usr/bin/env python3
"""scripts/mcp_servers/models.py

Shared Pydantic models for the /v1/call_tool unified endpoint.
Used by FileopMCPServer.py, WebSearchMCPServer.py, and GithubMCPServer.py.
"""

from collections.abc import Mapping
from typing import Any, NotRequired, Required, TypedDict

from pydantic import BaseModel, Field, field_validator
from shared.runtime_tool import AgentSafetyTier
from shared.tool_metadata import (
    PreviewCapability,
    ReconciliationPolicy,
    ResourceKeyKind,
    RetryPolicy,
    SideEffectClass,
)

from mcp_servers.tool_validators import validate_tool_args


class CallToolRequest(BaseModel):
    """Request body for POST /v1/call_tool."""

    name: str = Field(..., description="Tool name")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        """Reject blank tool names early so dispatch logic can assume non-empty."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Tool name must not be blank")
        return stripped

    def validate_args(self) -> None:
        """Run tool-specific argument validation if a validator is registered.

        Must be called explicitly before dispatching the tool call.
        Pydantic does not call this automatically.
        Raises ValueError when args violate tool constraints.
        """
        validate_tool_args(self.name, self.args)


class CallToolResponse(BaseModel):
    """Response body for POST /v1/call_tool."""

    result: str = Field(..., description="Formatted result text")
    is_error: bool = Field(..., description="True when the tool call failed")
    dedup_state: str = Field(
        default="",
        description="Durable-dedup state tag for this call ('' when no dedup branch was taken)",
    )


class McpTool(TypedDict):
    """TypedDict for a single MCP tool definition in TOOL_LIST.

    agentcfg003 (REQ-003/AC-03): the schema-2.1 required field set is declared
    here with the value types from shared.tool_metadata, so a producer literal
    that omits or mistypes a required declaration fails at type-check time as
    well as at the runtime schema gate (validate_tool_schema_v2). No field is
    NotRequired.
    """

    name: Required[str]
    description: Required[str]
    inputSchema: Required[dict[str, Any]]
    status: Required[str]
    config_dependent: Required[bool]
    is_write: Required[bool]
    requires_serial: Required[bool]
    resource_scope_kind: Required[str]
    resource_scope_keys: Required[Mapping[str, ResourceKeyKind]]
    agent_safety_tier: Required[AgentSafetyTier]
    side_effect_class: Required[SideEffectClass]
    retry_policy: Required[RetryPolicy]
    reconciliation_policy: Required[ReconciliationPolicy]
    idempotency_required: Required[bool]
    preview_capability: Required[PreviewCapability]
    policy_version: Required[str]


class McpToolProperty(TypedDict):
    """TypedDict for a single MCP tool property definition."""

    type: Required[str]
    description: Required[str]
    minItems: NotRequired[int]
