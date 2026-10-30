"""scripts/eventbus/migrations.py — EventBus forward-only migration registry.

Registers the ``eventbus.sqlite`` migration path on the domain-neutral framework
in ``shared.db_migrations`` (REQ-001 migration framework, REQ-009 registered paths
preserve rows). This is the domain-specific home where future EventBus version
steps register; it currently holds one bootstrap step that adds the migration
ledger and bumps the baseline to the post-ledger fingerprint source.

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

# Target ``PRAGMA user_version`` once the ledger DDL is applied. Must match the
# ``PRAGMA user_version`` line in scripts/eventbus/schema.sql, which is the
# fingerprint source the postcondition re-verifies.
_TARGET_VERSION = 4

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
    f"{_LEDGER_CREATE_SQL} PRAGMA user_version = {_TARGET_VERSION};"
)


def _precondition_baseline(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is exactly at the pre-ledger baseline version."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _BASELINE_VERSION:
        raise RuntimeError(
            f"eventbus.sqlite is at user_version {current}; the ledger bootstrap "
            f"step applies only to a {_BASELINE_VERSION}-stamped database",
        )


def _postcondition_fingerprint(conn: sqlite3.Connection) -> None:
    """Re-verify the canonical EventBus shape after the ledger lands."""
    assert_matches(conn, label="eventbus.sqlite")


# Ordered registry consumed by startup wiring (scripts/eventbus/schema.py) and the
# migration CLI (scripts/eventbus/migrate.py). Registration order, not insertion
# side effects, defines the forward path.
REGISTRY: dict[str, MigrationSpec] = {
    "eventbus_ledger_baseline": MigrationSpec(
        id="eventbus_ledger_baseline",
        from_version=_BASELINE_VERSION,
        to_version=_TARGET_VERSION,
        preconditions=(_precondition_baseline,),
        mutation_sql=_BOOTSTRAP_MUTATION_SQL,
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
