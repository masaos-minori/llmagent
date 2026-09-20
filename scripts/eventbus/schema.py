"""Schema layer: schema definition, migration logic."""

from pathlib import Path
from sqlite3 import Connection

logger = __import__("logging").getLogger(__name__)

# _SCHEMA_PATH is relative to the project root
_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_DEFAULT_BUSY_TIMEOUT_MS = 30_000

# Shared column constants
from eventbus._constants import (
    _COL_CONSUMER_DELIVERY_FAILURE_COUNT,
    _COL_CYCLE_FAILURE_COUNT,
    _COL_DELIVERY_FAILURE_COUNT,
    _COL_DLQ_REQUEUE_COUNT,
    _COL_REDISTRIBUTED_FROM,
)


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
    """Create or migrate the events table schema."""
    # First check if the table exists at all
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
    )
    if cur.fetchone():
        # Table exists — run additive migration for new columns
        _migrate(conn)
        return
    # Table doesn't exist — create from schema.sql
    sql = _SCHEMA_PATH.read_text()
    conn.executescript(sql)


def _migrate(conn: Connection) -> None:
    """Add new columns and indexes if they don't already exist; drop removed columns.

    SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS, so we
    catch the duplicate column error and ignore it. Indexes are created
    with CREATE INDEX IF NOT EXISTS which is idempotent.
    """
    for col in (_COL_DELIVERY_FAILURE_COUNT, _COL_DLQ_REQUEUE_COUNT):
        try:
            conn.execute(
                f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
            )
            logger.info("migrated: added column %s to events", col)
        except Exception as exc:
            if exc.args and "duplicate column name" in str(exc.args[0]):
                pass  # column already exists
            else:
                raise

    for col in (_COL_CYCLE_FAILURE_COUNT, _COL_REDISTRIBUTED_FROM):
        try:
            if col == "cycle_failure_count":
                conn.execute(
                    f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
                )
            else:
                conn.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT")
            logger.info("migrated: added column %s to events", col)
        except Exception as exc:
            if exc.args and "duplicate column name" in str(exc.args[0]):
                pass  # column already exists
            else:
                raise

    # Add consumer-specific failure counter column
    try:
        conn.execute(
            f"ALTER TABLE events ADD COLUMN {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} INTEGER NOT NULL DEFAULT 0"
        )
        logger.info(
            "migrated: added column %s to events", _COL_CONSUMER_DELIVERY_FAILURE_COUNT
        )
    except Exception as exc:
        if exc.args and "duplicate column name" in str(exc.args[0]):
            pass  # column already exists
        else:
            raise

    # Add consumer_id column for tracking which consumer last received the event
    try:
        conn.execute("ALTER TABLE events ADD COLUMN consumer_id TEXT")
        logger.info("migrated: added column consumer_id to events")
    except Exception as exc:
        if exc.args and "duplicate column name" in str(exc.args[0]):
            pass  # column already exists
        else:
            raise

    try:
        conn.execute("ALTER TABLE events DROP COLUMN retry_count")
        logger.info("migrated: dropped column retry_count from events")
    except Exception as exc:
        if exc.args and "no such column" in str(exc.args[0]).lower():
            pass  # already dropped, or table created fresh without it
        else:
            raise

    for idx in (
        "idx_events_dlq_at ON events(dlq_at)",
        "idx_events_dlq_seq ON events(dlq_at, seq)",
    ):
        try:
            conn.execute(f"CREATE INDEX IF NOT EXISTS {idx}")
            logger.info("migrated: added index %s", idx)
        except Exception as exc:
            if exc.args and "duplicate" in str(exc.args[0]).lower():
                pass  # index already exists
            else:
                raise

    # New tables added in REQ-001/REQ-002: per-consumer delivery state and offset
    for tbl_name, ddl in [
        (
            "consumer_delivery",
            "CREATE TABLE IF NOT EXISTS consumer_delivery ("
            "    consumer_id TEXT NOT NULL,"
            "    event_id TEXT NOT NULL,"
            "    acked_at TEXT,"
            "    PRIMARY KEY (consumer_id, event_id)"
            ")",
        ),
        (
            "consumer_offsets",
            "CREATE TABLE IF NOT EXISTS consumer_offsets ("
            "    consumer_id TEXT PRIMARY KEY,"
            "    offset INTEGER NOT NULL DEFAULT 0"
            ")",
        ),
    ]:
        try:
            conn.execute(ddl)
            logger.info("migrated: created table %s", tbl_name)
        except Exception as exc:
            if exc.args and "duplicate column name" in str(exc.args[0]).lower():
                pass  # table already exists (unlikely but defensive)
            else:
                raise
