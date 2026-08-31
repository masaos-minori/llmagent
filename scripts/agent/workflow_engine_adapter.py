#!/usr/bin/env python3
"""scripts/agent/workflow_engine_adapter.py

Workflow engine integration: task creation, activation/deactivation,
approval pending handling, halt handling.

Extracted from orchestrator.py (_init_workflow_task, _activate_workflow,
_deactivate_workflow, _handle_workflow_approval_pending, _handle_workflow_halt).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps as _json_dumps
from shared.llm_exceptions import LLMTransportError

from agent.conversation_state_manager import ConversationStateManager
from agent.llm_turn_executor import LlmTurnExecutor
from agent.mode_classification import classify_and_inject_mode
from agent.output_tags import OutputTag
from agent.tool_audit import (
    audit_approval_requested,
    audit_stage_completed,
    audit_workflow_start,
)
from agent.tool_output import emit_approval_pending_notice
from agent.workflow import (
    StateStore,
    TaskRecord,
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from agent.workflow.task_ops import create_task, get_task_by_id

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.diagnostic_store import DiagnosticStore

# ── WorkflowEngineAdapter class ───────────────────────────────────────────────


class WorkflowEngineAdapter:
    """Wires workflow engine lifecycle around an LLM turn.

    Responsibilities:
      - Create/resume workflow tasks
      - Activate/deactivate workflow state on context
      - Handle approval-pending and halt events
      - Run the workflow engine with plan/execute/verify callbacks
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        state_store: StateStore,
        workflow_engine: WorkflowEngine,
        conversation_manager: ConversationStateManager,
        llm_executor: LlmTurnExecutor,
        diagnostic_store: DiagnosticStore | None = None,
        tracer: Any = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize the workflow engine adapter."""
        self._ctx = ctx
        self._state_store = state_store
        self._workflow_engine = workflow_engine
        self._conversation_manager = conversation_manager
        self._llm_executor = llm_executor
        self._diagnostic_store = diagnostic_store
        self._tracer = tracer
        self._on_error = on_error

    # ── Backward-compatible public API ────────────────────────────────────────

    def init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        """Create a workflow task and audit its start.

        If existing_task_id is provided, use that task instead of creating a new one.
        The caller may pass a pre-opened StateStore via the `store` parameter to avoid
        opening a second connection.

        Backward-compatible alias for _init_workflow_task.
        """
        return self._init_workflow_task(ctx, session_id, existing_task_id, store)

    def activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Set workflow state to active.

        Backward-compatible alias for _activate_workflow.
        """
        self._activate_workflow(ctx, task)

    def deactivate_workflow(self, ctx: AgentContext) -> None:
        """Reset workflow state after engine completion.

        Backward-compatible alias for _deactivate_workflow.
        """
        self._deactivate_workflow(ctx)

    def handle_workflow_approval_pending(
        self, ctx: AgentContext, exc: WorkflowPendingApprovalError, session_id: str
    ) -> None:
        """Handle workflow approval pending event.

        Backward-compatible alias for _handle_workflow_approval_pending.
        """
        self._handle_workflow_approval_pending(exc, session_id)

    def handle_workflow_halt(
        self, ctx: AgentContext, exc: WorkflowHaltError | WorkflowTimeoutError
    ) -> None:
        """Handle workflow halt event.

        Backward-compatible alias for _handle_workflow_halt.
        """
        self._handle_workflow_halt(exc)

    # ── Private implementation ────────────────────────────────────────────────

    async def execute_turn(
        self,
        line: str,
        turn_started_at: float,
        session_id: str,
        existing_task_id: str | None = None,
    ) -> tuple[str, str | None, bool]:
        """Execute one turn through the workflow engine."""
        answer: str = ""
        error_kind: str | None = None
        is_partial: bool = False
        engine_status_handled: bool = False
        task: TaskRecord | None = None

        try:
            (
                workflow_id,
                task,
            ) = self._init_workflow_task(
                self._ctx, session_id, existing_task_id, self._state_store
            )
            self._ctx.turn.pending_approval_task_id = None
            self._activate_workflow(self._ctx, task)
            engine = WorkflowEngine(
                self._workflow_engine._wdef,
                self._state_store,
                tracer=self._tracer,
            )

            async def plan_fn() -> str | None:
                """No-op placeholder: planning work is done by TurnCoordinator.handle_turn_start before engine.run()."""
                return None

            async def execute_fn() -> str | None:
                """Process the user turn via process_turn and log stage completion."""
                nonlocal answer, error_kind, is_partial
                answer, error_kind, is_partial = await self._process_turn(
                    line, self._ctx, turn_started_at
                )
                elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
                audit_stage_completed(
                    self._ctx,
                    task.task_id,
                    "execute",
                    elapsed_ms,
                    workflow_id=workflow_id,
                    session_id=session_id,
                )
                return None

            async def verify_fn() -> str | None:
                """Run turn-end processing after the execute stage completes."""
                await self._handle_turn_end(
                    line, answer, turn_started_at, error_kind, is_partial
                )
                return None

            await engine.run(task, plan_fn, execute_fn, verify_fn)
        except WorkflowPendingApprovalError as exc:
            engine_status_handled = True
            self._handle_workflow_approval_pending(exc, session_id)
        except (WorkflowHaltError, WorkflowTimeoutError) as exc:
            engine_status_handled = True
            self._handle_workflow_halt(exc)
        finally:
            try:
                _task = task
                if _task is not None and _task.task_id and not engine_status_handled:
                    if error_kind is not None:
                        self._state_store.update_task_status(_task.task_id, "failed")
                    else:
                        self._state_store.update_task_status(_task.task_id, "completed")
            except Exception as e:  # noqa: BLE001 — updating task status on engine exit is best-effort; failure must not abort the turn
                logger.warning("Failed to update task status on engine exit: %s", e)
            self._deactivate_workflow(self._ctx)
            self._state_store.close()

        return answer, error_kind, is_partial

    def _format_session_id(self, session_id: int | None) -> str:
        """Format session_id for audit logs, returning empty string when None."""
        return str(session_id) if session_id is not None else ""

    def _build_turn_end_event(
        self,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
        is_partial: bool = False,
    ) -> dict[str, int | float | str | None]:
        """Build turn_end audit log event dict."""
        ctx = self._ctx
        return {
            "event": "turn_end",
            **self._build_turn_end_metadata(ctx),
            "elapsed_ms": elapsed_ms,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            **self._build_turn_end_llm_stats(ctx.services_required.llm),
            "partial_completion": is_partial,
            "error_kind": error_kind,
        }

    def _build_turn_end_metadata(
        self,
        ctx: AgentContext,
    ) -> dict[str, str]:
        """Build turn_end metadata (task_id, workflow_id, session_id)."""
        return {
            "task_id": ctx.turn.current_turn_id or "",
            "workflow_id": ctx.workflow.workflow_id or "",
            "session_id": self._format_session_id(ctx.session.session_id),
        }

    def _build_turn_end_llm_stats(
        self,
        llm: Any,
    ) -> dict[str, int]:
        """Build turn_end LLM stats fields."""
        return {
            "parse_error_count": getattr(llm, "stat_parse_errors", 0),
            "heartbeat_timeout_count": getattr(llm, "stat_heartbeat_timeouts", 0),
            "reconnect_count": getattr(llm, "stat_reconnects", 0),
        }

    def _init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        """Create a workflow task and audit its start."""
        assert self._workflow_engine._wdef is not None  # noqa: B101 — _wdef is required for workflow task creation; None indicates misconfiguration
        close_store = False
        if store is None:
            store = StateStore()
            close_store = True
        try:
            if existing_task_id is None:
                workflow_id = str(uuid.uuid4())
                task = create_task(
                    store._db,
                    session_id=session_id,
                    turn_number=ctx.stats.stat_turns,
                    workflow_version=self._workflow_engine._wdef.version,
                    workflow_id=workflow_id,
                )
                audit_workflow_start(
                    ctx,
                    task.task_id,
                    self._workflow_engine._wdef.version,
                    workflow_id=workflow_id,
                    session_id=session_id,
                )
            else:
                _fetched = get_task_by_id(store._db, existing_task_id)
                if _fetched is None:
                    raise RuntimeError(f"Task {existing_task_id} not found")
                if _fetched.status == "halted":
                    raise RuntimeError(
                        f"Task {existing_task_id} is halted and cannot be automatically resumed"
                    )
                task = _fetched
                workflow_id = task.workflow_id or str(uuid.uuid4())
        finally:
            if close_store:
                store.close()
        return workflow_id, task

    def _activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Set workflow state to active."""
        ctx.workflow.current_task_id = task.task_id
        ctx.workflow.workflow_id = task.workflow_id
        ctx.workflow.current_workflow_version = self._workflow_engine._wdef.version
        ctx.workflow.active = True

    def _deactivate_workflow(self, ctx: AgentContext) -> None:
        """Reset workflow state after engine completion."""
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None

    def _handle_workflow_approval_pending(
        self, exc: WorkflowPendingApprovalError, session_id: str
    ) -> None:
        """Handle workflow approval pending event."""
        ctx = self._ctx
        logger.info(
            "Turn suspended: awaiting approval %s for task %s",
            exc.approval_id,
            exc.task_id,
        )
        audit_approval_requested(
            ctx,
            exc.task_id,
            exc.approval_id,
            workflow_id=ctx.workflow.workflow_id or "",
            session_id=session_id,
        )
        ctx.turn.pending_approval_id = exc.approval_id
        ctx.workflow.approval_pending = True
        emit_approval_pending_notice(
            approval_id=exc.approval_id,
            task_id=exc.task_id or "unknown",
        )
        logger.warning(
            "%s Approval required. Use /approve %s [reason] or /reject %s [reason].",
            OutputTag.WORKFLOW,
            exc.approval_id,
            exc.approval_id,
        )

    def _handle_workflow_halt(
        self, exc: WorkflowHaltError | WorkflowTimeoutError
    ) -> None:
        """Handle workflow halt event."""
        ctx = self._ctx
        logger.error("Turn halted by workflow engine: %s", exc)
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None
        if self._on_error:
            self._on_error(exc)

    async def _process_turn(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None, bool]:
        """Process a turn and return (answer, error_kind, is_partial)."""
        answer = ""
        error_kind = None
        is_partial = False

        with self._tool_override(None):
            self._conversation_manager.clear_previous_turn_ephemeral_messages()
            await self._conversation_manager.handle_memory_injection(line)
            await classify_and_inject_mode(line, ctx)
            await self._conversation_manager.append_user_message(line)
            await self._conversation_manager.handle_history_compression()

            result = await self._llm_executor.handle_llm_turn(ctx.conv.llm_url)
            answer = result.answer
            if result.action != "continue":
                error_kind = result.error_kind or result.reason or result.action
                if (
                    isinstance(result.exception, LLMTransportError)
                    and result.exception.partial_text
                ):
                    is_partial = True

        return answer, error_kind, is_partial

    @contextmanager
    def _tool_override(self, allowed: list[str] | None) -> Iterator[None]:
        """Temporarily override allowed_tools for the duration of a turn."""
        original = self._ctx.cfg.tool.allowed_tools
        if allowed is not None:
            self._ctx.cfg.tool.allowed_tools = allowed
        try:
            yield
        finally:
            self._ctx.cfg.tool.allowed_tools = original

    async def _handle_turn_end(
        self,
        line: str,
        answer: str,
        turn_started_at: float,
        error_kind: str | None,
        is_partial: bool = False,
    ) -> None:
        """Emit a turn_end audit event and clear the current turn ID."""
        ctx = self._ctx
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services_required.audit_logger is not None:
            event = self._build_turn_end_event(
                elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial
            )
            ctx.services_required.audit_logger.info(_json_dumps(event))
        ctx.turn.current_turn_id = None
