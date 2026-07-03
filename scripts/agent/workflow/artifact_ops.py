#!/usr/bin/env python3
"""agent/workflow/artifact_ops.py — Artifact operations for workflow.sqlite."""

import uuid
from datetime import UTC, datetime

from db.helper import SQLiteHelper

from agent.workflow.models import ArtifactRef


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_artifact(db: SQLiteHelper, task_id: str, stage_id: str, uri: str) -> ArtifactRef:
    artifact_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        """
        INSERT INTO artifacts (artifact_id, task_id, stage_id, uri, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (artifact_id, task_id, stage_id, uri, now),
    )
    db.commit()
    return ArtifactRef(
        artifact_id=artifact_id,
        task_id=task_id,
        stage_id=stage_id,
        uri=uri,
        created_at=now,
    )
