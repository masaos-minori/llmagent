"""agent/commands/cmd_workflow.py
Workflow approval mixin for CommandRegistry.

Provides _WorkflowMixin with:
  _cmd_approve  — /approve [reason]  Approve a suspended workflow task
  _cmd_reject   — /reject [reason]   Reject a suspended workflow task
"""

from __future__ import annotations

import logging

from agent.commands.mixin_base import MixinBase

logger = logging.getLogger(__name__)


class _WorkflowMixin(MixinBase):
    """Workflow approval slash-command handlers."""

    def _cmd_approve(self, arg: str) -> None:
        """Approve the pending workflow task, optionally with a reason."""
        from agent.workflow import (
            StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
        )

        store = StateStore()
        try:
            result = store.find_latest_pending_approval()
            if result is None:
                self._out.write_validation_error(
                    "No pending approval. Run a workflow task first."
                )
                return
            _task_id, approval = result
            approval_id = approval.approval_id
            reason = arg.strip() or None
            store.resolve_approval(approval_id, "approved", reason)
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()
        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._out.write(f"Approved: {approval_id}")

    def _cmd_reject(self, arg: str) -> None:
        """Reject the pending workflow task, optionally with a reason."""
        from agent.workflow import (
            StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
        )

        store = StateStore()
        try:
            result = store.find_latest_pending_approval()
            if result is None:
                self._out.write_validation_error(
                    "No pending approval. Run a workflow task first."
                )
                return
            _task_id, approval = result
            approval_id = approval.approval_id
            reason = arg.strip() or None
            store.resolve_approval(approval_id, "rejected", reason)
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()
        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._out.write(f"Rejected: {approval_id}")
