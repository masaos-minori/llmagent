from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import orjson

logger = logging.getLogger(__name__)


def promote_to_dlq(
    db: sqlite3.Connection,
    deadletter_dir: str,
    max_retry: int,
) -> int:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, retry_count"
        " FROM events WHERE retry_count >= ? AND dlq_at IS NULL",
        (max_retry,),
    ).fetchall()

    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        record = {
            "seq": row["seq"],
            "event_id": event_id,
            "topic": row["topic"],
            "payload": orjson.loads(row["payload"]),
            "producer": row["producer"],
            "published_at": row["published_at"],
            "retry_count": row["retry_count"],
            "dlq_at": now,
        }
        _atomic_write(deadletter_dir, event_id, record)
        db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ?",
            (now, event_id),
        )
        db.commit()
        logger.warning(
            "dlq promoted event_id=%s retry_count=%d", event_id, row["retry_count"]
        )
        promoted += 1

    return promoted


def _atomic_write(deadletter_dir: str, event_id: str, record: dict) -> None:
    dir_path = Path(deadletter_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    dst = dir_path / f"{event_id}.json"
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, prefix=".dlq_tmp_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(orjson.dumps(record))
        os.replace(tmp_path, dst)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
