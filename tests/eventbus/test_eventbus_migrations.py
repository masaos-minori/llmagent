"""tests/eventbus/test_eventbus_migrations.py — EventBus migration registry tests.

Exercises scripts/eventbus/migrations.py against a realistic eventbus.sqlite built
from the canonical schema.sql (REQ-001 migration framework, REQ-002 backup gate,
REQ-003 refusal semantics, REQ-004 dry-run). No db-layer imports (keeps
lint-imports clean for tests/eventbus).
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from eventbus import migrate as _cli_module
from eventbus.migrations import (
    _DLQ_OUTBOX_SQL,
    REGISTRY,
    _precommit_ledger_baseline,
    _precommit_outbox_baseline,
    _precondition_fk_dedup_step,
    _precondition_outbox_step,
    verify_backup,
)
from eventbus.schema import _SCHEMA_PATH
from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    MigrationRunner,
    MigrationSpec,
    read_ledger,
    record_applied,
)
from shared.eventbus_schema_fingerprint import (
    apply_schema_in_memory,
    assert_matches,
    build_fingerprint,
)

_ISO8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# ── Fixtures ────────────────────────────────────────────────────────────────


def _baseline_v3_db(db_path: Path) -> sqlite3.Connection:
    """Open a realistic pre-migration eventbus database at user_version 3.

    Built from the canonical schema.sql (so every real table/column is present),
    then the post-baseline shapes are removed to simulate a database created
    before dbmig001 landed the ledger and before dlqbox001 landed dlq_outbox:
    the migration ledger and dlq_outbox are dropped and the version reset to 3.
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.execute("DROP TABLE dlq_outbox")  # dropping the table drops its index
    conn.execute("DROP TABLE schema_migrations")
    conn.execute("PRAGMA user_version = 3")  # nosec B608 — version is a fixed test int
    conn.commit()
    return conn


def _baseline_v4_db(db_path: Path) -> sqlite3.Connection:
    """Open a ledger-compatible post-bootstrap database at user_version 4.

    Same canonical shape as ``_baseline_v3_db`` plus the migration ledger, which
    is what a database created from schema.sql at the dbmig001 baseline looks
    like (ledger table present, no rows recorded yet).
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.execute("DROP TABLE dlq_outbox")  # nosec B608 — fixed test DDL
    conn.execute("PRAGMA user_version = 4")  # nosec B608 — version is a fixed test int
    conn.commit()
    return conn


def _baseline_v5_db(db_path: Path) -> sqlite3.Connection:
    """Open a post-outbox database at user_version 5 in the frozen double-FK shape.

    Built from canonical schema.sql (v6, single-FK), then dlq_outbox is dropped
    and recreated with the frozen 4 -> 5 step SQL so the seeded database looks
    exactly like a real one migrated to version 5: double-FK dlq_outbox, ledger
    table, version-5 stamp.
    """
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.execute("DROP TABLE dlq_outbox")  # nosec B608 — fixed test DDL
    conn.executescript(_DLQ_OUTBOX_SQL)
    conn.execute("PRAGMA user_version = 5")  # nosec B608 — version is a fixed test int
    conn.commit()
    return conn


def _ok_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Passing backup verifier (domain identity: required tables present)."""


def _failing_verifier(_conn: sqlite3.Connection, _path: str) -> None:
    """Backup verifier that rejects the backup as unusable."""
    raise RuntimeError("backup failed domain verification")


def _logical_state(conn: sqlite3.Connection) -> tuple:
    """Return a comparable snapshot of the database's logical state."""
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    ledger = [(r.id, r.from_version, r.to_version) for r in read_ledger(conn)]
    return (version, event_count, frozenset(tables), tuple(ledger))


def _hash_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _registry_with_step(step: MigrationSpec) -> dict[str, MigrationSpec]:
    """A registry containing only ``step`` for isolated path testing."""
    return {step.id: step}


# ── Tests ───────────────────────────────────────────────────────────────────


