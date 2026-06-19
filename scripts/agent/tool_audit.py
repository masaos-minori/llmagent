"""agent/tool_audit.py
Structured audit-log writers for tool approval and execution events.

Isolated here to keep audit concerns separate from execution logic.
"""

from __future__ import annotations

import dataclasses
import time
from typing import TYPE_CHECKING

from shared.json_utils import dumps as _json_dumps

from agent.shared.models import ApprovalDecisionEvent, ToolApprovalEvent, ToolExecEvent
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_models import ApprovalOutcome
from agent.tool_policy import classify_operation_type
from agent.tool_result_formatter import mask_args

if TYPE_CHECKING:
    from agent.context import AgentContext


def _extract_resource_scope(ctx: AgentContext, masked: dict) -> dict[str, str]:
    """Pull path/branch keys from masked args for audit events."""
    path_keys = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    branch_keys = set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    return {k: str(v) for k, v in masked.items() if k in path_keys | branch_keys}


def audit_approval(
    ctx: AgentContext,
    tool_name: str,
    risk: RiskLevel | str,
    args: dict,
    decision: ApprovalDecisionType | str,
) -> None:
    """Write a structured tool_approval event to the audit log."""
    if ctx.services.audit_logger is None:
        return
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolApprovalEvent(
        event="tool_approval",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(tool_name),
        resource_scope=resource_scope,
        risk=str(risk),
        decision=str(decision),
        args_preview=masked,
        ts=time.time(),
        workflow_id=ctx.workflow.workflow_id or "",
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
    )
    ctx.services.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))


def log_approval_decision(ctx: AgentContext, outcome: ApprovalOutcome) -> None:
    """Write a structured approval_decision event to the audit log."""
    if ctx.services.audit_logger is None:
        return
    evt = ApprovalDecisionEvent(
        event="approval_decision",
        task_id=ctx.turn.current_turn_id or "",
        tool=outcome.tool_name,
        risk_level=str(outcome.risk_level),
        decision=str(outcome.decision),
        escalation_reason=outcome.escalation_reason,
        ts=time.time(),
        workflow_id=ctx.workflow.workflow_id or "",
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
    )
    ctx.services.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))


def audit_workflow_start(
    ctx: AgentContext,
    task_id: str,
    workflow_version: str,
    workflow_id: str = "",
    session_id: str = "",
) -> None:
    """Write workflow_start event to audit log."""
    if ctx.services.audit_logger is None:
        return
    ctx.services.audit_logger.info(
        _json_dumps(
            {
                "event": "workflow_start",
                "task_id": task_id,
                "workflow_id": workflow_id,
                "session_id": session_id,
                "workflow_version": workflow_version,
                "ts": time.time(),
            }
        )
    )


def audit_stage_completed(
    ctx: AgentContext,
    task_id: str,
    stage_id: str,
    elapsed_ms: float,
    workflow_id: str = "",
    session_id: str = "",
) -> None:
    """Write stage_completed event to audit log."""
    if ctx.services.audit_logger is None:
        return
    ctx.services.audit_logger.info(
        _json_dumps(
            {
                "event": "stage_completed",
                "task_id": task_id,
                "workflow_id": workflow_id,
                "session_id": session_id,
                "stage_id": stage_id,
                "elapsed_ms": elapsed_ms,
                "ts": time.time(),
            }
        )
    )


def audit_approval_requested(
    ctx: AgentContext,
    task_id: str,
    approval_id: str,
    workflow_id: str = "",
    session_id: str = "",
) -> None:
    """Write approval_requested event to audit log."""
    if ctx.services.audit_logger is None:
        return
    ctx.services.audit_logger.info(
        _json_dumps(
            {
                "event": "approval_requested",
                "task_id": task_id,
                "workflow_id": workflow_id,
                "session_id": session_id,
                "approval_id": approval_id,
                "ts": time.time(),
            }
        )
    )


def audit_tool_exec(
    ctx: AgentContext,
    tool_name: str,
    args: dict,
    is_error: bool,
    mcp_request_id: str,
    error_type: str = "",
    artifact_uri: str | None = None,
) -> None:
    """Write a tool_exec event with mcp_request_id to the audit log."""
    if ctx.services.audit_logger is None or not mcp_request_id:
        return
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolExecEvent(
        event="tool_exec",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(tool_name),
        resource_scope=resource_scope,
        mcp_request_id=mcp_request_id,
        is_error=is_error,
        args_preview=masked,
        ts=time.time(),
        error_type=error_type,
        workflow_id=ctx.workflow.workflow_id or "",
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
        artifact_uri=artifact_uri,
    )
    ctx.services.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))


def write_round_exec(
    ctx: AgentContext,
    *,
    round_id: str,
    tool_count: int,
    mode: str,
    has_side_effect: bool,
    trigger_tool: str | None,
    elapsed_ms: float,
) -> None:
    """Log a round-wide execution event, capturing serialization impact."""
    if ctx.services.audit_logger is None:
        return
    ctx.services.audit_logger.info(
        "round_exec",
        extra={
            "round_id": round_id,
            "tool_count": tool_count,
            "mode": mode,
            "has_side_effect": has_side_effect,
            "trigger_tool": trigger_tool,
            "elapsed_ms": round(elapsed_ms, 1),
        },
    )
