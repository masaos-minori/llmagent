"""scripts/eventbus/dlq_repo.py — DLQ repository: dead-letter queue operations."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass
from typing import cast

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

    Redelivery uniqueness ("one descendant per original") is enforced by the
    database: the partial unique index idx_events_redelivered_from in
    schema.sql makes any second INSERT with the same redelivered_from fail.
    The `redelivered_from`-existence pre-check in front of the transaction is
    the fast classification path: a sequential re-request sees the existing
    descendant (redelivered_from = event_id) and returns status
    "already_redelivered" without touching the write path. A race that slips
    between the pre-check and the INSERT surfaces as an IntegrityError on the
    index and is mapped to the same "already_redelivered" status after a
    rollback, so callers cannot produce duplicate descendants either way.

    Performs a conditional-update guard on the original row
    (WHERE event_id = ? AND dlq_at IS NOT NULL), then inserts a new row with a
    fresh UUID v4 event_id, no event-level failure counters (the per-consumer
    model is authoritative), and redelivered_from set to the original event_id.
    The requeue timestamp is computed in Python (now_iso()) and bound as a SQL
    parameter. Update + insert + seq lookup run in one transaction: every failure
    path calls conn.rollback() so no partial state can be committed by a later
    request on the shared connection; an IntegrityError naming the
    events.redelivered_from index is rolled back and returned as
    "already_redelivered", every other sqlite3.Error is rolled back and re-raised.

    Returns a RequeueResult whose status classifies the outcome (the caller
    needs no follow-up SQL to distinguish 404 from 409).
    """
    # Fast classification path (the enforcement layer is the unique index
    # idx_events_redelivered_from): look for an existing row with
    # redelivered_from = event_id before opening the write transaction.
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
                f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
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
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        # Map only the redelivery-uniqueness violation (the message names the
        # violated index, e.g. "UNIQUE constraint failed: events.redelivered_from");
        # any other integrity error keeps the raise path so the existing
        # event_id-collision and injected-failure regression anchors hold.
        if "events.redelivered_from" in str(exc):
            return RequeueResult("already_redelivered", True, True, None, None)
        raise
    except sqlite3.Error:
        conn.rollback()
        raise
    return RequeueResult("success", True, False, new_event_id, new_seq)


# -- dlq_outbox row operations (dlqbox001) ------------------------------------
# None of these functions commit: the commit lives in the caller's transaction
# (the promotion transaction for the insert, a locked closure for the updates),
# mirroring redeliver_event's caller-managed transaction style.


def insert_outbox_row(db: sqlite3.Connection, event_id: str, requested_at: str) -> None:
    """Insert a pending dlq_outbox row inside the caller's promotion transaction.

    REQ-002: the dlq_at UPDATE and this INSERT share one transaction so a committed
    promotion always carries its durable generation request.
    """
    db.execute(
        "INSERT INTO dlq_outbox (event_id, requested_at, status, attempts)"
        " VALUES (?, ?, 'pending', 0)",
        (event_id, requested_at),
    )


def fetch_due_pending(db: sqlite3.Connection, now: str) -> list[sqlite3.Row]:
    """Return pending outbox rows due now, oldest request first.

    A row is due when next_attempt_at is NULL (never attempted) or <= now.
    REQ-004/REQ-005: the worker consumes exactly these rows each cycle. Whole rows
    are returned so the worker reads event_id and attempts without a second query.

    ``now`` is an ISO timestamp string; the name avoids shadowing the now_iso()
    helper imported by this module.
    """
    return db.execute(
        "SELECT event_id, requested_at, status, attempts, last_error,"
        " next_attempt_at, completed_at"
        " FROM dlq_outbox"
        " WHERE status = 'pending'"
        " AND (next_attempt_at IS NULL OR next_attempt_at <= ?)"
        " ORDER BY requested_at",
        (now,),
    ).fetchall()


def mark_done(db: sqlite3.Connection, event_id: str, completed_at: str) -> None:
    """Mark one outbox row done inside the caller's locked transaction.

    The status guard makes the write idempotent: only a pending row transitions,
    so a repeated completion cannot overwrite a terminal or unattempted state.
    """
    db.execute(
        "UPDATE dlq_outbox SET status = 'done', completed_at = ?"
        " WHERE event_id = ? AND status = 'pending'",
        (completed_at, event_id),
    )


def record_attempt_failure(
    db: sqlite3.Connection,
    event_id: str,
    last_error: str,
    next_attempt_at: str,
    terminal: bool,
) -> None:
    """Persist one failed generation attempt for an outbox row.

    increments attempts, stores last_error and the next due time; when terminal
    the row becomes 'failed' and is never fetched again. Commit lives in the
    caller's locked transaction.
    """
    status = "failed" if terminal else "pending"
    db.execute(
        "UPDATE dlq_outbox SET attempts = attempts + 1, last_error = ?,"
        " next_attempt_at = ?, status = ?"
        " WHERE event_id = ? AND status = 'pending'",
        (last_error, next_attempt_at, status, event_id),
    )


def get_outbox_state(db: sqlite3.Connection, event_id: str) -> sqlite3.Row | None:
    """Return the dlq_outbox row for one event, or None when absent."""
    row = db.execute(
        "SELECT event_id, requested_at, status, attempts, last_error,"
        " next_attempt_at, completed_at"
        " FROM dlq_outbox WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    return cast("sqlite3.Row | None", row)


def done_outbox_event_ids(db: sqlite3.Connection) -> set[str]:
    """Return event ids whose outbox row is done — the orphan classifier's set."""
    return {
        str(row[0])
        for row in db.execute("SELECT event_id FROM dlq_outbox WHERE status = 'done'")
    }
