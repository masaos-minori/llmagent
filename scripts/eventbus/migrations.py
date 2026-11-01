"""scripts/eventbus/migrations.py — EventBus forward-only migration registry.

Registers the ``eventbus.sqlite`` migration path on the domain-neutral framework
in ``shared.db_migrations`` (REQ-001 migration framework, REQ-009 registered paths
preserve rows). This is the domain-specific home where future EventBus version
steps register; it currently holds the ledger bootstrap step (3 -> 4) and the
dlqbox001 ``dlq_outbox`` step (4 -> 5).

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

# Target ``PRAGMA user_version`` once the dlq_outbox step lands (dlqbox001). Must
# match the ``PRAGMA user_version`` line in scripts/eventbus/schema.sql, which is
# the fingerprint source the post-outbox postcondition re-verifies.
_OUTBOX_VERSION = 5

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

# dlq_outbox DDL + pending-scan index, byte-identical in shape to the same block
# appended to scripts/eventbus/schema.sql, so baseline-created and migrated
# databases are fingerprint-equal (dlqbox001 row 01 contract).
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


def _postcondition_ledger_baseline(conn: sqlite3.Connection) -> None:
    """Re-verify this step's own effect: ledger present, core tables, stamp 4.

    The full canonical fingerprint is intentionally NOT run here: schema.sql is
    the fingerprint source and already contains shapes added by later registered
    steps (dlq_outbox), so a full-shape assert would fail at this intermediate
    version. Full-shape verification runs at path end (schema.py, migrate.py)
    and in the post-outbox postcondition below.
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


def _postcondition_fingerprint(conn: sqlite3.Connection) -> None:
    """Re-verify the canonical EventBus shape after the outbox lands."""
    assert_matches(conn, label="eventbus.sqlite")


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
        postcondition=_postcondition_ledger_baseline,
    ),
    "eventbus_dlq_outbox": MigrationSpec(
        id="eventbus_dlq_outbox",
        from_version=_LEDGER_VERSION,
        to_version=_OUTBOX_VERSION,
        preconditions=(_precondition_outbox_step,),
        mutation_sql=_OUTBOX_MUTATION_SQL,
        postcondition=_postcondition_fingerprint,
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
