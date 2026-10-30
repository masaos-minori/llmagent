#!/usr/bin/env python3
"""scripts/agent/workflow/errors.py — Typed errors for workflow.sqlite state changes."""

from __future__ import annotations


class WorkflowStateError(RuntimeError):
    """Base class for workflow state errors; keeps `except RuntimeError` handlers working."""


class TaskNotFoundError(WorkflowStateError):
    """Raised when a task id has no row in `tasks`."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"task not found: {task_id}")


class TaskTransitionError(WorkflowStateError):
    """Raised when a task status change is invalid or lost a race."""

    def __init__(self, task_id: str, found: str, requested: str) -> None:
        self.task_id = task_id
        self.found = found
        self.requested = requested
        super().__init__(
            f"invalid task transition for {task_id}: "
            f"current status is {found}, requested {requested}"
        )


class AttemptTransitionError(WorkflowStateError):
    """Raised when an attempt status change is invalid or the row is not `running`."""

    def __init__(self, attempt_id: str, found: str, requested: str) -> None:
        self.attempt_id = attempt_id
        self.found = found
        self.requested = requested
        super().__init__(
            f"invalid attempt transition for {attempt_id}: "
            f"current status is {found}, requested {requested}"
        )


class StageAlreadyRunningError(WorkflowStateError):
    """Raised when a stage is started while another attempt of it is `running`."""

    def __init__(self, task_id: str, stage_id: str) -> None:
        self.task_id = task_id
        self.stage_id = stage_id
        super().__init__(f"stage already running: {task_id}:{stage_id}")
