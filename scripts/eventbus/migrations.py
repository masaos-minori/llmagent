"""scripts/eventbus/migrations.py — EventBus forward-only migration registry.

Registers the ``eventbus.sqlite`` migration path on the domain-neutral framework
in ``shared.db_migrations`` (REQ-001 migration framework, REQ-009 registered paths
preserve rows). This is the domain-specific home where future EventBus version
steps register; it currently holds the ledger bootstrap step (3 -> 4), the
dlqbox001 ``dlq_outbox`` step (4 -> 5), and the ebschema001
``eventbus_dlq_outbox_fk_dedup`` rebuild (5 -> 6).

This module imports only ``shared.db_migrations``, ``shared.eventbus_schema_fingerprint``,
and the standard library, so the ``.importlinter`` contracts ``eventbus-is-isolated``
and ``shared-is-leaf`` stay KEPT (``eventbus`` may import ``shared`` but never ``db``).
"""

from __future__ import annotations

import logging
import sqlite3

from shared.db_migrations import MigrationRunner, MigrationSpec
from shared.eventbus_schema_fingerprint import assert_matches

logger = logging.getLogger(__name__)

# Required eventbus tables that define a valid eventbus database. The pre-migration
# backup verifier (see ``verify_backup``) checks these are present; a backup
# missing any of them is not a usable recovery point.
_REQUIRED_TABLES = ("events", "consumer_delivery", "consumer_offsets")

# Baseline ``PRAGMA user_version`` of the eventbus event schema before the
# migration ledger lands (the value stamped by ``schema.sql`` prior to dbmig001).
_BASELINE_VERSION = 3

# Target ``PRAGMA user_version`` of the ledger bootstrap step.
_LEDGER_VERSION = 4

# Target ``PRAGMA user_version`` of the frozen 4 -> 5 dlq_outbox step (dlqbox001).
# NOT the current schema.sql stamp anymore: ebschema001 moved canonical schema.sql
# to version 6 (single-FK dlq_outbox); this step stays the double-FK v5
# intermediate, and the 5 -> 6 rebuild step below converges on the new stamp.
_OUTBOX_VERSION = 5

# Target ``PRAGMA user_version`` of the FK-dedup rebuild step (ebschema001). Must
# match the ``PRAGMA user_version`` line in scripts/eventbus/schema.sql, which is
# the fingerprint source the post-rebuild verifier checks.
_FK_DEDUP_VERSION = 6

_LEDGER_CREATE_SQL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations ("
    "id TEXT PRIMARY KEY,"
    " applied_at TEXT,"
    " from_version INTEGER,"
    " to_version INTEGER"
    ");"
)

# The bootstrap step stamps the ledger and bumps the baseline in one transaction.
_BOOTSTRAP_MUTATION_SQL = (
    f"{_LEDGER_CREATE_SQL} PRAGMA user_version = {_LEDGER_VERSION};"
)

# dlq_outbox DDL + pending-scan index, frozen in its released double-FK v5 shape.
# Intentionally NOT identical to canonical scripts/eventbus/schema.sql anymore:
# schema.sql v6 carries a single inline FK (ebschema001); the registered 5 -> 6
# rebuild step below converges migrated databases on the canonical fingerprint
# (dlqbox001 row 01 contract, superseded by ebschema001 for the v5 intermediate).
_DLQ_OUTBOX_SQL = """CREATE TABLE IF NOT EXISTS dlq_outbox (
    event_id          TEXT    PRIMARY KEY REFERENCES events(event_id),
    requested_at      TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'done', 'failed')),
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    next_attempt_at   TEXT,
    completed_at      TEXT,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
CREATE INDEX IF NOT EXISTS idx_dlq_outbox_status
    ON dlq_outbox(status, next_attempt_at);"""

_OUTBOX_MUTATION_SQL = f"{_DLQ_OUTBOX_SQL} PRAGMA user_version = {_OUTBOX_VERSION};"

# FK-dedup rebuild (ebschema001): rebuild dlq_outbox down to the single inline FK
# of canonical schema.sql v6 via create-copy-drop-rename. The uniquely named
# intermediate table never collides with the live dlq_outbox and never appears in
# the fingerprint; the index is recreated explicitly so the fingerprinted index
# definition is identical to canonical.
_FK_DEDUP_CREATE_SQL = """CREATE TABLE dlq_outbox_v6 (
    event_id          TEXT    PRIMARY KEY REFERENCES events(event_id),
    requested_at      TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'done', 'failed')),
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    next_attempt_at   TEXT,
    completed_at      TEXT
);"""

