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

from shared.db_migrations import (
    MigrationRefusalError,
    MigrationRefusalReason,
    MigrationRunner,
    MigrationSpec,
)

from db.recovery import _backup_is_usable
from db.schema_sql import WORKFLOW_SCHEMA_VERSION

logger = logging.getLogger(__name__)

# ``workflow_schema_version`` strings mapped to their integer ledger codes.
# Mirrors ``db.schema_sql.WORKFLOW_SCHEMA_VERSION`` (the head value must match
# the registry's head step); a string absent from this map cannot be migrated
# (refusal), keeping today's fail-closed semantics.
WORKFLOW_VERSION_CODES: dict[str, int] = {
    "1.1.0": 0,
    "1.2.0": 2,
    "1.3.0": 3,
    "1.4.0": 4,
}

# Head ledger code of the registry: 0 (legacy, no ledger) -> 1 (baseline) ->
# 2 (tool_call_state/execution_snapshots, toolexec001 row 06) ->
# 3 (tasks.idempotency_key -> tasks.task_nonce rename, wftaskapi001 row 12) ->
# 4 (attempts owner_id/lease_expires_at lease columns, wflease001 row 17).
# The integer ledger code is a namespace separate from the string marker; the
# bootstrap moves 0 -> 1 (the framework rejects a from == to step as a cycle).
WORKFLOW_TARGET_VERSION: int = 4

# Pre-ledger ``PRAGMA user_version`` the bootstrap applies only to. Legacy
# workflow databases carry no stamp (it is 0); anything else is refused.
_BASELINE_VERSION: int = 0

# Target ``PRAGMA user_version`` of the ledger bootstrap step.
_LEDGER_VERSION: int = 1

# Target ``PRAGMA user_version`` of the lifecycle-tables step.
_TOOL_STATE_VERSION: int = 2

# Target ``PRAGMA user_version`` of the task-key rename step.
_TASK_NONCE_VERSION: int = 3

# Target ``PRAGMA user_version`` of the attempt-lease columns step. Must match
# ``WORKFLOW_TARGET_VERSION`` and the shape the canonical schema template creates.
_ATTEMPT_LEASE_VERSION: int = 4

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
    f"{_LEDGER_CREATE_SQL} PRAGMA user_version = {_LEDGER_VERSION};"
)

# Tool-call lifecycle tables (toolexec001 REQ-007), byte-identical in shape to
# the same block in ``db.schema_sql.build_workflow_schema_sql`` (row 06 contract),
# so fresh-created and migrated databases converge. The step also replaces the
# string marker with the post-step version (delete + insert keeps a single
# latest row: readers resolve "latest" by applied_at at one-second granularity,
# and a same-second INSERT of two rows would be ambiguous) so the create path's
# fail-closed check accepts the migrated database, then stamps the ledger head
# code.
_TOOL_CALL_STATE_SQL = """CREATE TABLE IF NOT EXISTS execution_snapshots (
    snapshot_id   TEXT PRIMARY KEY,
    snapshot_json TEXT NOT NULL,
    recorded_at   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_call_state (
    idempotency_key TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL,
    tool            TEXT NOT NULL,
    state           TEXT NOT NULL CHECK (state IN ('pending', 'completed', 'failed', 'interrupted')),
    retry_class     TEXT NOT NULL,
    snapshot_id     TEXT REFERENCES execution_snapshots(snapshot_id),
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_call_state_task_state
    ON tool_call_state(task_id, state);"""

_TOOL_STATE_MUTATION_SQL = (
    f"{_TOOL_CALL_STATE_SQL} "  # nosec B608 — fixed module constants, no user input
    "DELETE FROM workflow_schema_version; "
    f"INSERT INTO workflow_schema_version (version) VALUES ('{WORKFLOW_SCHEMA_VERSION}'); "
    f"PRAGMA user_version = {_TOOL_STATE_VERSION};"
)

# Task-key rename (wftaskapi001 REQ-003/REQ-004). ``RENAME COLUMN`` preserves every
# row's stored value; the step also replaces the string marker with the post-step
# version and stamps the ledger head code, mirroring _TOOL_STATE_MUTATION_SQL's
# shape so fresh-created and migrated databases converge.
_TASK_NONCE_MUTATION_SQL = (
    "ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce; "
    "DELETE FROM workflow_schema_version; "
    f"INSERT INTO workflow_schema_version (version) VALUES ('{WORKFLOW_SCHEMA_VERSION}'); "  # nosec B608 — fixed module constants, no user input
    f"PRAGMA user_version = {_TASK_NONCE_VERSION};"
)

