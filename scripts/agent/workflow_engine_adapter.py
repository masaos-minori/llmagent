#!/usr/bin/env python3
"""scripts/agent/workflow_engine_adapter.py

Workflow engine integration: task creation, activation/deactivation,
halt handling.

Extracted from orchestrator.py (_init_workflow_task, _activate_workflow,
_deactivate_workflow, _handle_workflow_halt).
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from shared.llm_exceptions import LLMTransportError

from agent.conversation_state_manager import ConversationStateManager
from agent.llm_turn_executor import LlmTurnExecutor
from agent.mode_classification import classify_and_inject_mode
from agent.tool_audit import (
    audit_stage_completed,
    audit_workflow_start,
)
from agent.workflow import (
    StateStore,
    TaskRecord,
    WorkflowEngine,
    WorkflowHaltError,
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
      - Handle halt events
      - Run the workflow engine with plan/execute/verify callbacks

    Engine lifecycle: ``self._workflow_engine`` is the single source of truth for
    engine lifecycle — it is injected once and reused across turns. Do not recreate
    it per-turn; reuse ``self._workflow_engine`` directly.
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
        allowed_tools: list[str] | None = None,
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
        self._allowed_tools = allowed_tools
        self._owns_state_store = False

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
            self._activate_workflow(self._ctx, task)
            assert self._workflow_engine is not None, (
                "WorkflowEngine must be injected via constructor"
            )
            engine = self._workflow_engine

            async def plan_fn() -> str | None:
                return None

            async def execute_fn() -> str | None:
                """Run one execute-stage attempt and return its result."""
                nonlocal answer, error_kind, is_partial
                answer, error_kind, is_partial = await self._run_execute_stage(
                    self._ctx, workflow_id, session_id, task.task_id, turn_started_at
                )
                return None

            async def verify_fn() -> str | None:
                # The verify stage is required by workflow_loader.py:49; turn-end work
                # moved to the Orchestrator's _execute_turn bracket (see its plan). No-op.
                return None

            with self._tool_override(self._allowed_tools):
                try:
                    await self._prepare_turn_input(line, self._ctx)
                except (WorkflowHaltError, WorkflowTimeoutError):
                    raise
                except Exception as prepared_exc:
                    # A turn-entry failure must surface exactly as a stage failure
                    # does today (REQ-003): mark the task halted and route it
                    # through the existing halt handler so on_error receives a
                    # WorkflowHaltError — identical end state to a stage halt.
                    if task is not None and task.task_id:
                        self._state_store.update_task_status(task.task_id, "halted")
                    raise WorkflowHaltError(
                        f"Turn-entry preparation failed: {prepared_exc}"
                    ) from prepared_exc
                await engine.run(task, plan_fn, execute_fn, verify_fn)
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
            if self._owns_state_store:
                self._state_store.close()
            self._owns_state_store = False

        return answer, error_kind, is_partial

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
            self._owns_state_store = True
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

    def _handle_workflow_halt(
        self, exc: WorkflowHaltError | WorkflowTimeoutError
    ) -> None:
        """Handle workflow halt event."""
        logger.error("Turn halted by workflow engine: %s", exc)
        if self._on_error:
            self._on_error(exc)

    async def _prepare_turn_input(self, line: str, ctx: AgentContext) -> None:
        """Run turn-entry input preparation once, before the engine runs.

        Clears the previous turn's ephemeral messages, injects memory, classifies
        the turn mode, appends the user message, and compresses history. Runs once
        per execute_turn() regardless of execute-stage retries (REQ-001). Called
        from execute_turn() inside the single self._tool_override scope that also
        wraps engine.run(), so the mode-classified allowed_tools is in force for
        the LLM stage (REQ-004).
        """
        self._conversation_manager.clear_previous_turn_ephemeral_messages()
        await self._conversation_manager.handle_memory_injection(line)
        await classify_and_inject_mode(line, ctx)
        await self._conversation_manager.append_user_message(line)
        await self._conversation_manager.handle_history_compression()

    async def _run_execute_stage(
        self,
        ctx: AgentContext,
        workflow_id: str,
        session_id: str,
        task_id: str,
        turn_started_at: float,
    ) -> tuple[str, str | None, bool]:
        """Perform one execute-stage attempt: LLM/tool execution, error and
        partial-answer classification, assistant persistence, and
        audit_stage_completed. Per-attempt only; turn-entry preparation lives in
        _prepare_turn_input (REQ-002). Returns (answer, error_kind, is_partial)
        with the same contract as the removed _process_turn().
        """
        result = await self._llm_executor.handle_llm_turn(
            ctx.conv.llm_url,
            workflow_id=ctx.workflow.workflow_id or "",
            task_id=ctx.workflow.current_task_id or "",
            stage_id="execute",
            attempt_id=ctx.turn.current_turn_id or "",
        )
        answer = result.answer
        error_kind: str | None = None
        is_partial = False
        if result.action != "continue":
            error_kind = result.error_kind or result.reason or result.action
            if (
                isinstance(result.exception, LLMTransportError)
                and result.exception.partial_text
            ):
                is_partial = True
        elif result.persist_as_assistant:
            ctx.session.save("assistant", answer)

        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        audit_stage_completed(
            ctx,
            task_id,
            "execute",
            elapsed_ms,
            workflow_id=workflow_id,
            session_id=session_id,
        )
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
