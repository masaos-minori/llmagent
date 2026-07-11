"""tests/test_workflow_engine.py
Unit tests for agent/workflow/workflow_engine.py.
Uses a temp workflow.sqlite and mocks stage callbacks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.approval_ops import (
    get_pending_approval,
    request_approval,
    resolve_approval,
)
from agent.workflow.attempt_ops import count_attempts
from agent.workflow.idempotency_ops import is_event_processed
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.task_ops import (
    create_task,
    get_task_by_idempotency_key,
    update_task_status,
)
from agent.workflow.workflow_engine import (
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from db.config import DbConfig
from db.create_schema import create_workflow_schema


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


def _make_wdef(
    max_attempts: int = 3, backoff_sec: int = 0, require_approval: bool = False
) -> WorkflowDef:
    stages = [
        StageDefinition(id="plan", description="d", timeout_sec=5, retryable=False),
        StageDefinition(id="execute", description="d", timeout_sec=5, retryable=True),
        StageDefinition(id="verify", description="d", timeout_sec=5, retryable=False),
    ]
    policy = RetryPolicy(
        max_attempts=max_attempts, backoff="fixed", backoff_sec=backoff_sec
    )
    return WorkflowDef(
        name="default",
        version="1.0.0",
        stages=stages,
        retry_policy=policy,
        require_approval=require_approval,
    )


@pytest.fixture()
def workflow_db(tmp_path: Path) -> Path:
    from unittest.mock import patch

    from db.config import DbConfig

    db_path = tmp_path / "workflow.sqlite"
    rag_path = tmp_path / "rag.sqlite"
    session_path = tmp_path / "session.sqlite"
    with patch(
        "db.helper.build_db_config",
        return_value=DbConfig(
            rag_db_path=str(rag_path),
            session_db_path=str(session_path),
            workflow_db_path=str(db_path),
        ),
    ):
        create_workflow_schema()
    return db_path


@pytest.fixture()
def store(workflow_db: Path):
    from agent.workflow.state_store import StateStore

    with patch("db.helper.build_db_config", return_value=_make_cfg(str(workflow_db))):
        s = StateStore()
    yield s
    s.close()


async def _noop() -> str | None:
    return None


class TestWorkflowEngineHappyPath:
    @pytest.mark.asyncio
    async def test_run_sets_task_status_completed(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved")
        await engine.run(task, _noop, _noop, _noop)
        found = get_task_by_idempotency_key(store._db, "s:1")
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_all_stages_recorded(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved")
        await engine.run(task, _noop, _noop, _noop)
        for stage in ("plan", "execute", "verify"):
            event_id = f"{task.task_id}:{stage}:1"
            assert is_event_processed(store._db, event_id)


class TestWorkflowEngineRetry:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved")

        calls = {"n": 0}

        async def flaky_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("first attempt fails")
            return None

        await engine.run(task, _noop, flaky_execute, _noop)
        found = get_task_by_idempotency_key(store._db, "s:1")
        assert found is not None
        assert found.status == "completed"
        assert calls["n"] == 2

    @pytest.mark.asyncio
    async def test_halt_after_max_attempts(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def always_fail() -> str | None:
            raise RuntimeError("always fails")

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, _noop, always_fail, _noop)

        found = get_task_by_idempotency_key(store._db, "s:1")
        assert found is not None
        assert found.status == "halted"

    @pytest.mark.asyncio
    async def test_attempt_count_matches_max_attempts(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def always_fail() -> str | None:
            raise RuntimeError("fail")

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, _noop, always_fail, _noop)

        assert count_attempts(store._db, task.task_id, "execute") == 3


class TestWorkflowEngineTimeout:
    @pytest.mark.asyncio
    async def test_timeout_raises_workflow_timeout_error(self, store) -> None:
        stages = [
            StageDefinition(id="plan", description="d", timeout_sec=5, retryable=False),
            StageDefinition(
                id="execute", description="d", timeout_sec=1, retryable=True
            ),
            StageDefinition(
                id="verify", description="d", timeout_sec=5, retryable=False
            ),
        ]
        policy = RetryPolicy(max_attempts=1, backoff="fixed", backoff_sec=0)
        wdef = WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def slow_execute() -> str | None:
            await asyncio.sleep(10)
            return None

        with pytest.raises((WorkflowHaltError, WorkflowTimeoutError)):
            await engine.run(task, _noop, slow_execute, _noop)


class TestWorkflowEngineIdempotency:
    @pytest.mark.asyncio
    async def test_skip_already_processed_stage(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        call_count = {"n": 0}

        async def counting_fn() -> str | None:
            call_count["n"] += 1
            return None

        # Pre-approve so the gate passes in both runs
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved")

        # First run
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        first_count = call_count["n"]

        # Second run — all event_ids already in processed_events → all skipped
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        assert call_count["n"] == first_count  # no additional calls


class TestWorkflowEngineApprovalGate:
    @pytest.mark.asyncio
    async def test_gate_always_raises_pending_on_new_task(self, store) -> None:
        wdef = _make_wdef(require_approval=True)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        with pytest.raises(WorkflowPendingApprovalError) as exc_info:
            await engine.run(task, _noop, _noop, _noop)
        assert exc_info.value.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_approved_task_gate_passes(self, store) -> None:
        wdef = _make_wdef(require_approval=True)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        approval = request_approval(store._db, task.task_id)
        resolve_approval(store._db, approval.approval_id, "approved")
        await engine._gate_approval(task)  # must not raise

    @pytest.mark.asyncio
    async def test_rejected_task_halts(self, store) -> None:
        wdef = _make_wdef(require_approval=True)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        with pytest.raises(WorkflowPendingApprovalError):
            await engine.run(task, _noop, _noop, _noop)
        approval = get_pending_approval(store._db, task.task_id)
        assert approval is not None
        resolve_approval(store._db, approval.approval_id, "rejected", "not safe")
        with pytest.raises(WorkflowHaltError, match="approval rejected"):
            await engine._gate_approval(task)

    @pytest.mark.asyncio
    async def test_resume_does_not_rerun_plan_or_execute(self, store) -> None:
        """After /approve, resume must not rerun plan or execute stages."""
        wdef = _make_wdef(require_approval=True)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        # First run — suspends at approval gate
        with pytest.raises(WorkflowPendingApprovalError):
            await engine.run(task, _noop, _noop, _noop)

        # Approve the task
        approval = get_pending_approval(store._db, task.task_id)
        assert approval is not None
        resolve_approval(store._db, approval.approval_id, "approved")

        # Resume — plan and execute should be skipped via idempotency
        call_counts = {"plan": 0, "execute": 0, "verify": 0}

        async def counting_fn(stage: str) -> str | None:
            call_counts[stage] += 1
            return None

        # We need to pass the stage name to the callback; use a different approach
        plan_calls = []
        execute_calls = []
        verify_calls = []

        async def plan_fn() -> str | None:
            plan_calls.append(1)
            return None

        async def execute_fn() -> str | None:
            execute_calls.append(1)
            return None

        async def verify_fn() -> str | None:
            verify_calls.append(1)
            return None

        await engine.run(task, plan_fn, execute_fn, verify_fn)

        # Plan and execute should NOT be called again (idempotency)
        assert len(plan_calls) == 0, "Plan stage should not be rerun after resume"
        assert len(execute_calls) == 0, "Execute stage should not be rerun after resume"
        # Verify stage should be called once
        assert len(verify_calls) == 1, "Verify stage should run after resume"

    @pytest.mark.asyncio
    async def test_startup_recovered_approval_can_resume(self, store) -> None:
        """After startup recovery restores pending approval, the task can resume."""
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        # Simulate startup recovery: task is still in pending_approval state
        approval = request_approval(store._db, task.task_id)
        update_task_status(store._db, task.task_id, "pending_approval")

        # Approve the task (as if user ran /approve after startup)
        resolve_approval(store._db, approval.approval_id, "approved")

        # Resume — should complete without raising
        await engine.run(task, _noop, _noop, _noop)
        found = get_task_by_idempotency_key(store._db, "s:1")
        assert found is not None
        assert found.status == "completed"