# Attempt-lease columns (wflease001 REQ-004). Two nullable ``ADD COLUMN``
# statements: an existing database with ``running`` rows migrates with null
# values, which is exactly the legacy-row population the REQ-008 age rule
# governs. The step also replaces the string marker with the post-step version
# and stamps the ledger head code, mirroring _TASK_NONCE_MUTATION_SQL's shape
# so fresh-created and migrated databases converge.
_ATTEMPT_LEASE_MUTATION_SQL = (
    "ALTER TABLE attempts ADD COLUMN owner_id TEXT; "
    "ALTER TABLE attempts ADD COLUMN lease_expires_at TEXT; "
    "DELETE FROM workflow_schema_version; "
    f"INSERT INTO workflow_schema_version (version) VALUES ('{WORKFLOW_SCHEMA_VERSION}'); "  # nosec B608 — fixed module constants, no user input
    f"PRAGMA user_version = {_ATTEMPT_LEASE_VERSION};"
)


def _latest_workflow_string(conn: sqlite3.Connection) -> str | None:
    """Return the latest recorded ``workflow_schema_version`` string, if any.

    Returns None when the table is absent (a database that predates the marker
    table) so the caller can treat "no marker" and "unmigratable" uniformly.
    """
    try:
        row = conn.execute(
            "SELECT version FROM workflow_schema_version "
            "ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        # The marker table is absent on a database that predates it.
        return None
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
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is at user_version {current}; the ledger bootstrap "
            f"step applies only to a {_BASELINE_VERSION}-stamped database",
        )
    latest = _latest_workflow_string(conn)
    if latest is None:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "no workflow_schema_version recorded; cannot resolve a baseline code",
        )
    if latest not in WORKFLOW_VERSION_CODES:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow schema version {latest!r} is not in the migration map "
            f"{list(WORKFLOW_VERSION_CODES)}; recreate the database",
        )


def _postcondition_fingerprint(conn: sqlite3.Connection) -> None:
    """Re-verify the ledger landed and the version was stamped to the step target."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _LEDGER_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}; expected "
            f"{_LEDGER_VERSION} after bootstrap",
        )
    baseline = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
    ).fetchone()
    if baseline is None:
        raise RuntimeError("workflow baseline row missing after bootstrap")


def _table_names(conn: sqlite3.Connection) -> set[str]:
    """Return the set of user table names in the database."""
    return {
        str(row[0])
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _precondition_tool_state(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is a bootstrapped pre-lifecycle baseline.

    Rejects: a database not exactly at the ledger version, a database whose
    ledger carries no ``workflow_ledger_baseline`` row (a forged stamp — the
    runner creates the ledger table itself, so only the recorded baseline row
    proves it went through the gated bootstrap), a database missing the core
    ``tasks`` table, and a database already carrying the lifecycle tables.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _LEDGER_VERSION:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is at user_version {current}; the "
            f"workflow_tool_call_state step applies only to a "
            f"{_LEDGER_VERSION}-stamped database",
        )
    baseline = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
    ).fetchone()
    if baseline is None:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "no workflow_ledger_baseline row in the ledger; refusing the "
            "workflow_tool_call_state step on a database that never went "
            "through the bootstrap",
        )
    tables = _table_names(conn)
    if _REQUIRED_TABLE not in tables:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is missing required table '{_REQUIRED_TABLE}'",
        )
    if {"tool_call_state", "execution_snapshots"} & tables:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "workflow.sqlite already has the tool_call_state/execution_snapshots "
            "tables; the step applies only to a database without them",
        )


def _postcondition_tool_state(conn: sqlite3.Connection) -> None:
    """Re-verify this step's own effect: lifecycle tables, stamped head code."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _TOOL_STATE_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}, not "
            f"{_TOOL_STATE_VERSION}, after the workflow_tool_call_state step",
        )
    tables = _table_names(conn)
    missing = sorted({"tool_call_state", "execution_snapshots"} - tables)
    if missing:
        raise RuntimeError(f"workflow_tool_call_state step did not create: {missing}")


