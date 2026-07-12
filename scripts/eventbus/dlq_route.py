#!/usr/bin/env python3
"""eventbus/dlq_route.py — Dead Letter Queue endpoint handlers."""

import asyncio
import logging
from typing import Any

from eventbus.db import count_dlq, fetch_dlq, get_db_lock, requeue_event
from eventbus.route_helpers import get_config, get_db
from fastapi import HTTPException, Query, Request

logger = logging.getLogger(__name__)


async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    db = get_db(request)

    def _dlq_count() -> int:
        with get_db_lock():
            count: int = count_dlq(db)
            return count

    def _dlq_fetch() -> list:
        with get_db_lock():
            rows: list = fetch_dlq(db, limit=limit, offset=offset)
            return rows

    total = await asyncio.to_thread(_dlq_count)
    rows = await asyncio.to_thread(_dlq_fetch)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in rows],
    }


async def dlq_requeue(request: Request, event_id: str) -> dict[str, Any]:
    db = get_db(request)
    cfg = get_config(request)

    def _requeue() -> tuple[bool, int | None]:
        with get_db_lock():
            found = requeue_event(db, event_id)
            if not found:
                return False, None
            row = db.execute(
                "SELECT delivery_failure_count FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            return True, int(row[0]) if row else None

    requeued, failure_count = await asyncio.to_thread(_requeue)
    if requeued:
        logger.info("dlq requeued event_id=%s", event_id)
        resp: dict[str, Any] = {"event_id": event_id, "requeued": True}
        if failure_count is not None and failure_count >= cfg.max_retry:
            resp["dlq_imminent"] = True
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already requeued or acked
    row = await asyncio.to_thread(
        lambda: db.execute(
            "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    )
    if row is not None:
        raise HTTPException(status_code=409, detail="event is not in DLQ")
    raise HTTPException(status_code=404, detail="event not found")
