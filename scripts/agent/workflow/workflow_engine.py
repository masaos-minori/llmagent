#!/usr/bin/env python3
"""scripts/agent/workflow/workflow_engine.py

Stage transition engine: plan -> execute -> verify -> (retry loop).

Callers pass async callbacks for each stage. WorkflowEngine handles
timeout enforcement, retry counting, idempotency, and state persistence.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from typing import Protocol

from shared.mcp_dedup import load_dedup_config

from agent.workflow.artifact_ops import record_artifact
from agent.workflow.idempotency_ops import begin_stage_if_new
from agent.workflow.models import TaskRecord, WorkflowDef
from agent.workflow.state_store import StateStore

logger = logging.getLogger(__name__)

_ERROR_KIND_TIMEOUT = "timeout"
_ERROR_KIND_EXCEPTION = "exception"
_ERROR_KIND_LLM_FAILURE = "llm_failure"

# Lease horizon added on top of a stage's enforced timeout (wflease001
# REQ-005, Plan UNK-03: named constant, not configuration). A normal stage
# is bounded by the asyncio.timeout deadline, so the lease only outlives the
# stage by this margin; no heartbeat renewal exists (Plan UNK-02).
_LEASE_MARGIN_SEC = 30

StageCallback = Callable[[], Awaitable[str | None]]  # returns artifact URI or None


class _Span(Protocol):
    """Protocol for OTel span-like objects."""

    def start_as_current_span(self, name: str) -> _Span:
        """Start a new child span and enter it as the current span."""
        ...

    def set_attribute(self, key: str, value: object) -> None:
        """Set an attribute on the span."""
        ...

    def record_exception(self, exc: BaseException) -> None:
        """Record an exception on the span."""
        ...

    def __enter__(self) -> _Span: ...

    def __exit__(self, *args: object) -> None: ...


class _NoOpSpan(_Span):
    """No-op OTel span used when no tracer is configured."""

    def start_as_current_span(self, name: str) -> _Span:
        """Return self as a no-op span."""
        return self

    def set_attribute(self, key: str, value: object) -> None:
        """No-op; ignores the attribute."""
        pass

    def record_exception(self, exc: BaseException) -> None:
        """No-op; ignores the exception."""
        pass

    def __enter__(self) -> _Span:
        """Return self as context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """No-op exit handler."""
        pass


class WorkflowHaltError(Exception):
    """Raised when a task exceeds max_attempts and is halted."""


class WorkflowTimeoutError(Exception):
    """Raised when a stage exceeds its timeout_sec."""


class WorkflowStageFailure(Exception):
    """Raised when a stage callback reports a typed failure result (kind llm_failure).

    Carries the (answer, error_kind, is_partial) values so the adapter can convert
    the failure back to the outward typed tuple at its boundary. Outward kinds
    (workflow_timeout, workflow_halted) are turn-level and are never persisted
    to attempts.error_kind (REQ-007 / AC-7).
    """

    def __init__(
        self,
        message: str = "stage failure",
        *,
        kind: str = _ERROR_KIND_LLM_FAILURE,
        answer: str | None = None,
        error_kind: str | None = None,
        is_partial: bool = False,
    ) -> None:
        """Initialize the stage failure with its persisted kind and typed values."""
        super().__init__(message)
        self.kind = kind
        self.answer = answer
        self.error_kind = error_kind
        self.is_partial = is_partial


