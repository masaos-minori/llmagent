"""scripts/eventbus/schema.py — Schema layer: schema definition and creation."""

import re
import sqlite3
from pathlib import Path
from sqlite3 import Connection

from shared.db_migrations import MigrationRefusalError, MigrationRunner, read_ledger
from shared.eventbus_schema_fingerprint import assert_matches

from eventbus.migrations import REGISTRY, verify_backup

logger = __import__("logging").getLogger(__name__)

# Shared forward-only migration runner for the eventbus domain (dbmig001).
_MIGRATIONS = MigrationRunner()

# _SCHEMA_PATH is relative to the project root
_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_DEFAULT_BUSY_TIMEOUT_MS = 30_000


def _apply_eventbus_pragmas(
    conn: Connection,
    *,
    busy_timeout_ms: int = _DEFAULT_BUSY_TIMEOUT_MS,
) -> None:
    """Apply WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragmas to a connection."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")  # nosec B608 — busy_timeout_ms is a configurable integer, not user input
    conn.execute("PRAGMA foreign_keys=ON")


_VERSION_RE = re.compile(r"^PRAGMA\s+user_version\s*=\s*(\d+)\s*;", re.MULTILINE)


def _expected_schema_version(sql: str) -> int:
    """Return the schema version that schema.sql stamps via PRAGMA user_version."""
    match = _VERSION_RE.search(sql)
    if match is None:
        raise RuntimeError(f"{_SCHEMA_PATH} does not stamp PRAGMA user_version")
    return int(match.group(1))


def _table_columns(conn: Connection) -> dict[str, list[tuple[object, ...]]]:
    """Return {table: PRAGMA table_info rows} for every user table."""
    tables = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    # PRAGMA cannot bind the table name; names come from sqlite_master, not user input.
    return {
        t: [tuple(r) for r in conn.execute(f'PRAGMA table_info("{t}")')]  # nosec B608 — table name read from sqlite_master
        for t in tables
    }


def _matches_current_schema(conn: Connection, sql: str) -> bool:
    """Return True when every table in schema.sql exists with identical columns."""
    fresh = sqlite3.connect(":memory:")
    try:
        fresh.executescript(sql)
        expected = _table_columns(fresh)
    finally:
        fresh.close()
    actual = _table_columns(conn)
    return all(actual.get(t) == cols for t, cols in expected.items())


def _init_schema(conn: Connection) -> None:
    """Create the schema when absent; verify the schema version when present.

    A database stamped with the current version is validated against the shared
    schema fingerprint before returning, so a correctly stamped but malformed
    database is refused. An existing unstamped database (user_version 0) is
    stamped only after its tables match schema.sql column for column. A database
    at a lower-but-registered version takes the forward-only migration path
    (dbmig001): the shared runner applies the registered steps gate-gated, and a
    still-unregistered, cyclic, or downgrade case keeps today's fail-closed
    refusal (it must be recreated, never migrated).
    """
    sql = _SCHEMA_PATH.read_text()
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
    )
    if not cur.fetchone():
        conn.executescript(sql)
        return
    expected = _expected_schema_version(sql)
    found = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if found == expected:
        assert_matches(conn)
        return
    if found == 0 and _matches_current_schema(conn, sql):
        conn.execute(f"PRAGMA user_version = {expected}")  # nosec B608 — expected is an int parsed from schema.sql
        return
    # Registered forward migration (dbmig001): a lower-but-registered version
    # takes the runner path instead of today's hard refusal. Fail-closed for any
    # unregistered, cyclic, or downgrade case (REQ-003/REQ-005); the gate runs
    # before any mutation so a refusal leaves the database at its previous state.
    try:
        path = _MIGRATIONS.plan(
            found, read_ledger(conn), REGISTRY, target_version=expected
        )
        applied = _MIGRATIONS.apply(conn, path, verify_backup)
    except (MigrationRefusalError, sqlite3.Error) as exc:
        raise RuntimeError(
            f"eventbus.sqlite schema version {found} differs from {expected} or its "
            "tables do not match schema.sql; recreate the database"
        ) from exc
    assert_matches(conn)
    logger.info(
        "eventbus.sqlite migrated %d -> %d (%d step(s)).",
        found,
        expected,
        len(applied),
    )
