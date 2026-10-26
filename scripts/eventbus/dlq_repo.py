"""scripts/eventbus/dlq_repo.py — DLQ repository: dead-letter queue operations."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Shared column constants
from eventbus._constants import (  # noqa: PLC0415 — deferred import avoids a circular import with eventbus._constants
    _COL_DLQ_AT,
    _COL_DLQ_REQUEUE_COUNT,
    _COL_EVENT_ID,
)
from eventbus.event_repo import get_seq
from eventbus.json_utils import now_iso


@dataclass
class RequeueResult:
    """Typed result of a redeliver_event() call (replaces the (bool, str | None) tuple).

    ``status`` is one of the four string values owned by this module:
      - "success": the descendant row was inserted and committed in one transaction.
      - "not_found": no row exists with this event_id.
      - "not_in_dlq": the row exists but dlq_at IS NULL.
      - "already_redelivered": a descendant row with redelivered_from = event_id exists.

    On success, ``new_event_id`` and ``new_seq`` come from the same atomic result;
    otherwise both are None.
    """

    status: str
    original_event_exists: bool
    already_redelivered: bool
    new_event_id: str | None
    new_seq: int | None


def redeliver_event(
    conn: sqlite3.Connection, event_id: str, now: str | None = None
) -> RequeueResult:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Uses a `redelivered_from`-existence check as a concurrency guard: if another
    request has already redelivered this event (i.e., a row exists with
    redelivered_from = event_id), return status "already_redelivered" to prevent
    duplicate redeliveries. This prevents the race condition where two concurrent
    requests could both see dlq_at IS NOT NULL and both insert new rows.

    Performs a conditional-update guard on the original row
    (WHERE event_id = ? AND dlq_at IS NOT NULL), then inserts a new row with a
    fresh UUID v4 event_id, no event-level failure counters (the per-consumer
    model is authoritative), and redelivered_from set to the original event_id.
    The requeue timestamp is computed in Python (now_iso()) and bound as a SQL
    parameter. Update + insert + seq lookup run in one transaction: every failure
    path calls conn.rollback() so no partial state can be committed by a later
    request on the shared connection; sqlite3.Error is rolled back and re-raised.

    Returns a RequeueResult whose status classifies the outcome (the caller
    needs no follow-up SQL to distinguish 404 from 409).
    """
    # Concurrency guard: check if this event has already been redelivered
    # by looking for an existing row with redelivered_from = event_id
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return RequeueResult("already_redelivered", True, True, None, None)

    # Timestamp computed in Python and bound as data (no f-string interpolation).
    ts = now if now is not None else now_iso()
    new_event_id = uuid.uuid4().hex
    try:
        cur = conn.execute(
            f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        )
        if cur.rowcount == 0:
            conn.rollback()
            # Single existence read classifies the no-match UPDATE: the row
            # exists but dlq_at IS NULL ("not_in_dlq"), or it never existed
            # ("not_found").
            row = conn.execute(
                f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?",
                (event_id,),
            ).fetchone()
            if row is not None:
                return RequeueResult("not_in_dlq", True, False, None, None)
            return RequeueResult("not_found", False, False, None, None)
        conn.execute(
            f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, redelivered_from) "
            f"SELECT ?, topic, payload, producer, ?, ? "
            f"FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (new_event_id, ts, event_id, event_id),
        )
        new_seq = get_seq(conn, new_event_id)
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return RequeueResult("success", True, False, new_event_id, new_seq)
