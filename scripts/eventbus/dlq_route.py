#!/usr/bin/env python3
"""scripts/eventbus/dlq_route.py — Dead Letter Queue endpoint handlers."""

import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Query, Request

from eventbus.auth import require_role, Role  # noqa: PLC0415 — new module, REQ-004
from eventbus.db import count_dlq, fetch_dlq, redeliver_event
from eventbus.route_helpers import (
    ERR_EVENT_NOT_FOUND,
    ERR_EVENT_NOT_IN_DLQ,
    get_broker,
    get_config,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support."""
    db = get_db(request)

    def _dlq_count() -> int:
        """Count total events in the dead letter queue."""
        count: int = count_dlq(db)
        return count

    def _dlq_fetch() -> list:
        """Fetch paginated events from the dead letter queue."""
        rows: list = fetch_dlq(db, limit=limit, offset=offset)
        return rows

    total = await run_with_db_lock(_dlq_count)
    rows = await run_with_db_lock(_dlq_fetch)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [dict(r) for r in rows],
    }


async def dlq_requeue(
    request: Request,
    event_id: str,
    _operator: Annotated[None, Depends(require_role(Role.OPERATOR))] = None,  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue."""
    db = get_db(request)
    cfg = get_config(request)

    def _requeue() -> tuple[bool, str | None, int | None]:
        """Redeliver a single event from the dead letter queue and return its new_event_id and seq."""
        success, new_event_id = redeliver_event(db, event_id)
        if not success:
            return False, None, None
        row = db.execute(
            "SELECT seq FROM events WHERE event_id = ?",
            (new_event_id,),
        ).fetchone()
        return True, new_event_id, int(row[0]) if row else None

    requeued, new_event_id, new_seq = await run_with_db_lock(_requeue)
    if requeued:
        logger.info("dlq redelivered event_id=%s new_event_id=%s new_seq=%d", event_id, new_event_id, new_seq)
        resp: dict[str, Any] = {"event_id": event_id, "requeued": True, "new_event_id": new_event_id, "new_seq": new_seq}
        if new_event_id is not None and new_seq is not None:
            try:
                from eventbus.broker import EventBroker  # noqa: PLC0415
                broker = get_broker(request)
                new_row = db.execute(
                    "SELECT topic, payload, producer, published_at FROM events WHERE event_id = ?",
                    (new_event_id,),
                ).fetchone()
                if new_row:
                    broker.publish({
                        "event_id": new_event_id,
                        "topic": new_row["topic"],
                        "payload": new_row["payload"],
                        "producer": new_row["producer"],
                        "published_at": new_row["published_at"],
                    })
            except Exception as exc:
                logger.warning("failed to publish redelivered event: %s", exc)
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already requeued or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
