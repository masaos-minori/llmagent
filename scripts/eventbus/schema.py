"""scripts/eventbus/schema.py — Schema layer: schema definition and creation."""

from pathlib import Path
from sqlite3 import Connection

from shared.schema_fingerprint import assert_matches

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


def _init_schema(conn: Connection) -> None:
    """Initialize eventbus database schema, enforcing an exact fingerprint match.

    A newly created database is created from schema.sql; an existing database is
    accepted only when its whole schema matches the shared fingerprint of that
    DDL. A mismatch raises before any write or DDL executes. Automatic migration
    and version stamping are not supported (REQ-003/REQ-004), the operator
    archives and recreates a mismatching database.
    """
    sql = _SCHEMA_PATH.read_text()
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
    )
    if not cur.fetchone():
        conn.executescript(sql)
        return
    assert_matches(conn, sql, label="eventbus.sqlite")
