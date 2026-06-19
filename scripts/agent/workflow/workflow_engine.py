#!/usr/bin/env python3
"""agent/workflow/workflow_engine.py
Stage transition engine: plan -> execute -> [approval gate] -> verify -> (retry loop).

Callers pass async callbacks for each stage. WorkflowEngine handles
timeout enforcement, retry counting, idempotency, state persistence, and
optional human approval gates between execute and verify.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import nullcontext
from typing import Any

from agent.workflow.models import TaskRecord, WorkflowDef
from agent.workflow.state_store import StateStore

logger = logging.getLogger(__name__)

StageCallback = Callable[[], Awaitable[str | None]]  # returns artifact URI or None


class _NoOpSpan:
    """No-op OTel span used when no tracer is configured."""

    def set_attribute(self, key: str, value: object) -> None:
        pass

    def record_exception(self, exc: BaseException) -> None:
        pass


class WorkflowHaltError(Exception):
    """Raised when a task exceeds max_attempts and is halted."""


class WorkflowTimeoutError(Exception):
    """Raised when a stage exceeds its timeout_sec."""


class WorkflowPendingApprovalError(Exception):
    """Raised when a task is suspended waiting for human approval."""

    def __init__(self, approval_id: str, task_id: str) -> None:
        self.approval_id = approval_id
        self.task_id = task_id
        super().__init__(f"task {task_id} awaiting approval {approval_id}")


class WorkflowEngine:
    """Runs a workflow definition against a set of stage callbacks."""

    def __init__(
        self,
        workflow_def: WorkflowDef,
        store: StateStore,
        require_approval: bool = False,
        tracer: Any = None,
    ) -> None:
        self._wdef = workflow_def
        self._store = store
        self._require_approval = require_approval
        self._tracer = tracer

    def _span_ctx(self, name: str) -> Any:
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
        """Execute plan -> execute -> [approval gate] -> verify with retry on execute failure."""
        with self._span_ctx("workflow.run") as span:
            span.set_attribute("workflow.task_id", task.task_id)
            span.set_attribute("workflow.version", task.workflow_version)
            span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            span.set_attribute("workflow.session_id", task.session_id or "")
            self._store.update_task_status(task.task_id, "running")
            try:
                await self._run_stage(task, "plan", plan_fn)
                await self._run_execute_with_retry(task, execute_fn)
                if self._require_approval:
                    await self._gate_approval(task)
                await self._run_stage(task, "verify", verify_fn)
            except WorkflowPendingApprovalError:
                raise
            except (WorkflowHaltError, WorkflowTimeoutError):
                self._store.update_task_status(task.task_id, "halted")
                raise
            except Exception:  # noqa: BLE001 — catch-all to mark task failed before re-raising
                self._store.update_task_status(task.task_id, "failed")
                raise
            self._store.update_task_status(task.task_id, "completed")

    async def _gate_approval(self, task: TaskRecord) -> None:
        """Suspend execution until a human approves the task."""
        existing = self._store.get_pending_approval(task.task_id)
        with self._span_ctx("workflow.approval") as approval_span:
            approval_span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            if existing is None:
                approval = self._store.request_approval(task.task_id)
                self._store.update_task_status(task.task_id, "pending_approval")
                approval_span.set_attribute(
                    "workflow.approval_id", approval.approval_id
                )
                approval_span.set_attribute("workflow.approval_status", "pending")
                raise WorkflowPendingApprovalError(approval.approval_id, task.task_id)
            approval_span.set_attribute("workflow.approval_id", existing.approval_id)
            approval_span.set_attribute("workflow.approval_status", existing.status)
            if existing.status == "pending":
                raise WorkflowPendingApprovalError(existing.approval_id, task.task_id)
            if existing.status == "rejected":
                self._store.update_task_status(task.task_id, "halted")
                raise WorkflowHaltError(f"approval rejected: {existing.reason}")

    async def _run_execute_with_retry(
        self, task: TaskRecord, execute_fn: StageCallback
    ) -> None:
        """Run execute stage; retry up to max_attempts on failure."""
        policy = self._wdef.retry_policy
        attempt = 0
        while True:
            attempt += 1
            try:
                await self._run_stage(task, "execute", execute_fn, attempt=attempt)
                return
            except WorkflowTimeoutError:
                raise
            except Exception as exc:  # noqa: BLE001 — catch-all to apply retry/halt logic before re-raising
                if attempt >= policy.max_attempts:
                    logger.error(
                        "Task %s: execute halted after %d attempts: %s",
                        task.task_id,
                        attempt,
                        exc,
                    )
                    raise WorkflowHaltError(
                        f"execute stage halted after {attempt} attempts"
                    ) from exc
                wait = policy.backoff_sec
                logger.warning(
                    "Task %s: execute attempt %d failed, retrying in %ds: %s",
                    task.task_id,
                    attempt,
                    wait,
                    exc,
                )
                with self._span_ctx("workflow.retry") as retry_span:
                    retry_span.set_attribute(
                        "workflow.workflow_id", task.workflow_id or ""
                    )
                    retry_span.set_attribute("workflow.task_id", task.task_id)
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
        """Run a single stage with idempotency check and timeout enforcement."""
        with self._span_ctx("workflow.stage") as span:
            span.set_attribute("workflow.stage_id", stage_id)
            span.set_attribute("workflow.attempt", attempt)
            span.set_attribute("workflow.workflow_id", task.workflow_id or "")
            stage_def = self._wdef.get_stage(stage_id)
            timeout = stage_def.timeout_sec if stage_def else 60
            event_id = f"{task.task_id}:{stage_id}:{attempt}"

            attempt_rec = self._store.begin_stage_if_new(
                event_id, task.task_id, stage_id
            )
            if attempt_rec is None:
                logger.info(
                    "Stage %s skipped (already processed): %s", stage_id, event_id
                )
                return

            try:
                artifact_uri = await asyncio.wait_for(fn(), timeout=timeout)
            except TimeoutError as exc:
                self._store.finish_attempt(
                    attempt_rec.attempt_id, "failed", f"timeout after {timeout}s"
                )
                raise WorkflowTimeoutError(
                    f"stage {stage_id!r} timed out after {timeout}s"
                ) from exc
            except Exception as exc:  # noqa: BLE001 — catch-all to persist failure state before re-raising
                self._store.finish_attempt(attempt_rec.attempt_id, "failed", str(exc))
                raise

            self._store.finish_attempt(attempt_rec.attempt_id, "completed")
            if artifact_uri:
                self._store.record_artifact(task.task_id, stage_id, artifact_uri)
            logger.info("Stage %s completed: task=%s", stage_id, task.task_id)
