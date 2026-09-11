#!/usr/bin/env python3
"""scripts/eventbus/ack_route.py — Ack/Nack endpoint handlers."""

import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Query, Request

from eventbus.auth import (
    require_consumer_identity,  # noqa: PLC0415 — new module, REQ-003
)
from eventbus.db import nack_event as _nack_event
from eventbus.json_utils import now_iso

# write_offset removed — replaced by ack_event_for_consumer() transactional path
from eventbus.route_helpers import (
    ERR_EVENT_ALREADY_ACKED,
    ERR_EVENT_ID_REQUIRED,
    ERR_EVENT_IN_DLQ,
    ERR_EVENT_NOT_FOUND,
    get_config,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def _do_ack(
    db: Any,
    cfg: Any,
    event_id: str,
    consumer_id: str = "",
) -> dict[str, Any]:
    """Common ack logic shared by /ack and /events/{event_id}/ack."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    def _ack_and_offset() -> tuple[bool, bool, int | None]:
        """Acknowledge an event atomically (delivery + offset in one transaction).

        ack_event_for_consumer() requires a non-empty consumer_id (it tracks
        a per-consumer offset); fall back to the plain, consumer-less
        ack_event() when the caller didn't supply one, matching this
        endpoint's own consumer_id: str = Query(default="") contract.
        """
        from eventbus.db import ack_event as _ack_event_plain  # noqa: PLC0415
        from eventbus.db import ack_event_for_consumer  # noqa: PLC0415

        now = now_iso()
        if consumer_id:
            found, newly_acked, seq = ack_event_for_consumer(
                db, event_id, consumer_id, now
            )
            return (found, newly_acked, seq)
        found, newly_acked = _ack_event_plain(db, event_id, now)
        return (found, newly_acked, None)

    found, newly_acked, seq = await run_with_db_lock(_ack_and_offset)
    # Check found first: ack_event_for_consumer()'s INSERT OR IGNORE into
    # consumer_delivery has no FK enforcement against events, so
    # newly_acked can be True even for a nonexistent event_id (found=False,
    # seq=None in that case) — found is the authoritative existence check.
    if not found:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    resp: dict[str, Any] = {"event_id": event_id, "acked": True}
    if newly_acked:
        logger.info("event acked event_id=%s", event_id)
        resp["seq"] = seq
        return resp
    logger.debug("event already acked event_id=%s", event_id)
    resp["already_acked"] = True
    return resp


async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(default=""),
    _identity: Annotated[dict, Depends(require_consumer_identity)] = {},  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id)


async def nack(
    request: Request,
    event_id: str = Query(default=""),
    _identity: Annotated[dict, Depends(require_consumer_identity)] = {},  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    db = get_db(request)
    cfg = get_config(request)

    def _nack_and_promote() -> tuple[int, bool]:
        """Nack an event and promote to DLQ if max retries exceeded.

        DLQ promotion is gated on delivery_failure_count (the lifetime
        failure counter), not cycle_failure_count (which resets per
        requeue/redeliver cycle) — see
        tests/eventbus/test_eventbus_dlq_promotion.py for the intended
        semantics.
        """
        failure_count, _cycle_count = _nack_event(db, event_id)
        if failure_count == -1:
            return (-1, False)
        promoted = False
        if failure_count >= cfg.max_retry:
            from eventbus.dlq import promote_single  # noqa: PLC0415

            promoted = promote_single(db, cfg.deadletter_dir, event_id)
        return (failure_count, promoted)

    failure_count, promoted = await run_with_db_lock(_nack_and_promote)
    if failure_count == -1:
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    if failure_count == -2:
        # Invalid transition: event is already ACKed or DLQ'd
        # Determine which state by checking the event directly
        row = await run_with_db_lock(lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone())
        if row and row["acked_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
        elif row and row["dlq_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
        else:
            raise HTTPException(status_code=409, detail="invalid NACK transition")
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
