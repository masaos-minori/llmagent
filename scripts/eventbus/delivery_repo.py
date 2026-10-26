"""scripts/eventbus/delivery_repo.py — Delivery repository: ack/nack semantics and per-consumer delivery state."""

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
    _COL_DLQ_AT,
    _COL_EVENT_ID,
)


@dataclass(frozen=True)
class NackResult:
    """Return value for nack_event().

    status: Literal["ok", "not_found", "invalid_state"] — "ok" when the NACK was
      recorded (or an idempotent repeat of the same attempt); "not_found" when the
      event does not exist; "invalid_state" when the event is already DLQ'd or
      already ACKed by this consumer.
    consumer_failure_count: int | None — per-consumer failure count when
      consumer_id was provided, None when consumer_id was not provided.
    """

    status: Literal["ok", "not_found", "invalid_state"]
    consumer_failure_count: int | None = None


def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str
    | None = None,  # internal-only: the /nack route always supplies consumer_id
    last_nack_attempt: str | None = None,  # REQ-001: idempotency key for NACK
) -> NackResult:
    """Record a per-consumer NACK failure for an event.

    When consumer_id is provided, the consumer's failure count is incremented and
    its last NACK attempt marker is stored. The per-consumer count is the only
    failure counter; the events table carries none.

    Nothing is recorded if the event is already DLQ'd (has dlq_at) or, when
    consumer_id is provided, if that consumer has already ACKed the event —
    attempting to do so would corrupt state.
    NACK is idempotent per delivery attempt: if the same consumer has already
    NACKed this event for the same attempt ID (last_nack_attempt matches), the
    count is not incremented again.

    Returns NackResult with:
      - status: "ok" when the NACK was recorded (or an idempotent repeat of the
        same attempt); "not_found" when the event does not exist;
        "invalid_state" when the event is already DLQ'd or already ACKed by this
        consumer.
      - consumer_failure_count: per-consumer count when consumer_id was provided,
        None otherwise.
    """
    try:
        # Check if event exists and is not DLQ'd
        existing = conn.execute(
            f"SELECT {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if not existing:
            return NackResult("not_found")
        if existing[_COL_DLQ_AT] is not None:
            return NackResult("invalid_state")

        if consumer_id is not None:
            # internal-only: the /nack route always supplies consumer_id
            # Per-consumer ACK guard: reject NACK if this consumer already ACKed
            acked = conn.execute(
                "SELECT 1 FROM consumer_delivery "
                "WHERE consumer_id = ? AND event_id = ? AND acked = 1",
                (consumer_id, event_id),
            ).fetchone()
            if acked:
                return NackResult("invalid_state")

            # NACK idempotency: skip if same consumer already NACKed this attempt
            last_attempt = conn.execute(
                f"SELECT {_COL_CONSUMER_LAST_NACK_ATTEMPT} FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
                f"WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
            if (
                last_attempt
                and last_attempt[_COL_CONSUMER_LAST_NACK_ATTEMPT] == last_nack_attempt
            ):
                # Idempotent: return current counts without incrementing
                consumer_row = conn.execute(
                    f"SELECT {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
                    f"WHERE consumer_id = ? AND event_id = ?",
                    (consumer_id, event_id),
                ).fetchone()
                if consumer_row:
                    return NackResult(
                        "ok",
                        consumer_failure_count=int(
                            consumer_row[_COL_CONSUMER_DELIVERY_FAILURE_COUNT]
                        ),
                    )
                return NackResult("not_found")

        # Per-consumer model: only the per-consumer failure counter is authoritative for
        # DLQ promotion (ADR-006 INV-13); there is no events-level failure counter under
        # this model.
        # Update consumer_delivery table if consumer_id is provided
        # internal-only: the /nack route always supplies consumer_id
        if consumer_id is not None:
            conn.execute(
                f"INSERT INTO consumer_delivery (consumer_id, event_id, {_COL_CONSUMER_DELIVERY_FAILURE_COUNT}, {_COL_CONSUMER_LAST_NACK_ATTEMPT}) "  # nosec B608 — column names are module-level constants, values parameterized
                f"VALUES (?, ?, 1, ?) "
                f"ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
                f"{_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1, "
                f"{_COL_CONSUMER_LAST_NACK_ATTEMPT} = excluded.{_COL_CONSUMER_LAST_NACK_ATTEMPT}",
                (consumer_id, event_id, last_nack_attempt),
            )

        conn.commit()

        # Read back the per-consumer count when a consumer was involved
        if consumer_id is not None:
            consumer_row = conn.execute(
                f"SELECT {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
                f"WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
            if consumer_row:
                return NackResult(
                    "ok",
                    consumer_failure_count=int(
                        consumer_row[_COL_CONSUMER_DELIVERY_FAILURE_COUNT]
                    ),
                )
        return NackResult("ok")
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
      - (True, False, None) = event found but already in the DLQ; nothing is
        written (the caller rejects the ACK)
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
            f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if not event_exists:
            return False, False, None

        # REQ-005: Reject ACK for DLQ events
        dlq_row = conn.execute(
            f"SELECT {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if dlq_row and dlq_row[_COL_DLQ_AT] is not None:
            return True, False, None

        # Check if the delivery record exists and its ACK status
        existing = conn.execute(
            "SELECT acked FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
        # Pending delivery (acked = 0) counts as newly_acked
        newly_acked = existing is None or existing["acked"] == 0

        # REQ-005: Mark the delivery acked. A pending (acked = 0) delivery becomes
        # acked on the first ACK; an already-acked row stays acked (idempotent).
        # MAX keeps the higher of the two so an ack never downgrades a prior ack.
        conn.execute(
            "INSERT INTO consumer_delivery "
            "(consumer_id, event_id, acked) VALUES (?, ?, 1) "
            "ON CONFLICT(consumer_id, event_id) DO UPDATE SET "
            "acked = MAX(consumer_delivery.acked, excluded.acked)",
            (consumer_id, event_id),
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
        "WHERE (cd.acked = 0 OR cd.event_id IS NULL) "
        "AND e.seq <= ?",
        (consumer_id, stored_offset),
    ).fetchone()

    if row and row[0]:
        # Unacked event found — deliver starting from the lowest unacked seq
        return int(row[0])
    else:
        # All events up to stored_offset are acked — fast-forward past them
        return stored_offset + 1