_FK_DEDUP_COPY_SQL = (
    "INSERT INTO dlq_outbox_v6 (event_id, requested_at, status, attempts,"
    " last_error, next_attempt_at, completed_at)"
    " SELECT event_id, requested_at, status, attempts, last_error,"
    " next_attempt_at, completed_at FROM dlq_outbox;"
)

_FK_DEDUP_RENAME_SQL = (
    "DROP TABLE dlq_outbox; ALTER TABLE dlq_outbox_v6 RENAME TO dlq_outbox;"
)

_FK_DEDUP_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_dlq_outbox_status"
    " ON dlq_outbox(status, next_attempt_at);"
)

_FK_DEDUP_MUTATION_SQL = (
    f"{_FK_DEDUP_CREATE_SQL} {_FK_DEDUP_COPY_SQL} {_FK_DEDUP_RENAME_SQL}"
    f" {_FK_DEDUP_INDEX_SQL} PRAGMA user_version = {_FK_DEDUP_VERSION};"
)


def _precondition_baseline(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is exactly at the pre-ledger baseline version."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _BASELINE_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}; the ledger bootstrap "
            f"step applies only to a {_BASELINE_VERSION}-stamped database",
        )


def _table_names(conn: sqlite3.Connection) -> set[str]:
    """Return the set of user table names in the database."""
    return {
        str(row[0])
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _precondition_outbox_step(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is a ledger-compatible post-bootstrap baseline.

    Rejects: a database not exactly at the ledger version, a forged stamp (no
    ``schema_migrations`` table), a database already carrying ``dlq_outbox``, and
    a database missing the core eventbus tables.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _LEDGER_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}; the dlq_outbox step "
            f"applies only to a {_LEDGER_VERSION}-stamped database",
        )
    tables = _table_names(conn)
    if "schema_migrations" not in tables:
        raise RuntimeError(
            "eventbus.sqlite is stamped 4 without a migration ledger; refusing a "
            "forged stamp (migrate a version-3 database through the registered path)",
        )
    missing = sorted(set(_REQUIRED_TABLES) - tables)
    if missing:
        raise RuntimeError(f"eventbus.sqlite is missing core tables: {missing}")
    if "dlq_outbox" in tables:
        raise RuntimeError(
            "eventbus.sqlite already has dlq_outbox; the step applies only to a "
            "database without it"
        )


def _precondition_fk_dedup_step(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is a post-outbox version-5 database.

    Rejects: a database not exactly at the outbox version, a forged stamp (no
    ``schema_migrations`` table), a database missing the core eventbus tables,
    and a database without ``dlq_outbox`` (there is nothing to rebuild).
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _OUTBOX_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}; the FK-dedup rebuild "
            f"step applies only to a {_OUTBOX_VERSION}-stamped database",
        )
    tables = _table_names(conn)
    if "schema_migrations" not in tables:
        raise RuntimeError(
            "eventbus.sqlite is stamped 5 without a migration ledger; refusing a "
            "forged stamp (migrate a lower-stamped database through the registered "
            "path)",
        )
    missing = sorted(set(_REQUIRED_TABLES) - tables)
    if missing:
        raise RuntimeError(f"eventbus.sqlite is missing core tables: {missing}")
    if "dlq_outbox" not in tables:
        raise RuntimeError(
            "eventbus.sqlite has no dlq_outbox; the FK-dedup rebuild step applies "
            "only to a database carrying it"
        )


