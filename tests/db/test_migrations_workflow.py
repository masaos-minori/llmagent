"""tests/db/test_migrations_workflow.py — Workflow migration registry + CLI tests.

Exercises scripts/db/migrations_workflow.py and scripts/db/migrate_db.py against
file-based workflow.sqlite fixtures (REQ-001 migration framework, REQ-002 backup
gate, REQ-003 refusal semantics, REQ-004 dry-run, REQ-009 registered paths
preserve rows). CLI coverage runs the operator CLI as a subprocess with a
sandboxed agent.toml so no production DB path is ever touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from db import schema_sql
from db.migrate_db import EXIT_GATE_FAILURE, EXIT_OK, EXIT_REFUSAL
from db.migrate_db import main as _cli_main
from db.migrations_workflow import (
    REGISTRY,
    WORKFLOW_TARGET_VERSION,
    WORKFLOW_VERSION_CODES,
    _precommit_attempt_lease,
    _precondition_attempt_lease,
    ensure_baseline,
    runner,
    verify_backup,
)
from db.schema_sql import build_workflow_schema_sql
from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    MigrationSpec,
    read_ledger,
)

_ISO8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_PYTHON = sys.executable


# ── Fixtures ────────────────────────────────────────────────────────────────


def _legacy_workflow_db(db_path: Path, marker: str = "1.1.0") -> sqlite3.Connection:
    """Open a legacy workflow.sqlite predating the migration ledger.

    Built from the canonical workflow DDL, then the ``tasks`` key column is
    renamed back to ``idempotency_key`` (the pre-wftaskapi001 shape), the
    ``attempts`` lease columns are dropped (the pre-wflease001 shape), and the
    ledger, the lifecycle tables added by the ``workflow_tool_call_state``
    step, and the integer version are dropped/reset to reproduce the deployed
    marker-only shape.
    The ``workflow_schema_version`` string is set to *marker* (default the
    baseline "1.1.0"; pass an unmapped value such as "2.0.0" for refusals).
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(build_workflow_schema_sql())
    conn.commit()
    conn.execute("ALTER TABLE tasks RENAME COLUMN task_nonce TO idempotency_key")  # nosec B608 — fixed names
    conn.execute("ALTER TABLE attempts DROP COLUMN owner_id")  # nosec B608 — fixed names
    conn.execute("ALTER TABLE attempts DROP COLUMN lease_expires_at")  # nosec B608 — fixed names
    conn.execute("DROP TABLE schema_migrations")  # nosec B608 — fixed table name
    conn.execute("DROP TABLE IF EXISTS tool_call_state")  # nosec B608 — fixed name
    conn.execute("DROP TABLE IF EXISTS execution_snapshots")  # nosec B608 — fixed name
    conn.execute("PRAGMA user_version = 0")  # nosec B608 — baseline is a fixed int
    conn.execute("DELETE FROM workflow_schema_version")
    conn.execute(
        "INSERT INTO workflow_schema_version (version) VALUES (?)",
        (marker,),
    )
    conn.commit()
    return conn


def _populate_tasks(conn: sqlite3.Connection) -> None:
    """Insert a couple of task rows for preservation checks."""
    conn.execute(
        "INSERT INTO tasks (task_id, workflow_id, workflow_version, "
        "idempotency_key) VALUES ('t1', 'w1', '1.1.0', 's1:1')"
    )
    conn.execute(
        "INSERT INTO tasks (task_id, workflow_id, workflow_version, "
        "idempotency_key) VALUES ('t2', 'w1', '1.1.0', 's1:2')"
    )
    conn.commit()