def _precondition_task_nonce(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is a migrated lifecycle-tables database.

    Rejects: a database not exactly at code 2, a database whose ledger carries no
    ``workflow_ledger_baseline`` row (a forged stamp), a database missing the
    ``tasks`` table, and a database whose tasks table already carries the renamed
    column or has lost the old one — either shape means this step does not apply.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _TOOL_STATE_VERSION:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is at user_version {current}; the "
            f"workflow_task_nonce step applies only to a "
            f"{_TOOL_STATE_VERSION}-stamped database",
        )
    baseline = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
    ).fetchone()
    if baseline is None:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "no workflow_ledger_baseline row in the ledger; refusing the "
            "workflow_task_nonce step on a database that never went "
            "through the bootstrap",
        )
    tables = _table_names(conn)
    if _REQUIRED_TABLE not in tables:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is missing required table '{_REQUIRED_TABLE}'",
        )
    columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "task_nonce" in columns:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "workflow.sqlite tasks already has task_nonce; the rename step "
            "applies only to a database still carrying idempotency_key",
        )
    if "idempotency_key" not in columns:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "workflow.sqlite tasks has no idempotency_key column; refusing "
            "the rename on a database that is not the pre-rename shape",
        )


def _postcondition_task_nonce(conn: sqlite3.Connection) -> None:
    """Re-verify this step's own effect: renamed column, stamped head code."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _TASK_NONCE_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}, not "
            f"{_TASK_NONCE_VERSION}, after the workflow_task_nonce step",
        )
    columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "task_nonce" not in columns or "idempotency_key" in columns:
        raise RuntimeError(
            "workflow_task_nonce step did not rename tasks.idempotency_key "
            "to task_nonce"
        )


def _precondition_attempt_lease(conn: sqlite3.Connection) -> None:
    """Refuse unless the database is a migrated task-nonce database.

    Rejects: a database not exactly at code 3, a database whose ledger carries no
    ``workflow_ledger_baseline`` row (a forged stamp), a database missing the
    ``attempts`` table, and a database whose attempts table already carries
    either lease column — either shape means this step does not apply.
    """
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _TASK_NONCE_VERSION:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            f"workflow.sqlite is at user_version {current}; the "
            f"workflow_attempt_lease step applies only to a "
            f"{_TASK_NONCE_VERSION}-stamped database",
        )
    baseline = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE id='workflow_ledger_baseline'"
    ).fetchone()
    if baseline is None:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "no workflow_ledger_baseline row in the ledger; refusing the "
            "workflow_attempt_lease step on a database that never went "
            "through the bootstrap",
        )
    tables = _table_names(conn)
    if "attempts" not in tables:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "workflow.sqlite is missing required table 'attempts'",
        )
    columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info(attempts)").fetchall()
    }
    if "owner_id" in columns or "lease_expires_at" in columns:
        raise MigrationRefusalError(
            MigrationRefusalReason.UNKNOWN_PATH,
            "workflow.sqlite attempts already has a lease column; the step "
            "applies only to a database without owner_id/lease_expires_at",
        )


def _postcondition_attempt_lease(conn: sqlite3.Connection) -> None:
    """Re-verify this step's own effect: lease columns, stamped head code."""
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current != _ATTEMPT_LEASE_VERSION:
        raise RuntimeError(
            f"workflow.sqlite is at user_version {current}, not "
            f"{_ATTEMPT_LEASE_VERSION}, after the workflow_attempt_lease step",
        )
    columns = {
        str(row[1]) for row in conn.execute("PRAGMA table_info(attempts)").fetchall()
    }
    missing = sorted({"owner_id", "lease_expires_at"} - columns)
    if missing:
        raise RuntimeError(
            f"workflow_attempt_lease step did not add attempts columns: {missing}"
        )


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
    "workflow_tool_call_state": MigrationSpec(
        id="workflow_tool_call_state",
        from_version=1,
        to_version=2,
        preconditions=(_precondition_tool_state,),
        mutation_sql=_TOOL_STATE_MUTATION_SQL,
        postcondition=_postcondition_tool_state,
    ),
    "workflow_task_nonce": MigrationSpec(
        id="workflow_task_nonce",
        from_version=2,
        to_version=3,
        preconditions=(_precondition_task_nonce,),
        mutation_sql=_TASK_NONCE_MUTATION_SQL,
        postcondition=_postcondition_task_nonce,
    ),
    "workflow_attempt_lease": MigrationSpec(
        id="workflow_attempt_lease",
        from_version=3,
        to_version=4,
        preconditions=(_precondition_attempt_lease,),
        mutation_sql=_ATTEMPT_LEASE_MUTATION_SQL,
        postcondition=_postcondition_attempt_lease,
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
    Stamps ``user_version`` to the registry head code because the canonical
    schema template already creates the shape every registered step adds, so a
    fresh database is table-for-table identical to one that ran the full
    registered path (toolexec001 row 06 equivalence test).
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
