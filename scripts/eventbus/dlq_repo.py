"""DLQ repository: dead-letter queue operations."""

from __future__ import annotations

import logging
import sqlite3
import uuid

logger = logging.getLogger(__name__)

# Shared column constants
from eventbus._constants import (  # noqa: PLC0415 — deferred import avoids a circular import with eventbus._constants
    _COL_DLQ_AT,
    _COL_EVENT_ID,
)

# Layer-owned column constants
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"


def requeue_event(conn: sqlite3.Connection, event_id: str) -> bool:
    """Increment dlq_requeue_count and clear dlq_at. Returns True if the event was found in DLQ."""
    cur = conn.execute(
        f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1, {_COL_DLQ_AT} = NULL WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    )
    conn.commit()
    return cur.rowcount > 0


def redeliver_event(
    conn: sqlite3.Connection, event_id: str, now: str | None = None
) -> tuple[bool, str | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Uses a `redelivered_from`-existence check as a concurrency guard: if another
    request has already redelivered this event (i.e., a row exists with
    redelivered_from = event_id), return (False, None) to prevent duplicate
    redeliveries. This prevents the race condition where two concurrent requests
    could both see dlq_at IS NOT NULL and both insert new rows.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id):
      - (True, new_event_id)   = event found and redelivered
      - (False, None)          = event not found in DLQ or already redelivered
    """
    # Concurrency guard: check if this event has already been redelivered
    # by looking for an existing row with redelivered_from = event_id
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return (False, None)

    ts = now if now is not None else "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
    new_event_id = uuid.uuid4().hex
    cur = conn.execute(
        f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    )
    if cur.rowcount == 0:
        return (False, None)
    conn.execute(
        f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}, redelivered_from) "
        f"SELECT ?, topic, payload, producer, {ts}, {_COL_DELIVERY_FAILURE_COUNT}, 0, ? "
        f"FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (new_event_id, event_id, event_id),
    )
    conn.commit()
    return (True, new_event_id)
