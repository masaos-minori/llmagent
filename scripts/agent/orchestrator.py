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
from datetime import UTC, datetime
from typing import Any

import orjson
from shared.json_utils import dumps as _json_dumps
from shared.llm_client import LLMTransportError
from shared.logger import Logger

from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.llm_turn_runner import LLMTurnRunner
from agent.mdq_rag_classifier import MdqRagMode, resolve_mode
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

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _mode_hint(mode: MdqRagMode) -> str:
    if mode == MdqRagMode.MDQ:
        return "For this query, prefer MDQ tools (search_docs, outline, get_chunk) for Markdown-structural retrieval."
    if mode == MdqRagMode.RAG:
        return "For this query, prefer RAG tools (rag_run_pipeline) for semantic/general retrieval."
    return ""


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
        tracer: Any = None,
        workflow_mode: str = "auto",
    ) -> None:
        self._ctx = ctx
        self._allowed_tools: list[str] | None = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._tracer = tracer
        self._workflow_mode = workflow_mode
        self._diagnostic_store = DiagnosticStore()
        ctx.diagnostics = self._diagnostic_store
        self._guard = ToolLoopGuard(ctx)
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._llm_runner = LLMTurnRunner(
            ctx,
            self._guard,
            tracer=tracer,
        )
        self._workflow_def: WorkflowDef | None = None
        if self._workflow_mode != "disabled":
            try:
                self._workflow_def = WorkflowLoader().load()
            except (WorkflowLoadError, Exception):
                logger.warning("WorkflowLoader failed — workflow tracking disabled")

    # ── Public entry point ────────────────────────────────────────────────────

    def _log_fallback(self, reason: str) -> None:
        """Log workflow fallback reason; raise in required mode."""
        if self._workflow_mode == "required":
            raise RuntimeError(
                f"Workflow mode=required but workflow unavailable: {reason}"
            )
        logger.warning(
            "Workflow tracking disabled (%s), falling back to direct execution", reason
        )

    async def handle_turn(self, line: str) -> None:
        """Call LLM with the user message and persist to DB."""
        ctx = self._ctx
        # Guard: block LLM processing while a workflow approval is pending
        if ctx.workflow.approval_pending:
            logger.warning(
                "Turn blocked: workflow pending approval. Use /approve or /reject."
            )
            if self._on_error:
                self._on_error(
                    RuntimeError(
                        "[workflow] Approval is pending — use /approve [reason] or /reject [reason]."
                    )
                )
            return
        turn_started_at = time.perf_counter()

        await self._handle_turn_start(line)

        answer: str = ""
        error_kind: str | None = None

        if self._workflow_mode == "disabled":
            logger.info("Workflow mode=disabled — direct execution")
            answer, error_kind = await self._process_turn(line, ctx, turn_started_at)
            await self._handle_turn_end(line, answer, turn_started_at, error_kind)
            return

        if self._workflow_def is None:
            self._log_fallback("workflow definition not loaded")
            answer, error_kind = await self._process_turn(line, ctx, turn_started_at)
            await self._handle_turn_end(line, answer, turn_started_at, error_kind)
            return

        session_id = str(ctx.session.session_id) if ctx.session.session_id else "none"
        store = StateStore()
        try:
            workflow_id = str(uuid.uuid4())
            task = store.create_task(
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
            ctx.workflow.current_task_id = task.task_id
            ctx.workflow.workflow_id = workflow_id
            ctx.workflow.current_workflow_version = self._workflow_def.version
            ctx.workflow.active = True
            engine = WorkflowEngine(self._workflow_def, store, tracer=self._tracer)

            async def plan_fn() -> str | None:
                return None  # _handle_turn_start already completed

            async def execute_fn() -> str | None:
                nonlocal answer, error_kind
                _t0 = time.perf_counter()
                answer, error_kind = await self._process_turn(
                    line, ctx, turn_started_at
                )
                elapsed_ms = round((time.perf_counter() - _t0) * 1000, 1)
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
                await self._handle_turn_end(line, answer, turn_started_at, error_kind)
                return None

            await engine.run(task, plan_fn, execute_fn, verify_fn)
            ctx.workflow.active = False
            ctx.workflow.current_task_id = None
            ctx.workflow.workflow_id = None
        except WorkflowPendingApprovalError as exc:
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
                "[workflow] Approval required. Use /approve [reason] or /reject [reason]."
            )
        except WorkflowHaltError as exc:
            logger.error("Turn halted by workflow engine: %s", exc)
            ctx.workflow.active = False
            ctx.workflow.current_task_id = None
            ctx.workflow.workflow_id = None
            if self._on_error:
                self._on_error(exc)
        finally:
            store.close()

    # ── Turn lifecycle ────────────────────────────────────────────────────────

    async def _handle_turn_start(self, line: str) -> None:
        ctx = self._ctx
        if ctx.services.hist_mgr is None:
            raise RuntimeError("hist_mgr service not initialized")
        ctx.turn.current_turn_id = str(uuid.uuid4())
        session_id = str(ctx.session.session_id) if ctx.session.session_id else "none"
        if ctx.services.audit_logger is not None:
            ctx.services.audit_logger.info(
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
        if ctx.services.memory is not None:
            memory_snippets = await ctx.services.memory.on_user_prompt(
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
                        "_memory_injected": True,  # type: ignore[typeddict-unknown-key]
                    }
                )

    async def _handle_note_injection(self, line: str) -> None:
        """Search notes by current query and inject relevant ones into history."""
        ctx = self._ctx
        if not ctx.cfg.tool.auto_inject_notes:
            return
        notes = ctx.session.search_notes(line, limit=3)
        if not notes:
            return
        note_block = "[Relevant Notes]\n" + "\n".join(
            f"- {n['content']}" for n in notes
        )
        ctx.conv.history.append(
            {
                "role": "system",
                "content": note_block,
                "_memory_injected": True,  # type: ignore[typeddict-unknown-key]
            }
        )

    async def _handle_history_compression(self) -> None:
        ctx = self._ctx
        if ctx.services.hist_mgr is None:
            raise RuntimeError("hist_mgr service not initialized")
        with self._llm_runner._span_ctx("compress"):
            ctx.conv.history, _ = await ctx.services.hist_mgr.compress(ctx.conv.history)

    async def _handle_llm_turn(self, llm_url: str) -> TurnResult:
        ctx = self._ctx
        try:
            if self._on_turn_start:
                self._on_turn_start()
            with self._llm_runner._span_ctx("llm") as llm_span:
                llm_span.set_attribute("model_url", llm_url)
                result = await self._llm_runner.run(llm_url)
                logger.info("LLM response: %s", result.answer)
                ctx.session.save("assistant", result.answer)
                if result.exception is not None:
                    # run() caught LLMTransportError internally; propagate callbacks
                    self._handle_llm_transport_error(result.exception, ctx)
                    if self._on_error:
                        self._on_error(result.exception)
                else:
                    if self._on_turn_end:
                        self._on_turn_end()
                return result
        except LLMTransportError as e:
            # Reached when run() is mocked with side_effect=e (tests) or re-raises
            self._handle_llm_transport_error(e, ctx)
            if self._on_error:
                self._on_error(e)
            return TurnResult(action="fail", answer="", error_kind=str(e), exception=e)

    async def _process_turn(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> tuple[str, str | None]:
        """Process a turn and return (answer, error_kind)."""
        answer = ""
        error_kind = None

        # Snapshot original and apply override for this turn
        original_allowed = ctx.cfg.tool.allowed_tools
        if self._allowed_tools is not None:
            ctx.cfg.tool.allowed_tools = self._allowed_tools
        try:
            await self._handle_memory_injection(line)
            await self._handle_note_injection(line)
            self._classify_and_inject_mode(line)
            self._append_user_message(line)
            await self._handle_history_compression()

            result = await self._handle_llm_turn(ctx.conv.llm_url)
            answer = result.answer
            if not result.success:
                error_kind = result.error_kind

        finally:
            ctx.cfg.tool.allowed_tools = original_allowed  # always restore

        return answer, error_kind

    async def _handle_turn_end(
        self, line: str, answer: str, turn_started_at: float, error_kind: str | None
    ) -> None:
        ctx = self._ctx
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services.audit_logger is not None:
            event = self._build_turn_end_event(
                elapsed_ms, error_kind, ctx.turn.current_turn_id
            )
            ctx.services.audit_logger.info(_json_dumps(event))
        ctx.turn.current_turn_id = None

    def _build_turn_end_event(
        self,
        elapsed_ms: float,
        error_kind: str | None,
        task_id: str | None,
    ) -> dict[str, object]:
        """Build turn_end audit log event dict."""
        ctx = self._ctx
        llm = ctx.services.llm
        return {
            "event": "turn_end",
            "task_id": task_id,
            "workflow_id": ctx.workflow.workflow_id or "",
            "session_id": str(ctx.session.session_id) if ctx.session.session_id else "",
            "elapsed_ms": elapsed_ms,
            "input_tokens": ctx.stats.stat_input_tokens,
            "output_tokens": ctx.stats.stat_output_tokens,
            "parse_error_count": llm.stat_parse_errors if llm is not None else 0,
            "heartbeat_timeout_count": (
                llm.stat_heartbeat_timeouts if llm is not None else 0
            ),
            "reconnect_count": llm.stat_reconnects if llm is not None else 0,
            "partial_completion": False,
            "error_kind": error_kind,
        }

    # ── User message helpers ──────────────────────────────────────────────────

    def _sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn.

        Also removes ephemeral system messages injected in the previous turn.
        """
        ctx = self._ctx
        # Remove ephemeral entries from the previous turn before rebuilding prompt
        ctx.conv.history = [m for m in ctx.conv.history if not m.get("_ephemeral")]
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            ctx.conv.history.insert(
                0, {"role": "system", "content": ctx.conv.system_prompt_content}
            )

    def _classify_and_inject_mode(self, query: str) -> None:
        """Inject MDQ/RAG routing hint into system prompt based on query classification."""
        ctx = self._ctx
        config_mode = getattr(ctx.cfg, "mdq_rag_mode", None)
        mode = resolve_mode(query, config_mode)
        if mode == MdqRagMode.MDQ:
            mdq_available = any(
                "search_docs" in (srv.tool_names or [])
                for srv in ctx.cfg.mcp.mcp_servers.values()
            )
            if not mdq_available:
                logger.warning(
                    "MDQ mode selected but mdq-mcp tools unavailable; falling back to RAG"
                )
                mode = MdqRagMode.RAG
        hint = _mode_hint(mode)
        if hint:
            ctx.conv.history.append(
                {"role": "system", "content": hint, "_ephemeral": True}  # type: ignore[typeddict-unknown-key]
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

    def _handle_llm_transport_error(
        self,
        e: LLMTransportError,
        ctx: AgentContext,
    ) -> bool:
        if e.partial_text:
            incomplete_msg = f"{e.partial_text}\n[INCOMPLETE: {e.kind}]"
            # Store in diagnostic channel only — do NOT add to conversation history
            self._diagnostic_store.save(
                ctx.session.session_id, "llm_transport_error", incomplete_msg
            )
            try:
                ctx.tool_result_store.store(
                    session_id=ctx.session.session_id,
                    turn=ctx.stats.stat_turns,
                    tool_name="llm_partial_completion",
                    args_masked="{}",
                    full_text=e.detail or f"partial={len(e.partial_text)} chars",
                    summary=f"[INCOMPLETE: {e.kind}]",
                    is_error=True,
                )
            except (RuntimeError, OSError) as store_err:
                logger.warning(
                    "ToolResultStore.store failed for partial completion: %s",
                    store_err,
                )
            if ctx.services.llm is not None:
                ctx.services.llm.stat_partial_completions += 1
            logger.warning("Partial LLM completion saved: %s", e.kind)
            return True
        self._diagnostic_store.save(
            ctx.session.session_id,
            "mid_turn_error",
            orjson.dumps(
                {
                    "action": "pre_stream_error",
                    "reason": "llm_transport_error_non_partial",
                    "error_kind": e.kind,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            ).decode(),
        )
        logger.error(
            "LLM transport error (pre-stream): %s status=%s",
            e.kind,
            e.status_code,
        )
        return False
