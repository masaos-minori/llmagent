from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

import orjson
from shared.json_utils import now_iso

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DdqEventRecord:
    seq: int
    event_id: str
    topic: str
    payload: object
    producer: str
    published_at: str
    delivery_failure_count: int
    dlq_at: str


def _build_dlq_record(row: sqlite3.Row, now: str) -> DdqEventRecord:
    return DdqEventRecord(
        seq=row["seq"],
        event_id=row["event_id"],
        topic=row["topic"],
        payload=orjson.loads(row["payload"]),
        producer=row["producer"],
        published_at=row["published_at"],
        delivery_failure_count=row["delivery_failure_count"],
        dlq_at=now,
    )


def promote_to_dlq(
    db: sqlite3.Connection,
    deadletter_dir: str,
    max_retry: int,
) -> int:
    now = now_iso()
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, delivery_failure_count"
        " FROM events WHERE delivery_failure_count >= ? AND dlq_at IS NULL",
        (max_retry,),
    ).fetchall()

    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        record = _build_dlq_record(row, now)
        _atomic_write(deadletter_dir, event_id, record)
        db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ?",
            (now, event_id),
        )
        db.commit()
        logger.warning(
            "dlq promoted event_id=%s delivery_failure_count=%d",
            event_id,
            row["delivery_failure_count"],
        )
        promoted += 1

    return promoted


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
    now = now_iso()
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, delivery_failure_count"
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
    now = now_iso()
    row = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, delivery_failure_count"
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


def _atomic_write(deadletter_dir: str, event_id: str, record: DdqEventRecord) -> None:
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
