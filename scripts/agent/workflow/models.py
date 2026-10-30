#!/usr/bin/env python3
"""scripts/agent/workflow/models.py

Dataclasses for the Metadata DB entities and workflow definition schema.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class TaskStatus(StrEnum):
    """Task lifecycle states; values equal the persisted `tasks.status` text."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


class AttemptStatus(StrEnum):
    """Attempt lifecycle states; values equal the persisted `attempts.status` text."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Allowed task status edges. `completed -> failed` is transitional: the adapter
# overwrites a completed task when a later failure is detected; the retry plan
# removes that edge.
TASK_TRANSITIONS: Mapping[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.HALTED}),
    TaskStatus.RUNNING: frozenset(
        {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.HALTED}
    ),
    TaskStatus.FAILED: frozenset({TaskStatus.RUNNING}),
    TaskStatus.COMPLETED: frozenset({TaskStatus.FAILED}),
    TaskStatus.HALTED: frozenset(),
}

ATTEMPT_TERMINAL_STATUSES: frozenset[AttemptStatus] = frozenset(
    {AttemptStatus.COMPLETED, AttemptStatus.FAILED}
)


def is_task_transition_allowed(current: TaskStatus, new: TaskStatus) -> bool:
    """Return True when the matrix allows moving a task from `current` to `new`."""
    return new in TASK_TRANSITIONS.get(current, frozenset())


@dataclass
class TaskRecord:
    """Database record for a workflow task execution."""

    task_id: str
    session_id: str | None
    turn_number: int | None
    workflow_version: str
    status: str  # pending | running | completed | failed | halted
    task_nonce: str
    created_at: str  # ISO-8601
    updated_at: str  # ISO-8601
    workflow_id: str = ""


@dataclass
class AttemptRecord:
    """Database record for a single stage attempt within a task."""

    attempt_id: str
    task_id: str
    stage_id: str
    status: str  # running | completed | failed
    started_at: str  # ISO-8601
    ended_at: str | None = None
    error_msg: str | None = None
    attempt_number: int = 0  # persisted per task-stage number; 0 = not yet assigned


@dataclass
class ArtifactRef:
    """Reference to an artifact produced by a stage execution."""

    artifact_id: str
    task_id: str
    stage_id: str
    uri: str
    created_at: str  # ISO-8601


@dataclass
class StageDefinition:
    """A single stage in a workflow definition."""

    id: str
    timeout_sec: int
    retryable: bool


@dataclass
class RetryPolicy:
    """Retry policy configuration for a workflow."""

    max_attempts: int
    backoff_sec: int


@dataclass
class WorkflowDef:
    """Workflow definition with stages and retry configuration."""

    name: str
    version: str
    stages: list[StageDefinition] = field(default_factory=list)
    retry_policy: RetryPolicy = field(
        default_factory=lambda: RetryPolicy(max_attempts=3, backoff_sec=1)
    )

    def get_stage(self, stage_id: str) -> StageDefinition | None:
        """Return the StageDefinition for the given id, or None."""
        return next((s for s in self.stages if s.id == stage_id), None)
