"""Delivery repository: ack/nack semantics and per-consumer delivery state."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

# Shared column constants
from eventbus._constants import (  # noqa: PLC0415 — deferred import avoids a circular import with eventbus._constants
    _COL_CONSUMER_DELIVERY_FAILURE_COUNT,
    _COL_CONSUMER_LAST_NACK_ATTEMPT,
    _COL_CYCLE_FAILURE_COUNT,
    _COL_DELIVERY_FAILURE_COUNT,
    _COL_DLQ_AT,
    _COL_EVENT_ID,
)


@dataclass(frozen=True)
class NackResult:
    """Return value for nack_event().

    delivery_failure_count: int | Literal[-1] — -1 if event not found, otherwise current count.
    cycle_failure_count: int | Literal[-2] — -2 if event in invalid state, otherwise current count.
    consumer_failure_count: int | None — per-consumer failure count when consumer_id was provided,
      None when consumer_id was not provided.
    """

    delivery_failure_count: int | Literal[-1]
    cycle_failure_count: int | Literal[-2]
    consumer_failure_count: int | None = None


def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str | None = None,  # Optional — for consumer-specific failure tracking
    last_nack_attempt: str | None = None,  # REQ-001: idempotency key for NACK
) -> NackResult:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (no dlq_at).
    Events that are already DLQ'd cannot have their failure counts incremented
    — attempting to do so would corrupt state.

    If consumer_id is provided, also increment the consumer-specific failure count.
    NACK is idempotent per delivery attempt: if the same consumer has already
    NACKed this event for the same attempt ID (last_nack_attempt matches), the
    count is not incremented again.

    Returns NackResult with:
      - delivery_failure_count: current count on success, -1 if event not found
      - cycle_failure_count: current count on success, -2 if event in invalid state
      - consumer_failure_count: per-consumer count when consumer_id was provided
    """
    try:
        # Check if event exists and is not DLQ'd
        existing = conn.execute(
            f"SELECT {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",
            (event_id,),
        ).fetchone()
        if not existing:
            return NackResult(-1, -1)
        if existing[_COL_DLQ_AT] is not None:
            return NackResult(-2, -2)

        if consumer_id is not None:
            # Per-consumer ACK guard: reject NACK if this consumer already ACKed
            acked = conn.execute(
                "SELECT 1 FROM consumer_delivery "
                "WHERE consumer_id = ? AND event_id = ? AND acked_at IS NOT NULL",
                (consumer_id, event_id),
            ).fetchone()
            if acked:
                return NackResult(-2, -2)

            # NACK idempotency: skip if same consumer already NACKed this attempt
            last_attempt = conn.execute(
                f"SELECT {_COL_CONSUMER_LAST_NACK_ATTEMPT} FROM consumer_delivery "
                f"WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
            if last_attempt and last_attempt[_COL_CONSUMER_LAST_NACK_ATTEMPT] == last_nack_attempt:
                # Idempotent: return current counts without incrementing
                consumer_row = conn.execute(
                    f"SELECT {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} FROM consumer_delivery "
                    f"WHERE consumer_id = ? AND event_id = ?",
                    (consumer_id, event_id),
                ).fetchone()
                if consumer_row:
                    return NackResult(
                        int(existing[_COL_DLQ_AT]) if existing else -1,
                        -2,
                        int(consumer_row[_COL_CONSUMER_DELIVERY_FAILURE_COUNT]),
                    )
                return NackResult(-1, -1)

        # Update events table (delivery_failure_count, cycle_failure_count)
        conn.execute(
            f"UPDATE events SET {_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, "
            f"{_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1 "
            f"WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NULL",
            (event_id,),
        )

        # Update consumer_delivery table if consumer_id is provided
        if consumer_id is not None:
            conn.execute(
                f"INSERT INTO consumer_delivery (consumer_id, event_id, {_COL_CONSUMER_DELIVERY_FAILURE_COUNT}, {_COL_CONSUMER_LAST_NACK_ATTEMPT}) "
                f"VALUES (?, ?, 1, ?) "
                f"ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
                f"{_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1, "
                f"{_COL_CONSUMER_LAST_NACK_ATTEMPT} = excluded.{_COL_CONSUMER_LAST_NACK_ATTEMPT}",
                (consumer_id, event_id, last_nack_attempt),
            )

        conn.commit()

        # Read back the counts
        row = conn.execute(
            f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",
            (event_id,),
        ).fetchone()
        if row:
            result = NackResult(
                int(row[_COL_DELIVERY_FAILURE_COUNT]),
                int(row[_COL_CYCLE_FAILURE_COUNT]),
            )
            # Include per-consumer failure count when consumer_id was provided
            if consumer_id is not None:
                consumer_row = conn.execute(
                    f"SELECT {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} FROM consumer_delivery "
                    f"WHERE consumer_id = ? AND event_id = ?",
                    (consumer_id, event_id),
                ).fetchone()
                if consumer_row:
                    result = NackResult(
                        result.delivery_failure_count,
                        result.cycle_failure_count,
                        int(consumer_row[_COL_CONSUMER_DELIVERY_FAILURE_COUNT]),
                    )
            return result
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
        # REQ-005: Verify event existence BEFORE writing consumer_delivery
        # This prevents orphan rows in consumer_delivery for nonexistent events
        event_exists = conn.execute(
            f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?",
            (event_id,),
        ).fetchone()
        if not event_exists:
            return False, False, None

        # REQ-005: Reject ACK for DLQ events
        dlq_row = conn.execute(
            f"SELECT {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",
            (event_id,),
        ).fetchone()
        if dlq_row and dlq_row[_COL_DLQ_AT] is not None:
            return True, False, None

        # Check if the delivery record exists and its acked_at status
        existing = conn.execute(
            "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
        # Pending delivery (acked_at IS NULL) counts as newly_acked
        newly_acked = existing is None or existing["acked_at"] is None

        # REQ-005: Keep first acked_at via COALESCE — do not overwrite
        conn.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, acked_at) VALUES (?, ?, ?) "
            "ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
            "acked_at = COALESCE(consumer_delivery.acked_at, excluded.acked_at)",
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
        return True, True, seq

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


def get_resume_position(conn: sqlite3.Connection, consumer_id: str) -> int:
    """Compute the resume position for a reconnecting consumer.

    Returns the maximum of:
      - The stored offset (high-water mark of acknowledged seq values)
      - The lowest unacked seq among events with seq <= stored offset

    This ensures no unacked event is skipped on reconnect while still
    allowing fast-forward past already-acked events.

    Args:
        conn: SQLite connection.
        consumer_id: Consumer identifier.

    Returns:
        Resume position (int). Returns 0 if no offset exists yet.
    """
    # Get stored offset
    row = conn.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    if row is None:
        return 0  # No offset yet — start from beginning

    stored_offset = int(row["offset"])

    # Find lowest unacked seq <= stored_offset
    # LEFT JOIN required: events with NO consumer_delivery record must be
    # treated as unacked (never attempted for delivery to this consumer).
    row = conn.execute(
        "SELECT MIN(e.seq) FROM events e "
        "LEFT JOIN consumer_delivery cd ON e.event_id = cd.event_id "
        "AND cd.consumer_id = ? "
        "WHERE (cd.acked_at IS NULL OR cd.event_id IS NULL) "
        "AND e.seq <= ?",
        (consumer_id, stored_offset),
    ).fetchone()

    if row and row[0]:
        # Unacked event found — deliver starting from the lowest unacked seq
        return int(row[0])
    else:
        # All events up to stored_offset are acked — fast-forward past them
        return stored_offset + 1
