#!/usr/bin/env python3
"""scripts/eventbus/dlq_route.py — Dead Letter Queue endpoint handlers."""

import logging
from typing import Any

from fastapi import HTTPException, Query, Request

from eventbus.auth import Role  # noqa: PLC0415 — new module, REQ-004
from eventbus.db import count_dlq, fetch_dlq, redeliver_event
from eventbus.route_helpers import (
    ERR_EVENT_NOT_FOUND,
    ERR_EVENT_NOT_IN_DLQ,
    get_config,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # type: ignore[assignment] — set by app.py wrapper
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
    _role: Role | None = None,  # type: ignore[assignment] — set by app.py wrapper
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue.

    Uses the lineage model: each requeue creates a new event row with
    redelivered_from pointing to the original event_id. The original row's
    dlq_at is intentionally left set so only one redeliver succeeds per
    original event.
    """
    db = get_db(request)
    cfg = get_config(request)

    def _redeliver() -> tuple[bool, str | None]:
        """Redeliver a single event from the dead letter queue using the lineage model."""
        success, new_event_id = redeliver_event(db, event_id)
        return (success, new_event_id)

    success, new_event_id = await run_with_db_lock(_redeliver)
    if success:
        logger.info("dlq redelivered event_id=%s -> %s", event_id, new_event_id)
        resp: dict[str, Any] = {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": new_event_id,
        }
        # Include new_seq by fetching the seq of the newly inserted row
        row = db.execute(
            "SELECT seq FROM events WHERE event_id = ?",
            (new_event_id,),
        ).fetchone()
        if row is not None:
            resp["new_seq"] = int(row[0])
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already redelivered or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
