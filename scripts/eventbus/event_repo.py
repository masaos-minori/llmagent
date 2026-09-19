"""Event repository: all event read/write operations."""

from __future__ import annotations

import logging
import sqlite3

import orjson

logger = logging.getLogger(__name__)

# Shared column constants

# Layer-owned column constants
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"


def _canonical_payload(payload_str: str) -> bytes:
    """Return canonical JSON representation of a payload string."""
    return orjson.dumps(orjson.loads(payload_str), option=orjson.OPT_SORT_KEYS)


def insert_event(
    conn: sqlite3.Connection,
    event_id: str,
    topic: str,
    payload_str: str,
    producer: str,
    published_at: str,
) -> tuple[int | None, bool, str]:
    """INSERT OR IGNORE. Returns (seq, inserted, status).

    For duplicates:
      - status="duplicate": identical content, return original seq
      - status="conflict": conflicting content, return None

    Canonical equality fields: topic, payload (canonical JSON), producer.
    published_at is excluded from canonical equality (server-generated).
    """
    cur = conn.execute(
        "INSERT OR IGNORE INTO events (event_id, topic, payload, producer, published_at) VALUES (?, ?, ?, ?, ?)",
        (event_id, topic, payload_str, producer, published_at),
    )
    conn.commit()
    inserted = cur.rowcount > 0

    if inserted:
        seq = int(cur.lastrowid) if cur.lastrowid else 0
        return seq, True, "inserted"

    # Duplicate detected — compare canonical fields
    existing_row = conn.execute(
        "SELECT topic, payload, producer FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()

    if existing_row is None:
        # Race condition: row was deleted between INSERT and SELECT
        return None, False, "conflict"

    # Compare canonical fields
    existing_payload_canonical = _canonical_payload(existing_row["payload"])
    incoming_payload_canonical = _canonical_payload(payload_str)

    if (
        existing_row["topic"] == topic
        and existing_payload_canonical == incoming_payload_canonical
        and existing_row["producer"] == producer
    ):
        # Identical content — idempotent success
        seq = get_seq(conn, event_id)
        return seq, False, "duplicate"
    else:
        # Conflicting content — reject without modifying stored data
        return None, False, "conflict"


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
        # Validate bounds before parameterizing
        if limit < 0 or offset < 0:
            raise ValueError(
                f"limit and offset must be non-negative, got limit={limit!r}, offset={offset!r}"
            )
        sql += " LIMIT ? OFFSET ?"
        params = params + (limit, offset)
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
    params: tuple[int, ...] = ()
    if limit is not None and offset is not None:
        # Validate bounds before parameterizing
        if limit < 0 or offset < 0:
            raise ValueError(
                f"limit and offset must be non-negative, got limit={limit!r}, offset={offset!r}"
            )
        sql += " LIMIT ? OFFSET ?"
        params = params + (limit, offset)
    return conn.execute(sql, params).fetchall()


def count_dlq(conn: sqlite3.Connection) -> int:
    """Return the number of events currently in the DLQ."""
    row = conn.execute(
        "SELECT COUNT(*) FROM events WHERE dlq_at IS NOT NULL"
    ).fetchone()
    return int(row[0]) if row else 0