class TestEventbusRegistry:
    def test_registry_holds_all_registered_steps(self) -> None:
        assert list(REGISTRY) == [
            "eventbus_ledger_baseline",
            "eventbus_dlq_outbox",
            "eventbus_dlq_outbox_fk_dedup",
        ]
        bootstrap = REGISTRY["eventbus_ledger_baseline"]
        assert bootstrap.from_version == 3
        assert bootstrap.to_version == 4
        assert bootstrap.mutation_sql  # non-empty mutation SQL
        outbox = REGISTRY["eventbus_dlq_outbox"]
        assert outbox.from_version == 4
        assert outbox.to_version == 5
        assert outbox.mutation_sql
        dedup = REGISTRY["eventbus_dlq_outbox_fk_dedup"]
        assert dedup.from_version == 5
        assert dedup.to_version == 6
        assert dedup.mutation_sql
        assert dedup.disable_foreign_keys
        assert dedup.pre_commit_verification is not None
        assert dedup.postcondition is not None
        # dbmigsafe001 REQ-003: the two pre-dedup specs verify inside the step
        # transaction; neither keeps a post-commit postcondition callback. The
        # ebschema001 dedup step adds postcondition as defense in depth.
        for spec in (bootstrap, outbox):
            assert spec.pre_commit_verification is not None, spec.id
            assert spec.postcondition is None, spec.id

    def test_runner_resolves_the_unique_forward_path(self, tmp_path: Path) -> None:
        conn = _baseline_v3_db(tmp_path / "eventbus.sqlite")
        try:
            runner = MigrationRunner()
            planned = runner.plan(3, read_ledger(conn), REGISTRY, target_version=6)
            assert [s.id for s in planned] == [
                "eventbus_ledger_baseline",
                "eventbus_dlq_outbox",
                "eventbus_dlq_outbox_fk_dedup",
            ]
        finally:
            conn.close()

    def test_apply_migrates_and_preserves_rows_and_fingerprint(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        conn.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES ('evt-1', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
        )
        conn.commit()
        before = _logical_state(conn)
        before_hash = _hash_file(db)

        try:
            runner = MigrationRunner()
            planned = runner.plan(3, read_ledger(conn), REGISTRY, target_version=6)
            applied = runner.apply(conn, planned, _ok_verifier)

            assert [a.id for a in applied] == [
                "eventbus_ledger_baseline",
                "eventbus_dlq_outbox",
                "eventbus_dlq_outbox_fk_dedup",
            ]
            # Ends at version 6 with a ledger row for each step.
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 6
            assert_matches(conn)  # pre-commit fingerprint check passes
            rows = read_ledger(conn)
            # read_ledger returns append (rowid) order; compare the recorded
            # set here and pin the ordering separately in the seq test below.
            assert {(r.id, r.from_version, r.to_version) for r in rows} == {
                ("eventbus_ledger_baseline", 3, 4),
                ("eventbus_dlq_outbox", 4, 5),
                ("eventbus_dlq_outbox_fk_dedup", 5, 6),
            }
            assert all(_ISO8601_UTC_RE.match(r.applied_at) for r in rows), rows
        finally:
            conn.close()

        # Canonical rows survive; only the ledger and dlq_outbox were added.
        after = _logical_state(conn := sqlite3.connect(str(db)))
        after_hash = _hash_file(db)
        conn.close()
        assert after[1] == before[1]  # event count unchanged
        assert set(after[3]) == {
            ("eventbus_ledger_baseline", 3, 4),
            ("eventbus_dlq_outbox", 4, 5),
            ("eventbus_dlq_outbox_fk_dedup", 5, 6),
        }
        assert after_hash != before_hash  # the migration DDL changed the file


class TestEventbusResume:
    def test_resume_skips_already_applied_step(self, tmp_path: Path) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        runner = MigrationRunner()
        try:
            # Simulate an interruption after the bootstrap commits.
            runner.apply(
                conn, runner.plan(3, read_ledger(conn), REGISTRY, 4), _ok_verifier
            )
            # Re-plan from the migrated state: nothing left to do for target 4.
            rest = runner.plan(4, read_ledger(conn), REGISTRY, target_version=4)
            assert rest == []
        finally:
            conn.close()


class TestEventbusOutboxStep:
    def test_v4_database_migrates_to_outbox_baseline_preserving_rows(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v4_db(db)
        conn.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES ('evt-1', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
        )
        conn.commit()
        try:
            runner = MigrationRunner()
            planned = runner.plan(4, read_ledger(conn), REGISTRY, target_version=5)
            assert [s.id for s in planned] == ["eventbus_dlq_outbox"]
            applied = runner.apply(conn, planned, _ok_verifier)
            assert [a.id for a in applied] == ["eventbus_dlq_outbox"]
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 5
            assert (
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dlq_outbox'"
                ).fetchone()
                is not None
            )
            assert (
                conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
            )  # canonical rows preserved
            assert [(r.id, r.to_version) for r in read_ledger(conn)] == [
                ("eventbus_dlq_outbox", 5)
            ]
        finally:
            conn.close()

    def test_fresh_baseline_and_migrated_database_are_fingerprint_equal(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        try:
            runner = MigrationRunner()
            runner.apply(
                conn, runner.plan(3, read_ledger(conn), REGISTRY, 6), _ok_verifier
            )
            fresh = apply_schema_in_memory()
            try:
                assert build_fingerprint(conn) == build_fingerprint(fresh)
            finally:
                fresh.close()
        finally:
            conn.close()

    def test_registry_order_prevents_outbox_before_ledger(self, tmp_path: Path) -> None:
        # A registry holding only the outbox step cannot move a version-3
        # database: the ledger bootstrap must run first (registration order).
        conn = _baseline_v3_db(tmp_path / "eventbus.sqlite")
        runner = MigrationRunner()
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.plan(
                    3,
                    read_ledger(conn),
                    _registry_with_step(REGISTRY["eventbus_dlq_outbox"]),
                    target_version=5,
                )
            assert excinfo.value.reason == MigrationRefusalReason.UNKNOWN_PATH
        finally:
            conn.close()

    def test_outbox_step_precondition_refuses_stale_state(self, tmp_path: Path) -> None:
        # A version-4 database that already carries dlq_outbox (e.g. a restored
        # post-migration backup with a stale stamp) is refused before mutation.
        db = tmp_path / "eventbus.sqlite"
        conn = sqlite3.connect(str(db))
        conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        conn.commit()
        runner = MigrationRunner()
        try:
            planned = runner.plan(4, read_ledger(conn), REGISTRY, target_version=5)
            with pytest.raises(RuntimeError, match="already has dlq_outbox"):
                runner.apply(conn, planned, _ok_verifier)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 4  # untouched
        finally:
            conn.close()

    def test_outbox_step_precondition_refuses_wrong_version(
        self, tmp_path: Path
    ) -> None:
        # A pre-ledger (version-3) database is refused: the step applies only to
        # a 4-stamped database (REQ-003 refusal before mutation).
        conn = _baseline_v3_db(tmp_path / "eventbus.sqlite")
        try:
            with pytest.raises(
                RuntimeError, match="applies only to a 4-stamped database"
            ):
                _precondition_outbox_step(conn)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3  # untouched
        finally:
            conn.close()

    def test_outbox_step_precondition_refuses_forged_stamp(
        self, tmp_path: Path
    ) -> None:
        # A 4-stamped database with no migration ledger is a forged stamp.
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="forged stamp"):
                _precondition_outbox_step(conn)
        finally:
            conn.close()

    def test_outbox_step_precondition_refuses_missing_core_tables(
        self, tmp_path: Path
    ) -> None:
        # A stamped, ledger-bearing database missing the core eventbus tables is
        # not a valid eventbus database.
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.execute(
            "CREATE TABLE schema_migrations (id TEXT PRIMARY KEY,"
            " applied_at TEXT, from_version INTEGER, to_version INTEGER)"
        )
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="missing core tables"):
                _precondition_outbox_step(conn)
        finally:
            conn.close()

    def test_ledger_baseline_precommit_refuses_unstamped_result(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            before = (
                conn.execute("PRAGMA user_version").fetchone()[0],
                {r[0] for r in conn.execute("SELECT name FROM sqlite_master")},
            )
            with pytest.raises(
                RuntimeError, match="not 4, after the ledger bootstrap step"
            ):
                _precommit_ledger_baseline(conn)
            # A refused verification leaves schema and version untouched (AC-003).
            assert conn.execute("PRAGMA user_version").fetchone()[0] == before[0]
            assert {
                r[0] for r in conn.execute("SELECT name FROM sqlite_master")
            } == before[1]
        finally:
            conn.close()

    def test_ledger_baseline_precommit_refuses_missing_ledger(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        try:
            before = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
            with pytest.raises(RuntimeError, match="did not create schema_migrations"):
                _precommit_ledger_baseline(conn)
            assert {
                r[0] for r in conn.execute("SELECT name FROM sqlite_master")
            } == before
        finally:
            conn.close()

    def test_ledger_baseline_precommit_refuses_missing_core_tables(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE TABLE schema_migrations (id TEXT PRIMARY KEY,"
            " applied_at TEXT, from_version INTEGER, to_version INTEGER)"
        )
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        try:
            before = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
            with pytest.raises(RuntimeError, match="left core tables missing"):
                _precommit_ledger_baseline(conn)
            assert {
                r[0] for r in conn.execute("SELECT name FROM sqlite_master")
            } == before
        finally:
            conn.close()


class TestEventbusFkDedupStep:
    def test_v5_database_rebuilds_to_single_fk_preserving_rows(
        self, tmp_path: Path
    ) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v5_db(db)
        conn.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES ('evt-1', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO dlq_outbox (event_id, requested_at, status, attempts)"
            " VALUES ('evt-1', '2026-01-01T00:00:00Z', 'done', 2)"
        )
        conn.commit()
        assert len(conn.execute("PRAGMA foreign_key_list(dlq_outbox)").fetchall()) == 2
        runner = MigrationRunner()
        try:
            planned = runner.plan(5, read_ledger(conn), REGISTRY, target_version=6)
            assert [s.id for s in planned] == ["eventbus_dlq_outbox_fk_dedup"]
            applied = runner.apply(conn, planned, _ok_verifier)
            assert [a.id for a in applied] == ["eventbus_dlq_outbox_fk_dedup"]
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 6
            # Exactly one FK remains: the inline PRIMARY KEY REFERENCES (AC-005).
            assert (
                len(conn.execute("PRAGMA foreign_key_list(dlq_outbox)").fetchall()) == 1
            )
            # Rows survive the create-copy-drop-rename unchanged.
            assert conn.execute(
                "SELECT event_id, status, attempts FROM dlq_outbox"
            ).fetchall() == [("evt-1", "done", 2)]
            # The status CHECK vocabulary is preserved.
            conn.execute(
                "INSERT INTO events (event_id, topic, payload, producer, published_at)"
                " VALUES ('evt-2', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO dlq_outbox (event_id, requested_at, status)"
                    " VALUES ('evt-2', '2026-01-01T00:00:00Z', 'bogus')"
                )
            # The pending-scan index survives with the canonical definition.
            assert (
                conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='index'"
                    " AND name='idx_dlq_outbox_status'"
                ).fetchone()
                is not None
            )
            assert (conn.execute("PRAGMA index_list(dlq_outbox)").fetchone()[1]) == (
                "idx_dlq_outbox_status"
            )
            # The rebuilt database is fingerprint-equal to a fresh canonical apply.
            assert_matches(conn)
            assert [(r.id, r.to_version) for r in read_ledger(conn)] == [
                ("eventbus_dlq_outbox_fk_dedup", 6)
            ]
        finally:
            conn.close()

    def test_dangling_reference_rolls_back_schema_version_and_ledger(
        self, tmp_path: Path
    ) -> None:
        # A dlq_outbox row seeded with FK enforcement off dangles after the copy;
        # the runner's PRAGMA foreign_key_check refuses the step before commit and
        # the rollback restores schema, user_version, and ledger together (AC-003).
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v5_db(db)
        conn.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES ('evt-1', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
        )
        conn.commit()
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute(
            "INSERT INTO dlq_outbox (event_id, requested_at) VALUES ('ghost',"
            " '2026-01-01T00:00:00Z')"
        )
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        runner = MigrationRunner()
        try:
            planned = runner.plan(5, read_ledger(conn), REGISTRY, target_version=6)
            with pytest.raises(RuntimeError, match="dangling reference"):
                runner.apply(conn, planned, _ok_verifier)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 5
            assert read_ledger(conn) == []
            # The frozen double-FK v5 shape survived the rollback untouched.
            assert (
                len(conn.execute("PRAGMA foreign_key_list(dlq_outbox)").fetchall()) == 2
            )
            assert (
                conn.execute(
                    "SELECT COUNT(*) FROM dlq_outbox WHERE event_id='ghost'"
                ).fetchone()[0]
                == 1
            )
        finally:
            conn.close()

    def test_precondition_refuses_forged_version5_stamp(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.execute("PRAGMA user_version = 5")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="forged stamp"):
                _precondition_fk_dedup_step(conn)
        finally:
            conn.close()

    def test_precondition_refuses_version5_database_without_dlq_outbox(
        self, tmp_path: Path
    ) -> None:
        # A stamped, ledger-bearing database without dlq_outbox has nothing to
        # rebuild: the precondition refuses before any mutation.
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        conn.execute("DROP TABLE dlq_outbox")  # nosec B608 — fixed test DDL
        conn.execute("PRAGMA user_version = 5")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="has no dlq_outbox"):
                _precondition_fk_dedup_step(conn)
        finally:
            conn.close()

    def test_precondition_refuses_wrong_version(self, tmp_path: Path) -> None:
        # A version-4 database is refused: the rebuild applies only to a
        # 5-stamped database (refusal before mutation).
        conn = _baseline_v3_db(tmp_path / "eventbus.sqlite")
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(
                RuntimeError, match="applies only to a 5-stamped database"
            ):
                _precondition_fk_dedup_step(conn)
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 4  # untouched
        finally:
            conn.close()

    def test_precondition_refuses_missing_core_tables(self, tmp_path: Path) -> None:
        # A stamped, ledger-bearing database missing the core eventbus tables is
        # not a valid eventbus database.
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.execute(
            "CREATE TABLE schema_migrations (id TEXT PRIMARY KEY,"
            " applied_at TEXT, from_version INTEGER, to_version INTEGER)"
        )
        conn.execute("PRAGMA user_version = 5")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="missing core tables"):
                _precondition_fk_dedup_step(conn)
        finally:
            conn.close()

    def test_precommit_baseline_refuses_wrong_final_version(
        self, tmp_path: Path
    ) -> None:
        conn = _baseline_v5_db(tmp_path / "eventbus.sqlite")
        conn.execute("PRAGMA user_version = 4")  # nosec B608 — fixed test int
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="not 5, after the dlq_outbox step"):
                _precommit_outbox_baseline(conn)
        finally:
            conn.close()

    def test_precommit_baseline_refuses_missing_tables(self, tmp_path: Path) -> None:
        conn = _baseline_v5_db(tmp_path / "eventbus.sqlite")
        conn.execute("DROP TABLE dlq_outbox")  # nosec B608 — fixed test DDL
        conn.commit()
        try:
            with pytest.raises(RuntimeError, match="left tables missing"):
                _precommit_outbox_baseline(conn)
        finally:
            conn.close()

    def test_precommit_baseline_refuses_missing_index(self, tmp_path: Path) -> None:
        conn = _baseline_v5_db(tmp_path / "eventbus.sqlite")
        conn.execute("DROP INDEX idx_dlq_outbox_status")  # nosec B608 — fixed test DDL
        conn.commit()
        try:
            with pytest.raises(
                RuntimeError, match="did not create idx_dlq_outbox_status"
            ):
                _precommit_outbox_baseline(conn)
        finally:
            conn.close()


