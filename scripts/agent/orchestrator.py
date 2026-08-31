#!/usr/bin/env python3
"""scripts/agent/orchestrator.py

Turn-level orchestration facade.

Composes six extracted concern classes (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`):
  turnd_coordinator.py         — TurnCoordinator (turn lifecycle)
  workflow_engine_adapter.py   — WorkflowEngineAdapter (workflow engine integration)
  bg_task_monitor.py           — BgTaskMonitor (background task failure tracking)
  llm_turn_executor.py         — LlmTurnExecutor (LLM streaming and result processing)
  audit_event_emitter.py       — AuditEventEmitter (audit event construction)
  conversation_state_manager.py — ConversationStateManager (conversation history manipulation)

Delegates LLM streaming and tool-loop guarding to:
  llm_turn_runner.py  — LLMTurnRunner (streaming + inner tool-call loop)
  tool_loop_guard.py  — ToolLoopGuard + TurnLoopState (dedup/cycle/retry/error guards)

All other concerns are delegated to extracted concern classes:
  bg_task_monitor.py      — BgTaskMonitor
  audit_event_emitter.py  — AuditEventEmitter
  conversation_state_manager.py — ConversationStateManager
  turnd_coordinator.py    — TurnCoordinator
  llm_turn_executor.py    — LlmTurnExecutor
  workflow_engine_adapter.py — WorkflowEngineAdapter
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from shared.llm_exceptions import LLMTransportError
from shared.logger import Logger

from agent.audit_event_emitter import AuditEventEmitter
from agent.bg_task_monitor import BG_FAILURE_THRESHOLD, BgTaskMonitor
from agent.context import AgentContext
from agent.conversation_state_manager import ConversationStateManager
from agent.diagnostic_store import DiagnosticStore
from agent.llm_turn_executor import LlmTurnExecutor
from agent.llm_turn_runner import LLMTurnRunner
from agent.mode_classification import classify_and_inject_mode
from agent.output_tags import OutputTag
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from agent.turnd_coordinator import TurnCoordinator
from agent.workflow import (
    StateStore,
    TaskRecord,
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

    A thin composition facade over six extracted concern classes (see module
    docstring) — this class wires them together and preserves the previous
    private-method surface as delegating wrappers for backward compatibility.
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
        on_llm_wait_start: Callable[[], Any] | None = None,
        on_llm_wait_end: Callable[[], None] | None = None,
        tracer: Any = None,
        pause_on_critical_failure: bool = False,
    ):
        self._ctx = ctx
        self._allowed_tools = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end
        self._tracer = tracer
        self._pause_on_critical_failure = pause_on_critical_failure
        self._diagnostic_store = DiagnosticStore()
        ctx.diagnostics = self._diagnostic_store
        self._guard = ToolLoopGuard(ctx)
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._state_store = StateStore()
        self._state_store.recover_stale_attempts(self._state_store.get_connection())
        self._llm_runner = LLMTurnRunner(
            ctx,
            self._guard,
            tracer=tracer,
        )
        try:
            self._workflow_def: WorkflowDef | None = WorkflowLoader().load()
        except (WorkflowLoadError, FileNotFoundError) as exc:
            raise RuntimeError(
                f"{OutputTag.WORKFLOW} WorkflowLoader failed: {exc}. Expected definition at: {WORKFLOWS_DIR / 'default.json'}."
            ) from exc

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
            on_llm_wait_start=on_llm_wait_start,
            on_llm_wait_end=on_llm_wait_end,
        )
        self._conversation_manager = ConversationStateManager(
            ctx,
            diagnostic_store=self._diagnostic_store,
            tasks=self._background_tasks,
            on_discard=self._on_discard,
            tracer=tracer,
            on_first_turn=on_first_turn,
            on_turn_start=on_turn_start,
            on_turn_end=on_turn_end,
            on_error=on_error,
        )
        self._llm_executor = LlmTurnExecutor(
            ctx,
            diagnostic_store=self._diagnostic_store,
            tracer=tracer,
            on_turn_start=on_turn_start,
            on_turn_end=on_turn_end,
            on_error=on_error,
            on_llm_wait_start=on_llm_wait_start,
            on_llm_wait_end=on_llm_wait_end,
        )
        self._workflow_adapter = WorkflowEngineAdapter(
            ctx,
            state_store=self._state_store,
            workflow_engine=WorkflowEngine(
                self._workflow_def,
                self._state_store,
                tracer=tracer,
            ),
            conversation_manager=self._conversation_manager,
            llm_executor=self._llm_executor,
            diagnostic_store=self._diagnostic_store,
            tracer=tracer,
            on_error=on_error,
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

    # ── Backward-compatible delegating wrappers ─────────────────────────────
    # Preserve the pre-refactor private method/attribute surface that existing
    # tests call directly on an Orchestrator instance. Methods with no direct
    # external caller (confirmed via `rg` against tests/ and scripts/) are not
    # wrapped here — call the owning component directly instead.

    def _clear_previous_turn_ephemeral_messages(self) -> None:
        return self._conversation_manager.clear_previous_turn_ephemeral_messages()

    def _sync_system_prompt(self) -> None:
        return self._conversation_manager.sync_system_prompt()

    async def _append_user_message(self, line: str) -> None:
        return await self._conversation_manager.append_user_message(line)

    async def _handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None, bool]:
        return await self._workflow_adapter.execute_turn(line, turn_started_at, "")

    async def _process_turn(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None, bool]:
        """Process a turn and return (answer, error_kind, is_partial)."""
        answer = ""
        error_kind = None
        is_partial = False

        with self._tool_override(self._allowed_tools):
            self._clear_previous_turn_ephemeral_messages()
            await self._conversation_manager.handle_memory_injection(line)
            await classify_and_inject_mode(line, ctx)
            await self._append_user_message(line)
            await self._conversation_manager.handle_history_compression()

            result: TurnResult = await self._llm_executor.handle_llm_turn(
                ctx.conv.llm_url
            )
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

    def _init_workflow_task(
        self,
        ctx: AgentContext,
        session_id: str,
        existing_task_id: str | None = None,
        store: StateStore | None = None,
    ) -> tuple[str, TaskRecord]:
        return self._workflow_adapter._init_workflow_task(
            ctx, session_id, existing_task_id, store
        )

    def _activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        return self._workflow_adapter._activate_workflow(ctx, task)

    def _deactivate_workflow(self, ctx: AgentContext) -> None:
        return self._workflow_adapter._deactivate_workflow(ctx)

    async def _handle_memory_injection(self, line: str) -> None:
        return await self._conversation_manager.handle_memory_injection(line)

    async def _handle_history_compression(self) -> None:
        return await self._conversation_manager.handle_history_compression()

    def _discard_and_log(self, task: asyncio.Task[Any]) -> None:
        return self._bg_task_monitor.on_task_done(task)

    @property
    def _bg_pause_state(self) -> dict[str, bool]:
        return self._bg_task_monitor.bg_pause_state

    @_bg_pause_state.setter
    def _bg_pause_state(self, value: dict[str, bool]) -> None:
        self._bg_task_monitor._bg_pause_state = value

    @property
    def _consecutive_bg_failures(self) -> int:
        return self._bg_task_monitor.get_consecutive_failures("unknown_bg_task")

    @_consecutive_bg_failures.setter
    def _consecutive_bg_failures(self, value: int) -> None:
        self._bg_task_monitor.reset_consecutive_failures("unknown_bg_task")
