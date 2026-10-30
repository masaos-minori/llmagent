"""scripts/db/migrations_workflow.py — workflow.sqlite migration registry.

Declares how `workflow.sqlite` is opened, versioned, and shape-checked for the shared
migration framework, and holds the registry of forward steps (empty until a schema
change registers one). The version is the latest `workflow_schema_version` row, not
`PRAGMA user_version`.
"""

import sqlite3

from shared.db_migrations import MigrationDomain, MigrationSpec
from shared.eventbus_schema_fingerprint import build_fingerprint

from db.helper import apply_connection_pragmas
from db.schema_sql import WORKFLOW_SCHEMA_VERSION, build_workflow_schema_sql

_BUSY_TIMEOUT_S = 30.0


def _rename_task_key(conn: sqlite3.Connection) -> None:
    """Rename `tasks.idempotency_key` to `task_nonce`; the UNIQUE constraint follows."""
    conn.execute("ALTER TABLE tasks RENAME COLUMN idempotency_key TO task_nonce")


def _check_task_key_rename_applicable(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "idempotency_key" not in columns or "task_nonce" in columns:
        raise RuntimeError(
            "tasks must have idempotency_key and no task_nonce column before the rename"
        )


def _check_task_key_renamed(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "task_nonce" not in columns or "idempotency_key" in columns:
        raise RuntimeError("tasks.task_nonce is missing after the rename")


MIGRATIONS: tuple[MigrationSpec, ...] = (
    MigrationSpec(
        migration_id="rename-task-nonce",
        from_version="1.1.0",
        to_version="1.2.0",
        apply=_rename_task_key,
        precondition=_check_task_key_rename_applicable,
        postcondition=_check_task_key_renamed,
    ),
)


def connect_workflow(path: str) -> sqlite3.Connection:
    """Open `workflow.sqlite` (or a copy of it) with the standard connection pragmas."""
    conn = sqlite3.connect(path, timeout=_BUSY_TIMEOUT_S)
    apply_connection_pragmas(conn, write_mode=True)
    return conn


def read_workflow_version(conn: sqlite3.Connection) -> str | None:
    """Return the latest recorded schema version, or None when none is recorded.

    `applied_at` has one-second resolution, so `rowid` breaks ties between versions
    written in the same second.
    """
    try:
        row = conn.execute(
            "SELECT version FROM workflow_schema_version"
            " ORDER BY applied_at DESC, rowid DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return None if row is None else str(row[0])


def write_workflow_version(conn: sqlite3.Connection, version: str) -> None:
    """Record `version` as the newest schema version."""
    conn.execute("INSERT INTO workflow_schema_version (version) VALUES (?)", (version,))


def verify_workflow_shape(conn: sqlite3.Connection, version: str) -> None:
    """Raise RuntimeError when the schema differs from the canonical workflow DDL.

    Only the current version has a canonical DDL, so an intermediate version is
    covered by its spec's postcondition instead.
    """
    if version != WORKFLOW_SCHEMA_VERSION:
        return
    fresh = sqlite3.connect(":memory:")
    try:
        fresh.executescript(build_workflow_schema_sql())
        expected = build_fingerprint(fresh)
    finally:
        fresh.close()
    if build_fingerprint(conn) != expected:
        raise RuntimeError(
            f"workflow.sqlite shape differs from the canonical schema at {version}"
        )


WORKFLOW_DOMAIN = MigrationDomain(
    name="workflow",
    connect=connect_workflow,
    read_version=read_workflow_version,
    write_version=write_workflow_version,
    verify_shape=verify_workflow_shape,
)