class TestEventbusRefusal:
    def test_unknown_target_refused_before_mutation(self, tmp_path: Path) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        before_hash = _hash_file(db)
        runner = MigrationRunner()
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.plan(3, read_ledger(conn), REGISTRY, target_version=7)
            assert excinfo.value.reason == MigrationRefusalReason.UNKNOWN_PATH
            assert _hash_file(db) == before_hash  # no mutation occurred
        finally:
            conn.close()

    def test_downgrade_step_refused(self, tmp_path: Path) -> None:
        # Inject a registered backward step to exercise the downgrade guard.
        backward = MigrationSpec(
            id="backward",
            from_version=4,
            to_version=3,
            mutation_sql="PRAGMA user_version = 3",
        )
        reg = _registry_with_step(backward)
        conn = sqlite3.connect(str(tmp_path / "eventbus.sqlite"))
        conn.execute("PRAGMA user_version = 4")
        runner = MigrationRunner()
        try:
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.plan(4, [], reg, target_version=3)
            assert excinfo.value.reason == MigrationRefusalReason.DOWNGRADE
        finally:
            conn.close()

    def test_missing_clean_checkpoint_refuses(self, tmp_path: Path) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        # A second connection holds an uncommitted write; the WAL checkpoint
        # cannot complete cleanly. The refusal reason is the distinct
        # checkpoint-busy class, not a backup-integrity failure (REQ-004).
        holder = sqlite3.connect(str(db))
        holder.execute("BEGIN")
        holder.execute(
            "INSERT INTO events (event_id, topic, payload, producer, published_at)"
            " VALUES ('x', 't', '{}', 'p', '2026-01-01T00:00:00Z')"
        )

        runner = MigrationRunner()
        try:
            planned = runner.plan(3, read_ledger(conn), REGISTRY, target_version=4)
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.apply(conn, planned, _ok_verifier)
            assert excinfo.value.reason == MigrationRefusalReason.CHECKPOINT_BUSY
        finally:
            holder.rollback()
            holder.close()
            conn.close()