def _precommit_ledger_baseline(conn: sqlite3.Connection) -> None:
    """Verify before commit: ledger present, core tables, stamp 4.

    The full canonical fingerprint is intentionally NOT run here: schema.sql is
    the fingerprint source and already contains shapes added by later registered
    steps (dlq_outbox), so a full-shape assert would fail at this intermediate
    version. Full-shape verification runs at path end (schema.py, migrate.py)
    and in the pre-outbox-step-completion verifier below.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _LEDGER_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}, not {_LEDGER_VERSION}, "
            "after the ledger bootstrap step",
        )
    tables = _table_names(conn)
    if "schema_migrations" not in tables:
        raise RuntimeError("ledger bootstrap did not create schema_migrations")
    missing = sorted(set(_REQUIRED_TABLES) - tables)
    if missing:
        raise RuntimeError(f"ledger bootstrap left core tables missing: {missing}")


def _precommit_fingerprint(conn: sqlite3.Connection) -> None:
    """Verify before commit that the canonical EventBus shape holds after the mutation.

    Used by the 5 -> 6 FK-dedup step (both slots): its result is the full canonical
    shape, so the full fingerprint applies. Earlier intermediate steps use scoped
    verifiers instead — schema.sql is the fingerprint source and already contains
    shapes added by later registered steps.
    """
    assert_matches(conn, label="eventbus.sqlite")


def _precommit_outbox_baseline(conn: sqlite3.Connection) -> None:
    """Verify before commit: dlq_outbox landed at the version-5 intermediate shape.

    The full canonical fingerprint is intentionally NOT run here: schema.sql v6
    carries the single-FK dlq_outbox that the later 5 -> 6 step lands, so a
    full-shape assert would fail against this frozen double-FK intermediate
    (same contract as _precommit_ledger_baseline). Full-shape verification runs
    at path end (schema.py, migrate.py) and in the 5 -> 6 step's verifier.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _OUTBOX_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}, not {_OUTBOX_VERSION}, "
            "after the dlq_outbox step",
        )
    tables = _table_names(conn)
    missing = sorted(
        (set(_REQUIRED_TABLES) | {"schema_migrations", "dlq_outbox"}) - tables
    )
    if missing:
        raise RuntimeError(f"dlq_outbox step left tables missing: {missing}")
    if (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name"
            " = 'idx_dlq_outbox_status'"
        ).fetchone()
        is None
    ):
        raise RuntimeError("dlq_outbox step did not create idx_dlq_outbox_status")


# Ordered registry consumed by startup wiring (scripts/eventbus/schema.py) and the
# migration CLI (scripts/eventbus/migrate.py). Registration order, not insertion
# side effects, defines the forward path.
REGISTRY: dict[str, MigrationSpec] = {
    "eventbus_ledger_baseline": MigrationSpec(
        id="eventbus_ledger_baseline",
        from_version=_BASELINE_VERSION,
        to_version=_LEDGER_VERSION,
        preconditions=(_precondition_baseline,),
        mutation_sql=_BOOTSTRAP_MUTATION_SQL,
        pre_commit_verification=_precommit_ledger_baseline,
    ),
    "eventbus_dlq_outbox": MigrationSpec(
        id="eventbus_dlq_outbox",
        from_version=_LEDGER_VERSION,
        to_version=_OUTBOX_VERSION,
        preconditions=(_precondition_outbox_step,),
        mutation_sql=_OUTBOX_MUTATION_SQL,
        pre_commit_verification=_precommit_outbox_baseline,
    ),
    "eventbus_dlq_outbox_fk_dedup": MigrationSpec(
        id="eventbus_dlq_outbox_fk_dedup",
        from_version=_OUTBOX_VERSION,
        to_version=_FK_DEDUP_VERSION,
        preconditions=(_precondition_fk_dedup_step,),
        mutation_sql=_FK_DEDUP_MUTATION_SQL,
        disable_foreign_keys=True,
        pre_commit_verification=_precommit_fingerprint,
        postcondition=_precommit_fingerprint,
    ),
}

#: Shared runner for the eventbus domain.
runner = MigrationRunner()


def verify_backup(conn: sqlite3.Connection, _backup_path: str) -> None:
    """Injected backup verifier: confirm the backup is a real eventbus database.

    The runner already performs a WAL checkpoint, a SQLite backup-API copy, and an
    independent ``PRAGMA integrity_check`` on the copy. This adds domain identity by
    requiring the eventbus tables to be present. A strict fingerprint match is
    intentionally NOT run here: the backup is the pre-migration baseline database,
    whose shape predates the ``schema_migrations`` table this step adds, so a
    post-migration fingerprint would reject a perfectly good pre-migration backup.

    Args:
        conn: Open connection to the verified backup copy.
        _backup_path: Temp path of the backup copy (accepted for the runner's
            ``BackupVerifier`` contract; not needed for a table-presence check).
    """
    for table in _REQUIRED_TABLES:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if present is None:
            raise RuntimeError(f"eventbus backup is missing required table '{table}'")
