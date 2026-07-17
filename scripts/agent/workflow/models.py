#!/usr/bin/env python3
"""agent/workflow/models.py

Dataclasses for the Metadata DB entities and workflow definition schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskRecord:
    """Database record for a workflow task execution."""

    task_id: str
    session_id: str | None
    turn_number: int | None
    workflow_version: str
    status: str  # pending | running | pending_approval | completed | failed | halted
    idempotency_key: str
    created_at: str  # ISO-8601
    updated_at: str  # ISO-8601
    workflow_id: str = ""


@dataclass
class ApprovalRecord:
    """Database record for a workflow approval gate."""

    approval_id: str
    task_id: str
    stage_id: str | None  # None = task-level gate
    status: str  # pending | approved | rejected
    reason: str | None
    created_at: str  # ISO-8601
    resolved_at: str | None
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
    require_approval: bool = False

    def get_stage(self, stage_id: str) -> StageDefinition | None:
        """Return the StageDefinition for the given id, or None."""
        return next((s for s in self.stages if s.id == stage_id), None)