class TestEventbusDryRunAndGate:
    def test_dry_run_leaves_file_byte_identical(self, tmp_path: Path) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        runner = MigrationRunner()
        try:
            planned = runner.plan(3, read_ledger(conn), REGISTRY, target_version=4)
            before_hash = _hash_file(db)
            applied = runner.apply(conn, planned, _ok_verifier, dry_run=True)
            assert applied == []
            assert _hash_file(db) == before_hash
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
            assert read_ledger(conn) == []
        finally:
            conn.close()

    def test_backup_gate_refuses_on_bad_backup(self, tmp_path: Path) -> None:
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        runner = MigrationRunner()
        try:
            planned = runner.plan(3, read_ledger(conn), REGISTRY, target_version=4)
            with pytest.raises(MigrationRefusalError) as excinfo:
                runner.apply(conn, planned, _failing_verifier)
            assert excinfo.value.reason == MigrationRefusalReason.NO_VERIFIED_BACKUP
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 3  # untouched
        finally:
            conn.close()

    def test_verify_backup_requires_required_tables(self, tmp_path: Path) -> None:
        # A database missing a required eventbus table fails domain identity.
        conn = sqlite3.connect(str(tmp_path / "wrong.sqlite"))
        conn.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY)")
        conn.commit()
        with pytest.raises(RuntimeError, match="missing required table"):
            verify_backup(conn, str(tmp_path / "wrong.sqlite"))
        conn.close()


