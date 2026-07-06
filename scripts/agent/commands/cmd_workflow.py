"""agent/commands/cmd_workflow.py
Workflow approval mixin for CommandRegistry.

Provides _WorkflowMixin with:
  _cmd_approve  — /approve [approval_id] [reason]  Approve a suspended workflow task
  _cmd_reject   — /reject [approval_id] [reason]   Reject a suspended workflow task
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agent.commands.mixin_base import MixinBase
from agent.workflow.approval_ops import (
    count_pending_approvals,
    find_approval_by_id,
    find_latest_pending_approval,
    resolve_approval,
)
from agent.workflow.task_ops import update_task_status

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _parse_approval_arg(arg: str) -> tuple[str | None, str | None]:
    """Return (approval_id, reason) by splitting UUID prefix from free-text reason."""
    parts = arg.strip().split(None, 1)
    if parts and _UUID_RE.match(parts[0]):
        approval_id = parts[0]
        reason = parts[1] if len(parts) > 1 else None
        return approval_id, reason
    return None, arg.strip() or None


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

    def _emit_approval_audit(
        self,
        store: Any,
        approval_id: str,
        task_id: str,
        decision: str,
        reason: str | None,
    ) -> None:
        audit_logger = self._ctx.services_required.audit_logger
        if audit_logger is None:
            return
        task = store.get_task_by_id(task_id)
        audit_logger.info(
            json.dumps(
                {
                    "event_type": "workflow_approval",
                    "approval_id": approval_id,
                    "task_id": task_id,
                    "workflow_id": task.workflow_id if task else None,
                    "session_id": self._ctx.session.session_id,
                    "decision": decision,
                    "reason": reason,
                }
            )
        )

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
            explicit_id, reason = _parse_approval_arg(arg)
            count = count_pending_approvals(store._db)

            if count == 0:
                self._out.write_validation_error("No pending approval.")
                return

            if count > 1 and explicit_id is None:
                self._out.write_validation_error(
                    f"{count} pending approvals exist. Use: /approve <approval_id> [reason]"
                )
                return

            if explicit_id is not None:
                approval = find_approval_by_id(store._db, explicit_id)
                if approval is None or approval.status != "pending":
                    self._out.write_validation_error(
                        f"Approval {explicit_id!r} not found or not pending."
                    )
                    return
                task_id = approval.task_id
            else:
                result = find_latest_pending_approval(store._db)
                assert result is not None  # count == 1
                task_id, approval = result

            resolve_approval(store._db, approval.approval_id, "approved", reason)
            self._emit_approval_audit(
                store, approval.approval_id, task_id, "approved", reason
            )
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()

        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._ctx.turn.pending_approval_task_id = task_id
        self._out.write(
            f"Approved: {approval.approval_id} — workflow will resume on next turn"
        )

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
            explicit_id, reason = _parse_approval_arg(arg)
            count = count_pending_approvals(store._db)

            if count == 0:
                self._out.write_validation_error("No pending approval.")
                return

            if count > 1 and explicit_id is None:
                self._out.write_validation_error(
                    f"{count} pending approvals exist. Use: /reject <approval_id> [reason]"
                )
                return

            if explicit_id is not None:
                approval = find_approval_by_id(store._db, explicit_id)
                if approval is None or approval.status != "pending":
                    self._out.write_validation_error(
                        f"Approval {explicit_id!r} not found or not pending."
                    )
                    return
                task_id = approval.task_id
            else:
                result = find_latest_pending_approval(store._db)
                assert result is not None  # count == 1
                task_id, approval = result

            resolve_approval(store._db, approval.approval_id, "rejected", reason)
            update_task_status(store._db, task_id, "halted")
            self._emit_approval_audit(
                store, approval.approval_id, task_id, "rejected", reason
            )
        except RuntimeError as exc:
            self._out.write_validation_error(f"Failed to resolve approval: {exc}")
            return
        finally:
            store.close()

        self._ctx.turn.pending_approval_id = None
        self._ctx.workflow.approval_pending = False
        self._out.write(f"Rejected: {approval.approval_id} — task halted")
