"""tests/shared/test_db_migrations.py — Framework regression tests.

Exercises scripts/shared/db_migrations.py directly with a toy domain registry and
file-based SQLite fixtures (Plan row 14; issue Testing Expectations; REQ-001-REQ-004).
No db/eventbus layer imports (keeps lint-imports clean for tests/shared).
"""

import hashlib
import re
import sqlite3
from pathlib import Path

import pytest
from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    MigrationRunner,
    MigrationSpec,
    ensure_ledger,
    read_ledger,
)

_ISO8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# ── Fixtures ────────────────────────────────────────────────────────────────


def _init_db(db_path: Path, *, version: int = 1) -> sqlite3.Connection:
    """Open a toy database at the given user_version with one row in ``toy``."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS toy(t)")
    conn.execute("INSERT INTO toy(t) VALUES ('row1')")
    conn.execute(f"PRAGMA user_version = {version}")  # nosec B608 — version is a test int
    conn.commit()
    return conn


def _step(
    sid: str, frm: int, to: int, *, create_table: str | None = None
) -> MigrationSpec:
    """Build a toy spec that stamps ``to`` and optionally creates a table."""
    sql = f"PRAGMA user_version = {to}"  # nosec B608 — to is a test int
    if create_table:
        sql = f"CREATE TABLE IF NOT EXISTS {create_table}(x); {sql}"

    def _post(conn: sqlite3.Connection, expected: int = to) -> None:
        actual = conn.execute("PRAGMA user_version").fetchone()[0]
        assert actual == expected, f"expected version {expected}, got {actual}"

    return MigrationSpec(
        id=sid,
        from_version=frm,
        to_version=to,
        preconditions=(),
        mutation_sql=sql,
        postcondition=_post,
    )


def _toy_registry() -> dict[str, MigrationSpec]:
    return {
        "A": _step("A", 1, 2, create_table="toy_v2"),
        "B": _step("B", 2, 3, create_table="toy_v3"),
    }


def _ok_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Passing backup verifier (domain identity + fingerprint OK)."""


def _failing_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Backup verifier that rejects the backup as unusable."""
    raise RuntimeError("backup failed domain verification")


def _logical_state(conn: sqlite3.Connection) -> tuple:
    """Return a comparable snapshot of the database's logical state."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    toy_count = conn.execute("SELECT COUNT(*) FROM toy").fetchone()[0]
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    ledger = [(r.id, r.from_version, r.to_version) for r in read_ledger(conn)]
    return (version, toy_count, frozenset(tables), tuple(ledger))


def _hash_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ── Tests ───────────────────────────────────────────────────────────────────


class TestMigrationFramework:
    def test_happy_path_migrates_records_and_preserves_rows(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()

        planned = runner.plan(1, read_ledger(conn), reg, target_version=3)
        assert [s.id for s in planned] == ["A", "B"]

        applied = runner.apply(conn, planned, _ok_verifier)
        assert [a.id for a in applied] == ["A", "B"]

        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        # Canonical row survives both steps.
        assert conn.execute("SELECT COUNT(*) FROM toy").fetchone()[0] == 1
        for tbl in ("toy_v2", "toy_v3"):
            assert (
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (tbl,),
                ).fetchone()
                is not None
            )

        # One ledger row per step with ISO-8601 UTC applied_at.
        rows = read_ledger(conn)
        assert [(r.id, r.from_version, r.to_version) for r in rows] == [
            ("A", 1, 2),
            ("B", 2, 3),
        ]
        assert all(_ISO8601_UTC_RE.match(r.applied_at) for r in rows), rows
        conn.close()

    def test_mid_migration_failure_rolls_back_only_failing_step(self, tmp_path) -> None:
        runner = MigrationRunner()

        # Clean baseline: one successful step A -> v2.
        base = _init_db(tmp_path / "base.sqlite", version=1)
        ensure_ledger(base)
        runner.apply(
            base, runner.plan(1, read_ledger(base), _toy_registry(), 2), _ok_verifier
        )
        base_close_state = _logical_state(base)
        base.close()

        # Two-step apply where B fails mid-transaction (references a missing table).
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        reg["B"] = MigrationSpec(
            id="B",
            from_version=2,
            to_version=3,
            mutation_sql="INSERT INTO missing_table(x) VALUES (1)",
        )

        with pytest.raises(sqlite3.OperationalError):
            runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 3), _ok_verifier)

        # Rollback left the database at the last ledger-recorded version (AC-2).
        assert _logical_state(conn) == base_close_state
        assert [r.id for r in read_ledger(conn)] == ["A"]
        conn.close()

    def test_resume_resolves_from_ledger(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()

        # Simulate an interruption after step A commits, before step B.
        runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2

        # Resume: plan() skips the already-applied A and returns only [B].
        planned = runner.plan(2, read_ledger(conn), reg, target_version=3)
        assert [s.id for s in planned] == ["B"]
        runner.apply(conn, planned, _ok_verifier)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
        conn.close()

    def test_downgrade_refused_before_mutation(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=3)
        ensure_ledger(conn)
        reg = _toy_registry()
        reg["C"] = _step("C", 3, 2)  # a backward edge
        runner = MigrationRunner()

        before = _logical_state(conn)
        before_hash = _hash_file(db)

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.plan(3, read_ledger(conn), reg, target_version=1)
        assert excinfo.value.reason == MigrationRefusalReason.DOWNGRADE

        # Refusal happened before any mutation.
        assert _logical_state(conn) == before
        assert _hash_file(db) == before_hash
        conn.close()

    def test_unknown_target_refused(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()  # no step leaves version 3
        runner = MigrationRunner()

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.plan(1, read_ledger(conn), reg, target_version=9)
        assert excinfo.value.reason == MigrationRefusalReason.UNKNOWN_PATH
        conn.close()

    def test_cycle_detected_at_resolution(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        reg["C"] = _step("C", 3, 2)  # 2 -> 3 -> 2 forms a cycle
        runner = MigrationRunner()

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.plan(1, read_ledger(conn), reg)  # target=None walks the whole graph
        assert excinfo.value.reason == MigrationRefusalReason.CYCLE
        conn.close()

    def test_dry_run_leaves_file_byte_identical(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=3)
        before_hash = _hash_file(db)

        # Dry-run runs resolution + gate against a throwaway copy; mutates nothing.
        applied = runner.apply(conn, planned, _ok_verifier, dry_run=True)

        assert applied == []
        assert _hash_file(db) == before_hash
        # Nothing was recorded in the ledger.
        assert read_ledger(conn) == []
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        conn.close()

    def test_backup_gate_refuses_on_bad_backup(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=2)

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.apply(conn, planned, _failing_verifier)
        assert excinfo.value.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP
        # Refusal happened before mutation.
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        conn.close()

    def test_missing_clean_checkpoint_refuses(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()

        # A second connection holds an uncommitted write; the WAL checkpoint cannot
        # complete cleanly, so no verified recovery point exists (REQ-002).
        holder = sqlite3.connect(str(db))
        holder.execute("BEGIN")
        holder.execute("INSERT INTO toy(t) VALUES ('blocked')")

        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=2)
        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.apply(conn, planned, _ok_verifier)
        assert excinfo.value.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP

        holder.rollback()
        holder.close()
        conn.close()

    def test_empty_path_applies_nothing(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        runner = MigrationRunner()
        applied = runner.apply(conn, [], _ok_verifier)
        assert applied == []
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        conn.close()
