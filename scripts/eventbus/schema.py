"""scripts/eventbus/schema.py — Schema layer: schema definition and creation."""

import re
from pathlib import Path
from sqlite3 import Connection

from shared.eventbus_schema_fingerprint import assert_matches

logger = __import__("logging").getLogger(__name__)

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


def _init_schema(conn: Connection) -> None:
    """Create the schema when absent; accept only the current schema when present.

    A database stamped with the current version is validated against the shared
    schema fingerprint before returning, so a correctly stamped but malformed
    database is refused. Every other existing database — including an unstamped
    one (user_version 0) — is refused before any mutation and left untouched:
    automatic migration and version stamping are not supported (REQ-003/REQ-004),
    the operator archives and recreates such databases.
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
    raise RuntimeError(
        f"eventbus.sqlite (user_version {found}, expected {expected}): "
        "The database does not match the current schema. Automatic migration and "
        "version stamping are not supported. Stop the service, archive the existing "
        "database if required, remove or rename it, and create a new database using "
        "the current schema."
    )
