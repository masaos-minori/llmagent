"""agent/commands/cmd_workflow.py
Workflow approval mixin for CommandRegistry.

Provides _WorkflowMixin with:
  _cmd_approve  — /approve [reason]  Approve a suspended workflow task
  _cmd_reject   — /reject [reason]   Reject a suspended workflow task
"""

from __future__ import annotations

import logging

from agent.commands.mixin_base import MixinBase
from agent.workflow.approval_ops import find_latest_pending_approval, resolve_approval
from agent.workflow.task_ops import update_task_status

logger = logging.getLogger(__name__)


class _WorkflowMixin(MixinBase):
    """Workflow approval slash-command handlers.

    These commands resolve workflow-level approval gates only (DB-persisted,
    per-task record in ``approvals``). Per-tool interactive approval
    (``run_approval_checks``) is handled separately via stdin prompts and is
    not affected by these commands.

    Startup recovery: if the agent restarts while an approval is pending,
    ``startup._recover_pending_approvals()`` restores ``ctx.workflow.approval_pending``
    before the REPL starts. The user will see a startup notice and can then
    use ``/approve`` or ``/reject`` to resolve it.
    """

    def _cmd_approve(self, arg: str) -> None:
        """Approve the pending workflow-level approval gate (approvals table only).

        Does not affect per-tool interactive approval (tool_approval.run_approval_checks).
        After approval, the workflow engine will auto-resume on the next turn.
        """
        from agent.workflow import (
            StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
        )

        store = StateStore()
        try:
            result = find_latest_pending_approval(store._db)
            if result is None:
                self._out.write_validation_error(
                    "No pending approval. Run a workflow task first."
                )
                return
            task_id, approval = result
            approval_id = approval.approval_id
            reason = arg.strip() or None
            resolve_approval(store._db, approval_id, "approved", reason)
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()
        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._ctx.turn.pending_approval_task_id = task_id
        self._out.write(f"Approved: {approval_id} — workflow will resume on next turn")

    def _cmd_reject(self, arg: str) -> None:
        """Reject the pending workflow-level approval gate (approvals table only).

        Does not affect per-tool interactive approval (tool_approval.run_approval_checks).
        Immediately marks the task as halted.
        """
        from agent.workflow import (
            StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
        )

        store = StateStore()
        try:
            result = find_latest_pending_approval(store._db)
            if result is None:
                self._out.write_validation_error(
                    "No pending approval. Run a workflow task first."
                )
                return
            task_id, approval = result
            approval_id = approval.approval_id
            reason = arg.strip() or None
            resolve_approval(store._db, approval_id, "rejected", reason)
            update_task_status(store._db, task_id, "halted")
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()
        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._out.write(f"Rejected: {approval_id} — task halted")
