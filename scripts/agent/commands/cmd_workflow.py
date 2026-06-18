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
        approval_id = self._ctx.turn.pending_approval_id
        if approval_id is None:
            self._out.write_validation_error(
                "No pending approval. Run a workflow task first."
            )
            return
        reason = arg.strip() or None
        try:
            from agent.workflow import (
                StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
            )

            store = StateStore()
            try:
                store.resolve_approval(approval_id, "approved", reason)
            finally:
                store.close()
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        self._ctx.turn.pending_approval_id = None
        self._out.write(f"Approved: {approval_id}")

    def _cmd_reject(self, arg: str) -> None:
        """Reject the pending workflow task, optionally with a reason."""
        approval_id = self._ctx.turn.pending_approval_id
        if approval_id is None:
            self._out.write_validation_error(
                "No pending approval. Run a workflow task first."
            )
            return
        reason = arg.strip() or None
        try:
            from agent.workflow import (
                StateStore,  # noqa: PLC0415 — lazy: avoids startup cost
            )

            store = StateStore()
            try:
                store.resolve_approval(approval_id, "rejected", reason)
            finally:
                store.close()
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        self._ctx.turn.pending_approval_id = None
        self._out.write(f"Rejected: {approval_id}")
