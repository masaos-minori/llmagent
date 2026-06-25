"""tests/test_workflow_engine.py
Unit tests for agent/workflow/workflow_engine.py.
Uses a temp workflow.sqlite and mocks stage callbacks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.workflow_engine import (
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowPendingApprovalError,
    WorkflowTimeoutError,
)
from db.config import DbConfig
from db.workflow_schema import init_schema


def _make_cfg(db_path: str) -> DbConfig:
    return DbConfig(
        rag_db_path="/opt/llm/db/rag.sqlite",
        session_db_path="/opt/llm/db/session.sqlite",
        workflow_db_path=db_path,
    )


def _make_wdef(max_attempts: int = 3, backoff_sec: int = 0) -> WorkflowDef:
    stages = [
        StageDefinition(id="plan", description="d", timeout_sec=5, retryable=False),
        StageDefinition(id="execute", description="d", timeout_sec=5, retryable=True),
        StageDefinition(id="verify", description="d", timeout_sec=5, retryable=False),
    ]
    policy = RetryPolicy(
        max_attempts=max_attempts, backoff="fixed", backoff_sec=backoff_sec
    )
    return WorkflowDef(
        name="default", version="1.0.0", stages=stages, retry_policy=policy
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
        init_schema()
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
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)
        await engine.run(task, _noop, _noop, _noop)
        found = store.get_task_by_idempotency_key("s:1")
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_all_stages_recorded(self, store) -> None:
        wdef = _make_wdef()
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)
        await engine.run(task, _noop, _noop, _noop)
        for stage in ("plan", "execute", "verify"):
            event_id = f"{task.task_id}:{stage}:1"
            assert store.is_event_processed(event_id)


class TestWorkflowEngineRetry:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def flaky_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("first attempt fails")
            return None

        await engine.run(task, _noop, flaky_execute, _noop)
        found = store.get_task_by_idempotency_key("s:1")
        assert found is not None
        assert found.status == "completed"
        assert calls["n"] == 2

    @pytest.mark.asyncio
    async def test_halt_after_max_attempts(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)

        async def always_fail() -> str | None:
            raise RuntimeError("always fails")

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, _noop, always_fail, _noop)

        found = store.get_task_by_idempotency_key("s:1")
        assert found is not None
        assert found.status == "halted"

    @pytest.mark.asyncio
    async def test_attempt_count_matches_max_attempts(self, store) -> None:
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)

        async def always_fail() -> str | None:
            raise RuntimeError("fail")

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, _noop, always_fail, _noop)

        assert store.count_attempts(task.task_id, "execute") == 3


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
        task = store.create_task("s", 1, wdef.version)
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
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store)

        call_count = {"n": 0}

        async def counting_fn() -> str | None:
            call_count["n"] += 1
            return None

        # First run
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        first_count = call_count["n"]

        # Second run — all event_ids already in processed_events → all skipped
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        assert call_count["n"] == first_count  # no additional calls


class TestWorkflowEngineApprovalGate:
    @pytest.mark.asyncio
    async def test_require_approval_raises_pending(self, store) -> None:
        wdef = _make_wdef()
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store, require_approval=True)
        with pytest.raises(WorkflowPendingApprovalError) as exc_info:
            await engine.run(task, _noop, _noop, _noop)
        assert exc_info.value.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_no_approval_required_completes(self, store) -> None:
        wdef = _make_wdef()
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store, require_approval=False)
        await engine.run(task, _noop, _noop, _noop)
        found = store.get_task_by_idempotency_key("s:1")
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_approved_task_gate_passes(self, store) -> None:
        wdef = _make_wdef()
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store, require_approval=True)
        approval = store.request_approval(task.task_id)
        store.resolve_approval(approval.approval_id, "approved")
        await engine._gate_approval(task)  # must not raise

    @pytest.mark.asyncio
    async def test_rejected_task_halts(self, store) -> None:
        wdef = _make_wdef()
        task = store.create_task("s", 1, wdef.version)
        engine = WorkflowEngine(wdef, store, require_approval=True)
        with pytest.raises(WorkflowPendingApprovalError):
            await engine.run(task, _noop, _noop, _noop)
        approval = store.get_pending_approval(task.task_id)
        assert approval is not None
        store.resolve_approval(approval.approval_id, "rejected", "not safe")
        with pytest.raises(WorkflowHaltError, match="approval rejected"):
            await engine._gate_approval(task)
