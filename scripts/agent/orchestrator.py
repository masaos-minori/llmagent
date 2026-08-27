#!/usr/bin/env python3
"""scripts/agent/orchestrator.py

Turn-level orchestration facade.

Delegates LLM streaming and tool-loop guarding to:
  llm_turn_runner.py  — LLMTurnRunner (streaming + inner tool-call loop)
  tool_loop_guard.py  — ToolLoopGuard + TurnLoopState (dedup/cycle/retry/error guards)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from shared.json_utils import dumps as _json_dumps
from shared.llm_exceptions import LLMTransportError
from shared.logger import Logger
from shared.types import LLMMessage

from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.llm_transport_errors import handle_llm_transport_error
from agent.llm_turn_runner import LLMTurnRunner
from agent.mdq_rag_classifier import MdqRagMode
from agent.message_schema import validate_message
from agent.mode_classification import classify_and_inject_mode
from agent.output_tags import OutputTag
from agent.tool_audit import (
    audit_approval_requested,
    audit_stage_completed,
    audit_workflow_start,
)
from agent.tool_loop_guard import ToolLoopGuard
from agent.turn_result import TurnResult
from agent.workflow import (
    StateStore,
    TaskRecord,
    WorkflowDef,
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowLoader,
    WorkflowLoadError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from agent.workflow.task_ops import create_task, get_task_by_id
from agent.workflow.workflow_loader import WORKFLOWS_DIR

# Threshold for the first-turn background task's consecutive-failure counter
# (see `_discard_and_log` / `self._consecutive_bg_failures`).
#
# - Effect: log-level selection only. Below this threshold, failures log via
#   `logger.warning`; at or above it, they log via `logger.error`. There is no
#   circuit-breaking or task-disabling behavior — the background task keeps
#   being scheduled on every first turn regardless of this counter's value.
# - Scope: applies only to the first-turn session-title-generation background
#   task (`self._on_first_turn`, scheduled from `_append_user_message`). It is
#   not a general-purpose background-task failure budget.
# - Reset semantics: the counter resets to 0 on a successful completion or on
#   `asyncio.CancelledError`; it is NOT reset by `/clear` or `/session load`
#   (see `_discard_and_log`'s docstring for why).
# - Configurability: evaluated and deferred. Moving this into `AgentConfig`
#   would require touching `config/agent.toml`, `config_dataclasses.py`,
#   `config_validators.py`, and `config_builders.py` in addition to this file,
#   which is disproportionate for a value whose only effect is a log-level
#   choice. If this is revisited, `ToolConfig.tool_error_max_consecutive`
#   (`scripts/agent/config_dataclasses.py:168`) is the copyable precedent for
#   wiring a similar threshold through config.
BG_FAILURE_THRESHOLD: int = 10

logger = Logger(__name__, "/opt/llm/logs/agent.log")


def _mode_hint(mode: MdqRagMode) -> str:
    """Return a human-readable hint about which tool category to use for the given mode."""
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
        "parse_error_count": getattr(llm, "stat_parse_errors", 0),
        "heartbeat_timeout_count": getattr(llm, "stat_heartbeat_timeouts", 0),
        "reconnect_count": getattr(llm, "stat_reconnects", 0),
    }


class Orchestrator:
    """Turn-level coordinator: compression -> LLM loop -> tool dispatch.

    Receives AgentContext (shared state) at construction. All terminal output
    and side effects are routed via optional callbacks so this class has no
    direct I/O dependency.
    """

    _EPHEMERAL_KEYS: frozenset[str] = frozenset(
        {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
    )

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
    ) -> None:
        """Initialize the orchestrator with context, callbacks, and diagnostic storage."""
        self._ctx = ctx
        self._allowed_tools: list[str] | None = allowed_tools
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error
        self._on_llm_wait_start = on_llm_wait_start
        self._on_llm_wait_end = on_llm_wait_end
        self._tracer = tracer
        # Opt-in: when True, a background task type is paused (see
        # `_bg_pause_state`) once its consecutive-failure count reaches
        # `BG_FAILURE_THRESHOLD`. Defaults to False so existing callers are
        # unaffected until they explicitly opt in.
        self._pause_on_critical_failure = pause_on_critical_failure
        # Per-task-type pause flags, keyed by `asyncio.Task.get_name()`. A
        # `True` entry blocks further `handle_turn()` processing until the
        # process is restarted (see `_notify_bg_failure_threshold` and the
        # guard at the top of `handle_turn`).
        self._bg_pause_state: dict[str, bool] = {}
        self._diagnostic_store = DiagnosticStore()
        ctx.diagnostics = self._diagnostic_store
        self._guard = ToolLoopGuard(ctx)
        self._background_tasks: set[asyncio.Task[object]] = set()
        # Startup recovery for stale running attempts
        self._state_store = StateStore()
        self._state_store.recover_stale_attempts(self._state_store.get_connection())
        # Scoped to a single background-task type today (the first-turn
        # session-title-generation task handled by `_discard_and_log`). Do not
        # reuse this single counter for a second, distinct background-task
        # type — give any new task type its own counter instead, since a
        # shared counter would conflate unrelated failure streams and distort
        # the log-level threshold in `_discard_and_log`.
        self._consecutive_bg_failures: int = 0
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

    # ── Public entry point ────────────────────────────────────────────────────

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
                        f"{OutputTag.WORKFLOW} Approval is pending — use /approve {ctx.turn.pending_approval_id} [reason] "
                        f"or /reject {ctx.turn.pending_approval_id} [reason]."
                    )
                )
            return
        # Guard: block turn processing while any background task type is
        # paused (only reachable when `pause_on_critical_failure=True` was
        # passed to __init__ and that task type has hit BG_FAILURE_THRESHOLD).
        if any(self._bg_pause_state.values()):
            paused = [
                name for name, is_paused in self._bg_pause_state.items() if is_paused
            ]
            logger.warning(
                "Turn blocked: agent paused due to background task failures: %s", paused
            )
            if self._on_error:
                self._on_error(
                    RuntimeError(
                        f"{OutputTag.WORKFLOW} Agent paused due to repeated failures in: {paused}. "
                        "Restart the process to clear pause state."
                    )
                )
            return
        turn_started_at = time.perf_counter()

        await self._handle_turn_start(line)

        # self._workflow_def is guaranteed non-None here: __init__() already raised
        # RuntimeError if WorkflowLoader().load() failed, so handle_turn() can only be
        # reached with a successfully loaded workflow definition.
        await self._handle_workflow_engine(line, ctx, turn_started_at)

    async def _handle_workflow_engine(
        self, line: str, ctx: AgentContext, turn_started_at: float
    ) -> None:
        """Execute a turn through the workflow engine."""
        assert self._workflow_def is not None  # noqa: B101 only called when workflow_def exists
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
            ) = self._init_workflow_task(
                ctx, session_id, ctx.turn.pending_approval_task_id, store
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
                """No-op placeholder: planning work is done by _handle_turn_start before engine.run()."""
                return None

            async def execute_fn() -> str | None:
                """Process the user turn via _process_turn and log stage completion."""
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
            self._deactivate_workflow(ctx)
            store.close()

    def _init_workflow_task(
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
        assert self._workflow_def is not None  # noqa: B101
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

    def _activate_workflow(self, ctx: AgentContext, task: TaskRecord) -> None:
        """Set workflow state to active."""
        ctx.workflow.current_task_id = task.task_id
        ctx.workflow.workflow_id = task.workflow_id
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
        from agent.tool_output import emit_approval_pending_notice

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

    # ── Turn lifecycle ────────────────────────────────────────────────────────

    async def _handle_turn_start(self, line: str) -> None:
        """Assign a turn ID and emit a turn_start audit event."""
        ctx = self._ctx
        ctx.turn.current_turn_id = str(uuid.uuid4())
        session_id = _format_session_id(ctx.session.session_id) or "none"
        if ctx.services_required.audit_logger is not None:
            ctx.services_required.audit_logger.info(
                _json_dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.turn.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ),
            )

    async def _handle_memory_injection(self, line: str) -> None:
        """Retrieve relevant memory snippets and inject them into conversation history."""
        ctx = self._ctx
        if ctx.services_required.memory is not None:
            memory_snippets = await ctx.services_required.memory.on_user_prompt(
                query=line,
                session_id=ctx.session.session_id,
            )
            if memory_snippets:
                memory_block = "--- USER MEMORY ---\n" + "\n".join(
                    f"- {snippet.text}" for snippet in memory_snippets
                )
                await ctx.conv.append_message(
                    {
                        "role": "system",
                        "content": memory_block,
                        "_memory_injected": True,
                    },
                    source="memory_injection",
                )

    async def _handle_history_compression(self) -> None:
        """Compress conversation history and replace messages if compression occurred.

        Note: ephemeral/memory-injected messages are NOT filtered here because
        _clear_previous_turn_ephemeral_messages() already strips them before every
        turn. Passing the full history avoids double-filtering.

        Note: the compressed history is also NOT routed through
        ConversationState.replace_history() — hist_mgr.compress() only produces
        role/content-only summary messages (see history.py's
        _build_summary_message()), which are already schema-conformant by
        construction, so re-validating here would be redundant.
        """
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
                ctx.session.replace_messages(ctx.conv.history)

    def _call_on_llm_wait_end(self) -> None:
        """Invoke on_llm_wait_end if configured."""
        if self._on_llm_wait_end:
            self._on_llm_wait_end()

    def _call_on_turn_end(self) -> None:
        """Invoke on_turn_end if configured."""
        if self._on_turn_end:
            self._on_turn_end()

    def _call_on_error(self, exc: Exception) -> None:
        """Invoke on_error with exc if configured."""
        if self._on_error:
            self._on_error(exc)

    async def _handle_llm_turn(self, llm_url: str) -> TurnResult:
        """Execute an LLM streaming turn with wait/start/end callbacks and error handling."""
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
                if result.exception is not None:
                    # run() caught LLMTransportError internally; propagate callbacks
                    handle_llm_transport_error(
                        result.exception, ctx, self._diagnostic_store
                    )
                    self._call_on_llm_wait_end()
                    self._call_on_error(result.exception)
                    self._call_on_turn_end()
                else:
                    self._call_on_llm_wait_end()
                    self._call_on_turn_end()
                return result
        except LLMTransportError as e:
            # Reached when run() is mocked with side_effect=e (tests) or re-raises
            handle_llm_transport_error(e, ctx, self._diagnostic_store)
            self._call_on_llm_wait_end()
            self._call_on_error(e)
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

        with self._tool_override(self._allowed_tools):
            self._clear_previous_turn_ephemeral_messages()
            await self._handle_memory_injection(line)
            await classify_and_inject_mode(line, ctx)
            await self._append_user_message(line)
            await self._handle_history_compression()

            result = await self._handle_llm_turn(ctx.conv.llm_url)
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

    def _clear_previous_turn_ephemeral_messages(self) -> None:
        """Strip ephemeral/memory-injected system messages left over from the
        previous turn. Must run before this turn's own injections
        (_handle_memory_injection, classify_and_inject_mode) so it never
        strips content just added for the current turn.
        """
        ctx = self._ctx
        ctx.conv.history = [
            m
            for m in ctx.conv.history
            if not any(k in self._EPHEMERAL_KEYS for k in m.keys())
        ]

    def _sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        ctx = self._ctx
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            msg: LLMMessage = {
                "role": "system",
                "content": ctx.conv.system_prompt_content,
            }
            result = validate_message(dict(msg))
            if not result.success:
                logger.error(
                    "Dropping system prompt sync message that failed validation: %s",
                    result.reason,
                )
                return
            ctx.conv.history.insert(0, msg)

    async def _append_user_message(self, line: str) -> None:
        """Append user message to history, sync system prompt, and increment turn counter."""
        ctx = self._ctx
        self._sync_system_prompt()
        await ctx.conv.append_message({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            _task = asyncio.create_task(
                self._on_first_turn(line),
                name=getattr(self._on_first_turn, "__name__", "unknown_bg_task"),
            )
            self._background_tasks.add(_task)

            _task.add_done_callback(self._discard_and_log)
        ctx.session.save("user", line)

    def _discard_and_log(self, task: asyncio.Task[Any]) -> None:
        """Callback for first-turn background task completion.

        Cross-session accumulation: `self._consecutive_bg_failures` can span
        multiple `/clear` / `/session load` cycles within one process
        lifetime. `Orchestrator` is a long-lived singleton constructed once
        (`startup.py:117`) and reused across
        `conversation_service.clear_conversation` and
        `agent/services/session_restore.py:46` — neither of those reset
        points touches this counter, so a failure streak that started before
        a `/clear` or session switch continues to count toward
        `BG_FAILURE_THRESHOLD` afterward. Only a successful
        completion or an `asyncio.CancelledError` completion of this
        callback resets it to 0.
        """
        task_name = task.get_name()
        exc = task.exception()
        if exc is not None:
            if isinstance(exc, asyncio.CancelledError):
                # Task was cancelled — reset counter, do not log as error.
                self._consecutive_bg_failures = 0
            else:
                self._consecutive_bg_failures += 1
                if self._consecutive_bg_failures == 1:
                    logger.warning(
                        "First background task failure (%s): %s", task_name, exc
                    )
                    # Surface first-turn failure to user immediately
                    if isinstance(exc, Exception) and self._on_error is not None:
                        try:
                            self._on_error(exc)
                        except Exception as notif_err:  # noqa: BLE001 — caller-supplied error callback must not raise and crash the background-task monitor
                            logger.error(
                                "Failed to notify user of background task failure: %s",
                                notif_err,
                            )
                elif self._consecutive_bg_failures >= BG_FAILURE_THRESHOLD:
                    if (
                        self._consecutive_bg_failures == BG_FAILURE_THRESHOLD
                        or (self._consecutive_bg_failures - BG_FAILURE_THRESHOLD) % 5
                        == 0
                    ):
                        logger.error(
                            "Consecutive background task failures (%d) for '%s': %s",
                            self._consecutive_bg_failures,
                            task_name,
                            exc,
                        )
                        if self._consecutive_bg_failures == BG_FAILURE_THRESHOLD:
                            self._notify_bg_failure_threshold(
                                task_name, self._consecutive_bg_failures
                            )
                    else:
                        logger.warning(
                            "Background task failure #%d (%s): %s",
                            self._consecutive_bg_failures,
                            task_name,
                            exc,
                        )
        else:
            # Task completed successfully — reset counter
            self._consecutive_bg_failures = 0
        self._background_tasks.discard(task)

    def _notify_bg_failure_threshold(self, task_name: str, count: int) -> None:
        """Guarantee the user is notified when a background task hits the failure threshold."""
        message = RuntimeError(
            f"Background task '{task_name}' has failed {count} consecutive times "
            f"(threshold: {BG_FAILURE_THRESHOLD})."
        )
        if self._on_error is not None:
            try:
                self._on_error(message)
            except Exception as notif_err:  # noqa: BLE001 — caller-supplied error callback must not raise and crash the background-task monitor
                logger.critical(
                    "Failed to notify user of threshold breach for '%s': %s",
                    task_name,
                    notif_err,
                )
        else:
            logger.critical(str(message))
        if self._pause_on_critical_failure:
            self._bg_pause_state[task_name] = True
            logger.warning(
                "Background task type '%s' paused after reaching threshold.", task_name
            )
