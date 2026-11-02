"""scripts/agent/tool_audit.py

Structured audit-log writers for tool approval and execution events.

Isolated here to keep audit concerns separate from execution logic.
"""

from __future__ import annotations

import dataclasses
import logging
import time
from typing import TYPE_CHECKING

from shared.execution_snapshot import build_execution_snapshot, snapshot_json
from shared.json_utils import dumps as _json_dumps

from agent.shared.models import ApprovalDecisionEvent, ToolApprovalEvent, ToolExecEvent
from agent.tool_enums import ApprovalDecisionType, RiskLevel
from agent.tool_models import ApprovalOutcome
from agent.tool_policy import classify_operation_type
from agent.tool_result_formatter import mask_args

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

AUDIT_ARGS_PREVIEW_MAX_CHARS = 1500

_ERROR_TYPE_DENIED = "denied"


def _bounded_preview(masked: dict) -> dict:
    """Bound the serialized args preview; oversized payloads become an envelope."""
    serialized = _json_dumps(masked)
    if len(serialized) <= AUDIT_ARGS_PREVIEW_MAX_CHARS:
        return masked
    return {
        "preview": serialized[:AUDIT_ARGS_PREVIEW_MAX_CHARS],
        "truncated": True,
    }


def _extract_resource_scope(ctx: AgentContext, masked: dict) -> dict[str, str]:
    """Pull path/branch keys from masked args for audit events."""
    path_keys = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    branch_keys = set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    return {k: str(v) for k, v in masked.items() if k in path_keys | branch_keys}


def _workflow_id_or_skip(ctx: AgentContext, writer: str, tool: str) -> str | None:
    """Return the workflow id, or None after logging a skip warning.

    assertaudit001: a missing workflow_id must not raise — these writers can run
    after tool side effects, so an exception here would abort post-execution.
    The warning names the writer and the tool only, never argument values.
    """
    workflow_id = ctx.workflow.workflow_id
    if not workflow_id:
        logger.warning(
            "%s skipped: called outside workflow context (tool=%s)",
            writer,
            tool,
        )
        return None
    return workflow_id


def audit_approval(
    ctx: AgentContext,
    tool_name: str,
    risk: RiskLevel | str,
    args: dict,
    decision: ApprovalDecisionType | str,
) -> None:
    """Write a structured tool_approval event to the audit log."""
    if ctx.services_required.audit_logger is None:
        return
    workflow_id = _workflow_id_or_skip(ctx, "audit_approval", tool_name)
    if workflow_id is None:
        return
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolApprovalEvent(
        event="tool_approval",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(
            tool_name, ctx.services_required.runtime_tools
        ),
        resource_scope=resource_scope,
        risk=str(risk),
        decision=str(decision),
        args_preview=_bounded_preview(masked),
        ts=time.time(),
        workflow_id=workflow_id,
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
    )
    ctx.services_required.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))


def log_approval_decision(ctx: AgentContext, outcome: ApprovalOutcome) -> None:
    """Write a structured approval_decision event to the audit log."""
    if ctx.services_required.audit_logger is None:
        return
    workflow_id = _workflow_id_or_skip(ctx, "log_approval_decision", outcome.tool_name)
    if workflow_id is None:
        return
    evt = ApprovalDecisionEvent(
        event="approval_decision",
        task_id=ctx.turn.current_turn_id or "",
        tool=outcome.tool_name,
        risk_level=str(outcome.risk_level),
        decision=str(outcome.decision),
        escalation_reason=outcome.escalation_reason,
        ts=time.time(),
        workflow_id=workflow_id,
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
    )
    ctx.services_required.audit_logger.info(_json_dumps(dataclasses.asdict(evt)))


def audit_workflow_start(
    ctx: AgentContext,
    task_id: str,
    workflow_version: str,
    workflow_id: str = "",
    session_id: str = "",
) -> None:
    """Write workflow_start event to audit log."""
    if ctx.services_required.audit_logger is None:
        return
    ctx.services_required.audit_logger.info(
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
    if ctx.services_required.audit_logger is None:
        return
    ctx.services_required.audit_logger.info(
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


def audit_tool_exec(
    ctx: AgentContext,
    tool_name: str,
    args: dict,
    is_error: bool,
    mcp_request_id: str,
    error_type: str = "",
    artifact_uri: str | None = None,
    source: str = "",
    idempotency_key: str = "",
    task_linkage: str = "",
    dedup_state: str = "",
) -> None:
    """Write a tool_exec event with mcp_request_id to the audit log.

    Every record carries ``execution_snapshot_json`` (canonical JSON of the
    deployment fingerprint captured at call time, toolexec001 REQ-004);
    ``dedup_state`` is serialized only when non-empty (dispatcher dedup outcome,
    REQ-005; empty for non-dispatch-originated or freshly executed calls).
    """
    if ctx.services_required.audit_logger is None:
        return
    if not mcp_request_id and not source and error_type != _ERROR_TYPE_DENIED:
        return
    workflow_id = _workflow_id_or_skip(ctx, "audit_tool_exec", tool_name)
    if workflow_id is None:
        return
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    resource_scope = _extract_resource_scope(ctx, masked)
    evt = ToolExecEvent(
        event="tool_exec",
        task_id=ctx.turn.current_turn_id or "",
        tool=tool_name,
        operation_type=classify_operation_type(
            tool_name, ctx.services_required.runtime_tools
        ),
        resource_scope=resource_scope,
        mcp_request_id=mcp_request_id,
        is_error=is_error,
        args_preview=_bounded_preview(masked),
        ts=time.time(),
        source=source if source else "agent",
        error_type=error_type,
        workflow_id=workflow_id,
        session_id=str(ctx.session.session_id) if ctx.session.session_id else "",
        idempotency_key=idempotency_key,
        task_linkage=task_linkage,
        artifact_uri=artifact_uri,
    )
    payload = dataclasses.asdict(evt)
    payload["execution_snapshot_json"] = snapshot_json(build_execution_snapshot())
    if dedup_state:
        payload["dedup_state"] = dedup_state
    ctx.services_required.audit_logger.info(_json_dumps(payload))


def write_round_exec(
    ctx: AgentContext,
    *,
    round_id: str,
    tool_count: int,
    mode: str,
    has_side_effect: bool,
    trigger_tool: str | None,
    elapsed_ms: float,
    affected_tools: list[str] | None = None,
    serial_reason: str | None = None,
    estimated_parallel_ms: float | None = None,
    scheduling_mode: str | None = None,
) -> None:
    """Log a round-wide execution event, capturing serialization impact."""
    if ctx.services_required.audit_logger is None:
        return
    ctx.services_required.audit_logger.info(
        _json_dumps(
            {
                "event": "round_exec",
                "source": "agent",
                "ts": time.time(),
                "round_id": round_id,
                "tool_count": tool_count,
                "mode": mode,
                "has_side_effect": has_side_effect,
                "trigger_tool": trigger_tool,
                "elapsed_ms": round(elapsed_ms, 1),
                "affected_tools": affected_tools or [],
                "serial_reason": serial_reason,
                "estimated_parallel_ms": (
                    round(estimated_parallel_ms, 1)
                    if estimated_parallel_ms is not None
                    else None
                ),
                "scheduling_mode": scheduling_mode,
            }
        )
    )
