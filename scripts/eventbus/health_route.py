#!/usr/bin/env python3
"""eventbus/health_route.py — Health check endpoint handler."""

import asyncio
import logging
from typing import TYPE_CHECKING

from eventbus.broker import EventBroker
from eventbus.db import check_db, get_db_lock
from fastapi import Request
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from eventbus.config import EventBusConfig

logger = logging.getLogger(__name__)


def _get_broker(request: Request) -> EventBroker:
    broker = request.app.state.broker
    assert broker is not None
    return broker  # type: ignore[no-any-return]


def _get_config(request: Request) -> "EventBusConfig":
    cfg = request.app.state.config
    assert cfg is not None
    return cfg  # type: ignore[no-any-return]


async def health_check(request: Request) -> JSONResponse:
    db = request.app.state.db
    assert db is not None
    broker = _get_broker(request)

    def _check() -> bool:
        with get_db_lock():
            return check_db(db)

    db_ok = await asyncio.to_thread(_check)
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
