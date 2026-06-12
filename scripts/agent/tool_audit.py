"""agent/tool_audit.py
Structured audit-log writers for tool approval and execution events.

Extracted from repl_tool_exec.py to isolate audit concern.
"""

from __future__ import annotations

import dataclasses
import time
from typing import TYPE_CHECKING

import orjson

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
    )
    ctx.services.audit_logger.info(orjson.dumps(dataclasses.asdict(evt)).decode())


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
    )
    ctx.services.audit_logger.info(orjson.dumps(dataclasses.asdict(evt)).decode())


def audit_tool_exec(
    ctx: AgentContext,
    tool_name: str,
    args: dict,
    is_error: bool,
    mcp_request_id: str,
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
    )
    ctx.services.audit_logger.info(orjson.dumps(dataclasses.asdict(evt)).decode())
