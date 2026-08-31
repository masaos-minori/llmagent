#!/usr/bin/env python3
"""scripts/agent/workflow_engine_adapter.py

Workflow engine integration (task init, activation, deactivation,
approval/halt handling), extracted from Orchestrator (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from shared.logger import Logger

from agent.audit_event_emitter import _format_session_id
from agent.context import AgentContext
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
    WorkflowDef,
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from agent.workflow.task_ops import create_task, get_task_by_id

logger = Logger(__name__, "/opt/llm/logs/agent.log")

ProcessTurnFn = Callable[
    [str, AgentContext, float], Awaitable[tuple[str, str | None, bool]]
]
HandleTurnEndFn = Callable[
    [AgentContext, str, str, float, str | None, bool], Awaitable[None]
]


class WorkflowEngineAdapter:
    """Runs a turn through the WorkflowEngine, managing task lifecycle and
    approval/halt events."""

    def __init__(
        self,
        workflow_def: WorkflowDef,
        state_store: StateStore,
        *,
        tracer: Any = None,
        process_turn: ProcessTurnFn,
        handle_turn_end: HandleTurnEndFn,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize with the loaded workflow definition, default state
        store, and the injected process_turn/handle_turn_end callables this
        adapter delegates to during engine execution."""
        self._workflow_def = workflow_def
        self._state_store = state_store
        self._tracer = tracer
        self._process_turn = process_turn
        self._handle_turn_end = handle_turn_end
        self._on_error = on_error

    async def handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> None:
        """Execute a turn through the workflow engine."""
        assert self._workflow_def is not None  # noqa: B101 — only called when workflow_def exists
        session_id = _format_session_id(ctx.session.session_id) or "none"
        store = self._state_store
        answer: str = ""
        error_kind: str | None = None
        is_partial: bool = False
        engine_status_handled: bool = False  # WorkflowEngine already persisted terminal status; do not overwrite in finally
        task: TaskRecord | None = None
        try:
            (
                workflow_id,
                task,
            ) = self.init_workflow_task(
                ctx, session_id, ctx.turn.pending_approval_task_id, store
            )
            # Clear pending approval task ID after retrieval
            ctx.turn.pending_approval_task_id = None
            self.activate_workflow(ctx, task)
            engine = WorkflowEngine(
                self._workflow_def,
                store,
                tracer=self._tracer,
            )

            async def plan_fn() -> str | None:
                """No-op placeholder: planning work is done by TurnCoordinator.handle_turn_start before engine.run()."""
                return None

            async def execute_fn() -> str | None:
                """Process the user turn via process_turn and log stage completion."""
                nonlocal answer, error_kind, is_partial
                answer, error_kind, is_partial = await self._process_turn(
                    line, ctx, turn_started_at
                )
                elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
                audit_stage_completed(
                    ctx,
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
                    ctx, line, answer, turn_started_at, error_kind, is_partial
                )
                return None

            await engine.run(task, plan_fn, execute_fn, verify_fn)
        except WorkflowPendingApprovalError as exc:
            engine_status_handled = True
            self.handle_workflow_approval_pending(ctx, exc, session_id)
        except (WorkflowHaltError, WorkflowTimeoutError) as exc:
            engine_status_handled = True
            self.handle_workflow_halt(ctx, exc)
        finally:
            # Update task status before deactivating to prevent orphaned records
            try:
                _task = task
                if _task is not None and _task.task_id and not engine_status_handled:
                    if error_kind is not None:
                        store.update_task_status(_task.task_id, "failed")
                    else:
                        store.update_task_status(_task.task_id, "completed")
            except Exception as e:  # noqa: BLE001 — task-status update failure on engine exit must not block workflow deactivation
                logger.warning("Failed to update task status on engine exit: %s", e)
            self.deactivate_workflow(ctx)
            store.close()

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
        """
        assert self._workflow_def is not None  # noqa: B101 — only called when workflow_def exists
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
                    workflow_version=self._workflow_def.version,
                    workflow_id=workflow_id,
                )
                audit_workflow_start(
                    ctx,
                    task.task_id,
                    self._workflow_def.version,
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

    def activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Set workflow state to active."""
        ctx.workflow.current_task_id = task.task_id
        ctx.workflow.workflow_id = task.workflow_id
        ctx.workflow.current_workflow_version = self._workflow_def.version
        ctx.workflow.active = True

    def deactivate_workflow(self, ctx: AgentContext) -> None:
        """Reset workflow state after engine completion."""
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None

    def handle_workflow_approval_pending(
        self, ctx: AgentContext, exc: WorkflowPendingApprovalError, session_id: str
    ) -> None:
        """Handle workflow approval pending event."""
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

    def handle_workflow_halt(
        self, ctx: AgentContext, exc: WorkflowHaltError | WorkflowTimeoutError
    ) -> None:
        """Handle workflow halt event."""
        logger.error("Turn halted by workflow engine: %s", exc)
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None
        if self._on_error:
            self._on_error(exc)
