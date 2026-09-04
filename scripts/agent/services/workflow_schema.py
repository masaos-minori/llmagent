"""scripts/agent/services/workflow_schema.py

Workflow schema validation functions.

Extracted from agent/repl_health.py to allow targeted loading when modifying
health check behaviour.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/agent.log")

# ── Workflow definition check ──────────────────────────────────────────────────


def check_workflow_definition(workflows_dir: Path | None = None) -> None:
    """Raise RuntimeError if the workflow definition file is missing."""
    from agent.workflow.workflow_loader import (  # lazy to avoid circular import
        WORKFLOWS_DIR,
    )

    target_dir = workflows_dir if workflows_dir is not None else WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"
    if not workflow_file.exists():
        raise RuntimeError(
            f"Workflow definition file not found: {workflow_file}. Deploy config/workflows/default.json to fix this."
        )


# ── Workflow schema constants ─────────────────────────────────────────────────

REQUIRED_WORKFLOW_TABLES: dict[str, list[str]] = {
    "tasks": ["task_id", "session_id", "workflow_id", "status", "created_at"],
    "attempts": ["attempt_id", "task_id", "stage_id", "status"],
    "processed_events": ["event_id", "task_id"],
    "artifacts": ["artifact_id", "task_id"],
    "approvals": ["approval_id", "task_id", "status"],
    "workflow_schema_version": ["version", "applied_at"],
}

_WORKFLOW_SCHEMA_READ_ONLY = True

# ── SchemaCheckResult ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SchemaCheckResult:
    """Result of a workflow schema check."""

    valid: bool
    error: str | None = None


# ── Workflow schema validation ────────────────────────────────────────────────


def check_workflow_schema(db_path: str | None = None) -> SchemaCheckResult:
    """Return SchemaCheckResult indicating whether the workflow DB schema is valid."""
    from db.helper import SQLiteHelper
    from db.schema_sql import WORKFLOW_SCHEMA_VERSION

    db = SQLiteHelper(target="workflow", db_path=db_path)

    # Check DB existence first — sqlite3.connect() creates files automatically
    if db_path and not os.path.exists(db_path):
        return SchemaCheckResult(valid=False, error=f"Workflow DB not found: {db_path}")

    try:
        db.open(write_mode=_WORKFLOW_SCHEMA_READ_ONLY, row_factory=False)
    except Exception as e:  # noqa: BLE001 — workflow DB open failure must be reported as a schema-check failure, not raised
        return SchemaCheckResult(valid=False, error=f"Failed to open workflow DB: {e}")

    try:
        tables = {
            row[0]
            for row in db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table'", ()
            )
        }
        for table, required_cols in REQUIRED_WORKFLOW_TABLES.items():
            if table not in tables:
                return SchemaCheckResult(
                    valid=False,
                    error=f"Workflow schema missing table {table!r}. Run create_workflow_schema() to initialize.",
                )
            existing = {
                row[1] for row in db.fetchall(f"PRAGMA table_info({table})", ())
            }
            for col in required_cols:
                if col not in existing:
                    return SchemaCheckResult(
                        valid=False,
                        error=f"Workflow schema missing column {table}.{col}. Reinitialize the workflow database.",
                    )

        rows = db.fetchall(
            "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1",
            (),
        )
        actual_version = rows[0][0] if rows else None
        if actual_version != WORKFLOW_SCHEMA_VERSION:
            return SchemaCheckResult(
                valid=False,
                error=f"Workflow schema version mismatch: expected {WORKFLOW_SCHEMA_VERSION!r}, "
                f"found {actual_version!r}. Run create_workflow_schema() to migrate.",
            )

        return SchemaCheckResult(valid=True)
    finally:
        db.close()