# ── Ledger append order + CLI archive requirement (dbmigsafe001) ────────────


class TestEventbusLedgerOrder:
    def test_same_second_rows_read_in_insertion_order(self, tmp_path: Path) -> None:
        # AC-006 through the eventbus ledger: read_ledger orders by rowid, so
        # same-second applied_at stamps cannot scramble application order.
        conn = _baseline_v4_db(tmp_path / "eventbus.sqlite")
        same = "2026-01-01T00:00:00Z"
        try:
            record_applied(
                conn,
                MigrationSpec(id="zeta", from_version=4, to_version=5),
                applied_at=same,
            )
            record_applied(
                conn,
                MigrationSpec(id="alpha", from_version=4, to_version=5),
                applied_at=same,
            )
            record_applied(
                conn,
                MigrationSpec(id="mid", from_version=4, to_version=5),
                applied_at=same,
            )
            conn.commit()
            rows = read_ledger(conn)
            assert [r.id for r in rows] == ["zeta", "alpha", "mid"]
            assert [r.seq for r in rows] == [
                rows[0].seq,
                rows[0].seq + 1,
                rows[0].seq + 2,
            ]
        finally:
            conn.close()


class TestEventbusCliArchive:
    def test_apply_without_archive_dir_refuses(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # AC-001 CLI half (eventbus): --apply without an explicit archive
        # target is a refusal (exit 2); no location is ever inferred, and the
        # database stays byte-identical.
        db = tmp_path / "eventbus.sqlite"
        conn = _baseline_v3_db(db)
        conn.close()
        cfg = SimpleNamespace(db_path=str(db), port=1)  # port 1: nothing listens
        monkeypatch.setattr(_cli_module, "load_config", lambda path=None: cfg)
        before = _hash_file(db)
        assert _cli_module.main(["--apply"]) == _cli_module.EXIT_REFUSAL
        assert _hash_file(db) == before
