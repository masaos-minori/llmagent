"""tests/test_workflow_engine.py
Unit tests for agent/workflow/workflow_engine.py.
Uses a temp workflow.sqlite and mocks stage callbacks.
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from agent.workflow.attempt_ops import count_attempts
from agent.workflow.idempotency_ops import is_event_processed
from agent.workflow.models import RetryPolicy, StageDefinition, WorkflowDef
from agent.workflow.task_ops import (
    create_task,
    get_task_by_id,
)
from agent.workflow.workflow_engine import (
    WorkflowEngine,
    WorkflowHaltError,
    WorkflowStageFailure,
    WorkflowTimeoutError,
)
from agent.workflow.workflow_loader import WorkflowLoader
from db.config import DbConfig
from db.create_schema import create_workflow_schema
from shared.json_utils import parse_iso_utc


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


def _attempt_lease_rows(
    db_path: Path, task_id: str, stage_id: str
) -> list[sqlite3.Row]:
    """Read persisted attempt rows for a task/stage (AC-5 asserts the stored row)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT started_at, owner_id, lease_expires_at FROM attempts "
            "WHERE task_id=? AND stage_id=? ORDER BY started_at, attempt_id",
            (task_id, stage_id),
        ).fetchall()
    finally:
        conn.close()


def _attempt_error_kinds(
    db_path: Path, task_id: str, stage_id: str
) -> list[str | None]:
    """Read persisted attempt-row error_kind values for a task/stage in insertion
    order (REQ-007). None = the attempt finished without an error kind (success)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [
            row["error_kind"]
            for row in conn.execute(
                "SELECT error_kind FROM attempts "
                "WHERE task_id=? AND stage_id=? ORDER BY rowid",
                (task_id, stage_id),
            )
        ]
    finally:
        conn.close()


def _lease_delta_sec(row: sqlite3.Row) -> float:
    """lease_expires_at minus started_at, both parsed with parse_iso_utc (REQ-009)."""
    return (
        parse_iso_utc(row["lease_expires_at"]) - parse_iso_utc(row["started_at"])
    ).total_seconds()


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
    async def test_retry_succeeds_on_second_attempt(
        self, store, workflow_db: Path
    ) -> None:
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

        # AC-5: both execute attempts carry an owner stamp and a
        # timeout(5)+margin(30) lease horizon (wflease001 REQ-005).
        rows = _attempt_lease_rows(workflow_db, task.task_id, "execute")
        assert len(rows) == 2
        for row in rows:
            assert row["owner_id"]
            assert _lease_delta_sec(row) == 35

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
    async def test_timeout_raises_workflow_timeout_error(
        self, store, workflow_db: Path
    ) -> None:
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

        # AC-2: deadline expiry raises exactly WorkflowTimeoutError, not a generic halt.
        with pytest.raises(WorkflowTimeoutError):
            await engine.run(task, _noop, slow_execute, _noop)

        # AC-5: the timed-out attempt row still carries the stamped lease
        # horizon: timeout(1)+margin(30).
        rows = _attempt_lease_rows(workflow_db, task.task_id, "execute")
        assert len(rows) == 1
        assert rows[0]["owner_id"]
        assert _lease_delta_sec(rows[0]) == 31

        # REQ-007: deadline expiry persists kind `timeout` on the attempt row.
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == ["timeout"]


class TestWorkflowEngineRetryKinds:
    """wfretry001 AC-2/AC-3/AC-5/AC-6: kind-based retry semantics (REQ-002/003/005/006)."""

    @pytest.mark.asyncio
    async def test_inner_timeout_error_kind_exception_and_retried(
        self, store, workflow_db: Path
    ) -> None:
        """AC-2: an inner TimeoutError raised by the callback (well before its
        5 s stage deadline) persists kind exception and is retried when
        `exception` is in retry_on, instead of being relabeled WorkflowTimeoutError."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)  # shipped default retry_on
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def inner_timeout_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("inner timeout from callback")
            return None

        await engine.run(task, _noop, inner_timeout_execute, _noop)

        assert calls["n"] == 2
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == [
            "exception",
            None,
        ]
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_deadline_timeout_retried_when_kind_in_retry_on(
        self, store, workflow_db: Path
    ) -> None:
        """REQ-003: with `timeout` in retry_on, a deadline expiry consumes one
        budget unit and the retry can succeed."""
        stages = [
            StageDefinition(id="plan", timeout_sec=5, retryable=False),
            StageDefinition(id="execute", timeout_sec=1, retryable=True),
            StageDefinition(id="verify", timeout_sec=5, retryable=False),
        ]
        wdef = WorkflowDef(
            name="default",
            version="1.0.0",
            stages=stages,
            retry_policy=RetryPolicy(
                max_attempts=3, backoff_sec=0, retry_on=("exception", "timeout")
            ),
        )
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def slow_then_fast() -> str | None:
            calls["n"] += 1
            if calls["n"] == 1:
                await asyncio.sleep(10)
            return None

        await engine.run(task, _noop, slow_then_fast, _noop)

        assert calls["n"] == 2
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == [
            "timeout",
            None,
        ]
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "completed"

    @pytest.mark.asyncio
    async def test_deadline_timeout_terminal_under_shipped_retry_on(
        self, store, workflow_db: Path
    ) -> None:
        """AC-3 / owner decision (Plan UNK-01): under the shipped retry_on
        ("exception",) a deadline expiry is terminal at once — one attempt row,
        no retry, WorkflowTimeoutError propagates, task halted."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        wdef.stages[1] = StageDefinition(id="execute", timeout_sec=1, retryable=True)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def slow_execute() -> str | None:
            calls["n"] += 1
            await asyncio.sleep(10)
            return None

        with pytest.raises(WorkflowTimeoutError):
            await engine.run(task, _noop, slow_execute, _noop)

        assert calls["n"] == 1
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == ["timeout"]
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "halted"

    @pytest.mark.asyncio
    async def test_exception_exhaustion_consumes_full_budget(
        self, store, workflow_db: Path
    ) -> None:
        """REQ-003: exception exhaustion halts only after consuming the full
        budget — attempt-row count equals max_attempts, all kind exception."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def always_fail() -> str | None:
            raise RuntimeError("always fails")

        with pytest.raises(WorkflowHaltError):
            await engine.run(task, _noop, always_fail, _noop)

        assert count_attempts(store._db, task.task_id, "execute") == 3
        assert (
            _attempt_error_kinds(workflow_db, task.task_id, "execute")
            == ["exception"] * 3
        )
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "halted"

    @pytest.mark.asyncio
    async def test_terminal_kind_no_backoff_and_single_attempt(
        self, store, workflow_db: Path
    ) -> None:
        """REQ-003: a kind not in retry_on is terminal at once — no backoff
        sleep and exactly one attempt row despite max_attempts=3."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=1)  # retry_on ("exception",)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def failing_execute() -> str | None:
            raise WorkflowStageFailure("llm failed")

        with patch("agent.workflow.workflow_engine.asyncio.sleep") as mock_sleep:
            with pytest.raises(WorkflowStageFailure):
                await engine.run(task, _noop, failing_execute, _noop)
        mock_sleep.assert_not_called()

        assert count_attempts(store._db, task.task_id, "execute") == 1

    @pytest.mark.asyncio
    async def test_llm_failure_persisted_kind_terminal_under_shipped_config(
        self, store, workflow_db: Path
    ) -> None:
        """REQ-005 / REQ-007 / owner decision (Plan UNK-02): a WorkflowStageFailure
        persists kind llm_failure on the attempt row and is terminal under the
        shipped retry_on, leaving the task failed and propagating unchanged."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def failing_execute() -> str | None:
            raise WorkflowStageFailure(
                "llm failed",
                answer="partial",
                error_kind="CONNECT_ERROR",
                is_partial=True,
            )

        with pytest.raises(WorkflowStageFailure) as excinfo:
            await engine.run(task, _noop, failing_execute, _noop)

        assert excinfo.value.error_kind == "CONNECT_ERROR"
        assert excinfo.value.answer == "partial"
        assert excinfo.value.is_partial is True
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == [
            "llm_failure"
        ]
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "failed"

    @pytest.mark.asyncio
    async def test_callback_halt_not_retried_even_when_exception_retryable(
        self, store, workflow_db: Path
    ) -> None:
        """AC-6 (engine half): a WorkflowHaltError raised by the stage callback
        is terminal even when retry_on includes exception — one attempt only."""
        wdef = _make_wdef(max_attempts=3, backoff_sec=0)
        wdef.retry_policy = RetryPolicy(
            max_attempts=3, backoff_sec=0, retry_on=("exception", "timeout")
        )
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        calls = {"n": 0}

        async def halting_execute() -> str | None:
            calls["n"] += 1
            raise WorkflowHaltError("side effect attempted")

        with pytest.raises(WorkflowHaltError, match="side effect attempted"):
            await engine.run(task, _noop, halting_execute, _noop)

        assert calls["n"] == 1
        assert count_attempts(store._db, task.task_id, "execute") == 1
        found = get_task_by_id(store._db, task.task_id)
        assert found is not None
        assert found.status == "halted"


