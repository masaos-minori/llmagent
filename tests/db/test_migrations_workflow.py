"""tests/db/test_migrations_workflow.py — Workflow migration registry + CLI tests.

Exercises scripts/db/migrations_workflow.py and scripts/db/migrate_db.py against
file-based workflow.sqlite fixtures (REQ-001 migration framework, REQ-002 backup
gate, REQ-003 refusal semantics, REQ-004 dry-run, REQ-009 registered paths
preserve rows). CLI coverage runs the operator CLI as a subprocess with a
sandboxed agent.toml so no production DB path is ever touched.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from db.migrations_workflow import REGISTRY, runner, verify_backup
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

    Built from the canonical workflow DDL, then the ledger dropped and the
    integer version reset to 0 to reproduce the deployed marker-only shape.
    The ``workflow_schema_version`` string is set to *marker* (default the
    baseline "1.1.0"; pass an unmapped value such as "2.0.0" for refusals).
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(build_workflow_schema_sql())
    conn.commit()
    conn.execute("DROP TABLE schema_migrations")  # nosec B608 — fixed table name
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


# ── Registry + path resolution ──────────────────────────────────────────────


class TestWorkflowRegistry:
    def test_registry_holds_the_ledger_bootstrap_step(self) -> None:
        assert set(REGISTRY) == {"workflow_ledger_baseline"}
        spec = REGISTRY["workflow_ledger_baseline"]
        assert spec.from_version == 0
        assert spec.to_version == 1
        assert spec.mutation_sql  # non-empty mutation SQL

    def test_runner_resolves_the_unique_forward_path(self, tmp_path: Path) -> None:
        conn = _legacy_workflow_db(tmp_path / "workflow.sqlite")
        try:
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
            assert [s.id for s in planned] == ["workflow_ledger_baseline"]
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
            planned = runner.plan(0, read_ledger(conn), REGISTRY)
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
                conn, runner.plan(0, read_ledger(conn), REGISTRY), _ok_verifier
            )
            rest = runner.plan(1, read_ledger(conn), REGISTRY)
            assert rest == []
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
        # cannot complete cleanly, so no verified recovery point exists (REQ-002).
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
            assert excinfo.value.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP
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
        apply = _run_cli(db, config_dir, "--apply")
        assert apply.returncode == 0
        assert "user_version now 1" in apply.stdout
        status = _run_cli(db, config_dir, "--status")
        assert status.returncode == 0
        assert "user_version=1" in status.stdout
        assert "workflow_ledger_baseline" in status.stdout
        assert "0 -> 1" in status.stdout

    def test_apply_is_idempotent_after_bootstrap(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db)
        conn.close()
        _run_cli(db, config_dir, "--apply")
        again = _run_cli(db, config_dir, "--apply")
        assert again.returncode == 0
        assert "already at target version" in again.stdout

    def test_unmapped_string_version_refused_no_mutation(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        db = tmp_path / "workflow.sqlite"
        conn = _legacy_workflow_db(db, marker="2.0.0")
        conn.close()
        before = _hash_file(db)
        result = _run_cli(db, config_dir, "--apply")
        # REFUSAL exit class (2); the CLI pre-runs preconditions so nothing is
        # mutated (AC-2).
        assert result.returncode == 2
        assert _hash_file(db) == before

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
            result = _run_cli(db, config_dir, "--apply")
            # Gate failure maps to EXIT_GATE_FAILURE (1).
            assert result.returncode == 1
        finally:
            holder.rollback()
            holder.close()
