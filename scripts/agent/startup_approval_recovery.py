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
        # Wire up the most recent approval (first in DESC order) for immediate action
        task_id, approval = results[0]
        ctx.workflow.approval_pending = True
        ctx.turn.pending_approval_id = approval.approval_id
        if ctx.turn.pending_approval_task_id is not None:
            # Only overwrite if the current value is stale (from a previous session).
            # If both exist and differ, prefer the current value assuming it's active.
            existing_task_id = ctx.turn.pending_approval_task_id
            if existing_task_id != task_id:
                logger.warning(
                    "Keeping existing pending_approval_task_id %s instead of overwriting with %s during recovery",
                    existing_task_id,
                    task_id,
                )
            else:
                logger.warning(
                    "Overwriting pending_approval_task_id %s with %s during recovery",
                    existing_task_id,
                    task_id,
                )
        if (
            ctx.turn.pending_approval_task_id is None
            or ctx.turn.pending_approval_task_id == task_id
        ):
            ctx.turn.pending_approval_task_id = task_id
        # List all pending approvals for resolution
        lines = []
        for i, (tid, appr) in enumerate(results, start=1):
            lines.append(
                f"  [{i}] task={tid} approval={appr.approval_id} reason={appr.reason}"
            )
        logger.info(
            "Recovered %d pending approval(s); wired up: task=%s approval=%s reason=%s",
            len(results),
            task_id,
            approval.approval_id,
            approval.reason or "none",
        )
        logger.info("All pending approvals:")
        for line in lines:
            logger.info(line)
        self._view.write_warning(
            f"{OutputTag.WORKFLOW} Pending approval from previous session — "
            f"{len(results)} pending approval(s); wired up: task={task_id} approval={approval.approval_id} reason={approval.reason or 'none'}.\n"
            f"All pending approvals:\n" + "\n".join(lines) + "\n"
            "Use /approve <approval_id> [reason] or /reject <approval_id> [reason]."
        )