def _ok_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Passing backup verifier (domain identity: required tables present)."""


def _failing_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Backup verifier that rejects the backup as unusable."""
    raise RuntimeError("backup failed domain verification")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _logical_state(conn: sqlite3.Connection) -> tuple[int, int, tuple]:
    """Return a comparable snapshot of the database's logical state."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    ledger = [(r.id, r.from_version, r.to_version) for r in read_ledger(conn)]
    return (version, task_count, tuple(ledger))


def _registry_with_steps(*specs: MigrationSpec) -> dict[str, MigrationSpec]:
    """A registry holding exactly the given specs for isolated path testing."""
    return {s.id: s for s in specs}


def _boom_precommit(_conn: sqlite3.Connection) -> None:
    """Pre-commit verifier that always fails (injected integrity violation)."""
    raise RuntimeError("injected pre-commit failure")


def _registry_with_failing_last_step() -> dict[str, MigrationSpec]:
    """The real registry with the last step's verification replaced by a fault.

    Mirrors the registered path exactly except that ``workflow_attempt_lease``
    fails its pre-commit check, so a mid-chain refusal can be observed against
    production-equivalent mutation SQL (AC-003).
    """
    reg: dict[str, MigrationSpec] = {}
    for sid, spec in REGISTRY.items():
        if sid == "workflow_attempt_lease":
            spec = MigrationSpec(
                id=spec.id,
                from_version=spec.from_version,
                to_version=spec.to_version,
                preconditions=spec.preconditions,
                mutation_sql=spec.mutation_sql,
                pre_commit_verification=_boom_precommit,
            )
        reg[sid] = spec
    return reg


# ── Registry + path resolution ──────────────────────────────────────────────


class TestWorkflowRegistry:
    def test_registry_holds_the_ledger_bootstrap_step(self) -> None:
        assert set(REGISTRY) == {
            "workflow_ledger_baseline",
            "workflow_tool_call_state",
            "workflow_task_nonce",
            "workflow_attempt_lease",
        }
        spec = REGISTRY["workflow_ledger_baseline"]
        assert spec.from_version == 0
        assert spec.to_version == 1
        assert spec.mutation_sql  # non-empty mutation SQL

    def test_registry_holds_the_tool_call_state_step(self) -> None:
        spec = REGISTRY["workflow_tool_call_state"]
        assert spec.from_version == 1
        assert spec.to_version == 2
        assert spec.preconditions
        assert spec.mutation_sql  # non-empty mutation SQL

    def test_registry_holds_the_task_nonce_step(self) -> None:
        spec = REGISTRY["workflow_task_nonce"]
        assert spec.from_version == 2
        assert spec.to_version == 3
        assert spec.preconditions
        assert spec.mutation_sql  # non-empty mutation SQL

    def test_registry_holds_the_attempt_lease_step(self) -> None:
        spec = REGISTRY["workflow_attempt_lease"]
        assert spec.from_version == 3
        assert spec.to_version == 4
        assert spec.preconditions
        assert spec.pre_commit_verification is not None
        assert spec.mutation_sql  # non-empty mutation SQL

    def test_registry_verifies_precommit_not_postcommit(self) -> None:
        # dbmigsafe001 REQ-003: every spec verifies inside the step
        # transaction; no spec keeps a post-commit postcondition callback.
        for spec in REGISTRY.values():
            assert spec.pre_commit_verification is not None, spec.id
            assert spec.postcondition is None, spec.id

    def test_version_codes_and_target_include_the_lease_code(self) -> None:
        assert WORKFLOW_VERSION_CODES == {
            "1.1.0": 0,
            "1.2.0": 2,
            "1.3.0": 3,
            "1.4.0": 4,
        }
        assert WORKFLOW_TARGET_VERSION == 4
        assert max(spec.to_version for spec in REGISTRY.values()) == (
            WORKFLOW_TARGET_VERSION
        )

    def test_runner_resolves_the_unique_forward_path(self, tmp_path: Path) -> None:
        conn = _legacy_workflow_db(tmp_path / "workflow.sqlite")
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            assert [s.id for s in planned] == [
                "workflow_ledger_baseline",
                "workflow_tool_call_state",
                "workflow_task_nonce",
                "workflow_attempt_lease",
            ]
        finally:
            conn.close()


# ── Bootstrap ───────────────────────────────────────────────────────────────


class TestWorkflowBootstrap:
    def test_apply_migrates_and_preserves_rows_and_marker(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        before = _logical_state(conn)
        before_hash = _hash_file(db)

        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY, target_version=1)
            applied = runner.apply(conn, planned, _ok_verifier)

            assert [a.id for a in applied] == ["workflow_ledger_baseline"]
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
            # Ledger row recorded with an ISO-8601 UTC stamp.
            rows = read_ledger(conn)
            assert [(r.id, r.from_version, r.to_version) for r in rows] == [
                ("workflow_ledger_baseline", 0, 1)
            ]
            assert all(_ISO8601_UTC_RE.match(r.applied_at) for r in rows), rows
            # Legacy string marker preserved unchanged.
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.1.0"
        finally:
            conn.close()

        after = _logical_state(sqlite3.connect(str(db)))
        after_hash = _hash_file(db)
        assert after[1] == before[1]  # task count unchanged
        assert after[0] == 1  # stamped to target
        assert after[2] == before[2] + (("workflow_ledger_baseline", 0, 1),)
        assert after_hash != before_hash  # the ledger DDL changed the file


class TestWorkflowResume:
    def test_resume_skips_already_applied_step(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        try:
            runner.apply(
                conn,
                runner.plan(0, read_ledger(conn), REGISTRY, target_version=1),
                _ok_verifier,
            )
            rest = runner.plan(1, read_ledger(conn), REGISTRY, target_version=1)
            assert rest == []
        finally:
            conn.close()


# ── Tool-call lifecycle tables (toolexec001 row 06: 1 -> 2) ────────────────


class TestWorkflowToolCallStateStep:
    def _bootstrapped(self, tmp_path: Path) -> tuple[Path, sqlite3.Connection]:
        """A post-bootstrap (code 1) workflow database with task rows."""
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        runner.apply(
            conn,
            runner.plan(0, read_ledger(conn), REGISTRY, target_version=1),
            _ok_verifier,
        )
        return db, conn

    def test_step_migrates_preserves_rows_and_stamps_marker(
        self, tmp_path: Path
    ) -> None:
        db, conn = self._bootstrapped(tmp_path)
        try:
            planned = runner.plan(1, read_ledger(conn), REGISTRY, target_version=2)
            assert [s.id for s in planned] == ["workflow_tool_call_state"]
            applied = runner.apply(conn, planned, _ok_verifier)
            assert [a.id for a in applied] == ["workflow_tool_call_state"]

            version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert version == 2
            tables = {
                str(r[0])
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert {"tool_call_state", "execution_snapshots"} <= tables
            indexes = {
                str(r[0])
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND name LIKE 'idx_tool_call_state%'"
                )
            }
            assert indexes  # the (task_id, state) pending-scan index landed

            # Task rows preserved; marker advanced to the step's pinned literal.
            task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            assert task_count == 2
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.2.0"
            assert [
                (r.id, r.from_version, r.to_version) for r in read_ledger(conn)
            ] == [
                ("workflow_ledger_baseline", 0, 1),
                ("workflow_tool_call_state", 1, 2),
            ]
        finally:
            conn.close()

    def test_resume_after_full_path_is_empty(self, tmp_path: Path) -> None:
        _db, conn = self._bootstrapped(tmp_path)
        try:
            runner.apply(
                conn, runner.plan(1, read_ledger(conn), REGISTRY), _ok_verifier
            )
            assert runner.plan(2, read_ledger(conn), REGISTRY) == []
        finally:
            conn.close()

    def test_forged_stamp_without_ledger_refused(self, tmp_path: Path) -> None:
        # A database stamped 1 that never went through the gated bootstrap
        # (no ledger) cannot take the lifecycle step.
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.execute("PRAGMA user_version = 1")  # nosec B608 — fixed int
        conn.commit()
        try:
            planned = runner.plan(1, [], REGISTRY)
            with pytest.raises(MigrationRefusalError):
                runner.apply(conn, planned, _ok_verifier)
            assert "workflow_tool_call_state" not in [r.id for r in read_ledger(conn)]
        finally:
            conn.close()

    def test_step_refused_when_tables_already_present(self, tmp_path: Path) -> None:
        _db, conn = self._bootstrapped(tmp_path)
        conn.execute("CREATE TABLE tool_call_state (idempotency_key TEXT PRIMARY KEY)")  # nosec B608 — fixed DDL
        conn.commit()
        try:
            with pytest.raises(MigrationRefusalError, match="tool_call_state"):
                runner.apply(
                    conn, runner.plan(1, read_ledger(conn), REGISTRY), _ok_verifier
                )
        finally:
            conn.close()

    def test_fresh_and_migrated_databases_converge(self, tmp_path: Path) -> None:
        """Fresh-create and migrated shapes are identical (completion criterion)."""
        fresh_conn = sqlite3.connect(str(tmp_path / "fresh.sqlite"))
        fresh_conn.executescript(build_workflow_schema_sql())
        fresh_conn.execute(
            "INSERT INTO workflow_schema_version (version) VALUES (?)",
            ("1.4.0",),
        )
        ensure_baseline(fresh_conn)
        _db, migrated_conn = self._bootstrapped(
            tmp_path,
        )
        try:
            runner.apply(
                migrated_conn,
                runner.plan(1, read_ledger(migrated_conn), REGISTRY),
                _ok_verifier,
            )

            def tables(conn: sqlite3.Connection) -> set[str]:
                return {
                    str(r[0])
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }

            def columns(conn: sqlite3.Connection, table: str) -> list[tuple]:
                return [
                    (r[1], r[2], r[3], r[5])
                    for r in conn.execute(f"PRAGMA table_info({table})")
                ]

            assert tables(fresh_conn) == tables(migrated_conn)
            fresh_version = fresh_conn.execute("PRAGMA user_version").fetchone()[0]
            migrated_version = migrated_conn.execute("PRAGMA user_version").fetchone()[
                0
            ]
            assert fresh_version == migrated_version == 4
            for table in (
                "tasks",
                "tool_call_state",
                "execution_snapshots",
                "attempts",
            ):
                assert columns(fresh_conn, table) == columns(migrated_conn, table)
            fresh_marker = fresh_conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            migrated_marker = migrated_conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert fresh_marker == migrated_marker == "1.4.0"
        finally:
            fresh_conn.close()
            migrated_conn.close()


# ── Task-key rename (wftaskapi001 row 12: 2 -> 3) ──────────────────────────


class TestWorkflowTaskNonceStep:
    def _at_code_2(self, tmp_path: Path) -> tuple[Path, sqlite3.Connection]:
        """A bootstrapped, lifecycle-migrated (code 2) database with task rows."""
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        runner.apply(
            conn,
            runner.plan(0, read_ledger(conn), REGISTRY, target_version=2),
            _ok_verifier,
        )
        return db, conn

    def test_step_renames_column_and_preserves_rows(self, tmp_path: Path) -> None:
        _db, conn = self._at_code_2(tmp_path)
        try:
            planned = runner.plan(2, read_ledger(conn), REGISTRY, target_version=3)
            assert [s.id for s in planned] == ["workflow_task_nonce"]
            applied = runner.apply(conn, planned, _ok_verifier)
            assert [a.id for a in applied] == ["workflow_task_nonce"]

            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
            columns = {str(r[1]) for r in conn.execute("PRAGMA table_info(tasks)")}
            assert "task_nonce" in columns
            assert "idempotency_key" not in columns
            # RENAME COLUMN never touches stored values (AC-4).
            rows = conn.execute(
                "SELECT task_id, task_nonce FROM tasks ORDER BY task_id"
            ).fetchall()
            assert rows == [("t1", "s1:1"), ("t2", "s1:2")]
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.3.0"
            # read_ledger orders by (applied_at, id); rows written in the same
            # second tie-break by id, so compare as a sorted set of rows.
            assert sorted(
                (r.id, r.from_version, r.to_version) for r in read_ledger(conn)
            ) == sorted(
                [
                    ("workflow_ledger_baseline", 0, 1),
                    ("workflow_tool_call_state", 1, 2),
                    ("workflow_task_nonce", 2, 3),
                ]
            )
        finally:
            conn.close()

    def test_step_refused_when_column_already_renamed(self, tmp_path: Path) -> None:
        _db, conn = self._at_code_2(tmp_path)
        # Rename the column by hand (no ledger row): the precondition must
        # refuse instead of re-running, and the plan stays unmutated.
        conn.execute("ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce")  # nosec B608 — fixed names
        conn.commit()
        try:
            with pytest.raises(MigrationRefusalError, match="task_nonce"):
                runner.apply(
                    conn, runner.plan(2, read_ledger(conn), REGISTRY), _ok_verifier
                )
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 2  # untouched
            assert "workflow_task_nonce" not in [r.id for r in read_ledger(conn)]
        finally:
            conn.close()

    def test_resume_after_full_path_skips_rename_step(self, tmp_path: Path) -> None:
        _db, conn = self._at_code_2(tmp_path)
        try:
            runner.apply(
                conn, runner.plan(2, read_ledger(conn), REGISTRY), _ok_verifier
            )
            assert runner.plan(3, read_ledger(conn), REGISTRY) == []
        finally:
            conn.close()


# ── Attempt-lease columns (wflease001 row 17: 3 -> 4) ───────────────────────


class TestWorkflowAttemptLeaseStep:
    def _at_code_3(self, tmp_path: Path) -> tuple[Path, sqlite3.Connection]:
        """A migrated task-nonce (code 3) database with a seeded running attempt.

        The attempt row is seeded with the exact production ``Z`` timestamp
        format (REQ-009) so the migrated row also feeds procedure 02's legacy
        age branch.
        """
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        runner.apply(
            conn,
            runner.plan(0, read_ledger(conn), REGISTRY, target_version=3),
            _ok_verifier,
        )
        conn.execute(
            "INSERT INTO attempts (attempt_id, task_id, stage_id, status, "
            "started_at) VALUES ('a1', 't1', 's1', 'running', "
            "'2026-10-30T00:00:00Z')"
        )
        conn.commit()
        return db, conn

    def test_step_adds_columns_and_preserves_running_rows(self, tmp_path: Path) -> None:
        _db, conn = self._at_code_3(tmp_path)
        try:
            planned = runner.plan(3, read_ledger(conn), REGISTRY)
            assert [s.id for s in planned] == ["workflow_attempt_lease"]
            applied = runner.apply(conn, planned, _ok_verifier)
            assert [a.id for a in applied] == ["workflow_attempt_lease"]

            assert conn.execute("PRAGMA user_version").fetchone()[0] == 4
            columns = {str(r[1]) for r in conn.execute("PRAGMA table_info(attempts)")}
            assert {"owner_id", "lease_expires_at"} <= columns
            # ADD COLUMN never touches stored values; both new columns are
            # null on the pre-existing running row (AC-8).
            row = conn.execute(
                "SELECT attempt_id, task_id, stage_id, status, started_at, "
                "owner_id, lease_expires_at FROM attempts"
            ).fetchone()
            assert row == (
                "a1",
                "t1",
                "s1",
                "running",
                "2026-10-30T00:00:00Z",
                None,
                None,
            )
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.4.0"
            assert sorted(
                (r.id, r.from_version, r.to_version) for r in read_ledger(conn)
            ) == sorted(
                [
                    ("workflow_ledger_baseline", 0, 1),
                    ("workflow_tool_call_state", 1, 2),
                    ("workflow_task_nonce", 2, 3),
                    ("workflow_attempt_lease", 3, 4),
                ]
            )
        finally:
            conn.close()

    def test_resume_after_full_path_skips_lease_step(self, tmp_path: Path) -> None:
        _db, conn = self._at_code_3(tmp_path)
        try:
            runner.apply(
                conn, runner.plan(3, read_ledger(conn), REGISTRY), _ok_verifier
            )
            assert runner.plan(4, read_ledger(conn), REGISTRY) == []
        finally:
            conn.close()

    def test_step_refused_when_lease_columns_already_present(
        self, tmp_path: Path
    ) -> None:
        _db, conn = self._at_code_3(tmp_path)
        # Add a lease column by hand (no ledger row): the precondition must
        # refuse instead of re-running, and the ledger stays unmutated.
        conn.execute("ALTER TABLE attempts ADD COLUMN owner_id TEXT")  # nosec B608 — fixed DDL
        conn.commit()
        try:
            with pytest.raises(MigrationRefusalError, match="lease"):
                runner.apply(
                    conn, runner.plan(3, read_ledger(conn), REGISTRY), _ok_verifier
                )
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3  # untouched
            assert "workflow_attempt_lease" not in [r.id for r in read_ledger(conn)]
        finally:
            conn.close()

    def test_forged_stamp_without_ledger_refused(self, tmp_path: Path) -> None:
        # A database stamped 3 that never went through the gated bootstrap
        # (no baseline ledger row) cannot take the lease step (pattern of the
        # lifecycle step's forged-stamp refusal).
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.execute("PRAGMA user_version = 3")  # nosec B608 — fixed int
        conn.commit()
        try:
            planned = runner.plan(3, [], REGISTRY)
            with pytest.raises(MigrationRefusalError, match="workflow_attempt_lease"):
                runner.apply(conn, planned, _ok_verifier)
            assert "workflow_attempt_lease" not in [r.id for r in read_ledger(conn)]
        finally:
            conn.close()

    def test_precondition_refuses_a_database_at_another_version(
        self, tmp_path: Path
    ) -> None:
        _db, conn = self._at_code_3(tmp_path)
        try:
            # The happy path first: a 3-stamped database passes unchanged.
            _precondition_attempt_lease(conn)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
            for forged in (2, 4):
                conn.execute(f"PRAGMA user_version = {forged}")  # nosec B608 — fixed int
                with pytest.raises(
                    MigrationRefusalError, match="applies only to a 3-stamped"
                ):
                    _precondition_attempt_lease(conn)
        finally:
            conn.close()

    def test_precondition_names_the_missing_attempts_table(
        self, tmp_path: Path
    ) -> None:
        _db, conn = self._at_code_3(tmp_path)
        try:
            conn.execute("DROP TABLE attempts")  # nosec B608 — fixed name
            with pytest.raises(MigrationRefusalError, match="missing required table"):
                _precondition_attempt_lease(conn)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3  # untouched
        finally:
            conn.close()

    def test_precommit_refuses_a_stale_version_stamp(self, tmp_path: Path) -> None:
        # The verifier runs pre-commit inside the step transaction: a mismatch
        # is an integrity violation, raised as RuntimeError, not a refusal.
        _db, conn = self._at_code_3(tmp_path)
        try:
            with pytest.raises(RuntimeError, match="not 4"):
                _precommit_attempt_lease(conn)
        finally:
            conn.close()

    def test_precommit_refuses_a_forged_stamp_without_columns(
        self, tmp_path: Path
    ) -> None:
        # The stamp moved to 4 but the columns did not — a half-applied
        # database the pre-commit verifier must surface instead of blessing.
        _db, conn = self._at_code_3(tmp_path)
        try:
            conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed int
            with pytest.raises(RuntimeError, match="did not add"):
                _precommit_attempt_lease(conn)
        finally:
            conn.close()


# ── Pre-commit rollback (dbmigsafe001 REQ-003 / AC-003) ──────────────────────


class TestPrecommitRollback:
    def test_failed_precommit_rolls_back_schema_version_and_ledger(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        try:
            reg = _registry_with_failing_last_step()
            planned = runner.plan(0, read_ledger(conn), reg)
            assert [s.id for s in planned] == [
                "workflow_ledger_baseline",
                "workflow_tool_call_state",
                "workflow_task_nonce",
                "workflow_attempt_lease",
            ]
            with pytest.raises(RuntimeError, match="injected pre-commit failure"):
                runner.apply(conn, planned, _ok_verifier)
            # The failing step left no trace: its schema change, version stamp,
            # and ledger row all rolled back with it; the earlier committed
            # steps stand (AC-003/AC-2).
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
            columns = {r[1] for r in conn.execute("PRAGMA table_info(attempts)")}
            assert "owner_id" not in columns
            assert "lease_expires_at" not in columns
            assert [r.id for r in read_ledger(conn)] == [
                "workflow_ledger_baseline",
                "workflow_tool_call_state",
                "workflow_task_nonce",
            ]
            assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 2
        finally:
            conn.close()


# ── Refusals ────────────────────────────────────────────────────────────────


class TestWorkflowRefusal:
    def test_unknown_target_refused_before_mutation(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        before_hash = _hash_file(db)
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.plan(0, read_ledger(conn), REGISTRY, target_version=5)
            assert excinfo.value.reason == MigrationRefusalReason.UNKNOWN_PATH
            assert _hash_file(db) == before_hash  # no mutation occurred
        finally:
            conn.close()

    def test_downgrade_step_refused(self, tmp_path: Path) -> None:
        # Inject a registered backward step to exercise the downgrade guard.
        backward = MigrationSpec(
            id="backward",
            from_version=1,
            to_version=0,
            mutation_sql="PRAGMA user_version = 0",
        )
        reg = _registry_with_steps(backward)
        conn = sqlite3.connect(str(tmp_path / "workflow.sqlite"))
        conn.execute("PRAGMA user_version = 1")
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.plan(1, [], reg, target_version=0)
            assert excinfo.value.reason == MigrationRefusalReason.DOWNGRADE
        finally:
            conn.close()

    def test_unmapped_string_version_refused_by_precondition(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db, marker="2.0.0")
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.apply(conn, planned, _ok_verifier)
            assert excinfo.value.reason == MigrationRefusalReason.UNKNOWN_PATH
            # The bootstrap mutation never stamped the version.
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        finally:
            conn.close()

    def test_missing_clean_checkpoint_refuses(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        # A second connection holds an uncommitted write; the WAL checkpoint
        # cannot complete cleanly. The refusal reason is the distinct
        # checkpoint-busy class, not a backup-integrity failure (REQ-004).
        holder = sqlite3.connect(str(db))
        holder.execute("BEGIN")
        holder.execute(
            "INSERT INTO tasks (task_id, workflow_id, workflow_version, "
            "idempotency_key) VALUES ('x', 'w', '1.1.0', 's:x')"
        )
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.apply(conn, planned, _ok_verifier)
            assert excinfo.value.reason == MigrationRefusalReason.CHECKPOINT_BUSY
        finally:
            holder.rollback()
            holder.close()
            conn.close()

    def test_backup_gate_refuses_on_bad_backup(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.apply(conn, planned, _failing_verifier)
            assert excinfo.value.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 0  # untouched
        finally:
            conn.close()

    def test_verify_backup_requires_required_tables(self, tmp_path: Path) -> None:
        # A database missing the required workflow table fails domain identity.
        conn = sqlite3.connect(str(tmp_path / "wrong.sqlite"))
        conn.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY)")
        conn.commit()
        with pytest.raises(RuntimeError, match="missing required table"):
            verify_backup(conn, str(tmp_path / "wrong.sqlite"))
        conn.close()


class TestWorkflowStepFailure:
    def test_failing_step_leaves_db_at_last_good_state(self, tmp_path: Path) -> None:
        # A two-step chain where the second step's precondition fails mid
        # migration: the framework rolls back only the failing step and leaves
        # the database at the last completed step (AC-2).
        step_a = MigrationSpec(
            id="step_a",
            from_version=0,
            to_version=1,
            mutation_sql="PRAGMA user_version = 1",
        )

        def _fail_precondition(_conn: sqlite3.Connection) -> None:
            raise MigrationRefusalError(
                MigrationRefusalReason.UNKNOWN_PATH,
                "forced step failure",
            )

        step_b = MigrationSpec(
            id="step_b",
            from_version=1,
            to_version=2,
            preconditions=(_fail_precondition,),
            mutation_sql="PRAGMA user_version = 2",
        )
        reg = _registry_with_steps(step_a, step_b)
        conn = _legacy_workflow_db(tmp_path / "workflow.sqlite")
        try:
            planned = runner.plan(0, read_ledger(conn), reg)
            assert [s.id for s in planned] == ["step_a", "step_b"]
            with pytest.raises(MigrationRefusalError):
                runner.apply(conn, planned, _ok_verifier)
            # Ended at step_a's state: version advanced once, step_b absent.
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
            ledger_ids = [r.id for r in read_ledger(conn)]
            assert "step_a" in ledger_ids
            assert "step_b" not in ledger_ids
        finally:
            conn.close()


# ── Dry-run ─────────────────────────────────────────────────────────────────


class TestWorkflowDryRun:
    def test_dry_run_leaves_file_byte_identical(self, tmp_path: Path) -> None:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        before = _logical_state(conn)
        before_hash = _hash_file(db)
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            applied = runner.apply(conn, planned, _ok_verifier, dry_run=True)
            assert applied == []
            assert _hash_file(db) == before_hash
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
            assert read_ledger(conn) == []
        finally:
            conn.close()
        assert _logical_state(conn := sqlite3.connect(str(db))) == before
        conn.close()


# ── Step version literals (procedure 05, Plan REQ-005) ─────────────────────


class TestStepVersionLiterals:
    """Each mutation step writes its own pinned marker literal."""

    def _latest_marker(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT version FROM workflow_schema_version "
            "ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
        return str(row[0])

    def _bootstrap(self, tmp_path: Path) -> sqlite3.Connection:
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        _populate_tasks(conn)
        return conn

    def test_each_step_writes_its_pinned_literal(self, tmp_path: Path) -> None:
        conn = self._bootstrap(tmp_path)
        try:
            runner.apply(
                conn,
                runner.plan(0, read_ledger(conn), REGISTRY, target_version=2),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.2.0"

            runner.apply(
                conn,
                runner.plan(2, read_ledger(conn), REGISTRY, target_version=3),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.3.0"

            runner.apply(
                conn,
                runner.plan(3, read_ledger(conn), REGISTRY, target_version=4),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.4.0"
        finally:
            conn.close()

    def test_bumped_head_constant_does_not_move_step_markers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(schema_sql, "WORKFLOW_SCHEMA_VERSION", "9.9.9")
        conn = self._bootstrap(tmp_path)
        try:
            runner.apply(
                conn,
                runner.plan(0, read_ledger(conn), REGISTRY, target_version=2),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.2.0"

            runner.apply(
                conn,
                runner.plan(2, read_ledger(conn), REGISTRY, target_version=3),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.3.0"

            runner.apply(
                conn,
                runner.plan(3, read_ledger(conn), REGISTRY, target_version=4),
                _ok_verifier,
            )
            assert self._latest_marker(conn) == "1.4.0"
        finally:
            conn.close()


# ── CLI (subprocess) ─────────────────────────────────────────────────────────


def _write_cli_config(config_dir: Path, workflow_db: Path) -> None:
    """Write a sandboxed agent.toml pointing every DB path inside *config_dir*.

    The workflow path points at the caller's fixture so the CLI opens it while
    the subprocess never resolves a production path under /opt/llm.
    """
    (config_dir / "agent.toml").write_text(
        f'rag_db_path = "{config_dir / "rag.sqlite"}"\n'
        f'session_db_path = "{config_dir / "session.sqlite"}"\n'
        f'workflow_db_path = "{workflow_db}"\n'
        f'eventbus_db_path = "{config_dir / "eventbus.sqlite"}"\n'
        "sqlite_timeout = 30\n"
        "sqlite_busy_timeout_ms = 30000\n",
        encoding="utf-8",
    )


def _run_cli(workflow_db: Path, config_dir: Path, *args: str) -> Any:
    """Run the workflow migration CLI as a subprocess with a sandboxed env."""
    _write_cli_config(config_dir, workflow_db)
    env = {
        **os.environ,
        "PYTHONPATH": str(_SCRIPTS),
        "LLMAGENT_CONFIG_DIR": str(config_dir),
    }
    return subprocess.run(
        [_PYTHON, "-m", "db.migrate_db", *args],  # nosec B603 — fixed argv
        cwd=str(_SCRIPTS),
        env=env,
        capture_output=True,
        text=True,
    )


class TestWorkflowCli:
    def test_status_reports_marker_and_empty_ledger(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.close()  # checkpoint WAL into the main file before the subprocess copies it
        result = _run_cli(db, config_dir, "--status")
        assert result.returncode == 0
        assert "user_version=0" in result.stdout
        assert "marker=1.1.0" in result.stdout
        assert "ledger: (empty)" in result.stdout

    def test_dry_run_leaves_fixture_byte_identical(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.close()
        before = _hash_file(db)
        result = _run_cli(db, config_dir, "--dry-run")
        assert result.returncode == 0
        assert "would apply" in result.stdout
        assert _hash_file(db) == before  # nothing mutated

    def test_apply_then_status_shows_baseline_row(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.close()
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        apply = _run_cli(db, config_dir, "--apply", "--archive-dir", str(archive_dir))
        assert apply.returncode == 0
        assert "user_version now 4" in apply.stdout
        status = _run_cli(db, config_dir, "--status")
        assert status.returncode == 0
        # AC-007: both --status fields pinned — user_version= integer code and
        # marker= semantic string.
        assert "user_version=4" in status.stdout
        assert "marker=1.4.0" in status.stdout
        assert "workflow_ledger_baseline" in status.stdout
        assert "0 -> 1" in status.stdout
        assert "workflow_tool_call_state" in status.stdout
        assert "1 -> 2" in status.stdout
        assert "workflow_task_nonce" in status.stdout
        assert "2 -> 3" in status.stdout
        assert "workflow_attempt_lease" in status.stdout
        assert "3 -> 4" in status.stdout
        # Ledger append order (REQ-005): seq monotonic with the printed order.
        conn = sqlite3.connect(str(db))
        try:
            seqs = [r.seq for r in read_ledger(conn)]
            assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs) == 4
        finally:
            conn.close()
        # CLI apply archived the pre-run state (AC-001 CLI half).
        assert len(list(archive_dir.glob("*.sqlite"))) == 1
        assert len(list(archive_dir.glob("*.audit.json"))) == 1

    def test_apply_is_idempotent_after_bootstrap(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.close()
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        _run_cli(db, config_dir, "--apply", "--archive-dir", str(archive_dir))
        again = _run_cli(db, config_dir, "--apply", "--archive-dir", str(archive_dir))
        assert again.returncode == 0
        assert "already at target version" in again.stdout

    def test_unmapped_string_version_refused_no_mutation(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db, marker="2.0.0")
        conn.close()
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        before = _hash_file(db)
        result = _run_cli(db, config_dir, "--apply", "--archive-dir", str(archive_dir))
        # REFUSAL exit class (2); the CLI pre-runs preconditions so nothing is
        # mutated (AC-2) and no archive is created for a refused run.
        assert result.returncode == 2
        assert _hash_file(db) == before
        assert list(archive_dir.iterdir()) == []

    def test_busy_database_produces_gate_refusal(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        # Hold an uncommitted write so the gate's WAL checkpoint stays busy.
        holder = sqlite3.connect(str(db))
        holder.execute("BEGIN")
        holder.execute(
            "INSERT INTO tasks (task_id, workflow_id, workflow_version, "
            "idempotency_key) VALUES ('x', 'w', '1.1.0', 's:x')"
        )
        conn.close()  # only the holder keeps a write transaction open
        try:
            archive_dir = tmp_path / "archive"
            archive_dir.mkdir()
            result = _run_cli(
                db, config_dir, "--apply", "--archive-dir", str(archive_dir)
            )
            # CHECKPOINT_BUSY is a gate-family reason: EXIT_GATE_FAILURE (1).
            assert result.returncode == EXIT_GATE_FAILURE
            assert "checkpoint busy" in result.stderr
            # A gate refusal archives nothing.
            assert list(archive_dir.iterdir()) == []
        finally:
            holder.rollback()
            holder.close()


# ── CLI --db option (procedure 05, Plan REQ-006) ────────────────────────────


class TestWorkflowCliDbOption:
    """Every CLI mode operates on the --db file and never opens the configured one."""

    def _sandbox(self, tmp_path: Path) -> tuple[Path, Path, Path]:
        """Configured database (must stay untouched) and a separate legacy copy."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        configured = tmp_path / "configured.sqlite"
        _legacy_workflow_db(configured).close()
        target = tmp_path / "target.sqlite"
        _legacy_workflow_db(target).close()
        return config_dir, configured, target

    def test_status_reports_copy_and_leaves_configured_untouched(
        self, tmp_path: Path
    ) -> None:
        config_dir, configured, target = self._sandbox(tmp_path)
        configured_before = _hash_file(configured)
        result = _run_cli(configured, config_dir, "--status", "--db", str(target))
        assert result.returncode == 0
        assert "1.1.0" in result.stdout
        assert _hash_file(configured) == configured_before

    def test_dry_run_leaves_copy_byte_identical(self, tmp_path: Path) -> None:
        config_dir, configured, target = self._sandbox(tmp_path)
        configured_before = _hash_file(configured)
        target_before = _hash_file(target)
        result = _run_cli(configured, config_dir, "--dry-run", "--db", str(target))
        assert result.returncode == 0
        assert _hash_file(target) == target_before
        assert _hash_file(configured) == configured_before

    def test_apply_migrates_copy_and_leaves_configured_untouched(
        self, tmp_path: Path
    ) -> None:
        config_dir, configured, target = self._sandbox(tmp_path)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        configured_before = _hash_file(configured)
        result = _run_cli(
            configured,
            config_dir,
            "--apply",
            "--db",
            str(target),
            "--archive-dir",
            str(archive_dir),
        )
        assert result.returncode == 0

        conn = sqlite3.connect(str(target))
        try:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 4
            rows = {(r.id, r.from_version, r.to_version) for r in read_ledger(conn)}
            # read_ledger orders by append (rowid) order; same-second steps are
            # distinguished by seq, so compare the recorded set, not raw order.
            assert rows == {
                ("workflow_ledger_baseline", 0, 1),
                ("workflow_tool_call_state", 1, 2),
                ("workflow_task_nonce", 2, 3),
                ("workflow_attempt_lease", 3, 4),
            }
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.4.0"
        finally:
            conn.close()
        assert _hash_file(configured) == configured_before

    def test_apply_with_missing_db_refuses_and_creates_no_file(
        self, tmp_path: Path
    ) -> None:
        config_dir, configured, _target = self._sandbox(tmp_path)
        missing = tmp_path / "missing.sqlite"
        configured_before = _hash_file(configured)
        result = _run_cli(configured, config_dir, "--apply", "--db", str(missing))
        assert result.returncode == 2  # EXIT_REFUSAL
        assert not missing.exists()
        assert _hash_file(configured) == configured_before

    # In-process twins of the subprocess cases above: the repo coverage gate
    # (diff-cover >= 90% on changed lines) cannot observe subprocess runs, so
    # main() is called directly. With --db the helper bypasses configuration and
    # only the tmp_path copy is opened.
    def test_main_status_on_copy_in_process(self, tmp_path: Path, capsys) -> None:
        _config_dir, _configured, target = self._sandbox(tmp_path)
        assert _cli_main(["--status", "--db", str(target)]) == EXIT_OK
        assert "marker=1.1.0" in capsys.readouterr().out

    def test_main_dry_run_in_process_leaves_copy_byte_identical(
        self, tmp_path: Path
    ) -> None:
        _config_dir, _configured, target = self._sandbox(tmp_path)
        before = _hash_file(target)
        assert _cli_main(["--dry-run", "--db", str(target)]) == EXIT_OK
        assert _hash_file(target) == before

    def test_main_apply_in_process_migrates_copy(self, tmp_path: Path) -> None:
        _config_dir, _configured, target = self._sandbox(tmp_path)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        code = _cli_main(
            ["--apply", "--db", str(target), "--archive-dir", str(archive_dir)]
        )
        assert code == EXIT_OK
        conn = sqlite3.connect(str(target))
        try:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 4
            latest = conn.execute(
                "SELECT version FROM workflow_schema_version "
                "ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()[0]
            assert latest == "1.4.0"
        finally:
            conn.close()

    def test_main_apply_missing_db_refuses_in_process(self, tmp_path: Path) -> None:
        _config_dir, _configured, _target = self._sandbox(tmp_path)
        missing = tmp_path / "missing.sqlite"
        assert _cli_main(["--apply", "--db", str(missing)]) == EXIT_REFUSAL
        assert not missing.exists()

    def test_main_apply_without_archive_dir_refuses_in_process(
        self, tmp_path: Path
    ) -> None:
        # --apply without an explicit archive target is a refusal (exit 2);
        # no default location is ever inferred, and the database is untouched.
        _config_dir, _configured, target = self._sandbox(tmp_path)
        before = _hash_file(target)
        with pytest.raises(SystemExit) as excinfo:
            _cli_main(["--apply", "--db", str(target)])
        assert excinfo.value.code == EXIT_REFUSAL
        assert _hash_file(target) == before

    def test_main_apply_creates_archive_and_audit_in_process(
        self, tmp_path: Path
    ) -> None:
        # AC-001 CLI half: the durable archive + machine-readable audit exist
        # under the operator-supplied dir and match the pre-run state.
        _config_dir, _configured, target = self._sandbox(tmp_path)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        code = _cli_main(
            ["--apply", "--db", str(target), "--archive-dir", str(archive_dir)]
        )
        assert code == EXIT_OK
        archives = sorted(archive_dir.glob("target-v0-*.sqlite"))
        audits = sorted(archive_dir.glob("target-v0-*.audit.json"))
        assert len(archives) == 1 and len(audits) == 1
        audit = json.loads(audits[0].read_text(encoding="utf-8"))
        assert audit["archive_path"] == str(archives[0])
        assert audit["sha256"] == _hash_file(archives[0])
        assert audit["source_version"] == 0
        assert audit["retention_status"] == "unset"
        ach = sqlite3.connect(str(archives[0]))
        try:
            assert ach.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert ach.execute("PRAGMA user_version").fetchone()[0] == 0
        finally:
            ach.close()


# ── REQ-007: durable archive restore integration (AC-002) ───────────────────


class TestArchiveRestoreIntegration:
    def test_restore_archive_after_mid_run_failure(self, tmp_path: Path) -> None:
        """A WAL-mode database is restorable from the durable archive after a
        mid-chain failure that already committed the earlier steps."""
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.execute("PRAGMA journal_mode=WAL")
        _populate_tasks(conn)
        pre_tasks = conn.execute(
            "SELECT task_id, workflow_id, workflow_version, idempotency_key "
            "FROM tasks ORDER BY task_id"
        ).fetchall()

        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        reg = _registry_with_failing_last_step()
        planned = runner.plan(0, read_ledger(conn), reg)
        with pytest.raises(RuntimeError, match="injected pre-commit failure"):
            runner.apply(conn, planned, _ok_verifier, archive_dir=archive_dir)

        # The live database is partially migrated: the last step failed but the
        # earlier steps committed — exactly the state recovery must undo.
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        conn.close()

        # The durable archive survived the failure and its audit verifies it.
        archives = list(archive_dir.glob("*.sqlite"))
        audits = list(archive_dir.glob("*.audit.json"))
        assert len(archives) == 1 and len(audits) == 1
        audit = json.loads(audits[0].read_text(encoding="utf-8"))
        assert audit["sha256"] == _hash_file(archives[0])
        assert audit["source_version"] == 0

        # Restore: the archive replaces the live database (sidecars removed).
        shutil.copyfile(archives[0], db)
        for sidecar in (
            db.parent / "workflow.sqlite-wal",
            db.parent / "workflow.sqlite-shm",
        ):
            sidecar.unlink(missing_ok=True)

        restored = sqlite3.connect(str(db))
        try:
            assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert restored.execute("PRAGMA user_version").fetchone()[0] == 0
            assert (
                restored.execute(
                    "SELECT task_id, workflow_id, workflow_version, idempotency_key "
                    "FROM tasks ORDER BY task_id"
                ).fetchall()
                == pre_tasks
            )
            assert read_ledger(restored) == []
        finally:
            restored.close()
