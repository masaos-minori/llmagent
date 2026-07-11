#!/usr/bin/env python3
"""agent/orchestrator.py
Turn-level orchestration facade.

Delegates LLM streaming and tool-loop guarding to:
  llm_turn_runner.py  — LLMTurnRunner (streaming + inner tool-call loop)
  tool_loop_guard.py  — ToolLoopGuard + TurnLoopState (dedup/cycle/retry/error guards)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable
from typing import Any

import orjson
from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.llm_transport_errors import handle_llm_transport_error
from agent.llm_turn_runner import LLMTurnRunner
from agent.mdq_rag_classifier import MdqRagMode
from agent.mode_classification import classify_and_inject_mode
from agent.tool_audit import (
    audit_approval_requested,
    audit_stage_completed,
    audit_workflow_start,
)
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from agent.workflow import (
    StateStore,
    WorkflowDef,
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowLoader,
    WorkflowLoadError,
    WorkflowPendingApprovalError,
)
from agent.workflow.task_ops import create_task, get_task_by_id
from agent.workflow.workflow_loader import WORKFLOWS_DIR
from shared.json_utils import dumps as _json_dumps
from shared.llm_exceptions import LLMTransportError
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _mode_hint(mode: MdqRagMode) -> str:
    if mode == MdqRagMode.MDQ:
        return "For this query, prefer MDQ tools (search_docs, outline, get_chunk) for Markdown-structural retrieval."
    if mode == MdqRagMode.RAG:
        return "For this query, prefer RAG tools (rag_run_pipeline) for semantic/general retrieval."
    return ""


def _format_session_id(session_id: int | None) -> str:
    """Format session_id for audit logs, returning empty string when None."""
    return str(session_id) if session_id is not None else ""


def _build_turn_end_metadata(
    ctx: AgentContext,
) -> dict[str, str]:
    """Build turn_end metadata (task_id, workflow_id, session_id)."""
    return {
        "task_id": ctx.turn.current_turn_id or "",
        "workflow_id": ctx.workflow.workflow_id or "",
        "session_id": _format_session_id(ctx.session.session_id),
    }


def _build_turn_end_llm_stats(
    llm: Any,
) -> dict[str, int]:
    """Build turn_end LLM stats fields."""
    return {
        "parse_error_count": llm.stat_parse_errors if llm is not None else 0,
        "heartbeat_timeout_count": llm.stat_heartbeat_timeouts
        if llm is not None
        else 0,
        "reconnect_count": llm.stat_reconnects if llm is not None else 0,
    }


class Orchestrator:
    """Turn-level coordinator: compression -> LLM loop -> tool dispatch.

    Receives AgentContext (shared state) at construction. All terminal output
    and side effects are routed via optional callbacks so this class has no
    direct I/O dependency.
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
    ) -> None:
        self._ctx = ctx
        self._allowed_tools: list[str] | None = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end
        self._tracer = tracer
        self._diagnostic_store = DiagnosticStore()
        ctx.diagnostics = self._diagnostic_store
        self._guard = ToolLoopGuard(ctx)
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._llm_runner = LLMTurnRunner(
            ctx,
            self._guard,
            tracer=tracer,
        )
        try:
            self._workflow_def: WorkflowDef | None = WorkflowLoader().load()
        except (WorkflowLoadError, Exception) as exc:
            raise RuntimeError(
                f"[workflow] WorkflowLoader failed: {exc}. "
                f"Expected definition at: {WORKFLOWS_DIR / 'default.json'}."
            ) from exc

    # ── Public entry point ────────────────────────────────────────────────────

    def _log_fallback(self, reason: str) -> None:
        raise RuntimeError(f"[workflow] Workflow unavailable: {reason}.")

    def workflow_status(self) -> dict[str, str]:
        """Return public workflow status for display purposes."""
        return {
            "mode": "active" if self._workflow_def is not None else "disabled",
            "tracking": "enabled" if self._workflow_def is not None else "not_loaded",
        }

    async def handle_turn(self, line: str) -> None:
        """Call LLM with the user message and persist to DB."""
        ctx = self._ctx
        # Guard: block LLM processing while a workflow approval is pending
        if ctx.workflow.approval_pending:
            logger.warning(
                "Turn blocked: workflow pending approval. Use /approve %s or /reject %s.",
                ctx.turn.pending_approval_id,
                ctx.turn.pending_approval_id,
            )
            if self._on_error:
                self._on_error(
                    RuntimeError(
                        f"[workflow] Approval is pending — use /approve {ctx.turn.pending_approval_id} [reason] "
                        f"or /reject {ctx.turn.pending_approval_id} [reason]."
                    )
                )
            return
        turn_started_at = time.perf_counter()

        await self._handle_turn_start(line)

        if self._workflow_def is None:
            self._log_fallback("workflow definition not loaded")
        await self._handle_workflow_engine(line, ctx, turn_started_at)

    async def _handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> None:
        """Execute a turn through the workflow engine."""
        assert self._workflow_def is not None  # noqa: B101 only called when workflow_def exists
        session_id = _format_session_id(ctx.session.session_id) or "none"
        store = StateStore()
        answer: str = ""
        error_kind: str | None = None
        is_partial: bool = False
        try:
            (
                workflow_id,
                task,
            ) = self._init_workflow_task(
                ctx, session_id, ctx.turn.pending_approval_task_id
            )
            # Clear pending approval task ID after retrieval
            ctx.turn.pending_approval_task_id = None
            self._activate_workflow(ctx, task)
            engine = WorkflowEngine(
                self._workflow_def,
                store,
                tracer=self._tracer,
            )

            async def plan_fn() -> str | None:
                return None  # _handle_turn_start already completed

            async def execute_fn() -> str | None:
                nonlocal answer, error_kind, is_partial
                answer, error_kind, is_partial = await self._process_turn(
                    line, ctx, turn_started_at
                )
                elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
                audit_stage_completed(
                    ctx,
                    task.task_id,  # type: ignore[attr-defined]
                    "execute",
                    elapsed_ms,
                    workflow_id=workflow_id,
                    session_id=session_id,
                )
                return None

            async def verify_fn() -> str | None:
                await self._handle_turn_end(
                    line, answer, turn_started_at, error_kind, is_partial
                )
                return None

            await engine.run(task, plan_fn, execute_fn, verify_fn)
        except WorkflowPendingApprovalError as exc:
            self._handle_workflow_approval_pending(exc, session_id)
        except WorkflowHaltError as exc:
            self._handle_workflow_halt(exc)
        finally:
            self._deactivate_workflow(ctx)
            store.close()

    def _init_workflow_task(
        self, ctx: AgentContext, session_id: str, existing_task_id: str | None = None
    ) -> tuple[str, object]:
        """Create a workflow task and audit its start.

        If existing_task_id is provided, use that task instead of creating a new one.
        """
        assert self._workflow_def is not None  # noqa: B101
        if existing_task_id is None:
            workflow_id = str(uuid.uuid4())
            store = StateStore()
            try:
                task = create_task(
                    store._db,
                    session_id=session_id,
                    turn_number=ctx.stats.stat_turns,
                    workflow_version=self._workflow_def.version,
                    workflow_id=workflow_id,
                )
            finally:
                store.close()
            audit_workflow_start(
                ctx,
                task.task_id,
                self._workflow_def.version,
                workflow_id=workflow_id,
                session_id=session_id,
            )
        else:
            store = StateStore()
            _fetched = get_task_by_id(store._db, existing_task_id)
            if _fetched is None:
                raise RuntimeError(f"Task {existing_task_id} not found")
            task = _fetched
            workflow_id = task.workflow_id or str(uuid.uuid4())
            store.close()
        return workflow_id, task

    def _activate_workflow(self, ctx: AgentContext, task: object) -> None:
        """Set workflow state to active."""
        ctx.workflow.current_task_id = task.task_id  # type: ignore[attr-defined]
        ctx.workflow.workflow_id = task.workflow_id  # type: ignore[attr-defined]
        ctx.workflow.current_workflow_version = self._workflow_def.version  # type: ignore[union-attr]
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
        from agent.tool_output import emit_approval_pending_notice  # noqa: PLC0415

        emit_approval_pending_notice(
            approval_id=exc.approval_id,
            task_id=exc.task_id or "unknown",
        )
        logger.warning(
            "[workflow] Approval required. Use /approve %s [reason] or /reject %s [reason].",
            exc.approval_id,
            exc.approval_id,
        )

    def _handle_workflow_halt(self, exc: WorkflowHaltError) -> None:
        """Handle workflow halt event."""
        ctx = self._ctx
        logger.error("Turn halted by workflow engine: %s", exc)
        ctx.workflow.active = False
        ctx.workflow.current_task_id = None
        ctx.workflow.workflow_id = None
        if self._on_error:
            self._on_error(exc)

    # ── Turn lifecycle ────────────────────────────────────────────────────────

    async def _handle_turn_start(self, line: str) -> None:
        ctx = self._ctx
        ctx.turn.current_turn_id = str(uuid.uuid4())
        session_id = _format_session_id(ctx.session.session_id) or "none"
        if ctx.services_required.audit_logger is not None:
            ctx.services_required.audit_logger.info(
                orjson.dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.turn.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ).decode(),
            )

    async def _handle_memory_injection(self, line: str) -> None:
        ctx = self._ctx
        if ctx.services_required.memory is not None:
            memory_snippets = await ctx.services_required.memory.on_user_prompt(
                query=line,
                session_id=ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "[Relevant memories]\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                ctx.conv.history.append(
                    {
                        "role": "system",
                        "content": memory_block,
                        "_memory_injected": True,
                    }
                )

    async def _handle_history_compression(self) -> None:
        ctx = self._ctx
        with self._llm_runner._span_ctx("compress"):
            ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(
                ctx.conv.history
            )
            if (
                result.compressed_count > 0
                or result.summary_added
                or result.is_fallback
            ):
                ctx.session.replace_messages(
                    [
                        m
                        for m in ctx.conv.history
                        if not m.get("_memory_injected") and not m.get("_ephemeral")
                    ]
                )

    async def _handle_llm_turn(self, llm_url: str) -> TurnResult:
        ctx = self._ctx
        try:
            if self._on_llm_wait_start:
                await self._on_llm_wait_start()
            if self._on_turn_start:
                self._on_turn_start()
            with self._llm_runner._span_ctx("llm") as llm_span:
                llm_span.set_attribute("model_url", llm_url)
                result = await self._llm_runner.run(
                    llm_url,
                    workflow_id=ctx.workflow.workflow_id or "",
                    task_id=ctx.workflow.current_task_id or "",
                    stage_id="execute",
                    attempt_id=ctx.turn.current_turn_id or "",
                )
                logger.info("LLM response: %s", result.answer)
                if result.persist_as_assistant:
                    ctx.session.save("assistant", result.answer)
                if self._on_llm_wait_end:
                    self._on_llm_wait_end()
                if result.exception is not None:
                    # run() caught LLMTransportError internally; propagate callbacks
                    handle_llm_transport_error(
                        result.exception, ctx, self._diagnostic_store
                    )
                    if self._on_error:
                        self._on_error(result.exception)
                else:
                    if self._on_turn_end:
                        self._on_turn_end()
                return result
        except LLMTransportError as e:
            # Reached when run() is mocked with side_effect=e (tests) or re-raises
            handle_llm_transport_error(e, ctx, self._diagnostic_store)
            if self._on_llm_wait_end:
                self._on_llm_wait_end()
            if self._on_error:
                self._on_error(e)
            return TurnResult(
                action="fail",
                answer="",
                error_kind=str(e),
                exception=e,
                persist_as_assistant=False,
            )

    async def _process_turn(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None, bool]:
        """Process a turn and return (answer, error_kind, is_partial)."""
        answer = ""
        error_kind = None
        is_partial = False

        # Snapshot original and apply override for this turn
        original_allowed = ctx.cfg.tool.allowed_tools
        if self._allowed_tools is not None:
            ctx.cfg.tool.allowed_tools = self._allowed_tools
        try:
            await self._handle_memory_injection(line)
            classify_and_inject_mode(line, ctx)
            self._append_user_message(line)
            await self._handle_history_compression()

            result = await self._handle_llm_turn(ctx.conv.llm_url)
            answer = result.answer
            if result.action != "continue":
                error_kind = result.error_kind
                if (
                    isinstance(result.exception, LLMTransportError)
                    and result.exception.partial_text
                ):
                    is_partial = True

        finally:
            ctx.cfg.tool.allowed_tools = original_allowed  # always restore

        return answer, error_kind, is_partial

    async def _handle_turn_end(
        self,
        line: str,
        answer: str,
        turn_started_at: float,
        error_kind: str | None,
        is_partial: bool = False,
    ) -> None:
        ctx = self._ctx
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services_required.audit_logger is not None:
            event = self._build_turn_end_event(
                elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial
            )
            ctx.services_required.audit_logger.info(_json_dumps(event))
        ctx.turn.current_turn_id = None

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
            **_build_turn_end_metadata(ctx),
            "elapsed_ms": elapsed_ms,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            **_build_turn_end_llm_stats(ctx.services_required.llm),
            "partial_completion": is_partial,
            "error_kind": error_kind,
        }

    # ── User message helpers ──────────────────────────────────────────────────

    def _sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn.

        Also removes ephemeral system messages injected in the previous turn.
        """
        ctx = self._ctx
        # Remove ephemeral entries from the previous turn before rebuilding prompt
        ctx.conv.history = [
            m
            for m in ctx.conv.history
            if not m.get("_ephemeral") and not m.get("_memory_injected")
        ]
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            ctx.conv.history.insert(
                0, {"role": "system", "content": ctx.conv.system_prompt_content}
            )

    def _append_user_message(self, line: str) -> None:
        ctx = self._ctx
        self._sync_system_prompt()
        ctx.conv.history.append({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            _task = asyncio.create_task(self._on_first_turn(line))
            self._background_tasks.add(_task)
            _task.add_done_callback(self._background_tasks.discard)
        ctx.session.save("user", line)
