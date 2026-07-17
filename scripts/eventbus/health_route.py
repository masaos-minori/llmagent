#!/usr/bin/env python3
"""eventbus/health_route.py — Health check endpoint handler."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from eventbus.db import check_db
from eventbus.route_helpers import get_broker, get_db, run_with_db_lock

logger = logging.getLogger(__name__)


async def health_check(request: Request) -> JSONResponse:
    db = get_db(request)
    broker = get_broker(request)

    def _check() -> bool:
        """Check database connectivity and return whether it's available."""
        ok: bool = check_db(db)
        return ok

    db_ok = await run_with_db_lock(_check)
    db_status = "ok" if db_ok else "unavailable"

    dlq_task_status = (
        "running"
        if (
            request.app.state.dlq_task is not None
            and not request.app.state.dlq_task.done()
        )
        else "stopped"
    )

    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()

    degraded_reasons: list[str] = []
    if db_status != "ok":
        degraded_reasons.append("db_unavailable")
    if dlq_task_status != "running":
        degraded_reasons.append("dlq_task_stopped")
    if max_queue_depth >= 500:
        degraded_reasons.append("broker_queue_backlog_high")
    if slow_consumers > 0:
        degraded_reasons.append("slow_consumers_detected")

    overall = "ok" if not degraded_reasons else "degraded"
    status_code = 200 if overall == "ok" else 503
    return JSONResponse(
        content={
            "status": overall,
            "db": db_status,
            "dlq_task": dlq_task_status,
            "active_subscribers": active_subscribers,
            "max_queue_depth": max_queue_depth,
            "slow_consumers": slow_consumers,
            "degraded_reasons": degraded_reasons,
        },
        status_code=status_code,
    )
