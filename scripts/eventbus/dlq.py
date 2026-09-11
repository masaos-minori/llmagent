"""scripts/eventbus/dlq.py"""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

import orjson

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
    delivery_failure_count: int
    dlq_at: str


def _build_dlq_record(row: sqlite3.Row, now: str) -> DlqEventRecord:
    """Construct a DlqEventRecord from a SQLite row and current timestamp."""
    return DlqEventRecord(
        seq=row["seq"],
        event_id=row["event_id"],
        topic=row["topic"],
        payload=orjson.loads(row["payload"]),
        producer=row["producer"],
        published_at=row["published_at"],
        delivery_failure_count=row["delivery_failure_count"],
        dlq_at=now,
    )


def _shared_promote(db: sqlite3.Connection, deadletter_dir: str, max_retry: int) -> int:
    """Shared promotion logic for sweep and inline paths."""
    now = now_iso()
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at,"
        " delivery_failure_count, cycle_failure_count"
        " FROM events WHERE delivery_failure_count >= ? AND dlq_at IS NULL",
        (max_retry,),
    ).fetchall()

    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        record = _build_dlq_record(row, now)
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
    db: sqlite3.Connection, deadletter_dir: str, event_id: str
) -> bool:
    """Shared promotion logic for single inline promotion."""
    now = now_iso()
    row = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at,"
        " delivery_failure_count, cycle_failure_count"
        " FROM events WHERE event_id = ? AND dlq_at IS NULL",
        (event_id,),
    ).fetchone()
    if not row:
        return False

    record = _build_dlq_record(row, now)
    _atomic_write(deadletter_dir, event_id, record)
    cur = db.execute(
        "UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL",
        (now, event_id),
    )
    db.commit()
    if cur.rowcount:
        logger.warning(
            "dlq inline promoted event_id=%s delivery_failure_count=%d",
            event_id,
            row["delivery_failure_count"],
        )
    return cur.rowcount > 0


def sweep_orphans(
    db: sqlite3.Connection,
    deadletter_dir: str,
    max_retry: int,
) -> int:
    """Sweep events that reached retry limit but were not promoted inline.

    This is a safety-net sweep only. Under normal operation (inline promotion via
    the nack endpoint working correctly), this returns 0.
    Non-zero return value indicates a bug in the inline promotion path.
    """
    return _shared_promote(db, deadletter_dir, max_retry)


def promote_single(
    db: sqlite3.Connection,
    deadletter_dir: str,
    event_id: str,
) -> bool:
    """Promote one event to DLQ immediately (inline on nack threshold).

    Returns True if promoted, False if already in DLQ or not found.
    Write the JSON file before updating the DB row to preserve consistency:
    if _atomic_write fails, the DB row is not updated and the event remains live.
    """
    return _shared_promote_single(db, deadletter_dir, event_id)


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
