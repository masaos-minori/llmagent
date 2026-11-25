"""scripts/agent/tool_result_audit.py — audit bridge for the tool-result write paths.

The two tool-result write paths, the tool_exec audit line and the transport_failure
diagnostic record, live here so the runner keeps only the call wiring.

The bridge passes the dispatcher dedup state and the logical call id through,
so the audit line, the state row, and the diagnostics record share one call
identity.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from shared.transport_dto import ToolCallResult

from agent.tool_audit import audit_tool_exec

if TYPE_CHECKING:
    from agent.context import AgentContext


def record_tool_exec(
    ctx: AgentContext,
    name: str,
    args: dict,
    result: ToolCallResult,
    call_id: str,
) -> None:
    """Write the tool_exec audit line for one executed call.

    ``dedup_state`` and the logical call id ride on the result and the
    preparation-time identity; the writers populate the event ids from context.
    """
    audit_tool_exec(
        ctx,
        name,
        args,
        result.is_error,
        result.request_id,
        result.error_type,
        source=result.source,
        idempotency_key=call_id,
        dedup_state=result.dedup_state,
    )


async def record_transport_failure(
    ctx: AgentContext,
    name: str,
    result: ToolCallResult,
    call_id: str,
) -> None:
    """Persist a transport-level failure to diagnostics off the loop, when wired.

    The guard conditions are carried over unchanged from the runner (REQ-007);
    the record gains the call identity keys (REQ-005): in the diagnostic record
    ``task_id`` is the workflow task id and ``turn_id`` the turn id, unlike the
    audit events where ``task_id`` carries the turn id (UNK-01 option B).
    """
    if (
        not result.is_error
        or result.error_type != "transport"
        or ctx.diagnostics is None
    ):
        return
    await asyncio.to_thread(
        ctx.diagnostics.save_transport_failure,
        session_id=getattr(ctx.session, "session_id", None),
        tool_name=name,
        server_key=result.server_key or "",
        error_msg=result.output[:500],
        call_id=call_id,
        request_id=result.request_id,
        task_id=ctx.workflow.current_task_id or "",
        turn_id=ctx.turn.current_turn_id or "",
    )
