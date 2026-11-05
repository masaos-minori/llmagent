"""tests/shared/test_db_migrations.py — Framework regression tests.

Exercises scripts/shared/db_migrations.py directly with a toy domain registry and
file-based SQLite fixtures (Plan row 14; issue Testing Expectations; REQ-001-REQ-004).
No db/eventbus layer imports (keeps lint-imports clean for tests/shared).
"""

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest
from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    MigrationRunner,
    MigrationSpec,
    _split_statements,
    archive_pre_migration,
    ensure_ledger,
    read_ledger,
    record_applied,
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
    sid: str,
    frm: int,
    to: int,
    *,
    create_table: str | None = None,
    mutation_sql: str | None = None,
    disable_foreign_keys: bool | None = None,
    pre_commit_verification: Callable[[sqlite3.Connection], None] | None = None,
) -> MigrationSpec:
    """Build a toy spec that stamps ``to`` and optionally creates a table."""
    sql = mutation_sql if mutation_sql is not None else f"PRAGMA user_version = {to}"  # nosec B608 — to is a test int
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
        disable_foreign_keys=bool(disable_foreign_keys),
        pre_commit_verification=pre_commit_verification,
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
        # complete cleanly, so no clean checkpoint exists. The refusal reason is
        # distinct from backup-integrity failures (REQ-004).
        holder = sqlite3.connect(str(db))
        holder.execute("BEGIN")
        holder.execute("INSERT INTO toy(t) VALUES ('blocked')")

        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=2)
        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.apply(conn, planned, _ok_verifier)
        assert excinfo.value.reason == MigrationRefusalReason.CHECKPOINT_BUSY

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


# ── Distinct refusal reasons (dbmigsafe001 REQ-004) ──────────────────────────


class TestDistinctRefusalReasons:
    def test_in_memory_database_refused_with_distinct_reason(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE toy(t)")
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=2)

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.apply(conn, planned, _ok_verifier)
        assert excinfo.value.reason == MigrationRefusalReason.IN_MEMORY_DATABASE

        with pytest.raises(MigrationRefusalError) as excinfo:
            runner.apply(conn, planned, _ok_verifier, dry_run=True)
        assert excinfo.value.reason == MigrationRefusalReason.IN_MEMORY_DATABASE

        with pytest.raises(MigrationRefusalError) as excinfo:
            archive_pre_migration(conn, Path("/unused"))
        assert excinfo.value.reason == MigrationRefusalReason.IN_MEMORY_DATABASE
        conn.close()

    def test_dry_run_snapshot_sees_committed_wal_rows(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = _toy_registry()
        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), reg, target_version=2)

        # A second connection commits a row that stays in the -wal sidecar: the
        # live main db file does not contain it until a checkpoint completes.
        writer = sqlite3.connect(str(db))
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO toy(t) VALUES ('wal-only')")
        writer.commit()

        db_hash = _hash_file(db)
        wal_hash = _hash_file(db.parent / "toydb.sqlite-wal")

        seen: list[int] = []

        def _spy_verifier(snapshot: sqlite3.Connection, _path: str) -> None:
            seen.append(int(snapshot.execute("SELECT COUNT(*) FROM toy").fetchone()[0]))

        applied = runner.apply(conn, planned, _spy_verifier, dry_run=True)

        assert applied == []
        # The live database and its sidecars are byte-identical (AC-5).
        assert _hash_file(db) == db_hash
        assert _hash_file(db.parent / "toydb.sqlite-wal") == wal_hash
        # The gate saw the WAL-committed row through the backup-API snapshot; a
        # plain copy of the main db file would have contained only the base row
        # (REQ-002/REQ-004).
        assert seen == [2]
        writer.close()
        conn.close()


# ── Durable pre-migration archive (dbmigsafe001 REQ-001) ─────────────────────


