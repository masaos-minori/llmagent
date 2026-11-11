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
from shared.schema_fingerprint import assert_matches

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
        from db.schema_sql import build_workflow_schema_sql

        # adrrev005 REQ-003/REQ-004: full-shape fingerprint gate. Legacy marker
        # tables (schema_migrations, workflow_schema_version) and any other
        # deviation are refused here as unexpected/unexpectedly-shaped tables,
        # with the shared archive-and-recreate refusal text.
        conn = db.conn
        if conn is None:
            return SchemaCheckResult(
                valid=False, error="Failed to open workflow DB: connection is not open"
            )
        assert_matches(conn, build_workflow_schema_sql(), label="workflow.sqlite")
        return SchemaCheckResult(valid=True)
    except RuntimeError as e:  # canonical fingerprint mismatch: refusal, not a raise
        return SchemaCheckResult(valid=False, error=str(e))
    finally:
        db.close()