class TestShippedRetryPolicyPin:
    """REQ-003 / AC-3: the shipped config/workflows/default.json policy pins
    timeout-not-retried / exception-retried behavior."""

    def test_shipped_retry_on_pins_exception_only(self) -> None:
        wdef = WorkflowLoader().load("default")
        assert wdef.retry_policy.retry_on == ("exception",)
        assert "timeout" not in wdef.retry_policy.retry_on
        assert "llm_failure" not in wdef.retry_policy.retry_on

    @pytest.mark.asyncio
    async def test_shipped_policy_timeout_terminal_and_exception_retried(
        self, store, workflow_db: Path
    ) -> None:
        """Engine behavior under the loaded shipped policy (stage timeouts
        shortened to 1 s for test runtime; the retry_policy itself is the shipped one)."""
        shipped = WorkflowLoader().load("default")
        stages = [
            StageDefinition(
                id=s.id,
                timeout_sec=1 if s.id == "execute" else 5,
                retryable=s.retryable,
            )
            for s in shipped.stages
        ]
        wdef = WorkflowDef(
            name=shipped.name,
            version=shipped.version,
            stages=stages,
            retry_policy=shipped.retry_policy,
        )

        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)

        async def slow_execute() -> str | None:
            await asyncio.sleep(10)
            return None

        with pytest.raises(WorkflowTimeoutError):
            await engine.run(task, _noop, slow_execute, _noop)
        assert _attempt_error_kinds(workflow_db, task.task_id, "execute") == ["timeout"]

        task2 = create_task(store._db, "s", 2, wdef.version, "wf-test")
        engine2 = WorkflowEngine(wdef, store)
        calls = {"n": 0}

        async def flaky_execute() -> str | None:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("first attempt fails")
            return None

        await engine2.run(task2, _noop, flaky_execute, _noop)
        assert calls["n"] == 2
        assert _attempt_error_kinds(workflow_db, task2.task_id, "execute") == [
            "exception",
            None,
        ]


