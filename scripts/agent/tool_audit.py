"""agent/tool_audit.py
Structured audit-log writers for tool approval and execution events.

Extracted from repl_tool_exec.py to isolate audit concern.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import orjson

from agent.tool_policy import classify_operation_type
from agent.tool_result_formatter import mask_args

if TYPE_CHECKING:
    from agent.context import AgentContext


def audit_approval(
    ctx: AgentContext,
    tool_name: str,
    risk: str,
    args: dict,
    decision: str,
) -> None:
    """Write a structured tool_approval event to the audit log."""
    if ctx.services.audit_logger is None:
        return
    masked = mask_args(args, ctx.cfg.tool.masked_fields)
    path_keys = set(ctx.cfg.approval.approval_resource_keys.get("path_keys", []))
    branch_keys = set(ctx.cfg.approval.approval_resource_keys.get("branch_keys", []))
    resource_scope = {k: v for k, v in masked.items() if k in path_keys | branch_keys}
    ctx.services.audit_logger.info(
        orjson.dumps(
            {
                "event": "tool_approval",
                "task_id": ctx.turn.current_turn_id,
                "tool": tool_name,
                "operation_type": classify_operation_type(tool_name),
                "resource_scope": resource_scope,
                "risk": risk,
                "decision": decision,
                "args_preview": masked,
                "ts": time.time(),
            },
        ).decode(),
    )


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
    ctx.services.audit_logger.info(
        orjson.dumps(
            {
                "event": "tool_exec",
                "task_id": ctx.turn.current_turn_id,
                "tool": tool_name,
                "mcp_request_id": mcp_request_id,
                "is_error": is_error,
                "args_preview": masked,
                "ts": time.time(),
            },
        ).decode(),
    )
