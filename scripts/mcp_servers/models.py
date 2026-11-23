#!/usr/bin/env python3
"""scripts/mcp_servers/models.py

Shared Pydantic models for the /v1/call_tool unified endpoint.
Used by FileopMCPServer.py, WebSearchMCPServer.py, and GithubMCPServer.py.
"""

from collections.abc import Mapping
from typing import Any, NotRequired, Required, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator
from shared.mcp_call_state_contract import (
    AGENT_RECOVERY_STATES,
    CONTROL_ERROR_CODES,
    RECONCILE_OUTCOMES,
    RESULT_CLASSES,
    agent_state_for,
)
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


# Decision vocabulary for the reconcile endpoint (mcpdl004 REQ-001). It is the
# boundary vocabulary of this module: the endpoint answers with one of these four,
# and nothing else can be written into `decision`.
RECONCILE_DECISIONS: frozenset[str] = frozenset(
    {
        "reused_completed",
        "reconciled",
        "operator_review",
        "refused",
    }
)


def _check_vocabulary(field: str, value: str, vocabulary: frozenset[str]) -> str:
    """Reject a value outside the closed vocabulary before it reaches a response."""
    if value not in vocabulary:
        raise ValueError(f"{field} must be one of the closed vocabulary values")
    return value


def _check_ledger_status(value: str) -> str:
    """Accept only the row states the mapping table covers.

    The mapping function is the single source for the states a control response can
    report, so this does not duplicate a list here.
    """
    try:
        agent_state_for(value, False)
    except ValueError as exc:
        raise ValueError("ledger_status must be a ledger row state") from exc
    return value


class CallStateResponse(BaseModel):
    """Response body for GET /v1/call_state/{key} (mcpdl004 REQ-001).

    Every field is a closed vocabulary value or an opaque identifier: no raw
    arguments, credentials, signed URLs, raw exceptions, or internal paths.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., description="Logical call id (opaque)")
    ledger_status: str = Field(
        ..., description="Ledger row state (the states the mapping table covers)"
    )
    agent_state: str = Field(..., description="Agent state from the shared mapping")
    attempt_number: int = Field(..., ge=1, description="Attempt number for this call")
    lease_live: bool = Field(..., description="True while the lease is still held")
    lease_expires_epoch: float | None = Field(
        None, description="Lease expiry as an epoch, None when there is no lease"
    )
    result_class: str | None = Field(
        None, description="Result availability class (RESULT_CLASSES)"
    )
    result_code: str = Field(default="", description="Opaque stable result code")
    result_size_bytes: int | None = Field(
        None, ge=0, description="Serialized result size in bytes"
    )
    result_sha256: str = Field(
        default="", description="Digest of the stored result, empty when absent"
    )
    external_ref: str = Field(
        default="", description="Opaque external reference, empty when absent"
    )
    reconciliation_required: bool = Field(
        ..., description="True when an operator or reconciler must review the call"
    )
    error_code: str = Field(
        ..., description="Stable control error code (none when none)"
    )

    @field_validator("ledger_status")
    @classmethod
    def ledger_status_is_closed(cls, value: str) -> str:
        return _check_ledger_status(value)

    @field_validator("agent_state")
    @classmethod
    def agent_state_is_closed(cls, value: str) -> str:
        return _check_vocabulary("agent_state", value, AGENT_RECOVERY_STATES)

    @field_validator("result_class")
    @classmethod
    def result_class_is_closed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _check_vocabulary("result_class", value, RESULT_CLASSES)

    @field_validator("error_code")
    @classmethod
    def error_code_is_closed(cls, value: str) -> str:
        return _check_vocabulary("error_code", value, CONTROL_ERROR_CODES)


class ReconcileResponse(BaseModel):
    """Response body for POST /v1/call_state/{key}/reconcile (mcpdl004 REQ-001).

    `evidence_digest` is a non-sensitive digest or fixed label; the response never
    carries the evidence text itself.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., description="Logical call id (opaque)")
    decision: str = Field(..., description="Reconcile decision (RECONCILE_DECISIONS)")
    outcome: str = Field(
        ..., description="Reconcile outcome, or none when no reconciler ran"
    )
    ledger_status: str = Field(..., description="Ledger row state after the decision")
    agent_state: str = Field(..., description="Agent state from the shared mapping")
    operator_review: bool = Field(
        ..., description="True when the outcome needs operator review"
    )
    evidence_digest: str = Field(
        default="", description="Non-sensitive digest of the evidence (opaque)"
    )
    error_code: str = Field(
        ..., description="Stable control error code (none when none)"
    )

    @field_validator("decision")
    @classmethod
    def decision_is_closed(cls, value: str) -> str:
        return _check_vocabulary("decision", value, RECONCILE_DECISIONS)

    @field_validator("outcome")
    @classmethod
    def outcome_is_closed(cls, value: str) -> str:
        if value == "none":
            return value
        return _check_vocabulary("outcome", value, RECONCILE_OUTCOMES)

    @field_validator("ledger_status")
    @classmethod
    def ledger_status_is_closed(cls, value: str) -> str:
        return _check_ledger_status(value)

    @field_validator("agent_state")
    @classmethod
    def agent_state_is_closed(cls, value: str) -> str:
        return _check_vocabulary("agent_state", value, AGENT_RECOVERY_STATES)

    @field_validator("error_code")
    @classmethod
    def error_code_is_closed(cls, value: str) -> str:
        return _check_vocabulary("error_code", value, CONTROL_ERROR_CODES)


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
