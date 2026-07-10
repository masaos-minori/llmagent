#!/usr/bin/env python3
"""eventbus/ack_route.py — Ack/Nack endpoint handlers."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from eventbus.db import ack_event as _ack_event
from eventbus.db import get_db_lock
from eventbus.db import nack_event as _nack_event
from eventbus.offsets import write_offset
from fastapi import HTTPException, Query, Request

logger = logging.getLogger(__name__)


async def _do_ack(
    db: Any,
    cfg: Any,
    event_id: str,
    consumer_id: str = "",
) -> dict[str, Any]:
    """Common ack logic shared by /ack and /events/{event_id}/ack."""
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    def _ack_and_offset() -> tuple[bool, bool, int | None]:
        with get_db_lock():
            now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            found, newly_acked = _ack_event(db, event_id, now)
            seq: int | None = None
            if consumer_id and newly_acked:
                row = db.execute(
                    "SELECT seq FROM events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if row:
                    seq = int(row["seq"])
                    write_offset(cfg.offsets_dir, consumer_id, seq)
            return (found, newly_acked, seq)

    found, newly_acked, seq = await asyncio.to_thread(_ack_and_offset)
    resp: dict[str, Any] = {"event_id": event_id, "acked": True}
    if newly_acked:
        logger.info("event acked event_id=%s", event_id)
        resp["seq"] = seq
        return resp
    if found:
        logger.debug("event already acked event_id=%s", event_id)
        resp["already_acked"] = True
        return resp
    raise HTTPException(status_code=404, detail="event not found")


async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
) -> dict[str, Any]:
    db = request.app.state.db
    assert db is not None
    cfg = request.app.state.config
    assert cfg is not None
    return await _do_ack(db, cfg, event_id, consumer_id)


async def nack(
    request: Request,
    event_id: str = Query(default=""),
) -> dict[str, Any]:
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    db = request.app.state.db
    assert db is not None
    cfg = request.app.state.config
    assert cfg is not None

    def _nack_and_promote() -> tuple[int, bool]:
        with get_db_lock():
            failure_count = _nack_event(db, event_id)
            if failure_count == -1:
                return (-1, False)
            promoted = False
            if failure_count >= cfg.max_retry:
                from eventbus.dlq import promote_single  # noqa: PLC0415

                promoted = promote_single(db, cfg.deadletter_dir, event_id)
            return (failure_count, promoted)

    failure_count, promoted = await asyncio.to_thread(_nack_and_promote)
    if failure_count == -1:
        raise HTTPException(status_code=404, detail="event not found")
    logger.info(
        "event nacked event_id=%s delivery_failure_count=%d", event_id, failure_count
    )
    result: dict[str, Any] = {
        "event_id": event_id,
        "delivery_failure_count": failure_count,
    }
    if promoted:
        result["dlq_promoted"] = True
    return result
