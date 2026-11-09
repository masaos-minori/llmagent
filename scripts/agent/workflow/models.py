#!/usr/bin/env python3
"""scripts/agent/workflow/models.py

Dataclasses for the Metadata DB entities and workflow definition schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Status vocabularies for the workflow state tables, mirroring the CHECK
# constraints in the DDL (db/schema_sql.py). The writers in task_ops,
# attempt_ops, and tool_call_state_ops validate against these before writing;
# tests/db/test_create_schema.py pins the DDL to these sets.
# tasks.status
TASK_STATUSES = frozenset({"pending", "running", "completed", "failed", "halted"})
# attempts.status
ATTEMPT_STATUSES = frozenset({"running", "completed", "failed"})
# tool_call_state.state
TOOL_CALL_STATES = frozenset({"pending", "completed", "failed", "interrupted"})


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
    """Retry policy configuration for a workflow.

    retry_on kinds: exception | timeout | llm_failure.
    """

    max_attempts: int
    retry_wait_sec: int
    retry_on: tuple[str, ...] = ("exception",)


@dataclass
class WorkflowDef:
    """Workflow definition with stages and retry configuration."""

    name: str
    version: str
    stages: list[StageDefinition] = field(default_factory=list)
    retry_policy: RetryPolicy = field(
        default_factory=lambda: RetryPolicy(max_attempts=3, retry_wait_sec=1)
    )

    def get_stage(self, stage_id: str) -> StageDefinition | None:
        """Return the StageDefinition for the given id, or None."""
        return next((s for s in self.stages if s.id == stage_id), None)
