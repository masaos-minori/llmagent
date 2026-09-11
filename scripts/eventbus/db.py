"""scripts/eventbus/db.py"""

from __future__ import annotations

import logging
import sqlite3
import threading
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_BUSY_TIMEOUT_MS = 30_000


def _apply_eventbus_pragmas(
    conn: sqlite3.Connection,
    *,
    busy_timeout_ms: int = _DEFAULT_BUSY_TIMEOUT_MS,
) -> None:
    """Apply WAL/synchronous=NORMAL/busy_timeout/foreign_keys pragmas to a connection."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")  # nosec B608 — busy_timeout_ms is a configurable integer, not user input
    conn.execute("PRAGMA foreign_keys=ON")


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
        _apply_eventbus_pragmas(conn)
        _init_schema(conn)
        return conn
    except sqlite3.Error as exc:
        logger.error(
            "eventbus: failed to open SQLite connection: path=%s err=%s", db_path, exc
        )
        raise


def _init_schema(conn: sqlite3.Connection) -> None:
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


def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns and indexes if they don't already exist; drop removed columns.

    SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS, so we
    catch the duplicate column error and ignore it. Indexes are created
    with CREATE INDEX IF NOT EXISTS which is idempotent.
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

    for col in ("cycle_failure_count", "redelivered_from"):
        try:
            if col == "cycle_failure_count":
                conn.execute(
                    f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
                )
            else:
                conn.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT")
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise

    try:
        conn.execute("ALTER TABLE events DROP COLUMN retry_count")
        logger.info("migrated: dropped column retry_count from events")
    except sqlite3.OperationalError as exc:
        if exc.args and "no such column" in exc.args[0].lower():
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
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate" in exc.args[0].lower():
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
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0].lower():
                pass  # table already exists (unlikely but defensive)
            else:
                raise


def ack_event(conn: sqlite3.Connection, event_id: str, now: str) -> tuple[bool, bool]:
    """Set acked_at on an event. Idempotent — will not overwrite existing ack.

    Returns (found, newly_acked):
      - (True, True)  = event found and newly acked
      - (True, False) = event found but already acked
      - (False, False) = event not found
    """
    cur = conn.execute(
        "UPDATE events SET acked_at = ? WHERE event_id = ? AND acked_at IS NULL",
        (now, event_id),
    )
    conn.commit()
    newly_acked = cur.rowcount > 0
    if newly_acked:
        return True, True
    # Check if event exists but was already acked
    exists = conn.execute(
        "SELECT 1 FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if exists:
        return True, False
    return False, False


def nack_event(conn: sqlite3.Connection, event_id: str) -> tuple[int, int]:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Returns (delivery_failure_count, cycle_failure_count), or (-1, -1) if the event was not found.
    """
    cur = conn.execute(
        "UPDATE events SET delivery_failure_count = delivery_failure_count + 1, cycle_failure_count = cycle_failure_count + 1 WHERE event_id = ?",
        (event_id,),
    )
    conn.commit()
    if cur.rowcount == 0:
        return (-1, -1)
    row = conn.execute(
        "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    if row:
        return (int(row["delivery_failure_count"]), int(row["cycle_failure_count"]))
    return (-1, -1)


def ack_event_for_consumer(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str,
    now: str,
) -> tuple[bool, bool, int | None]:
    """Acknowledge an event for a specific consumer atomically.

    Performs the per-consumer delivery-state UPSERT and the per-consumer
    offset advancement in a single SQLite transaction. Commits once at the
    end (or rolls back on exception).

    Returns (found, newly_acked, seq):
      - (True, True, seq)  = event found, newly acked by this consumer
      - (True, False, seq) = event found but already acked by this consumer
      - (False, False, None) = event not found

    Args:
        conn: SQLite connection (must be the shared eventbus connection).
        event_id: Event identifier.
        consumer_id: Non-empty consumer identifier.
        now: ISO-8601 UTC timestamp string.

    Raises:
        sqlite3.Error: If the transaction fails to commit or roll back.
    """
    assert consumer_id, "consumer_id must be non-empty"  # nosec B101 — contract invariant; caller validates before calling
    newly_acked = False
    seq: int | None = None

    try:
        # Per-consumer delivery-state UPSERT (idempotent)
        cur = conn.execute(
            "INSERT OR IGNORE INTO consumer_delivery "
            "(consumer_id, event_id, acked_at) VALUES (?, ?, ?)",
            (consumer_id, event_id, now),
        )
        newly_acked = cur.rowcount == 1  # INSERT happened; IGNORE means 0 rows affected

        if newly_acked:
            # Get the event seq for offset tracking
            row = conn.execute(
                "SELECT seq FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row:
                seq = int(row["seq"])
                # Atomic monotonic offset advancement
                conn.execute(
                    "INSERT INTO consumer_offsets(consumer_id, offset) "
                    "VALUES (?, ?) "
                    "ON CONFLICT(consumer_id) DO UPDATE SET "
                    "offset = excluded.offset "
                    "WHERE excluded.offset > consumer_offsets.offset",
                    (consumer_id, seq),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    if newly_acked:
        # seq is None only if event_id didn't actually exist in `events`
        # (consumer_delivery has no FK enforcement), which per the documented
        # contract means "not found" rather than a successful new ack.
        return (seq is not None), True, seq

    # Check if event exists but was already acked by this consumer
    already_acked = conn.execute(
        "SELECT 1 FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
        (consumer_id, event_id),
    ).fetchone()
    if already_acked:
        row = conn.execute(
            "SELECT seq FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return True, False, (int(row["seq"]) if row else None)

    return False, False, None


def get_consumer_offset(conn: sqlite3.Connection, consumer_id: str) -> int:
    """Return the last-committed sequence offset for a consumer, or 0 if none exists."""
    row = conn.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    return int(row["offset"]) if row else 0


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
        "INSERT OR IGNORE INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
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
            f" FROM events WHERE seq > ? AND topic IN ({placeholders}) ORDER BY seq"  # nosec B608 — all values bound via ? placeholders
        )
        params = (since_seq,) + tuple(topics)
    else:
        sql = "SELECT seq, event_id, topic, payload, producer, published_at FROM events WHERE seq > ? ORDER BY seq"
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
    """Increment dlq_requeue_count and clear dlq_at. Returns True if the event was found in DLQ."""
    row = conn.execute(
        "SELECT 1 FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    ).fetchone()
    if not row:
        return False
    cur = conn.execute(
        "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1, dlq_at = NULL WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    )
    conn.commit()
    return cur.rowcount > 0


def redeliver_event(conn: sqlite3.Connection, event_id: str) -> tuple[bool, str | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id):
      - (True, new_event_id)   = event found and redelivered
      - (False, None)          = event not found in DLQ
    """
    original_row = conn.execute(
        "SELECT delivery_failure_count FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    ).fetchone()
    if not original_row:
        return (False, None)

    new_event_id = uuid.uuid4().hex
    conn.execute(
        "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 WHERE event_id = ? AND dlq_at IS NOT NULL",
        (event_id,),
    )
    conn.execute(
        "INSERT INTO events (event_id, topic, payload, producer, published_at, delivery_failure_count, cycle_failure_count, redelivered_from) "
        "SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), delivery_failure_count, 0, ? "
        "FROM events WHERE event_id = ?",
        (new_event_id, event_id, event_id),
    )
    conn.commit()
    return (True, new_event_id)


def migrate_legacy_offsets(
    conn: sqlite3.Connection,
    offsets_dir: str,
) -> list[str]:
    """Migrate legacy file-based offsets into the consumer_offsets table.

    Reads each .map file under offsets_dir, recovers the original consumer_id
    from the .map companion file, reads its offset via read_offset(), and inserts
    a row into consumer_offsets using INSERT OR IGNORE (idempotent).

    For any offset file with no .map companion, falls back to the sanitized
    filename as consumer_id, logging a warning.

    Does NOT delete or modify any legacy files.

    Returns:
        List of consumer_ids that were migrated.
    """
    from eventbus.offsets import (
        _sanitize_consumer_id,  # noqa: PLC0415 — deferred to avoid a circular import with eventbus.offsets at module load time
    )

    migrated: list[str] = []
    dir_path = Path(offsets_dir)

    if not dir_path.exists():
        logger.warning("offsets_dir does not exist: %s", offsets_dir)
        return migrated

    # Iterate every offset file (not just ones with a .map companion) —
    # legacy files predating .map tracking, or written by any other means,
    # never get a .map companion and would otherwise be invisible to a
    # glob("*.map")-only scan.
    for offset_file in sorted(dir_path.iterdir()):
        if not offset_file.is_file() or offset_file.suffix == ".map":
            continue
        safe_id = offset_file.name
        map_file = dir_path / f"{safe_id}.map"
        try:
            stored_id = map_file.read_text().strip()
            if stored_id:
                consumer_id = stored_id
            else:
                # Empty .map file — fall back to sanitized filename
                consumer_id = _sanitize_consumer_id(safe_id)
                logger.warning(
                    "empty .map file for %s, using sanitized filename as consumer_id",
                    safe_id,
                )
        except FileNotFoundError:
            # No .map companion — use sanitized filename
            consumer_id = _sanitize_consumer_id(safe_id)
            logger.warning(
                "no .map companion for %s, using sanitized filename as consumer_id",
                safe_id,
            )

        # Read directly from the on-disk file rather than via read_offset(),
        # which re-sanitizes its consumer_id argument to build the path — since
        # safe_id here IS the raw on-disk filename (possibly unsanitized, e.g.
        # a legacy artifact), re-sanitizing it would look up a different path
        # than the one we just found.
        try:
            offset_val = int(offset_file.read_text().strip())
        except (FileNotFoundError, ValueError):
            offset_val = 0
        if offset_val > 0:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO consumer_offsets(consumer_id, offset) "
                    "VALUES (?, ?)",
                    (consumer_id, offset_val),
                )
                migrated.append(consumer_id)
                logger.debug(
                    "migrated offset: consumer=%s offset=%d",
                    consumer_id,
                    offset_val,
                )
            except sqlite3.IntegrityError as exc:
                logger.warning(
                    "failed to migrate offset for consumer %s: %s",
                    consumer_id,
                    exc,
                )

    return migrated
