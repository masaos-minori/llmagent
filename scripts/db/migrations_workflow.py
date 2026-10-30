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


_VALID_TASK_STATUSES = ("pending", "running", "completed", "failed", "halted")
_VALID_ATTEMPT_STATUSES = ("running", "completed", "failed")

# Frozen DDL of the 1.3.0 tables; the canonical DDL in db/schema_sql.py must stay equal
# (the runner's fingerprint check fails on drift), but this text must not follow later
# schema changes, so it is a literal copy.
_RECOVERY_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE tasks_new (
        task_id          TEXT PRIMARY KEY,
        session_id       TEXT,
        workflow_id      TEXT,
        turn_number      INTEGER,
        workflow_version TEXT NOT NULL,
        status           TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'running', 'completed', 'failed', 'halted')),
        task_nonce       TEXT UNIQUE NOT NULL,
        created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )
    """,
    """
    INSERT INTO tasks_new
        (task_id, session_id, workflow_id, turn_number, workflow_version, status,
         task_nonce, created_at, updated_at)
    SELECT task_id, session_id, workflow_id, turn_number, workflow_version, status,
           task_nonce, created_at, updated_at
    FROM tasks
    """,
    """
    CREATE TABLE attempts_new (
        attempt_id   TEXT PRIMARY KEY,
        task_id      TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id     TEXT NOT NULL,
        status       TEXT NOT NULL DEFAULT 'running'
                     CHECK (status IN ('running', 'completed', 'failed')),
        started_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        ended_at     TEXT,
        error_msg    TEXT,
        error_kind   TEXT,
        error_detail TEXT,
        attempt_number INTEGER NOT NULL
    )
    """,
    """
    INSERT INTO attempts_new
        (attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg,
         error_kind, error_detail, attempt_number)
    SELECT attempt_id, task_id, stage_id, status, started_at, ended_at, error_msg,
           error_kind, error_detail,
           ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)
    FROM attempts
    """,
    """
    CREATE TABLE processed_events_new (
        event_id    TEXT PRIMARY KEY,
        task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        stage_id    TEXT NOT NULL,
        recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        workflow_id TEXT,
        attempt_id  TEXT NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE,
        attempt_number INTEGER NOT NULL
    )
    """,
    # The old rows were started markers; the new ledger holds completed stages only,
    # so it is rebuilt from the completed attempts and the old rows are discarded.
    """
    INSERT INTO processed_events_new
        (event_id, task_id, stage_id, recorded_at, workflow_id, attempt_id,
         attempt_number)
    SELECT a.task_id || ':' || a.stage_id || ':' || a.attempt_number, a.task_id,
           a.stage_id, COALESCE(a.ended_at, a.started_at), t.workflow_id,
           a.attempt_id, a.attempt_number
    FROM attempts_new a JOIN tasks_new t ON t.task_id = a.task_id
    WHERE a.status = 'completed'
    """,
    "DROP TABLE processed_events",
    "DROP TABLE attempts",
    "DROP TABLE tasks",
    "ALTER TABLE tasks_new RENAME TO tasks",
    "ALTER TABLE attempts_new RENAME TO attempts",
    "ALTER TABLE processed_events_new RENAME TO processed_events",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_attempts_task_stage_number
        ON attempts(task_id, stage_id, attempt_number)
    """,
)


def _rebuild_recovery_schema(conn: sqlite3.Connection) -> None:
    """Rebuild tasks, attempts, and processed_events with the recovery constraints."""
    for statement in _RECOVERY_SCHEMA_STATEMENTS:
        conn.execute(statement)


def _check_statuses(conn: sqlite3.Connection) -> None:
    """Refuse rows whose status the new constraints would reject."""
    for table, valid in (
        ("tasks", _VALID_TASK_STATUSES),
        ("attempts", _VALID_ATTEMPT_STATUSES),
    ):
        marks = ", ".join("?" for _ in valid)
        row = conn.execute(
            f"SELECT status, COUNT(*) FROM {table} WHERE status NOT IN ({marks})"  # nosec B608 — table is a fixed literal, values are bound
            " GROUP BY status LIMIT 1",
            valid,
        ).fetchone()
        if row is not None:
            raise RuntimeError(
                f"{table} has {row[1]} row(s) with unknown status {row[0]!r}"
            )


def _check_foreign_keys(conn: sqlite3.Connection) -> None:
    """Fail the step when the rebuild left a dangling reference."""
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError(f"foreign key violations after rebuild: {len(violations)}")


MIGRATIONS: tuple[MigrationSpec, ...] = (
    MigrationSpec(
        migration_id="rename-task-nonce",
        from_version="1.1.0",
        to_version="1.2.0",
        apply=_rename_task_key,
        precondition=_check_task_key_rename_applicable,
        postcondition=_check_task_key_renamed,
    ),
    MigrationSpec(
        migration_id="recovery-schema",
        from_version="1.2.0",
        to_version="1.3.0",
        apply=_rebuild_recovery_schema,
        precondition=_check_statuses,
        postcondition=_check_foreign_keys,
    ),
)


def connect_workflow(path: str) -> sqlite3.Connection:
    """Open `workflow.sqlite` (or a copy of it) for a migration run."""
    conn = sqlite3.connect(path, timeout=_BUSY_TIMEOUT_S)
    # Foreign keys stay off: a table rebuild drops the parent `tasks`, and with them on
    # the implicit DELETE would cascade-remove every attempt row. The pragma cannot be
    # changed inside the runner's transaction, so the connection opens without it.
    apply_connection_pragmas(conn, write_mode=False)
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
