#!/usr/bin/env python3
"""scripts/agent/orchestrator.py

Turn-level orchestration facade.

Composes the extracted concern classes (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`):
  workflow_engine_adapter.py    — WorkflowEngineAdapter (workflow engine integration)
  bg_task_monitor.py            — BgTaskMonitor (background task failure tracking)
  llm_turn_executor.py          — LlmTurnExecutor (LLM streaming and result processing)
  audit_event_emitter.py        — AuditEventEmitter (audit event construction)
  conversation_state_manager.py — ConversationStateManager (conversation history manipulation)

A workflow definition that cannot be loaded is a fatal construction error: there
is no fallback mode (ADR-001 Decision 4, ADR-004 INV-03).

ADR-014: Orchestrator arbitrates processing within a single turn; it delegates
persistent task state, stage transitions, retries, and approval to
WorkflowEngine, and delegates the LLM/tool-call loop to LlmTurnExecutor.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from shared.logger import Logger

from agent.audit_event_emitter import AuditEventEmitter
from agent.bg_task_monitor import BG_FAILURE_THRESHOLD, BgTaskMonitor
from agent.context import AgentContext
from agent.conversation_state_manager import ConversationStateManager
from agent.diagnostic_store import DiagnosticStore
from agent.llm_turn_executor import LlmTurnExecutor
from agent.output_tags import OutputTag
from agent.workflow import (
    StateStore,
    WorkflowDef,
    WorkflowEngine,
    WorkflowLoader,
    WorkflowLoadError,
)
from agent.workflow.workflow_loader import WORKFLOWS_DIR
from agent.workflow_engine_adapter import WorkflowEngineAdapter

if TYPE_CHECKING:
    pass

__all__ = ["BG_FAILURE_THRESHOLD", "Orchestrator"]

logger = Logger(__name__, "/opt/llm/logs/agent.log")


class Orchestrator:
    """Turn-level coordinator: compression -> LLM loop -> tool dispatch.

    Receives AgentContext (shared state) at construction. All terminal output
    and side effects are routed via optional callbacks so this class has no
    direct I/O dependency.

    A thin composition facade over the extracted concern classes (see module
    docstring) — this class only wires them together and arbitrates a turn.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        allowed_tools: list[str] | None = None,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_first_turn: Callable[[str], Any] | None = None,
        on_llm_wait_start: Callable[[str], Any] | None = None,
        on_llm_wait_end: Callable[[], None] | None = None,
        tracer: Any = None,
        pause_on_critical_failure: bool = False,
        workflow_engine: Any = None,
    ):
        self._ctx = ctx
        self._allowed_tools = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_error = on_error
        self._tracer = tracer
        self._pause_on_critical_failure = pause_on_critical_failure
        self._diagnostic_store = DiagnosticStore()
        ctx.diagnostics = self._diagnostic_store
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._state_store = StateStore()
        self._state_store.recover_stale_attempts(self._state_store.get_connection())

        # ── Component initialization (new constructor signatures) ────────────
        self._bg_task_monitor = BgTaskMonitor(
            ctx,
            tasks=self._background_tasks,
            on_discard=self._on_discard,
            on_error=self._on_error,
            pause_on_critical_failure=pause_on_critical_failure,
        )
        self._audit_emitter = AuditEventEmitter(
            ctx,
            diagnostic_store=self._diagnostic_store,
            tracer=tracer,
            on_turn_start=on_turn_start,
            on_turn_end=on_turn_end,
            on_error=on_error,
            on_first_turn=on_first_turn,
        )
        self._conversation_manager = ConversationStateManager(
            ctx,
            diagnostic_store=self._diagnostic_store,
            tasks=self._background_tasks,
            on_discard=self._on_discard,
            tracer=tracer,
            on_first_turn=on_first_turn,
            on_error=on_error,
        )
        self._llm_executor = LlmTurnExecutor(
            ctx,
            diagnostic_store=self._diagnostic_store,
            tracer=tracer,
            on_error=on_error,
            on_llm_wait_start=on_llm_wait_start,
            on_llm_wait_end=on_llm_wait_end,
        )
        try:
            self._workflow_def: WorkflowDef = WorkflowLoader().load()
        except (WorkflowLoadError, FileNotFoundError) as exc:
            raise RuntimeError(
                f"Workflow definition failed to load "
                f"({WORKFLOWS_DIR / 'default.json'}): {exc}"
            ) from exc

        _engine = (
            workflow_engine
            if workflow_engine is not None
            else WorkflowEngine(
                self._workflow_def,
                self._state_store,
                tracer=tracer,
            )
        )
        self._workflow_adapter = WorkflowEngineAdapter(
            ctx,
            state_store=self._state_store,
            workflow_engine=_engine,
            conversation_manager=self._conversation_manager,
            llm_executor=self._llm_executor,
            diagnostic_store=self._diagnostic_store,
            tracer=tracer,
            on_error=on_error,
            allowed_tools=self._allowed_tools,
        )

    # ── Public entry point ────────────────────────────────────────────────────

    async def handle_turn(self, line):
        ctx = self._ctx
        if ctx.workflow.approval_pending:
            await self._on_approval_pending(ctx.turn.pending_approval_id)
            return
        is_paused, paused_names = self._bg_task_monitor.check_pause_state()
        if is_paused:
            await self._on_pause_blocked(paused_names)
            return
        await self._execute_turn(line)

    async def _execute_turn(self, line):
        await self._audit_emitter.emit_turn_start()
        answer, error_kind, is_partial = await self._workflow_adapter.execute_turn(
            line, 0.0, ""
        )
        await self._audit_emitter.emit_turn_end(
            line, answer, 0.0, error_kind, is_partial
        )

    def workflow_status(self) -> dict[str, str]:
        """Return the current workflow tracking status."""
        if self._ctx.workflow.active:
            return {"tracking": "enabled"}
        return {"tracking": "not_loaded"}

    async def _on_approval_pending(self, pending_approval_id):
        logger.warning(
            "Turn blocked: workflow pending approval. Use /approve %s or /reject %s.",
            pending_approval_id,
            pending_approval_id,
        )
        if self._on_error:
            self._on_error(
                RuntimeError(
                    f"{OutputTag.WORKFLOW} Approval is pending — use /approve {pending_approval_id} [reason] "
                    f"or /reject {pending_approval_id} [reason]."
                )
            )

    async def _on_pause_blocked(self, paused_names):
        logger.warning(
            "Turn blocked: agent paused due to background task failures: %s",
            paused_names,
        )
        if self._on_error:
            self._on_error(
                RuntimeError(
                    f"{OutputTag.WORKFLOW} Agent paused due to repeated failures in: {paused_names}. "
                    "Restart the process to clear pause state."
                )
            )

    def _on_discard(self, task):
        self._bg_task_monitor.on_task_done(task)
