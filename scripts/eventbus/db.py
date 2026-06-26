from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_db_lock = threading.Lock()


def get_db_lock() -> threading.Lock:
    """Return the lock that must be held for all DB operations.

    All asyncio.to_thread callables in app.py must acquire this lock before
    executing any sqlite3 operation on the shared connection.
    """
    return _db_lock


def open_db(db_path: str) -> sqlite3.Connection:
    """Return a shared SQLite connection for the Event Bus.

    Uses check_same_thread=False. Concurrent access from asyncio.to_thread()
    calls is serialized by the module-level _db_lock (retrieve via get_db_lock()).
    WAL mode additionally serializes concurrent writers at the SQLite level.
    A single shared connection avoids per-request connection churn.
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _init_schema(conn)
        return conn
    except sqlite3.Error as exc:
        logger.error(
            "eventbus: failed to open SQLite connection: path=%s err=%s", db_path, exc
        )
        raise


def _init_schema(conn: sqlite3.Connection) -> None:
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


def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns if they don't already exist.

    SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS, so we
    catch the duplicate column error and ignore it.
    """
    for col in ("delivery_failure_count", "dlq_requeue_count"):
        try:
            conn.execute(
                f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
            )
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise


def ack_event(conn: sqlite3.Connection, event_id: str, now: str) -> bool:
    """Set acked_at on an event. Idempotent — will not overwrite existing ack.

    Returns True if the event was found and acked; False if already acked or not found.
    """
    cur = conn.execute(
        "UPDATE events SET acked_at = ? WHERE event_id = ? AND acked_at IS NULL",
        (now, event_id),
    )
    conn.commit()
    return cur.rowcount > 0


def nack_event(conn: sqlite3.Connection, event_id: str) -> int:
    """Increment delivery_failure_count for an event.

    Returns the new delivery_failure_count, or -1 if the event was not found.
    """
    cur = conn.execute(
        "UPDATE events SET delivery_failure_count = delivery_failure_count + 1"
        " WHERE event_id = ?",
        (event_id,),
    )
    conn.commit()
    if cur.rowcount == 0:
        return -1
    row = conn.execute(
        "SELECT delivery_failure_count FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return int(row["delivery_failure_count"]) if row else -1


def check_db(conn: sqlite3.Connection) -> bool:
    """Return True if the DB connection is usable."""
    try:
        conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False


def insert_event(
    conn: sqlite3.Connection,
    event_id: str,
    topic: str,
    payload_str: str,
    producer: str,
    published_at: str,
) -> tuple[int, bool]:
    """INSERT OR IGNORE. Returns (seq, inserted). seq is lastrowid or fetched if duplicate."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO events (event_id, topic, payload, producer, published_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, payload_str, producer, published_at),
    )
    conn.commit()
    inserted = cur.rowcount > 0
    seq = (
        int(cur.lastrowid) if (inserted and cur.lastrowid) else get_seq(conn, event_id)
    )
    return seq, inserted


def get_seq(conn: sqlite3.Connection, event_id: str) -> int:
    """Return the seq for an existing event_id; 0 if not found."""
    row = conn.execute(
        "SELECT seq FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    return int(row["seq"]) if row else 0


def fetch_events_since(
    conn: sqlite3.Connection,
    since_seq: int,
    topics: list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[sqlite3.Row]:
    """Return events with seq > since_seq, optionally filtered by topics."""
    if topics:
        placeholders = ",".join("?" for _ in topics)
        sql = (
            f"SELECT seq, event_id, topic, payload, producer, published_at"
            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq"
        )
        params = (since_seq,) + tuple(topics)
    else:
        sql = (
            "SELECT seq, event_id, topic, payload, producer, published_at"
            " FROM events WHERE seq > ? ORDER BY seq"
        )
        params = (since_seq,)
    if limit is not None and offset is not None:
        sql += f" LIMIT {limit} OFFSET {offset}"
    return conn.execute(sql, params).fetchall()


def fetch_dlq(
    conn: sqlite3.Connection,
    limit: int | None = None,
    offset: int | None = None,
) -> list[sqlite3.Row]:
    """Return events currently in the DLQ (dlq_at IS NOT NULL)."""
    sql = (
        "SELECT seq, event_id, topic, producer, published_at,"
        " delivery_failure_count, dlq_requeue_count, dlq_at"
        " FROM events WHERE dlq_at IS NOT NULL ORDER BY seq"
    )
    if limit is not None and offset is not None:
        sql += f" LIMIT {limit} OFFSET {offset}"
    return conn.execute(sql).fetchall()


def count_dlq(conn: sqlite3.Connection) -> int:
    """Return the number of events currently in the DLQ."""
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE dlq_at IS NOT NULL"
    ).fetchone()
    return int(row[0]) if row else 0


def requeue_event(conn: sqlite3.Connection, event_id: str) -> bool:
    """Increment dlq_requeue_count and clear dlq_at. Returns True if the event was found."""
    cur = conn.execute(
        "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1, dlq_at = NULL WHERE event_id = ?",
        (event_id,),
    )
    conn.commit()
    return cur.rowcount > 0
