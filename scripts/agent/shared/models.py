"""agent/shared/models.py
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


@dataclass(frozen=True)
class ApprovalDecisionEvent:
    """Structured audit event for approval_decision log entries."""

    event: Literal["approval_decision"]
    task_id: str
    tool: str
    risk_level: str
    decision: str
    escalation_reason: str
    ts: float


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
    error_type: str = ""  # "transport" | "tool" | "" (none)