class WorkflowEngine:
    """Runs a workflow definition against a set of stage callbacks.

    The workflow has no approval stage. Human approval is decided before a Tool
    executes (tool_approval.run_approval_checks), during the execute stage, for
    MEDIUM/HIGH risk tools.
    """

    def __init__(
        self,
        workflow_def: WorkflowDef,
        store: StateStore,
        tracer: _Span | None = None,
    ) -> None:
        """Initialize the workflow engine with its definition, state store, and optional tracer."""
        self._wdef = workflow_def
        self._store = store
        self._tracer = tracer

    @property
    def version(self) -> str:
        """The workflow definition version, exposed so callers avoid reading _wdef."""
        return self._wdef.version

    def _span_ctx(self, name: str) -> _Span | nullcontext[_NoOpSpan]:
        """Return a span context manager; uses NoOpSpan when no tracer is available."""
        if self._tracer is not None:
            return self._tracer.start_as_current_span(name)
        return nullcontext(_NoOpSpan())

    def build_turn_control_message(self, task_id: str) -> str | None:
        """Build the replay control message for a task's interrupted tool calls.

        Turn-entry detection (toolexec001 REQ-008): stale pending rows are first
        classified to 'interrupted' (timeout from the dispatcher-side dedup config),
        then interrupted rows are listed — retryable ones with a re-issue instruction,
        non-retryable ones as unreplayable status text the LLM must report rather than
        replay (the dispatcher's ``dedup_unreplayable`` refusal semantics, row 04).

        Detection must not raise into the turn path: on store or config errors the
        turn proceeds with no control message (the dispatcher's own dedup still
        guards execution). No interrupted rows -> None -> byte-identical turn
        behavior (REQ-010). Fresh pending rows (within the timeout window) are not
        listed: they may still belong to a call in flight, and re-issuing them could
        duplicate live work.
        """
        try:
            timeout_seconds = load_dedup_config().pending_timeout_minutes * 60
            interrupted = self._store.classify_stale_pending(task_id, timeout_seconds)
        except Exception as exc:  # noqa: BLE001 — turn availability beats replay accuracy; the dispatcher dedup still guards execution
            logger.warning(
                "Tool-call state detection failed for task %s (%s); proceeding without control message",
                task_id,
                exc,
            )
            return None
        replayable = [c for c in interrupted if c.retry_class == "retryable"]
        unreplayable = [c for c in interrupted if c.retry_class != "retryable"]
        if not replayable and not unreplayable:
            return None
        lines = ["[tool-call replay control]"]
        if replayable:
            lines.append(
                "The following tool calls from a previous turn were interrupted."
                " Re-issue each call with the identical tool name and identical arguments;"
                " the dispatcher replays or deduplicates them by the recorded key."
            )
            lines.extend(
                f"- replay: tool={c.tool} idempotency_key={c.idempotency_key} state=interrupted"
                for c in replayable
            )
        if unreplayable:
            lines.append(
                "The following interrupted calls are NOT replayable. Do not re-issue them;"
                " tell the user they require manual action (unreplayable: manual action required)."
            )
            lines.extend(
                f"- unreplayable: tool={c.tool} idempotency_key={c.idempotency_key} state=interrupted"
                for c in unreplayable
            )
        return "\n".join(lines)

    async def run(
        self,
        task: TaskRecord,
        plan_fn: StageCallback,
        execute_fn: StageCallback,
        verify_fn: StageCallback,
    ) -> None:
        """Execute plan -> execute -> verify with retry on execute failure."""
        with self._span_ctx("workflow.run") as span:
            span.set_attribute("workflow.task_id", task.task_id)
            span.set_attribute("workflow.version", task.workflow_version)
            span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            span.set_attribute("workflow.session_id", task.session_id or "")
            self._store.update_task_status(task.task_id, "running")
            try:
                await self._run_stage_with_retry(task, "plan", plan_fn)
                await self._run_stage_with_retry(task, "execute", execute_fn)
                await self._run_stage_with_retry(task, "verify", verify_fn)
            except (WorkflowHaltError, WorkflowTimeoutError):
                self._store.update_task_status(task.task_id, "halted")
                raise
            except Exception:  # noqa: BLE001 — catch-all to mark task failed before re-raising
                self._store.update_task_status(task.task_id, "failed")
                raise
            self._store.update_task_status(task.task_id, "completed")

    async def _run_stage_with_retry(
        self, task: TaskRecord, stage_id: str, fn: StageCallback
    ) -> None:
        """Run a stage once, or with retry up to max_attempts on failure.

        Whether retries apply is gated on the stage's own `retryable` flag
        (config/workflows/*.json), not hardcoded to a specific stage_id.
        """
        stage_def = self._wdef.get_stage(stage_id)
        if stage_def is None or not stage_def.retryable:
            await self._run_stage(task, stage_id, fn)
            return

        policy = self._wdef.retry_policy
        attempt = 0
        while True:
            attempt += 1
            try:
                await self._run_stage(task, stage_id, fn, attempt=attempt)
                return
            except WorkflowHaltError:
                # Halts raised by the stage callback itself are terminal (REQ-006 / AC-6).
                raise
            except Exception as exc:  # noqa: BLE001 — catch-all to apply retry/halt logic before re-raising
                if isinstance(exc, WorkflowTimeoutError):
                    kind = _ERROR_KIND_TIMEOUT
                elif isinstance(exc, WorkflowStageFailure):
                    kind = _ERROR_KIND_LLM_FAILURE
                else:
                    kind = _ERROR_KIND_EXCEPTION
                if kind not in policy.retry_on:
                    # Terminal kind: propagate the original exception at once;
                    # run() writes the task status (REQ-003 / AC-3).
                    raise
                if attempt >= policy.max_attempts:
                    logger.error(
                        "Task %s: %s halted after %d attempts: %s",
                        task.task_id,
                        stage_id,
                        attempt,
                        exc,
                    )
                    raise WorkflowHaltError(
                        f"{stage_id} stage halted after {attempt} attempts"
                    ) from exc
                wait = policy.backoff_sec
                logger.warning(
                    "Task %s: %s attempt %d failed, retrying in %ds: %s",
                    task.task_id,
                    stage_id,
                    attempt,
                    wait,
                    exc,
                )
                with self._span_ctx("workflow.retry") as retry_span:
                    retry_span.set_attribute(
                        "workflow.workflow_id", task.workflow_id or ""
                    )
                    retry_span.set_attribute("workflow.task_id", task.task_id)
                    retry_span.set_attribute("workflow.stage_id", stage_id)
                    retry_span.set_attribute("retry.attempt", attempt)
                    retry_span.set_attribute("retry.max_attempts", policy.max_attempts)
                    retry_span.set_attribute("retry.error_type", type(exc).__name__)
                await asyncio.sleep(wait)

    async def _run_stage(
        self,
        task: TaskRecord,
        stage_id: str,
        fn: StageCallback,
        attempt: int = 1,
    ) -> None:
        """Run a single stage with idempotency check and timeout enforcement.

        Note: Retry attempts use distinct event IDs in the format
        '{task_id}:{stage_id}:{attempt}' where attempt is a 1-based
        integer incremented for each retry. Each retry is treated as
        a separate idempotency record.
        """
        with self._span_ctx("workflow.stage") as span:
            span.set_attribute("workflow.stage_id", stage_id)
            span.set_attribute("workflow.attempt", attempt)
            span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            stage_def = self._wdef.get_stage(stage_id)
            timeout = stage_def.timeout_sec if stage_def else 60
            event_id = f"{task.task_id}:{stage_id}:{attempt}"

            attempt_rec = begin_stage_if_new(
                self._store.get_connection(),
                event_id,
                task.task_id,
                stage_id,
                workflow_id=task.workflow_id,
                lease_duration_sec=timeout + _LEASE_MARGIN_SEC,
            )
            if attempt_rec is None:
                logger.info(
                    "Stage %s skipped (already processed): %s", stage_id, event_id
                )
                return

            try:
                async with asyncio.timeout(timeout) as deadline:
                    artifact_uri = await fn()
            except WorkflowStageFailure as exc:
                self._store.finish_attempt(
                    attempt_rec.attempt_id,
                    "failed",
                    error_msg=str(exc),
                    error_kind=_ERROR_KIND_LLM_FAILURE,
                    error_detail=repr(exc),
                )
                raise
            except TimeoutError as exc:
                if not deadline.expired():
                    # TimeoutError raised by the callback itself, not by the stage
                    # deadline: kind exception, propagated unchanged (REQ-002 / AC-2).
                    self._store.finish_attempt(
                        attempt_rec.attempt_id,
                        "failed",
                        error_msg=str(exc),
                        error_kind=_ERROR_KIND_EXCEPTION,
                        error_detail=repr(exc),
                    )
                    raise
                self._store.finish_attempt(
                    attempt_rec.attempt_id,
                    "failed",
                    error_msg=f"timeout after {timeout}s",
                    error_kind=_ERROR_KIND_TIMEOUT,
                    error_detail=str(exc),
                )
                raise WorkflowTimeoutError(
                    f"stage {stage_id!r} timed out after {timeout}s"
                ) from exc
            except Exception as exc:  # noqa: BLE001 — catch-all to persist failure state before re-raising
                self._store.finish_attempt(
                    attempt_rec.attempt_id,
                    "failed",
                    error_msg=str(exc),
                    error_kind=_ERROR_KIND_EXCEPTION,
                    error_detail=repr(exc),
                )
                raise

            self._store.finish_attempt(attempt_rec.attempt_id, "completed")
            if artifact_uri:
                record_artifact(
                    self._store.get_connection(),
                    task.task_id,
                    stage_id,
                    artifact_uri,
                    workflow_id=task.workflow_id,
                    attempt_number=attempt,
                )
            logger.info("Stage %s completed: task=%s", stage_id, task.task_id)
