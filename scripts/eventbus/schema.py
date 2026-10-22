"""scripts/eventbus/schema.py — Schema layer: schema definition and creation."""

from pathlib import Path
from sqlite3 import Connection

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
    """Create the events schema when the table is absent."""
    # First check if the table exists at all
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
    )
    if cur.fetchone():
        # Table exists — leave the existing database unchanged
        return
    # Table doesn't exist — create from schema.sql
    sql = _SCHEMA_PATH.read_text()
    conn.executescript(sql)
