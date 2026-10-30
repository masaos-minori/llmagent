"""tests/agent/workflow/test_workflow_errors.py
Unit tests for agent/workflow/errors.py: typed workflow state errors.
"""

from __future__ import annotations

from agent.workflow.errors import (
    AttemptTransitionError,
    StageAlreadyRunningError,
    TaskNotFoundError,
    TaskTransitionError,
    WorkflowStateError,
)


def test_all_errors_are_runtime_errors() -> None:
    for exc in (
        TaskNotFoundError("t1"),
        TaskTransitionError("t1", "halted", "running"),
        AttemptTransitionError("a1", "completed", "failed"),
        StageAlreadyRunningError("t1", "plan"),
    ):
        assert isinstance(exc, WorkflowStateError)
        assert isinstance(exc, RuntimeError)


def test_task_transition_error_names_current_status() -> None:
    exc = TaskTransitionError("t1", "halted", "running")
    assert "halted" in str(exc)
    assert (exc.task_id, exc.found, exc.requested) == ("t1", "halted", "running")


def test_attempt_transition_error_attributes() -> None:
    exc = AttemptTransitionError("a1", "completed", "failed")
    assert (exc.attempt_id, exc.found, exc.requested) == ("a1", "completed", "failed")
    assert "completed" in str(exc)


def test_stage_already_running_error_attributes() -> None:
    exc = StageAlreadyRunningError("t1", "execute")
    assert (exc.task_id, exc.stage_id) == ("t1", "execute")
