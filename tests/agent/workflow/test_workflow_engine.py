"""tests/test_workflow_engine.py
Unit tests for agent/workflow/workflow_engine.py.
Uses a temp workflow.sqlite and mocks stage callbacks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.attempt_ops import count_attempts
from agent.workflow.errors import TaskTransitionError
from agent.workflow.idempotency_ops import is_event_processed
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
)
from agent.workflow.workflow_engine import (
    WorkflowEngine,
    WorkflowHaltError,
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


def _make_wdef(max_attempts: int = 3, backoff_sec: int = 0) -> WorkflowDef:
    stages = [
        StageDefinition(id="plan", timeout_sec=5, retryable=False),
        StageDefinition(id="execute", timeout_sec=5, retryable=True),
        StageDefinition(id="verify", timeout_sec=5, retryable=False),
    ]
    policy = RetryPolicy(max_attempts=max_attempts, backoff_sec=backoff_sec)
    return WorkflowDef(
        name="default",
        version="1.0.0",
        stages=stages,
        retry_policy=policy,
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
        await engine.run(task, _noop, _noop, _noop)
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_all_stages_recorded(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
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

        calls = {"n": 0}

        async def flaky_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("first attempt fails")
            return None

        await engine.run(task, _noop, flaky_execute, _noop)
        found = get_task_by_id(store._db, task.task_id)
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

        found = get_task_by_id(store._db, task.task_id)
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
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=1, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=1, backoff_sec=0)
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
    async def test_completed_task_cannot_be_run_again(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        call_count = {"n": 0}

        async def counting_fn() -> str | None:
            call_count["n"] += 1
            return None

        await engine.run(task, counting_fn, counting_fn, counting_fn)
        first_count = call_count["n"]

        with pytest.raises(TaskTransitionError, match="completed"):
            await engine.run(task, counting_fn, counting_fn, counting_fn)
        assert call_count["n"] == first_count  # no additional calls

    @pytest.mark.asyncio
    async def test_resume_of_a_failed_task_skips_only_completed_stages(
        self, store
    ) -> None:
        wdef = _make_wdef(max_attempts=1)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        calls: list[str] = []

        def stage(name: str, fail: bool):
            async def fn() -> str | None:
                calls.append(name)
                if fail:
                    raise RuntimeError("boom")
                return None

            return fn

        with pytest.raises(WorkflowHaltError):
            await engine.run(
                task,
                stage("plan", False),
                stage("execute", True),
                stage("verify", False),
            )
        # The halt is terminal, so model a crash instead: the task is failed with the
        # plan stage completed and the execute attempt failed.
        store._db.execute(
            "UPDATE tasks SET status='failed' WHERE task_id=?", (task.task_id,)
        )
        store._db.commit()
        calls.clear()
        wdef2 = _make_wdef(max_attempts=3)
        engine2 = WorkflowEngine(wdef2, store)
        await engine2.run(
            task, stage("plan", False), stage("execute", False), stage("verify", False)
        )
        assert calls == ["execute", "verify"]  # plan was completed: skipped
        rows = store._db.fetchall(
            "SELECT attempt_number FROM attempts WHERE task_id=? AND stage_id='execute'"
            " ORDER BY attempt_number",
            (task.task_id,),
        )
        assert [r[0] for r in rows] == [1, 2]  # numbering continues across the restart
        assert get_task_by_id(store._db, task.task_id).status == "completed"

    @pytest.mark.asyncio
    async def test_retry_budget_survives_a_restart(self, store) -> None:
        wdef = _make_wdef(max_attempts=2)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        store._db.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at,"
            " attempt_number) VALUES ('old', ?, 'execute', 'failed', 't', 1)",
            (task.task_id,),
        )
        store._db.execute(
            "UPDATE tasks SET status='failed' WHERE task_id=?", (task.task_id,)
        )
        store._db.commit()
        engine = WorkflowEngine(wdef, store)
        calls = {"n": 0}

        async def failing() -> str | None:
            calls["n"] += 1
            raise RuntimeError("still failing")

        async def ok() -> str | None:
            return None

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, ok, failing, ok)
        # One attempt was already used before the restart, so only one more may run.
        assert calls["n"] == 1
        assert engine.current_attempt_number == 2

    @pytest.mark.asyncio
    async def test_exhausted_budget_halts_without_running_the_stage(
        self, store
    ) -> None:
        wdef = _make_wdef(max_attempts=1)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        store._db.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, started_at,"
            " attempt_number) VALUES ('old', ?, 'execute', 'failed', 't', 1)",
            (task.task_id,),
        )
        store._db.execute(
            "UPDATE tasks SET status='failed' WHERE task_id=?", (task.task_id,)
        )
        store._db.commit()
        engine = WorkflowEngine(wdef, store)
        called = {"n": 0}

        async def fn() -> str | None:
            called["n"] += 1
            return None

        with pytest.raises(WorkflowHaltError, match="already used"):
            await engine.run(task, fn, fn, fn)
        assert called["n"] == 1  # plan ran; execute did not
        assert get_task_by_id(store._db, task.task_id).status == "halted"

    @pytest.mark.asyncio
    async def test_running_task_cannot_be_claimed_twice(self, store) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        store.claim_task(task.task_id)
        engine = WorkflowEngine(wdef, store)

        async def fn() -> str | None:
            return None

        with pytest.raises(TaskTransitionError, match="running"):
            await engine.run(task, fn, fn, fn)


class TestWorkflowEngineStages:
    """Regression guards for how WorkflowEngine.run() invokes its stages."""

    @pytest.mark.asyncio
    async def test_run_never_invokes_retry_stage(self, store) -> None:
        """Regression guard: WorkflowEngine.run() must never invoke a retry-labeled stage."""
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        with patch.object(
            engine, "_run_stage", wraps=engine._run_stage
        ) as mock_run_stage:
            await engine.run(task, _noop, _noop, _noop)
            for call_args in mock_run_stage.call_args_list:
                stage_id = (
                    call_args[0][1]
                    if len(call_args[0]) > 1
                    else call_args[1].get("stage_id")
                )
                assert stage_id != "retry", (
                    "_run_stage was called with stage_id='retry' which should never happen"
                )


class TestRunStageWithRetryGeneralization:
    """_run_stage_with_retry gates retries on stage_def.retryable, not on stage_id.

    config/workflows/default.json declares retryable=false for plan/verify and
    retryable=true for execute — these tests lock that behavior in under the
    generalized wrapper (replacing the old hardcoded _run_execute_with_retry).
    """

    @pytest.mark.asyncio
    async def test_non_retryable_plan_stage_does_not_retry_on_failure(
        self, store
    ) -> None:
        """A retryable=false stage (plan) must fail on the first attempt, no retry loop."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def failing_plan() -> str | None:
            calls["n"] += 1
            raise RuntimeError("plan always fails")

        with pytest.raises(RuntimeError, match="plan always fails"):
            await engine.run(task, failing_plan, _noop, _noop)

        assert calls["n"] == 1, "non-retryable stage must not be retried"
        assert count_attempts(store._db, task.task_id, "plan") == 1

    @pytest.mark.asyncio
    async def test_non_retryable_verify_stage_does_not_retry_on_failure(
        self, store
    ) -> None:
        """A retryable=false stage (verify) must fail on the first attempt, no retry loop."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def failing_verify() -> str | None:
            calls["n"] += 1
            raise RuntimeError("verify always fails")

        with pytest.raises(RuntimeError, match="verify always fails"):
            await engine.run(task, _noop, _noop, failing_verify)

        assert calls["n"] == 1, "non-retryable stage must not be retried"
        assert count_attempts(store._db, task.task_id, "verify") == 1

    @pytest.mark.asyncio
    async def test_execute_success_verify_failure_marks_task_failed(
        self, store
    ) -> None:
        """INV-03: execute success then verify failure must leave task status as 'failed', not 'completed'."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def failing_verify() -> str | None:
            raise RuntimeError("verify always fails")

        with pytest.raises(RuntimeError, match="verify always fails"):
            await engine.run(task, _noop, _noop, failing_verify)

        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "failed"

    @pytest.mark.asyncio
    async def test_execute_retry_behavior_unchanged_under_generalized_wrapper(
        self, store
    ) -> None:
        """execute (retryable=true) still retries up to max_attempts via the shared wrapper."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def flaky_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("first attempt fails")
            return None

        await engine.run(task, _noop, flaky_execute, _noop)
        assert calls["n"] == 2
        assert count_attempts(store._db, task.task_id, "execute") == 2
