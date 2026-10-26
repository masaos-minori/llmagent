#!/usr/bin/env python3
"""scripts/eventbus/dlq_route.py — Dead Letter Queue endpoint handlers."""

import logging
from typing import Any

from fastapi import HTTPException, Query, Request

from eventbus.audit import log_privileged_action
from eventbus.db import count_dlq, fetch_dlq, redeliver_event
from eventbus.dlq_repo import RequeueResult
from eventbus.route_helpers import (
    ERR_EVENT_NOT_FOUND,
    ERR_EVENT_NOT_IN_DLQ,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List dead-letter queue entries with pagination support (one snapshot)."""
    db = get_db(request)

    def _snapshot() -> dict[str, Any]:
        """Count and fetch under one lock acquisition so total/items match."""
        total: int = count_dlq(db)
        rows: list = fetch_dlq(db, limit=limit, offset=offset)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [dict(r) for r in rows],
        }

    snapshot: dict[str, Any] = await run_with_db_lock(_snapshot)
    return snapshot


async def dlq_requeue(
    request: Request,
    event_id: str,
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue.

    Uses the lineage model: each requeue creates a new event row with
    redelivered_from pointing to the original event_id. The original row's
    dlq_at is intentionally left set so only one redeliver succeeds per
    original event.

    The 200/404/409 mapping comes from the typed RequeueResult produced inside
    the locked repository operation; the route performs no follow-up SQL.
    """
    db = get_db(request)

    def _redeliver() -> RequeueResult:
        """Redeliver a single event from the dead letter queue using the lineage model."""
        return redeliver_event(db, event_id)

    result = await run_with_db_lock(_redeliver)
    if result.status == "success":
        logger.info("dlq redelivered event_id=%s -> %s", event_id, result.new_event_id)

        # Emit privileged-action audit record
        log_privileged_action(
            consumer_id="",
            request_id=request.state.request_id,
            route="/dlq/requeue",
            target=event_id,
            detail="",
        )

        return {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": result.new_event_id,
            "new_seq": result.new_seq,
            "delivery": "replay",
        }
    if result.status == "not_found":
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
