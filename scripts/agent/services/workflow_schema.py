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
    """Raise RuntimeError if the workflow definition file is missing or invalid."""
    from agent.workflow.workflow_loader import (  # lazy to avoid circular import
        WORKFLOWS_DIR,
        WorkflowLoader,
        WorkflowLoadError,
    )

    target_dir = workflows_dir if workflows_dir is not None else WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"
    if not workflow_file.exists():
        raise RuntimeError(
            f"Workflow definition file not found: {workflow_file}. Deploy config/workflows/default.json to fix this."
        )
    try:
        WorkflowLoader(workflows_dir=target_dir).load("default")
    except (WorkflowLoadError, ValueError, TypeError, AttributeError) as exc:
        raise RuntimeError(
            f"Workflow definition invalid: {workflow_file}: {exc}"
        ) from exc


# ── Workflow schema constants ─────────────────────────────────────────────────

REQUIRED_WORKFLOW_TABLES: dict[str, list[str]] = {
    "tasks": ["task_id", "session_id", "workflow_id", "status", "created_at"],
    "attempts": [
        "attempt_id",
        "task_id",
        "stage_id",
        "status",
        "owner_id",
        "lease_expires_at",
    ],
    "processed_events": ["event_id", "task_id"],
    "artifacts": ["artifact_id", "task_id"],
    "tool_call_state": [
        "idempotency_key",
        "task_id",
        "tool",
        "state",
        "retry_class",
        "created_at",
        "updated_at",
    ],
}

# Legacy migration bookkeeping tables. Their presence in a database means it
# was created or carried by the removed migration tooling; the current-schema
# gate refuses such databases read-only (compatrm001).
LEGACY_MARKER_TABLES: tuple[str, ...] = ("schema_migrations", "workflow_schema_version")

LEGACY_MARKER_REFUSAL_MESSAGE = (
    "The database does not match the current schema. Automatic migration and "
    "version stamping are not supported. Stop the service, archive the existing "
    "database if required, remove or rename it, and create a new database using "
    "the current schema."
)

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

    db = SQLiteHelper(target="workflow", db_path=db_path)

    # Check DB existence first — sqlite3.connect() creates files automatically.
    # The guard runs on the resolved path (db.DB_PATH) so the default-path case
    # is covered too: it previously checked only the explicit db_path argument.
    if not os.path.exists(db.DB_PATH):
        return SchemaCheckResult(
            valid=False, error=f"Workflow DB not found: {db.DB_PATH}"
        )

    try:
        db.open(write_mode=False, row_factory=False)
    except Exception as e:  # noqa: BLE001 — workflow DB open failure must be reported as a schema-check failure, not raised
        return SchemaCheckResult(valid=False, error=f"Failed to open workflow DB: {e}")

    try:
        tables = {
            row[0]
            for row in db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table'", ()
            )
        }
        markers = sorted(marker for marker in LEGACY_MARKER_TABLES if marker in tables)
        if markers:
            return SchemaCheckResult(
                valid=False,
                error=(
                    f"Legacy migration marker table(s) present: {', '.join(markers)}. "
                    + LEGACY_MARKER_REFUSAL_MESSAGE
                ),
            )
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

        return SchemaCheckResult(valid=True)
    finally:
        db.close()
