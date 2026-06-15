#!/usr/bin/env python3
"""agent/workflow/models.py
Dataclasses for the Metadata DB entities and workflow definition schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskRecord:
    task_id: str
    session_id: str
    turn_number: int
    workflow_version: str
    status: str  # pending | running | completed | failed | halted
    idempotency_key: str
    created_at: str  # ISO-8601
    updated_at: str  # ISO-8601


@dataclass
class AttemptRecord:
    attempt_id: str
    task_id: str
    stage_id: str
    status: str  # running | completed | failed
    started_at: str  # ISO-8601
    ended_at: str | None = None
    error_msg: str | None = None


@dataclass
class ArtifactRef:
    artifact_id: str
    task_id: str
    stage_id: str
    uri: str
    created_at: str  # ISO-8601


@dataclass
class StageDefinition:
    id: str
    description: str
    timeout_sec: int
    retryable: bool


@dataclass
class RetryPolicy:
    max_attempts: int
    backoff: str  # "fixed" | "exponential"
    backoff_sec: int


@dataclass
class WorkflowDef:
    name: str
    version: str
    stages: list[StageDefinition] = field(default_factory=list)
    retry_policy: RetryPolicy = field(
        default_factory=lambda: RetryPolicy(
            max_attempts=3, backoff="fixed", backoff_sec=1
        )
    )

    def get_stage(self, stage_id: str) -> StageDefinition | None:
        """Return the StageDefinition for the given id, or None."""
        return next((s for s in self.stages if s.id == stage_id), None)
