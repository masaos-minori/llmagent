"""Delivery repository: ack/nack semantics and per-consumer delivery state."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

# Shared column constants
from eventbus._constants import (  # noqa: PLC0415 — deferred import avoids a circular import with eventbus._constants
    _COL_ACKED_AT,
    _COL_CONSUMER_DELIVERY_FAILURE_COUNT,
    _COL_CYCLE_FAILURE_COUNT,
    _COL_DELIVERY_FAILURE_COUNT,
    _COL_DLQ_AT,
    _COL_EVENT_ID,
    _COL_LAST_NACK_ATTEMPT,
    _COL_SEQ,
)


@dataclass(frozen=True)
class NackResult:
    """Return value for nack_event().

    delivery_failure_count: int | Literal[-1] — -1 if event not found, otherwise current failure count.
    cycle_failure_count: int | Literal[-2] — -2 if event in invalid state, otherwise current cycle count.
    """

    delivery_failure_count: int | Literal[-1]
    cycle_failure_count: int | Literal[-2]


def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str | None = None,  # Optional — for consumer-specific failure tracking
) -> NackResult:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (dlq_at IS NULL).
    Events that are already DLQ'd cannot have their failure counts incremented —
    attempting to do so would corrupt state. The per-consumer ``acked_at`` state now
    lives solely in ``consumer_delivery`` (``events.acked_at`` was dropped, REQ-004),
    so the event-level guard is ``dlq_at`` only; a consumer that already ACKed is
    rejected by the per-consumer guard below.

    If consumer_id is provided, also record the NACK on ``consumer_delivery``:
    increment the per-consumer ``consumer_delivery_failure_count`` and key NACK
    idempotency on the delivery attempt via ``last_nack_attempt`` (REQ-001). A NACK
    that repeats the stored attempt identity is a no-op (counted once).

    Returns NackResult with:
      - delivery_failure_count: current shared count on success, -1 if event not found
      - cycle_failure_count: current shared count on success, -2 if event in invalid state
    """
    try:
        # Existence and DLQ state up front (acked_at no longer exists on events).
        existing = conn.execute(
            f"SELECT {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if existing is None:
            return NackResult(-1, -1)
        if existing[_COL_DLQ_AT] is not None:
            return NackResult(-2, -2)

        increment_shared = True
        if consumer_id is not None:
            # Per-consumer ACK guard: reject a NACK when this consumer already ACKed.
            already_acked = conn.execute(
                "SELECT 1 FROM consumer_delivery "
                "WHERE consumer_id = ? AND event_id = ? AND acked_at IS NOT NULL",
                (consumer_id, event_id),
            ).fetchone()
            if already_acked:
                return NackResult(-2, -2)
            # Idempotency: a NACK repeating the stored attempt identity is a no-op.
            if _is_repeat_nack(conn, event_id, consumer_id):
                increment_shared = False

        if increment_shared:
            conn.execute(
                f"UPDATE events SET "
                f"{_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, "
                f"{_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1 "
                f"WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NULL",  # nosec B608 — column names are module-level constants, values parameterized
                (event_id,),
            )
            if consumer_id is not None:
                _record_consumer_nack(conn, event_id, consumer_id)
            conn.commit()

        return _current_failure_counts(conn, event_id)
    except Exception:
        conn.rollback()
        raise


def _is_repeat_nack(conn: sqlite3.Connection, event_id: str, consumer_id: str) -> bool:
    """Return True if a NACK for the same delivery attempt was already recorded.

    The attempt identity is the event ``seq`` captured in
    ``consumer_delivery.last_nack_attempt``. A repeat NACK for the same attempt
    (at-least-once redelivery of an unacked delivery) is counted once.
    """
    seq_row = conn.execute(
        f"SELECT seq FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    ).fetchone()
    attempt_identity = (
        str(seq_row["seq"]) if seq_row and seq_row["seq"] is not None else None
    )
    cd = conn.execute(
        f"SELECT {_COL_LAST_NACK_ATTEMPT} FROM consumer_delivery "
        f"WHERE consumer_id = ? AND event_id = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (consumer_id, event_id),
    ).fetchone()
    return (
        cd is not None
        and cd[_COL_LAST_NACK_ATTEMPT] is not None
        and cd[_COL_LAST_NACK_ATTEMPT] == attempt_identity
    )


def _record_consumer_nack(
    conn: sqlite3.Connection, event_id: str, consumer_id: str
) -> None:
    """Record a per-consumer NACK on ``consumer_delivery``.

    Increments ``consumer_delivery_failure_count`` and stores the current attempt
    identity in ``last_nack_attempt``. Callers must have already ruled out a repeat
    NACK and an already-ACKed consumer.
    """
    seq_row = conn.execute(
        f"SELECT seq FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    ).fetchone()
    attempt_identity = (
        str(seq_row["seq"]) if seq_row and seq_row["seq"] is not None else None
    )
    conn.execute(
        f"INSERT INTO consumer_delivery "
        f"(consumer_id, event_id, acked_at, {_COL_LAST_NACK_ATTEMPT}, "
        f"{_COL_CONSUMER_DELIVERY_FAILURE_COUNT}) VALUES (?, ?, NULL, ?, 1) "
        f"ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
        f"{_COL_LAST_NACK_ATTEMPT} = excluded.{_COL_LAST_NACK_ATTEMPT}, "
        f"{_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = "
        f"{_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1",  # nosec B608 — column names are module-level constants, values parameterized
        (consumer_id, event_id, attempt_identity),
    )


def _current_failure_counts(conn: sqlite3.Connection, event_id: str) -> NackResult:
    """Read the current shared failure counts for an event after a NACK."""
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


def ack_event_for_consumer(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str,
    now: str,
) -> tuple[bool, bool, int | None, bool]:
    """Acknowledge an event for a specific consumer atomically.

    Performs the per-consumer delivery-state UPSERT and the per-consumer
    offset advancement in a single SQLite transaction. Commits once at the
    end (or rolls back on exception).

    Returns (found, newly_acked, seq, dlq):
      - (True, True, seq, False)  = event found, newly acked by this consumer
      - (True, False, seq, False) = event found but already acked by this consumer
      - (False, False, None, False) = event not found (no write performed)
      - (True, False, seq, True)  = event in the DLQ — caller must return 409

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
        # REQ-005: verify event existence BEFORE any write (no orphan rows on miss).
        event_row = conn.execute(
            f"SELECT {_COL_SEQ}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if event_row is None:
            return (False, False, None, False)
        seq = int(event_row[_COL_SEQ])

        # REQ-005: reject ACKs for events already in the DLQ (signal 409 via dlq=True).
        if event_row[_COL_DLQ_AT] is not None:
            return (True, False, seq, True)

        # Determine whether this ack is new (delivery pending or no row yet).
        existing = conn.execute(
            f"SELECT {_COL_ACKED_AT} FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
            "WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
        newly_acked = existing is None or existing[_COL_ACKED_AT] is None

        if newly_acked:
            # Per-consumer delivery-state UPSERT: preserve the first acked_at
            # (COALESCE, never overwrite) and reset last_nack_attempt so a later
            # NACK starts a fresh attempt (REQ-001). consumer_delivery_failure_count
            # is intentionally NOT reset — it accumulates across attempts.
            conn.execute(
                "INSERT INTO consumer_delivery "
                f"(consumer_id, event_id, {_COL_ACKED_AT}) VALUES (?, ?, ?) "
                "ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
                f"{_COL_ACKED_AT} = CASE WHEN consumer_delivery.{_COL_ACKED_AT} IS NULL "
                f"THEN excluded.{_COL_ACKED_AT} ELSE consumer_delivery.{_COL_ACKED_AT} END, "
                f"{_COL_LAST_NACK_ATTEMPT} = NULL",  # nosec B608 — column names are module-level constants
                (consumer_id, event_id, now),
            )
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

    return (True, newly_acked, seq, False)


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
