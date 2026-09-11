#!/usr/bin/env python3
"""scripts/eventbus/health_route.py — Health check endpoint handler."""

import logging
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from eventbus.db import check_db
from eventbus.route_helpers import (
    _db_lock_contention,
    _db_lock_wait_time,
    _db_query_duration,
    get_broker,
    get_config,
    get_db,
    run_with_db_lock,
)

logger = logging.getLogger(__name__)


async def health_check(request: Request) -> JSONResponse:
    """Return DB/broker/DLQ task health status as a JSON response."""
    db = get_db(request)
    broker = get_broker(request)
    config = get_config(request)

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
    overflow_disconnects = 0
    duplicate_connection_rejections = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()
        overflow_disconnects = broker.overflow_disconnect_count()
        duplicate_connection_rejections = broker.duplicate_rejection_count()

    degraded_reasons: list[str] = []
    if db_status != "ok":
        degraded_reasons.append("db_unavailable")
    if dlq_task_status != "running":
        degraded_reasons.append("dlq_task_stopped")
    if max_queue_depth >= broker.backlog_health_threshold:
        degraded_reasons.append("broker_queue_backlog_high")
    if slow_consumers > 0:
        degraded_reasons.append("slow_consumers_detected")

    # Database-lock contention metrics
    def _hist_avg(hist: Any) -> float:
        """Return average observation for a Histogram, or 0.0 if no observations."""
        try:
            samples = hist._samples()
            s_sum = 0.0
            s_count = 0
            for s in samples:
                if s.name == "_sum":
                    s_sum = s.value
                elif s.name == "_count":
                    s_count = int(s.value)
            return s_sum / s_count if s_count > 0 else 0.0
        except (AttributeError, TypeError, ZeroDivisionError):
            return 0.0

    lock_wait_avg = _hist_avg(_db_lock_wait_time)
    query_dur_avg = _hist_avg(_db_query_duration)
    lock_contention_total = _db_lock_contention._value.get()

    # Capacity limit checks
    capacity_degraded_reasons: list[str] = []
    if active_subscribers >= config.subscriber_count:
        capacity_degraded_reasons.append("subscribers_at_capacity")
    if lock_wait_avg > 0.01:
        capacity_degraded_reasons.append("lock_wait_high")
    if query_dur_avg > 0.05:
        capacity_degraded_reasons.append("query_duration_high")

    degraded_reasons.extend(capacity_degraded_reasons)

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
            "overflow_disconnects": overflow_disconnects,
            "duplicate_connection_rejections": duplicate_connection_rejections,
            "degraded_reasons": degraded_reasons,
            "metrics": {
                "lock_wait_avg_seconds": round(lock_wait_avg, 6),
                "query_duration_avg_seconds": round(query_dur_avg, 6),
                "lock_contention_total": int(lock_contention_total),
            },
        },
        status_code=status_code,
    )