class TestPreMigrationArchive:
    def test_archive_writes_audit_artifact(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=2)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()

        archive = archive_pre_migration(conn, archive_dir)

        assert archive.archive_path.name.startswith("toydb-v2-")
        assert archive.audit_path == archive.archive_path.with_suffix(".audit.json")
        audit = json.loads(archive.audit_path.read_text(encoding="utf-8"))
        assert audit["archive_path"] == str(archive.archive_path)
        assert audit["source_db"] == str(db)
        assert audit["source_version"] == 2
        assert audit["sha256"] == _hash_file(archive.archive_path)
        assert _ISO8601_UTC_RE.match(audit["created_at"]), audit
        assert audit["retention_status"] == "unset"

        ach = sqlite3.connect(str(archive.archive_path))
        try:
            assert ach.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert ach.execute("PRAGMA user_version").fetchone()[0] == 2
        finally:
            ach.close()
        conn.close()

    def test_apply_archives_pre_run_state_before_mutation(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), _toy_registry(), target_version=2)

        applied = runner.apply(conn, planned, _ok_verifier, archive_dir=archive_dir)

        assert [a.id for a in applied] == ["A"]
        archives = sorted(archive_dir.glob("toydb-v1-*.sqlite"))
        assert len(archives) == 1
        assert len(list(archive_dir.glob("*.audit.json"))) == 1
        ach = sqlite3.connect(str(archives[0]))
        try:
            # The archive captured the exact pre-run state: version 1, no step-A
            # table, and a ledger with no step rows (the step ledger row is
            # written after the archive).
            assert ach.execute("PRAGMA user_version").fetchone()[0] == 1
            names = {
                r[0]
                for r in ach.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert "toy_v2" not in names
            ach_rows = ach.execute("SELECT id FROM schema_migrations").fetchall()
            assert ach_rows == []
        finally:
            ach.close()
        assert [r.id for r in read_ledger(conn)] == ["A"]
        conn.close()

    def test_missing_archive_directory_refuses(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        with pytest.raises(MigrationRefusalError) as excinfo:
            archive_pre_migration(conn, tmp_path / "nope")
        assert excinfo.value.reason == MigrationRefusalReason.NO_ARCHIVE_TARGET
        assert not (tmp_path / "nope").exists()
        conn.close()

    def test_unwritable_archive_directory_refuses(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        archive_dir.chmod(0o500)
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                archive_pre_migration(conn, archive_dir)
            assert excinfo.value.reason == MigrationRefusalReason.NO_ARCHIVE_TARGET
            assert list(archive_dir.iterdir()) == []
        finally:
            archive_dir.chmod(0o700)
        conn.close()


# ── Ledger append order (dbmigsafe001 REQ-005) ───────────────────────────────


class TestLedgerAppendOrder:
    def test_same_second_steps_read_in_insertion_order(self, tmp_path) -> None:
        conn = _init_db(tmp_path / "toydb.sqlite", version=1)
        ensure_ledger(conn)
        same = "2026-01-01T00:00:00Z"
        record_applied(conn, _step("zeta", 1, 2), applied_at=same)
        record_applied(conn, _step("alpha", 2, 3), applied_at=same)
        conn.commit()

        rows = read_ledger(conn)
        # Insertion (rowid) order, not id order: the old applied_at,id ordering
        # would have returned [alpha, zeta] for these same-second stamps.
        assert [r.id for r in rows] == ["zeta", "alpha"]
        assert [r.seq for r in rows] == [rows[0].seq, rows[0].seq + 1]
        assert rows[0].applied_at == same
        conn.close()


class TestRecordApplied:
    def test_explicit_timestamp_is_bound_not_interpolated(self, tmp_path) -> None:
        """A caller-supplied applied_at is stored verbatim as data, never run as SQL."""
        conn = _init_db(tmp_path / "toydb.sqlite")
        ensure_ledger(conn)
        hostile = "x'); DROP TABLE schema_migrations; --"
        record_applied(conn, _step("A", 1, 2), applied_at=hostile)
        rows = read_ledger(conn)
        assert [(r.id, r.applied_at) for r in rows] == [("A", hostile)]
        conn.close()

    def test_default_timestamp_is_iso8601_utc(self, tmp_path) -> None:
        conn = _init_db(tmp_path / "toydb.sqlite")
        ensure_ledger(conn)
        record_applied(conn, _step("A", 1, 2))
        rows = read_ledger(conn)
        assert len(rows) == 1
        assert _ISO8601_UTC_RE.match(rows[0].applied_at)
        conn.close()


# ── Per-step transaction contract fixtures (procedure 04, Plan REQ-001..004) ──


def _fk_db(db_path: Path) -> sqlite3.Connection:
    """Open a toy parent/child database with foreign keys enforced."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute(
        "CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))"
    )
    conn.execute("INSERT INTO parent(id, v) VALUES (1, 'p1')")
    conn.execute("INSERT INTO child(id, parent_id) VALUES (1, 1)")
    conn.execute("PRAGMA user_version = 1")
    ensure_ledger(conn)
    conn.commit()
    return conn


def _fk_state(conn: sqlite3.Connection) -> tuple:
    """Comparable logical-state snapshot for the parent/child fixture."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    parents = conn.execute("SELECT COUNT(*) FROM parent").fetchone()[0]
    children = conn.execute("SELECT COUNT(*) FROM child").fetchone()[0]
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    ledger = [(r.id, r.from_version, r.to_version) for r in read_ledger(conn)]
    return (version, parents, children, frozenset(tables), tuple(ledger))


def _failing_pre_commit(_conn: sqlite3.Connection) -> None:
    """Spec-level pre-commit verification that rejects the pending step."""
    raise RuntimeError("pre-commit verification failed")


def _failing_precondition(_conn: sqlite3.Connection) -> None:
    raise AssertionError("toy precondition failed")


class TestStepTransaction:
    """Runner per-step transaction contract (AC-1/AC-2, REQ-001/REQ-002)."""

    def test_partial_step_rolls_back_every_statement(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = {
            "A": _step(
                "A",
                1,
                2,
                mutation_sql=(
                    "CREATE TABLE toy_v2(x);"
                    " INSERT INTO toy_v2 VALUES (1);"
                    " SELECT no_such_fn(1);"
                    " PRAGMA user_version = 2"
                ),
            )
        }
        runner = MigrationRunner()
        before = _logical_state(conn)

        with pytest.raises(sqlite3.OperationalError):
            runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)

        # AC-1: statements before the failing one must not persist.
        assert _logical_state(conn) == before
        assert read_ledger(conn) == []
        conn.close()

    def test_ledger_and_version_roll_back_on_pre_commit_failure(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        reg = {
            "A": _step(
                "A",
                1,
                2,
                create_table="toy_v2",
                pre_commit_verification=_failing_pre_commit,
            )
        }
        runner = MigrationRunner()
        before = _logical_state(conn)

        with pytest.raises(RuntimeError, match="pre-commit verification failed"):
            runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)

        # AC-4: the ledger row and the mutation share one transaction.
        assert _logical_state(conn) == before
        assert read_ledger(conn) == []
        conn.close()

    def test_open_caller_transaction_is_refused(self, tmp_path) -> None:
        db = tmp_path / "toydb.sqlite"
        conn = _init_db(db, version=1)
        ensure_ledger(conn)
        conn.execute("INSERT INTO toy(t) VALUES ('open-tx')")
        assert conn.in_transaction

        runner = MigrationRunner()
        planned = runner.plan(1, read_ledger(conn), _toy_registry(), 2)
        with pytest.raises(RuntimeError, match="open transaction"):
            runner.apply(conn, planned, _ok_verifier)

        # The refusal must not commit the caller's pending write.
        assert conn.in_transaction
        conn.rollback()
        assert (
            conn.execute("SELECT COUNT(*) FROM toy WHERE t='open-tx'").fetchone()[0]
            == 0
        )
        conn.close()

    def test_default_and_autocommit_connections_both_apply(self, tmp_path) -> None:
        reg = _toy_registry()
        runner = MigrationRunner()

        db1 = tmp_path / "default-isolation.sqlite"
        conn1 = _init_db(db1, version=1)
        ensure_ledger(conn1)
        runner.apply(conn1, runner.plan(1, read_ledger(conn1), reg, 2), _ok_verifier)
        assert conn1.execute("PRAGMA user_version").fetchone()[0] == 2
        conn1.close()

        db2 = tmp_path / "autocommit.sqlite"
        seed = _init_db(db2, version=1)
        ensure_ledger(seed)
        seed.close()
        # Defensive contract: the runner must also work on an autocommit
        # (isolation_level=None) connection, which no repo caller currently uses.
        conn2 = sqlite3.connect(str(db2), isolation_level=None)
        runner.apply(conn2, runner.plan(1, read_ledger(conn2), reg, 2), _ok_verifier)
        assert conn2.execute("PRAGMA user_version").fetchone()[0] == 2
        assert [r.id for r in read_ledger(conn2)] == ["A"]
        conn2.close()


class TestForeignKeyStep:
    """Opt-in per-step foreign-key control (AC-3, REQ-003)."""

    def test_rebuild_with_disabled_keys_preserves_children(self, tmp_path) -> None:
        db = tmp_path / "fk.sqlite"
        conn = _fk_db(db)
        reg = {
            "FK": _step(
                "FK",
                1,
                2,
                mutation_sql=(
                    "CREATE TABLE parent_new(id INTEGER PRIMARY KEY, v TEXT);"
                    " INSERT INTO parent_new SELECT id, v FROM parent;"
                    " DROP TABLE parent;"
                    " ALTER TABLE parent_new RENAME TO parent;"
                    " PRAGMA user_version = 2"
                ),
                disable_foreign_keys=True,
            )
        }
        runner = MigrationRunner()

        runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)

        assert conn.execute("SELECT COUNT(*) FROM child").fetchone()[0] == 1
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        assert [r.id for r in read_ledger(conn)] == ["FK"]
        conn.close()

    def test_dangling_reference_fails_and_rolls_back(self, tmp_path) -> None:
        db = tmp_path / "fk.sqlite"
        conn = _fk_db(db)
        reg = {
            "FK": _step(
                "FK",
                1,
                2,
                mutation_sql="DELETE FROM parent WHERE id = 1; PRAGMA user_version = 2",
                disable_foreign_keys=True,
            )
        }
        runner = MigrationRunner()
        before = _fk_state(conn)

        with pytest.raises(Exception, match="foreign_key_check"):
            runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)

        assert _fk_state(conn) == before
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        conn.close()

    def test_failing_precondition_leaves_pragma_untouched(self, tmp_path) -> None:
        db = tmp_path / "fk.sqlite"
        conn = _fk_db(db)
        reg = {
            "FK": MigrationSpec(
                id="FK",
                from_version=1,
                to_version=2,
                preconditions=(_failing_precondition,),
                mutation_sql="PRAGMA user_version = 2",
                disable_foreign_keys=True,
            )
        }
        runner = MigrationRunner()

        with pytest.raises(AssertionError):
            runner.apply(conn, runner.plan(1, read_ledger(conn), reg, 2), _ok_verifier)

        # AC-3: refusal before BEGIN leaves pragma and schema untouched.
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert _fk_state(conn)[4] == ()
        conn.close()


# ── _split_statements helper (Plan REQ-001) ─────────────────────────────────


def test_split_statements_keeps_trigger_body_whole() -> None:
    sql = (
        "CREATE TABLE t(a); "
        "CREATE TRIGGER tr AFTER INSERT ON t BEGIN "
        "INSERT INTO t(a) VALUES (1); END; "
        "PRAGMA user_version = 2;"
    )
    parts = _split_statements(sql)
    assert len(parts) == 3
    assert parts[0].strip() == "CREATE TABLE t(a);"
    body = parts[1].strip()
    assert body.startswith("CREATE TRIGGER")
    assert body.endswith("END;")
    assert "INSERT INTO t(a) VALUES (1);" in body
    assert parts[2].strip() == "PRAGMA user_version = 2;"


def test_split_statements_skips_blanks_and_passes_incomplete_tail_through() -> None:
    assert _split_statements("") == []
    assert _split_statements("   \n  ") == []
    # An incomplete trailing fragment is returned (whitespace preserved) so the
    # execute call surfaces the syntax error instead of silently dropping it.
    assert [p.strip() for p in _split_statements("SELECT 1; SELECT")] == [
        "SELECT 1;",
        "SELECT",
    ]
