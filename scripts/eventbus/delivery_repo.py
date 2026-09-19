"""Delivery repository: ack/nack semantics and per-consumer delivery state."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

# Shared column constants
from eventbus._constants import _COL_ACKED_AT, _COL_EVENT_ID  # noqa: PLC0415

# Layer-owned column constants
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"
_COL_DLQ_AT = "dlq_at"


@dataclass(frozen=True)
class NackResult:
    """Return value for nack_event().

    delivery_failure_count: int | Literal[-1] — -1 if event not found, otherwise current failure count.
    cycle_failure_count: int | Literal[-2] — -2 if event in invalid state, otherwise current cycle count.
    """

    delivery_failure_count: int | Literal[-1]
    cycle_failure_count: int | Literal[-2]


def ack_event(
    conn: sqlite3.Connection,
    event_id: str,
    now: str,
) -> tuple[bool, bool]:
    """Set acked_at on an event. Idempotent — will not overwrite existing ack.

    Returns (found, newly_acked):
      - (True, True)  = event found and newly acked
      - (True, False) = event found but already acked
      - (False, False) = event not found
    """
    try:
        cur = conn.execute(
            f"UPDATE events SET {_COL_ACKED_AT} = ? WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL",  # nosec B608 — column names are module-level constants, values parameterized
            (now, event_id),
        )
        conn.commit()
        newly_acked = cur.rowcount > 0
        if newly_acked:
            return True, True
        exists = conn.execute(
            f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?",
            (event_id,),  # nosec B608 — column names are module-level constants, values parameterized
        ).fetchone()
        if exists:
            return True, False
        return False, False
    except Exception:
        conn.rollback()
        raise


def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str | None = None,  # Optional — for consumer-specific failure tracking
) -> NackResult:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (acked_at IS NULL
    AND dlq_at IS NULL). Events that are already ACKed or DLQ'd cannot have their
    failure counts incremented — attempting to do so would corrupt state.

    If consumer_id is provided, also increment the consumer-specific failure count.

    Returns NackResult with:
      - delivery_failure_count: current count on success, -1 if event not found
      - cycle_failure_count: current count on success, -2 if event in invalid state
    """
    try:
        # Build the UPDATE statement with optional consumer-specific failure tracking
        update_clause = (
            f"{_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, "
            f"{_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1"
        )
        where_clause = (
            f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"
        )
        params: list[str] = [event_id]

        if consumer_id is not None:
            # Also increment consumer-specific failure count
            update_clause += f", {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1"

        sql = f"UPDATE events SET {update_clause} WHERE {where_clause}"
        cur = conn.execute(sql, params)
        conn.commit()
        if cur.rowcount == 0:
            existing = conn.execute(
                f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
                (event_id,),
            ).fetchone()
            if existing:
                return NackResult(-2, -2)
            return NackResult(-1, -1)
        row = conn.execute(
            f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if row:
            return NackResult(
                int(row[_COL_DELIVERY_FAILURE_COUNT]),
                int(row[_COL_CYCLE_FAILURE_COUNT]),
            )
        return NackResult(-1, -1)
    except Exception:
        conn.rollback()
        raise


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
        # Check if the delivery record exists and its acked_at status
        existing = conn.execute(
            "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
        # Pending delivery (acked_at IS NULL) counts as newly_acked
        newly_acked = existing is None or existing["acked_at"] is None

        # Per-consumer delivery-state UPSERT (idempotent)
        conn.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, acked_at) VALUES (?, ?, ?) "
            "ON CONFLICT(consumer_id, event_id) DO UPDATE SET acked_at = excluded.acked_at",
            (consumer_id, event_id, now),
        )

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

    # Event exists but was already acked by this consumer
    row = conn.execute(
        "SELECT seq FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    return True, False, (int(row["seq"]) if row else None)


def get_consumer_offset(conn: sqlite3.Connection, consumer_id: str) -> int:
    """Return the last-committed sequence offset for a consumer, or 0 if none exists."""
    row = conn.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    return int(row["offset"]) if row else 0
