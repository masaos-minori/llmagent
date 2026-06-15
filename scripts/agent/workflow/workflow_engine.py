#!/usr/bin/env python3
"""agent/workflow/workflow_engine.py
Stage transition engine: plan -> execute -> verify -> (retry loop).

Callers pass async callbacks for each stage. WorkflowEngine handles
timeout enforcement, retry counting, idempotency, and state persistence.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from agent.workflow.models import TaskRecord, WorkflowDef
from agent.workflow.state_store import StateStore

logger = logging.getLogger(__name__)

StageCallback = Callable[[], Awaitable[str | None]]  # returns artifact URI or None


class WorkflowHaltError(Exception):
    """Raised when a task exceeds max_attempts and is halted."""


class WorkflowTimeoutError(Exception):
    """Raised when a stage exceeds its timeout_sec."""


class WorkflowEngine:
    """Runs a workflow definition against a set of stage callbacks."""

    def __init__(self, workflow_def: WorkflowDef, store: StateStore) -> None:
        self._wdef = workflow_def
        self._store = store

    async def run(
        self,
        task: TaskRecord,
        plan_fn: StageCallback,
        execute_fn: StageCallback,
        verify_fn: StageCallback,
    ) -> None:
        """Execute plan -> execute -> verify with retry on execute failure."""
        self._store.update_task_status(task.task_id, "running")
        try:
            await self._run_stage(task, "plan", plan_fn)
            await self._run_execute_with_retry(task, execute_fn)
            await self._run_stage(task, "verify", verify_fn)
        except (WorkflowHaltError, WorkflowTimeoutError):
            self._store.update_task_status(task.task_id, "halted")
            raise
        except Exception:
            self._store.update_task_status(task.task_id, "failed")
            raise
        self._store.update_task_status(task.task_id, "completed")

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
            except Exception as exc:
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
                await asyncio.sleep(wait)

    async def _run_stage(
        self,
        task: TaskRecord,
        stage_id: str,
        fn: StageCallback,
        attempt: int = 1,
    ) -> None:
        """Run a single stage with idempotency check and timeout enforcement."""
        stage_def = self._wdef.get_stage(stage_id)
        timeout = stage_def.timeout_sec if stage_def else 60
        event_id = f"{task.task_id}:{stage_id}:{attempt}"

        attempt_rec = self._store.begin_stage_if_new(event_id, task.task_id, stage_id)
        if attempt_rec is None:
            logger.info("Stage %s skipped (already processed): %s", stage_id, event_id)
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
        except Exception as exc:
            self._store.finish_attempt(attempt_rec.attempt_id, "failed", str(exc))
            raise

        self._store.finish_attempt(attempt_rec.attempt_id, "completed")
        if artifact_uri:
            self._store.record_artifact(task.task_id, stage_id, artifact_uri)
        logger.info("Stage %s completed: task=%s", stage_id, task.task_id)
