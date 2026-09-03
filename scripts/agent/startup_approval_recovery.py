"""scripts/agent/startup_approval_recovery.py

Approval recovery: restore workflow approval-pending state from a previous session.

Extracted from scripts/agent/startup.py (REQ-005).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.context import AgentContext
from agent.output_tags import OutputTag

if TYPE_CHECKING:
    from agent.cli_view import CLIView


class ApprovalRecovery:
    """Owns approval recovery from previous sessions."""

    def __init__(self, ctx: AgentContext, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    async def recover(self) -> None:
        """Restore workflow approval-pending state from a previous session."""
        from shared.logger import Logger

        logger = Logger(__name__, "/opt/llm/logs/agent.log")

        from agent.workflow.approval_ops import find_all_pending_approvals
        from agent.workflow.state_store import StateStore

        ctx = self._ctx
        store = StateStore()
        try:
            results = find_all_pending_approvals(store.get_connection())
        finally:
            store.close()
        if not results:
            logger.warning(
                "No pending approvals found; existing approvals may have expired"
            )
            return
        # Recover the most recent pending approval first
        task_id, approval = results[0]
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        if ctx.turn.pending_approval_task_id is not None:
            logger.warning(
                "Overwriting pending_approval_task_id %s with %s during recovery",
                ctx.turn.pending_approval_task_id,
                task_id,
            )
        ctx.turn.pending_approval_task_id = task_id
        logger.warning(
            "Recovered %d pending approval(s); showing last: task=%s approval=%s reason=%s",
            len(results),
            task_id,
            approval.approval_id,
            approval.reason or "none",
        )
        self._view.write_warning(
            f"{OutputTag.WORKFLOW} Pending approval from previous session — "
            f"{len(results)} pending approval(s); last: task={task_id} approval={approval.approval_id} reason={approval.reason or 'none'}.\n"
            f"Use /approve {approval.approval_id} [reason] or /reject {approval.approval_id} [reason]."
        )
