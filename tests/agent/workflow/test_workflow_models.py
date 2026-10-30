"""tests/test_workflow_models.py
Unit tests for agent/workflow/models.py — dataclass construction and WorkflowDef.get_stage.
"""

from __future__ import annotations

from agent.workflow.models import (
    ATTEMPT_TERMINAL_STATUSES,
    TASK_TRANSITIONS,
    ArtifactRef,
    AttemptRecord,
    AttemptStatus,
    RetryPolicy,
    StageDefinition,
    TaskRecord,
    TaskStatus,
    WorkflowDef,
    is_task_transition_allowed,
)


class TestTaskRecord:
    def test_create(self) -> None:
        r = TaskRecord(
            task_id="t1",
            session_id="s1",
            turn_number=3,
            workflow_version="1.0.0",
            status="pending",
            task_nonce="s1:3",
            created_at="2026-01-01T00:00:00+00:00",
            updated_at="2026-01-01T00:00:00+00:00",
        )
        assert r.task_id == "t1"
        assert r.status == "pending"


class TestAttemptRecord:
    def test_create_minimal(self) -> None:
        r = AttemptRecord(
            attempt_id="a1",
            task_id="t1",
            stage_id="plan",
            status="running",
            started_at="2026-01-01T00:00:00+00:00",
        )
        assert r.ended_at is None
        assert r.error_msg is None

    def test_create_with_error(self) -> None:
        r = AttemptRecord(
            attempt_id="a1",
            task_id="t1",
            stage_id="execute",
            status="failed",
            started_at="2026-01-01T00:00:00+00:00",
            ended_at="2026-01-01T00:01:00+00:00",
            error_msg="timeout",
        )
        assert r.error_msg == "timeout"


class TestArtifactRef:
    def test_create(self) -> None:
        ref = ArtifactRef(
            artifact_id="ar1",
            task_id="t1",
            stage_id="execute",
            uri="file:///tmp/result.json",
            created_at="2026-01-01T00:00:00+00:00",
        )
        assert ref.uri == "file:///tmp/result.json"


class TestWorkflowDef:
    def _make_wdef(self) -> WorkflowDef:
        stages = [
            StageDefinition(id="plan", timeout_sec=30, retryable=False),
            StageDefinition(id="execute", timeout_sec=120, retryable=True),
            StageDefinition(id="verify", timeout_sec=10, retryable=False),
        ]
        policy = RetryPolicy(max_attempts=3, backoff_sec=1)
        return WorkflowDef(
            name="default", version="1.0.0", stages=stages, retry_policy=policy
        )

    def test_get_stage_found(self) -> None:
        wdef = self._make_wdef()
        stage = wdef.get_stage("execute")
        assert stage is not None
        assert stage.id == "execute"
        assert stage.retryable is True

    def test_get_stage_not_found(self) -> None:
        wdef = self._make_wdef()
        assert wdef.get_stage("nonexistent") is None

    def test_default_retry_policy(self) -> None:
        wdef = WorkflowDef(name="x", version="1.0.0")
        assert wdef.retry_policy.max_attempts == 3
        assert wdef.retry_policy.backoff_sec == 1

    def test_stages_default_empty(self) -> None:
        wdef = WorkflowDef(name="x", version="1.0.0")
        assert wdef.stages == []


class TestStatusVocabulary:
    def test_task_status_values(self) -> None:
        assert {s.value for s in TaskStatus} == {
            "pending",
            "running",
            "completed",
            "failed",
            "halted",
        }

    def test_attempt_status_values(self) -> None:
        assert {s.value for s in AttemptStatus} == {"running", "completed", "failed"}

    def test_members_equal_plain_strings(self) -> None:
        assert TaskStatus.HALTED == "halted"
        assert AttemptStatus.FAILED == "failed"

    def test_attempt_terminal_statuses(self) -> None:
        assert ATTEMPT_TERMINAL_STATUSES == {
            AttemptStatus.COMPLETED,
            AttemptStatus.FAILED,
        }

    def test_transition_matrix_edges(self) -> None:
        edges = {(c, n) for c, nxt in TASK_TRANSITIONS.items() for n in nxt}
        assert edges == {
            (TaskStatus.PENDING, TaskStatus.RUNNING),
            (TaskStatus.PENDING, TaskStatus.HALTED),
            (TaskStatus.RUNNING, TaskStatus.COMPLETED),
            (TaskStatus.RUNNING, TaskStatus.FAILED),
            (TaskStatus.RUNNING, TaskStatus.HALTED),
            (TaskStatus.FAILED, TaskStatus.RUNNING),
            (TaskStatus.COMPLETED, TaskStatus.FAILED),
        }

    def test_is_task_transition_allowed(self) -> None:
        assert is_task_transition_allowed(TaskStatus.PENDING, TaskStatus.RUNNING)
        assert not is_task_transition_allowed(TaskStatus.HALTED, TaskStatus.RUNNING)
        assert not is_task_transition_allowed(TaskStatus.COMPLETED, TaskStatus.RUNNING)


class TestAttemptNumber:
    def test_defaults_to_zero(self) -> None:
        r = AttemptRecord(
            attempt_id="a1",
            task_id="t1",
            stage_id="plan",
            status="running",
            started_at="2026-01-01T00:00:00+00:00",
        )
        assert r.attempt_number == 0
