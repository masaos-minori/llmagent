#!/usr/bin/env python3
"""agent/workflow/artifact_ops.py — Artifact operations for workflow.sqlite."""

import uuid

from db.helper import SQLiteHelper
from shared.json_utils import now_iso as _now

from agent.workflow.models import ArtifactRef


def record_artifact(
    db: SQLiteHelper,
    task_id: str,
    stage_id: str,
    uri: str,
    workflow_id: str | None = None,
    attempt_number: int | None = None,
) -> ArtifactRef:
    artifact_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """

        INSERT INTO artifacts (artifact_id, task_id, stage_id, uri, created_at, workflow_id, attempt_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (artifact_id, task_id, stage_id, uri, now, workflow_id, attempt_number),
    )
    db.commit()
    return ArtifactRef(
        artifact_id=artifact_id,
        task_id=task_id,
        stage_id=stage_id,
        uri=uri,
        created_at=now,
    )
