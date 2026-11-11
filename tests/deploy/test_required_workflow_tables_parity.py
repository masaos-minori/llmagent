"""Pin the workflow schema gates to the canonical DDL fingerprint (wfaudit003,
adrrev005 REQ-003).

Historically deploy scripts mirrored REQUIRED_WORKFLOW_TABLES as hardcoded shell
lists and this test parsed those constants. The shell table-name lists were
subsumed by the shared fingerprint gate (deploy/init_db.sh now compares
workflow.sqlite against build_workflow_schema_sql() via shared.schema_fingerprint),
and the agent-side runtime gate (agent.services.workflow_schema.check_workflow_schema)
now runs the same fingerprint check, so REQUIRED_WORKFLOW_TABLES is gone: parity is
expressed directly against the canonical DDL. The canonical shape applies and
matches cleanly, and every shape mutation — extra table, drifted column, missing
table — is refused.
"""

from __future__ import annotations

import sqlite3

import pytest
from db.schema_sql import build_workflow_schema_sql
from shared import schema_fingerprint


def _canonical_workflow_db() -> sqlite3.Connection:
    return schema_fingerprint.apply_ddl_in_memory(build_workflow_schema_sql())


class TestWorkflowGateParityViaFingerprint:
    def test_canonical_workflow_ddl_applies_and_matches(self) -> None:
        conn = _canonical_workflow_db()
        try:
            schema_fingerprint.assert_matches(
                conn, build_workflow_schema_sql(), label="workflow"
            )
        finally:
            conn.close()

    def test_unexpected_extra_table_is_refused(self) -> None:
        conn = _canonical_workflow_db()
        try:
            conn.execute(
                "CREATE TABLE schema_migrations (id TEXT PRIMARY KEY)"  # nosec B608 — static fixture DDL
            )
            with pytest.raises(
                RuntimeError, match="unexpected table 'schema_migrations'"
            ):
                schema_fingerprint.assert_matches(
                    conn, build_workflow_schema_sql(), label="workflow"
                )
        finally:
            conn.close()

    def test_drifted_column_is_refused(self) -> None:
        conn = _canonical_workflow_db()
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN drifted_extra TEXT")  # nosec B608 — static fixture DDL
            with pytest.raises(RuntimeError, match="columns differ"):
                schema_fingerprint.assert_matches(
                    conn, build_workflow_schema_sql(), label="workflow"
                )
        finally:
            conn.close()

    def test_missing_required_table_is_refused(self) -> None:
        conn = _canonical_workflow_db()
        try:
            conn.execute("DROP TABLE tool_call_state")  # nosec B608 — static fixture DDL
            with pytest.raises(RuntimeError, match="missing table 'tool_call_state'"):
                schema_fingerprint.assert_matches(
                    conn, build_workflow_schema_sql(), label="workflow"
                )
        finally:
            conn.close()


class TestPythonGateShape:
    def test_python_gate_constants_are_gone(self) -> None:
        # adrrev005 row 10: the name-set gate and its constants were replaced by
        # the fingerprint check; they must not return.
        import agent.services.workflow_schema as ws

        for name in (
            "REQUIRED_WORKFLOW_TABLES",
            "LEGACY_MARKER_TABLES",
            "LEGACY_MARKER_REFUSAL_MESSAGE",
        ):
            assert not hasattr(ws, name), name
