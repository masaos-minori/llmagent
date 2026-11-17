"""tests/test_workflow_models.py
Unit tests for agent/workflow/models.py — dataclass construction and WorkflowDef.get_stage.
"""

from __future__ import annotations

import pytest
from agent.workflow.models import (
    ArtifactRef,
    AttemptRecord,
    RetryPolicy,
    StageDefinition,
    TaskRecord,
    WorkflowDef,
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
        policy = RetryPolicy(max_attempts=3, retry_wait_sec=1, retry_on=("exception",))
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

    def test_retry_on_required(self) -> None:
        with pytest.raises(TypeError):
            RetryPolicy(max_attempts=3, retry_wait_sec=1)

    def test_workflow_def_requires_all_three(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_wait_sec=1, retry_on=("exception",))
        stages = [StageDefinition(id="plan", timeout_sec=1, retryable=False)]
        # All three supplied constructs.
        WorkflowDef(name="x", version="1.0.0", stages=stages, retry_policy=policy)
        # Omitting stages or retry_policy raises TypeError.
        with pytest.raises(TypeError):
            WorkflowDef(name="x", version="1.0.0", stages=stages)
        with pytest.raises(TypeError):
            WorkflowDef(name="x", version="1.0.0", retry_policy=policy)

    def test_empty_stages_raises_assertion(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_wait_sec=1, retry_on=("exception",))
        with pytest.raises(AssertionError):
            WorkflowDef(name="x", version="1.0.0", stages=[], retry_policy=policy)