class TestWorkflowEngineLeaseStamping:
    """AC-5: every engine-started attempt carries owner_id and a timeout+30 lease."""

    @pytest.mark.asyncio
    async def test_attempt_start_stamps_lease(self, store, workflow_db: Path) -> None:
        wdef = _make_wdef()
        task = create_task(store._db, "s", 1, wdef.version, "wf-test")
        engine = WorkflowEngine(wdef, store)
        await engine.run(task, _noop, _noop, _noop)

        for stage in ("plan", "execute", "verify"):
            rows = _attempt_lease_rows(workflow_db, task.task_id, stage)
            assert len(rows) == 1, stage
            row = rows[0]
            assert row["owner_id"], stage
            # Stage fixtures use timeout_sec=5; expected horizon 35 s.
            assert _lease_delta_sec(row) == 35, stage


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

        # First run
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        first_count = call_count["n"]

        # Second run — all event_ids already in processed_events → all skipped
        await engine.run(task, counting_fn, counting_fn, counting_fn)
        assert call_count["n"] == first_count  # no additional calls


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


class TestBuildTurnControlMessage:
    """Turn-entry replay detection (toolexec001 REQ-008, row 08)."""

    def _stale_row(self, store, task_id: str, key: str, tool: str, retry_class: str):
        store.record_tool_call(task_id, key, tool, retry_class)
        store._db.execute(
            "UPDATE tool_call_state SET created_at=? WHERE idempotency_key=?",
            (time.time() - 3600, key),
        )
        store._db.commit()

    def test_retryable_interrupted_yields_replay_section(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        self._stale_row(store, task.task_id, "k1", "calculator__calculate", "retryable")
        engine = WorkflowEngine(_make_wdef(), store)
        msg = engine.build_turn_control_message(task.task_id)
        assert msg is not None
        assert (
            "replay: tool=calculator__calculate idempotency_key=k1 state=interrupted"
            in msg
        )
        assert "unreplayable" not in msg
        # Row was classified interrupted exactly once.
        row = store._db.execute(
            "SELECT state FROM tool_call_state WHERE idempotency_key='k1'"
        ).fetchone()
        assert row["state"] == "interrupted"

    def test_non_retryable_yields_unreplayable_section_not_replay(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        self._stale_row(
            store, task.task_id, "k2", "filesystem__write_file", "non_retryable"
        )
        engine = WorkflowEngine(_make_wdef(), store)
        msg = engine.build_turn_control_message(task.task_id)
        assert msg is not None
        assert "unreplayable: tool=filesystem__write_file idempotency_key=k2" in msg
        assert "replay: tool=filesystem__write_file" not in msg

    def test_no_rows_yields_none(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        engine = WorkflowEngine(_make_wdef(), store)
        assert engine.build_turn_control_message(task.task_id) is None

    def test_fresh_pending_is_not_listed(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        store.record_tool_call(task.task_id, "k3", "calculator__calculate", "retryable")
        engine = WorkflowEngine(_make_wdef(), store)
        assert engine.build_turn_control_message(task.task_id) is None
        assert len(store.pending_tool_calls(task.task_id)) == 1

    def test_interrupted_rows_are_consumed_once(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        self._stale_row(store, task.task_id, "k4", "calculator__calculate", "retryable")
        engine = WorkflowEngine(_make_wdef(), store)
        assert engine.build_turn_control_message(task.task_id) is not None
        # Second turn-entry: the row is already interrupted, not re-listed.
        assert engine.build_turn_control_message(task.task_id) is None

    def test_store_failure_returns_none_not_raise(self, store) -> None:
        task = create_task(store._db, "s1", 1, "1.0.0", "wf")
        engine = WorkflowEngine(_make_wdef(), store)
        with patch.object(
            type(store),
            "classify_stale_pending",
            side_effect=sqlite3.OperationalError("boom"),
        ):
            assert engine.build_turn_control_message(task.task_id) is None
