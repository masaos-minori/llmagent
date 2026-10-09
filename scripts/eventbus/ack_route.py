#!/usr/bin/env python3
"""scripts/eventbus/ack_route.py — Ack/Nack endpoint handlers."""

import logging
import sqlite3
from typing import Any, Literal

from fastapi import HTTPException, Query, Request

from eventbus.auth import (
    Principal,
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

# Outcome of the locked NACK operation in nack(): routes 404 vs 409 subtypes.
NackOutcome = Literal["not_found", "already_acked", "in_dlq", "invalid", "ok"]


async def _do_ack(
    db: Any,
    cfg: Any,
    event_id: str,
    consumer_id: str,  # Required — no default (REQ-004)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: Principal | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Common ack logic shared by /ack and /events/{event_id}/ack."""
    logger.debug("DEBUG _do_ack: _principal=%r, _identity=%r", _principal, _identity)
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    # REQ-004: consumer_id is mandatory for consumer ACK
    if not consumer_id:
        raise HTTPException(
            status_code=400, detail="consumer_id is required for consumer ACK"
        )

    # REQ-002: Validate principal owns the consumer_id
    if (
        _principal
        and _principal.allowed_consumer_ids is not None
        and consumer_id not in _principal.allowed_consumer_ids
    ):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    def _ack_and_offset() -> tuple[bool, bool, int | None, bool]:
        """Acknowledge an event atomically (delivery + offset in one transaction).

        ack_event_for_consumer() requires a non-empty consumer_id (it tracks
        a per-consumer offset). The consumer-less ack_event() path has been
        removed — all consumer-scoped operations must be attributable. The 4th
        tuple element (dlq) is True when the event is in the DLQ; the caller
        must return 409 (REQ-005).
        """
        from eventbus.db import ack_event_for_consumer  # noqa: PLC0415

        now = now_iso()
        return ack_event_for_consumer(db, event_id, consumer_id, now)

    found, newly_acked, seq, dlq = await run_with_db_lock(_ack_and_offset)
    # An event already in the DLQ is dead — reject the ACK with 409 (REQ-005).
    if dlq:
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
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
    # Already-acked: still include seq for idempotent consumers that expect it
    try:
        row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT seq FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
        )
        if row is not None:
            resp["seq"] = int(row["seq"])
    except (sqlite3.Error, TypeError):
        pass
    logger.debug("event already acked event_id=%s", event_id)
    resp["already_acked"] = True
    return resp


async def ack_event(
    request: Request,
    event_id: str,
    consumer_id: str = Query(...),  # Required — no default (REQ-004)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: Principal | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Acknowledge an event as successfully processed by a consumer."""
    db = get_db(request)
    cfg = get_config(request)
    return await _do_ack(db, cfg, event_id, consumer_id, _principal=_principal)


async def nack(
    request: Request,
    event_id: str = Query(default=""),
    consumer_id: str = Query(...),  # Required — no default (REQ-007)
    _principal: Principal | None = None,  # set by app.py wrapper
    _identity: Principal | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Negatively acknowledge an event, triggering retry logic."""
    if not event_id:
        raise HTTPException(status_code=400, detail=ERR_EVENT_ID_REQUIRED)

    # REQ-007: consumer_id is mandatory for NACK
    if not consumer_id:
        raise HTTPException(status_code=400, detail="consumer_id is required for NACK")

    # REQ-008: Validate principal owns the consumer_id
    if (
        _principal
        and _principal.allowed_consumer_ids is not None
        and consumer_id not in _principal.allowed_consumer_ids
    ):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    db = get_db(request)
    cfg = get_config(request)

    def _nack_and_promote() -> tuple[NackOutcome, int, bool]:
        """Nack an event and resolve invalid-transition state under one lock.

        State determination ('already acknowledged' from
        consumer_delivery.acked_at, 'in DLQ' from events.dlq_at) runs inside
        the same lock acquisition as the NACK increment, so the snapshot is
        atomic with the increment (eliminates the delete-in-between race,
        EVENTBUS-011). The events.acked_at column was removed (REQ-004);
        per-consumer ACK state lives solely in consumer_delivery.

        DLQ promotion is gated on delivery_failure_count (the lifetime
        failure counter), not cycle_failure_count (which resets per
        requeue/redeliver cycle) — see
        tests/eventbus/test_eventbus_dlq_promotion.py for the intended
        semantics.
        """
        from eventbus.dlq import promote_single  # noqa: PLC0415

        nack_result = _nack_event(db, event_id, consumer_id)
        count = nack_result.delivery_failure_count
        if count == -1:
            return ("not_found", -1, False)
        if count == -2:
            # Per-consumer guard rejected this NACK (already acked) or the
            # event is DLQ'd; distinguish the subtype under the same lock.
            consumer_row = db.execute(
                "SELECT acked_at FROM consumer_delivery "
                "WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
            if consumer_row is not None and consumer_row["acked_at"] is not None:
                return ("already_acked", -2, False)
            event_row = db.execute(
                "SELECT dlq_at FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if event_row is not None and event_row["dlq_at"] is not None:
                return ("in_dlq", -2, False)
            return ("invalid", -2, False)
        promoted = False
        if count >= cfg.max_retry:
            promoted = promote_single(db, cfg.deadletter_dir, event_id)
        return ("ok", count, promoted)

    outcome, failure_count, promoted = await run_with_db_lock(_nack_and_promote)
    if outcome == "not_found":
        raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
    if outcome == "already_acked":
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    if outcome == "in_dlq":
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
    if outcome == "invalid":
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
