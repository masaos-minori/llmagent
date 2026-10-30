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

from agent.workflow.artifact_ops import record_artifact
from agent.workflow.attempt_ops import max_attempt_number
from agent.workflow.errors import StageAlreadyRunningError
from agent.workflow.idempotency_ops import begin_stage_if_new, complete_stage_attempt
from agent.workflow.models import TaskRecord, WorkflowDef
from agent.workflow.state_store import StateStore

logger = logging.getLogger(__name__)

_ERROR_KIND_TIMEOUT = "timeout"
_ERROR_KIND_EXCEPTION = "exception"

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
        self._current_attempt_number: int | None = None

    @property
    def current_attempt_number(self) -> int | None:
        """Persisted attempt number of the stage attempt started most recently."""
        return self._current_attempt_number

    def _span_ctx(self, name: str) -> _Span | nullcontext[_NoOpSpan]:
        """Return a span context manager; uses NoOpSpan when no tracer is available."""
        if self._tracer is not None:
            return self._tracer.start_as_current_span(name)
        return nullcontext(_NoOpSpan())

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
            self._store.claim_task(task.task_id)
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
        db = self._store._db
        while True:
            used = max_attempt_number(db, task.task_id, stage_id)
            if used >= policy.max_attempts:
                raise WorkflowHaltError(
                    f"{stage_id} stage halted: {used} of {policy.max_attempts} "
                    "attempts already used"
                )
            try:
                await self._run_stage(task, stage_id, fn)
                return
            except (WorkflowTimeoutError, StageAlreadyRunningError):
                raise
            except Exception as exc:  # noqa: BLE001 — catch-all to apply retry/halt logic before re-raising
                attempt = max_attempt_number(db, task.task_id, stage_id)
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
    ) -> None:
        """Run a single stage attempt with a completed-stage check and timeout.

        The attempt number is persisted by `begin_stage_if_new`; a stage with a
        completed attempt in the ledger is skipped.
        """
        with self._span_ctx("workflow.stage") as span:
            span.set_attribute("workflow.stage_id", stage_id)
            span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            stage_def = self._wdef.get_stage(stage_id)
            timeout = stage_def.timeout_sec if stage_def else 60

            attempt_rec = begin_stage_if_new(self._store._db, task.task_id, stage_id)
            if attempt_rec is None:
                logger.info(
                    "Stage %s skipped (already completed): task=%s",
                    stage_id,
                    task.task_id,
                )
                return
            self._current_attempt_number = attempt_rec.attempt_number
            span.set_attribute("workflow.attempt", attempt_rec.attempt_number)

            try:
                artifact_uri = await asyncio.wait_for(fn(), timeout=timeout)
            except TimeoutError as exc:
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

            complete_stage_attempt(
                self._store._db, attempt_rec, workflow_id=task.workflow_id
            )
            if artifact_uri:
                record_artifact(
                    self._store._db,
                    task.task_id,
                    stage_id,
                    artifact_uri,
                    workflow_id=task.workflow_id,
                    attempt_number=attempt_rec.attempt_number,
                )
            logger.info("Stage %s completed: task=%s", stage_id, task.task_id)
