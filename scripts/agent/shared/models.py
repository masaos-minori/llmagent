"""scripts/agent/shared/models.py

Cross-cutting frozen dataclass DTOs for the agent layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ToolApprovalEvent:
    """Structured audit event for tool_approval log entries."""

    event: Literal["tool_approval"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    risk: str
    decision: str
    args_preview: dict[str, object]
    ts: float
    workflow_id: str = ""
    session_id: str = ""
    # Logical call id (uuid7) generated at preparation; the same value the
    # transport sends as X-Idempotency-Key and the state store keys on.
    idempotency_key: str = ""
    task_linkage: str = ""  # WorkflowEngine task-level linkage (current_task_id)
    # Approval provenance: the input request that asked the operator, where the
    # preview came from (static or dry_run), and why a fallback happened (if any).
    # The operator's answer text is deliberately not recorded.
    request_id: str = ""
    preview_source: str = ""
    fallback_reason: str = ""
    turn_id: str = ""  # turn id; task_id keeps the same value (ADR-001 INV-11)


@dataclass(frozen=True)
class ToolExecEvent:
    """Structured audit event for tool_exec log entries."""

    event: Literal["tool_exec"]
    task_id: str
    tool: str
    operation_type: str
    resource_scope: dict[str, str]
    mcp_request_id: str
    is_error: bool
    args_preview: dict[str, object]
    ts: float
    source: str = "agent"
    error_type: str = ""  # "transport" | "tool" | "" (empty on success)
    workflow_id: str = ""
    session_id: str = ""
    # Logical call id (uuid7) generated once at preparation and reused by the
    # transport X-Idempotency-Key, the tool_call_state row, and the approval
    # event — the single identity shared by all three (AC-2).
    idempotency_key: str = ""
    task_linkage: str = ""  # WorkflowEngine task-level linkage (current_task_id)
    artifact_uri: str | None = None
    turn_id: str = ""  # turn id; task_id keeps the same value (ADR-001 INV-11)


@dataclass(frozen=True)
class ApprovalGrant:
    """Proof that the approval gate authorized one specific prepared call.

    Issued by the approval gate (tool_approval) and re-checked at execution and
    at the repository gateway; single-use enforcement lives in the gateway, not
    in this model. `args_hash` is the hex sha256 of canonical-JSON args, the
    same computation as `ToolExecutionContext.args_hash`, so a re-bound or
    edited call fails the comparison. `issued_at`/`expires_at` are epoch
    seconds; the expiry horizon is a tool_approval module constant.
    """

    tool: str
    args_hash: str
    mode: str  # approval decision mode that issued the grant
    issued_at: float
    expires_at: float
