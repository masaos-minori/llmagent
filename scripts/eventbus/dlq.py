"""scripts/eventbus/dlq.py"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

import orjson

from eventbus._constants import _COL_CONSUMER_DELIVERY_FAILURE_COUNT
from eventbus.json_utils import now_iso

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DlqEventRecord:
    """A single event record written to the dead-letter queue as a JSON file on disk."""

    seq: int
    event_id: str
    topic: str
    payload: dict | list | str | int | float | bool
    producer: str
    published_at: str
    dlq_at: str
    consumer_delivery_failure_count: int | None = (
        None  # REQ-002: per-consumer failure count
    )


def _build_dlq_record(
    row: sqlite3.Row,
    now: str,
    consumer_delivery_failure_count: int | None = None,
) -> DlqEventRecord:
    """Construct a DlqEventRecord from a SQLite row and current timestamp."""
    return DlqEventRecord(
        seq=row["seq"],
        event_id=row["event_id"],
        topic=row["topic"],
        payload=orjson.loads(row["payload"]),
        producer=row["producer"],
        published_at=row["published_at"],
        dlq_at=now,
        consumer_delivery_failure_count=consumer_delivery_failure_count,
    )


# ADR-006 INV-13: an event is promotable only when every consumer that has a delivery
# record for it (created by that consumer's ACK or NACK) has exhausted its retry
# budget and none of them has ACKed. One parameter: the retry limit. Shared by the
# sweep query and is_promotable() so the two paths cannot drift apart.
_PROMOTABLE_CONDITION = (
    "EXISTS (SELECT 1 FROM consumer_delivery cd WHERE cd.event_id = e.event_id)"
    " AND NOT EXISTS (SELECT 1 FROM consumer_delivery cd"
    " WHERE cd.event_id = e.event_id"
    " AND (cd.acked = 1 OR cd.consumer_delivery_failure_count < ?))"
)


def is_promotable(db: sqlite3.Connection, event_id: str, max_retry: int) -> bool:
    """Return True if the event is not yet in the DLQ and meets the promotion rule.

    ADR-006 INV-13: every consumer with a delivery record for the event has reached
    ``max_retry`` and none has ACKed. An event with no delivery record is never
    promotable.
    """
    row = db.execute(
        "SELECT 1 FROM events e WHERE e.event_id = ? AND e.dlq_at IS NULL AND "  # nosec B608 — constant SQL fragment, values parameterized
        + _PROMOTABLE_CONDITION,
        (event_id, max_retry),
    ).fetchone()
    return row is not None


def _shared_promote(db: sqlite3.Connection, deadletter_dir: str, max_retry: int) -> int:
    """Shared promotion logic for the sweep path.

    REQ-002 and ADR-006 INV-13: promotes events where every consumer with a delivery
    record has reached the retry threshold and none has ACKed.
    """
    now = now_iso()
    rows = db.execute(
        "SELECT e.seq, e.event_id, e.topic, e.payload, e.producer, e.published_at"  # nosec B608 — constant SQL fragment, values parameterized
        " FROM events e"
        " WHERE e.dlq_at IS NULL AND " + _PROMOTABLE_CONDITION,
        (max_retry,),
    ).fetchall()

    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        # Get the per-consumer failure count for this event (max across consumers)
        consumer_row = db.execute(
            f"SELECT MAX({_COL_CONSUMER_DELIVERY_FAILURE_COUNT}) FROM consumer_delivery "  # nosec B608 — column names are module-level constants, values parameterized
            f"WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        consumer_failure_count = (
            int(consumer_row[0]) if consumer_row and consumer_row[0] else None
        )
        record = _build_dlq_record(row, now, consumer_failure_count)
        _atomic_write(deadletter_dir, event_id, record)
        cur = db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL",
            (now, event_id),
        )
        db.commit()
        if cur.rowcount:
            promoted += 1

    return promoted


def _shared_promote_single(
    db: sqlite3.Connection,
    deadletter_dir: str,
    event_id: str,
    consumer_failure_count: int | None = None,
) -> bool:
    """Shared promotion logic for single inline promotion.

    Args:
        db: Database connection.
        deadletter_dir: Directory for DLQ files.
        event_id: Event identifier.
        consumer_failure_count: Per-consumer failure count (REQ-002).
    """
    now = now_iso()
    row = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at"
        " FROM events WHERE event_id = ? AND dlq_at IS NULL",
        (event_id,),
    ).fetchone()
    if not row:
        return False

    record = _build_dlq_record(row, now, consumer_failure_count)
    _atomic_write(deadletter_dir, event_id, record)
    cur = db.execute(
        "UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL",
        (now, event_id),
    )
    db.commit()
    if cur.rowcount:
        logger.warning(
            "dlq inline promoted event_id=%s consumer_delivery_failure_count=%s",
            event_id,
            consumer_failure_count,
        )
    return cur.rowcount > 0


def sweep_orphans(
    db: sqlite3.Connection,
    deadletter_dir: str,
    max_retry: int,
) -> int:
    """Sweep events that meet the promotion rule but were not promoted inline.

    This is a safety-net sweep only. Under normal operation (inline promotion via
    the nack endpoint working correctly), this returns 0.
    Non-zero return value indicates a bug in the inline promotion path.
    """
    return _shared_promote(db, deadletter_dir, max_retry)


def promote_single(
    db: sqlite3.Connection,
    deadletter_dir: str,
    event_id: str,
    consumer_failure_count: int | None = None,
) -> bool:
    """Promote one event to DLQ immediately (inline on nack threshold).

    Returns True if promoted, False if already in DLQ or not found.
    Write the JSON file before updating the DB row to preserve consistency:
    if _atomic_write fails, the DB row is not updated and the event remains live.

    Args:
        db: Database connection.
        deadletter_dir: Directory for DLQ files.
        event_id: Event identifier.
        consumer_failure_count: Per-consumer failure count (REQ-002).
    """
    return _shared_promote_single(db, deadletter_dir, event_id, consumer_failure_count)


def _atomic_write(deadletter_dir: str, event_id: str, record: DlqEventRecord) -> None:
    """Atomically write a dead-letter queue event record to disk via temp file + rename."""
    dir_path = Path(deadletter_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    dst = dir_path / f"{event_id}.json"
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, prefix=".dlq_tmp_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(orjson.dumps(record))
        os.replace(tmp_path, dst)
    except (OSError, TypeError):
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def archive_dlq_record(deadletter_dir: str, event_id: str) -> bool:
    """Move {deadletter_dir}/{event_id}.json to {deadletter_dir}/requeued/{event_id}_{timestamp}.json.

    Creates the requeued/ subdirectory if it doesn't exist. Uses os.replace() for atomic move.
    Returns True if the file was moved, False if the source file didn't exist.
    """
    src_dir = Path(deadletter_dir)
    src_file = src_dir / f"{event_id}.json"
    if not src_file.exists():
        return False

    requeued_dir = src_dir / "requeued"
    requeued_dir.mkdir(parents=True, exist_ok=True)

    timestamp = now_iso().replace(":", "-").replace(".", "-")
    dst_file = requeued_dir / f"{event_id}_{timestamp}.json"

    try:
        os.replace(str(src_file), str(dst_file))
        return True
    except OSError:
        return False
