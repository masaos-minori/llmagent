#!/usr/bin/env python3
"""scripts/agent/workflow_engine_adapter.py

Workflow engine integration: task creation, activation/deactivation,
halt handling.

Extracted from orchestrator.py (_init_workflow_task, _activate_workflow,
deactivate_workflow, _handle_workflow_halt).
"""

# ADR-014: adapter between the Orchestrator and the WorkflowEngine that owns persistent state
from __future__ import annotations

import asyncio
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
    WorkflowStageFailure,
    WorkflowTimeoutError,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.diagnostic_store import DiagnosticStore

# ── Private helpers ───────────────────────────────────────────────────────────


def _status_for_exit(exit_reason: str, error_kind: str | None) -> str | None:
    """Return a status the adapter must write, or None when the engine already wrote it.

    `exit_reason` is one of "not-started" (the engine call was never reached),
    "engine-started" (engine.run raised or is still unwound), "halted", "cancelled" or
    "completed". `None` covers every exit the workflow engine already recorded: the
    engine writes the task status exactly once per turn (REQ-008), so a completed
    exit with a failure `error_kind` no longer triggers a second write here — the
    engine wrote `failed` for the terminal stage failure itself.
    """
    if exit_reason == "cancelled":
        return "halted"
    return None


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
        exit_reason: str = "not-started"
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
            exit_reason = "engine-started"

            async def plan_fn() -> str | None:
                return None

            async def execute_fn() -> str | None:
                """Run one execute-stage attempt and return its result."""
                nonlocal answer, error_kind, is_partial
                # Per-attempt side-effect flag reset (REQ-006): TurnState is not
                # recreated per attempt, so the adapter clears it at attempt start.
                self._ctx.turn.attempt_side_effect = False
                try:
                    answer, error_kind, is_partial = await self._run_execute_stage(
                        self._ctx,
                        workflow_id,
                        session_id,
                        task.task_id,
                        turn_started_at,
                    )
                except Exception as exc:
                    if self._ctx.turn.attempt_side_effect:
                        # A failed attempt that already attempted a side effect is
                        # terminal regardless of retry_on (REQ-006 / AC-6).
                        raise WorkflowHaltError(
                            "stage execute halted: side effect attempted"
                        ) from exc
                    raise
                if error_kind is not None:
                    # LLM-level failure results enter the engine as typed stage
                    # failures of kind llm_failure (REQ-005 / AC-5).
                    raise WorkflowStageFailure(
                        f"stage execute failed: {error_kind}",
                        answer=answer,
                        error_kind=error_kind,
                        is_partial=is_partial,
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
                exit_reason = "completed"
        except WorkflowTimeoutError as exc:
            exit_reason = "halted"
            error_kind = "workflow_timeout"
            self._handle_workflow_halt(exc)
        except WorkflowHaltError as exc:
            exit_reason = "halted"
            error_kind = "workflow_halted"
            self._handle_workflow_halt(exc)
        except WorkflowStageFailure as exc:
            # Terminal stage failure: the engine already wrote the task status once;
            # restore the outward typed tuple from the error attributes (REQ-004/005/008).
            exit_reason = "halted"
            answer = exc.answer or ""
            error_kind = exc.error_kind or "llm_failure"
            is_partial = exc.is_partial
        except asyncio.CancelledError:
            exit_reason = "cancelled"
            raise
        finally:
            self._record_exit_status(exit_reason, error_kind, task)
            if self._owns_state_store:
                self._state_store.close()
            self._owns_state_store = False

        return answer, error_kind, is_partial

    def _record_exit_status(
        self, exit_reason: str, error_kind: str | None, task: TaskRecord | None
    ) -> None:
        """Best-effort write of the status the adapter owns for this exit.

        Writes nothing when the workflow engine already recorded the outcome.
        """
        intended_status = _status_for_exit(exit_reason, error_kind)
        if intended_status is None or task is None or not task.task_id:
            return
        try:
            self._state_store.update_task_status(task.task_id, intended_status)
        except Exception as exc:  # noqa: BLE001 — updating task status on engine exit is best-effort; failure must not abort the turn
            logger.error(
                "Failed to update task status for task %s to %s: %s",
                task.task_id,
                intended_status,
                exc,
            )

    def _init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        """Create a workflow task and audit its start."""
        # Reset per-call ownership so a prior store-less init cannot leak True
        # across calls and close an injected store on the next turn's exit.
        self._owns_state_store = False
        close_store = False
        if store is None:
            store = StateStore()
            close_store = True
            self._owns_state_store = True
        try:
            if existing_task_id is None:
                workflow_id = str(uuid.uuid4())
                task = store.create_task(
                    session_id=session_id,
                    turn_number=ctx.stats.stat_turns,
                    workflow_version=self._workflow_engine.version,
                    workflow_id=workflow_id,
                )
                audit_workflow_start(
                    ctx,
                    task.task_id,
                    self._workflow_engine.version,
                    workflow_id=workflow_id,
                    session_id=session_id,
                )
            else:
                _fetched = store.get_task_by_id(existing_task_id)
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
        # Producer wiring (plans/20261101-105136_toolstate001 plan.md REQ-005):
        # tool_runner records tool_call_state through this facade while active.
        ctx.workflow.tool_call_recorder = self._state_store
        ctx.workflow.workflow_id = task.workflow_id
        ctx.workflow.current_workflow_version = self._workflow_engine.version
        ctx.workflow.active = True

    def deactivate_workflow(self, ctx: AgentContext) -> None:
        """Reset workflow state after engine completion."""
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.tool_call_recorder = None
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
        # Turn-entry replay detection (toolexec001 row 08): the engine owns the
        # decision; the adapter only carries the constructed message to the runner.
        control_message = self._workflow_engine.build_turn_control_message(task_id)
        result = await self._llm_executor.handle_llm_turn(
            ctx.conv.llm_url,
            workflow_id=ctx.workflow.workflow_id or "",
            task_id=ctx.workflow.current_task_id or "",
            stage_id="execute",
            attempt_id=ctx.turn.current_turn_id or "",
            control_message=control_message,
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
            # Persist the final answer through the turn's atomic boundary (SEQ-09)
            # instead of a standalone commit; a later failure compensates it with
            # every other turn write (AC-001, AC-002).
            boundary = ctx.turn.persistence_boundary
            assert boundary is not None, "persistence boundary not set for this turn"  # noqa: B101 — boundary required inside a turn; None means writes bypass the atomic boundary
            await boundary.save("assistant", answer)

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
