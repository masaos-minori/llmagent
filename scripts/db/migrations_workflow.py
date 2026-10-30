"""scripts/db/migrations_workflow.py — Workflow forward-only migration registry.

The domain-specific home where future workflow version steps register on the
domain-neutral framework in ``shared.db_migrations`` (REQ-001 migration
framework, REQ-009 registered paths preserve rows). This registry currently
holds one bootstrap step that adds the migration ledger to a legacy workflow
database whose only version marker is the ``workflow_schema_version`` string log.

Unlike the eventbus domain, ``workflow.sqlite`` has no ``PRAGMA user_version``
stamp today: its deployed marker is the ``workflow_schema_version`` TEXT table
written by ``create_schema._record_workflow_schema_version``. The integer ledger
therefore maps string versions to codes; the Plan's ledger contract
(``schema_migrations(id, applied_at, from_version, to_version)``) stays
integer-keyed for both domains.

This module imports only ``shared.db_migrations`` and sibling ``db`` modules, so
the ``.importlinter`` ``db-only-uses-shared`` contract family stays KEPT.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from shared.db_migrations import MigrationRunner, MigrationSpec

from db.recovery import _backup_is_usable

logger = logging.getLogger(__name__)

# Baseline ``workflow_schema_version`` string mapped to its integer ledger code.
# Mirrors ``db.schema_sql.WORKFLOW_SCHEMA_VERSION``; a string absent from this
# map cannot be migrated (refusal), keeping today's fail-closed semantics.
WORKFLOW_VERSION_CODES: dict[str, int] = {"1.1.0": 0}

# Target ledger code once the baseline row lands. The integer ledger code is a
# namespace separate from the string marker: a legacy database with no ledger is
# code 0, and after bootstrap it is code 1. The bootstrap step therefore moves
# 0 -> 1 (the framework rejects a from == to step as a cycle).
WORKFLOW_TARGET_VERSION: int = 1

# Pre-ledger ``PRAGMA user_version`` the bootstrap applies only to. Legacy
# workflow databases carry no stamp (it is 0); anything else is refused.
_BASELINE_VERSION: int = 0

# Required workflow table that defines a valid workflow database. The pre-migration
# backup verifier (see ``verify_backup``) checks this is present; a backup missing
# it is not a usable recovery point.
_REQUIRED_TABLE = "tasks"

# Ledger DDL identical to the row-09 workflow DDL set so baseline-created and
# migrated databases are shape-identical.
_LEDGER_CREATE_SQL = (
    "CREATE TABLE IF NOT EXISTS schema_migrations ("
    "id TEXT PRIMARY KEY,"
    " applied_at TEXT,"
    " from_version INTEGER,"
    " to_version INTEGER"
    ");"
)

# The bootstrap creates the ledger and stamps the integer version to the
# post-ledger code. The runner records the baseline ledger row (id, from/to)
# automatically via record_applied, so this inserts no row itself.
_BOOTSTRAP_MUTATION_SQL = (
    f"{_LEDGER_CREATE_SQL} PRAGMA user_version = {WORKFLOW_TARGET_VERSION};"
)


def _latest_workflow_string(conn: sqlite3.Connection) -> str | None:
    """Return the latest recorded ``workflow_schema_version`` string, if any."""
    row = conn.execute(
        "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None


def _precondition_baseline(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is at the pre-ledger baseline.

    A legacy workflow database carries no ``PRAGMA user_version`` stamp (it is
    ``_BASELINE_VERSION``) and only the ``workflow_schema_version`` string log.
    The bootstrap applies only to such a database; anything else is refused
    (fail-closed). The string must also map to a known code, matching today's
    fail-closed semantics.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _BASELINE_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}; the ledger bootstrap "
            f"step applies only to a {_BASELINE_VERSION}-stamped database",
        )
    latest = _latest_workflow_string(conn)
    if latest is None:
        raise RuntimeError(
            "no workflow_schema_version recorded; cannot resolve a baseline code",
        )
    if latest not in WORKFLOW_VERSION_CODES:
        raise RuntimeError(
            f"workflow schema version {latest!r} is not in the migration map "
            f"{list(WORKFLOW_VERSION_CODES)}; recreate the database",
        )


def _postcondition_fingerprint(conn: sqlite3.Connection) -> None:
    """Re-verify the ledger landed and the version was stamped to the target."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != WORKFLOW_TARGET_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}; expected "
            f"{WORKFLOW_TARGET_VERSION} after bootstrap",
        )
    baseline = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
    ).fetchone()
    if baseline is None:
        raise RuntimeError("workflow baseline row missing after bootstrap")


# Ordered registry consumed by the create path (row 08) and the CLI (row 07).
REGISTRY: dict[str, MigrationSpec] = {
    "workflow_ledger_baseline": MigrationSpec(
        id="workflow_ledger_baseline",
        from_version=0,
        to_version=1,
        preconditions=(_precondition_baseline,),
        mutation_sql=_BOOTSTRAP_MUTATION_SQL,
        postcondition=_postcondition_fingerprint,
    ),
}

#: Shared runner for the workflow domain.
runner = MigrationRunner()


def verify_backup(conn: sqlite3.Connection, _backup_path: str) -> None:
    """Injected backup verifier: confirm the backup is a real workflow database.

    The runner already performs a WAL checkpoint, a SQLite backup-API copy, and an
    independent ``PRAGMA integrity_check`` on the copy. This adds domain identity
    by requiring the workflow ``tasks`` table to be present. A strict fingerprint
    match is intentionally NOT run here: the backup is the pre-migration baseline
    database, whose shape predates the ``schema_migrations`` table this step adds.

    Args:
        conn: Open connection to the verified backup copy.
        _backup_path: Temp path of the backup copy (accepted for the runner's
            ``BackupVerifier`` contract; not needed for a table-presence check).
    """
    present = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (_REQUIRED_TABLE,),
    ).fetchone()
    if present is None:
        raise RuntimeError(
            f"workflow backup is missing required table '{_REQUIRED_TABLE}'"
        )


def ensure_baseline(conn: sqlite3.Connection) -> None:
    """Create the ledger if absent and insert the baseline row idempotently.

    Used by the create path (row 08) so a freshly created workflow database
    carries the ledger and baseline row without re-running the gated bootstrap.
    Stamps ``user_version`` to the target code so a freshly created database is
    byte-for-version identical to one that went through the gated bootstrap.
    """
    if (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        is None
    ):
        conn.executescript(_LEDGER_CREATE_SQL)
    if (
        conn.execute(
            "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
        ).fetchone()
        is None
    ):
        conn.execute(
            "INSERT INTO schema_migrations (id, from_version, to_version) "
            "VALUES ('workflow_ledger_baseline', 0, 1)"
        )
    conn.execute(f"PRAGMA user_version = {WORKFLOW_TARGET_VERSION}")
    conn.commit()


# Retained for callers that already hold a backup path rather than a connection.
# Not used by the runner (which injects a connection); kept for parity with the
# recovery module's ``_backup_is_usable`` signature.
def verify_backup_by_path(backup_path: Path, target: str = "workflow") -> None:
    """Wrap ``db.recovery._backup_is_usable`` for path-based callers.

    Raises ``RuntimeError`` when the backup is not a usable workflow recovery
    point (integrity failure or wrong domain).
    """
    failed_action, detail = _backup_is_usable(backup_path, target)
    if failed_action is not None:
        raise RuntimeError(
            f"workflow backup {backup_path} is not usable: {failed_action}: {detail}"
        )
