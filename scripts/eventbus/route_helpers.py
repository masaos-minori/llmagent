# /usr/bin/env python3
"""scripts/eventbus/route_helpers.py — Shared helpers for route handlers."""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, cast

from fastapi import Request
from prometheus_client import Counter, Histogram

if TYPE_CHECKING:
    from eventbus.broker import EventBroker  # noqa: F401

logger = logging.getLogger(__name__)

# -- Metrics ------------------------------------------------------------------

_db_lock_wait_time = Histogram(
    "eventbus_db_lock_wait_time_seconds",
    "Time spent waiting for database lock",
)
_db_query_duration = Histogram(
    "eventbus_db_query_duration_seconds",
    "Duration of database queries while holding lock",
)
_db_lock_contention = Counter(
    "eventbus_db_lock_contention_total",
    "Number of database lock contention events",
)

# -- Reusable error messages -------------------------------------------------

ERR_EVENT_NOT_FOUND = "event not found"
ERR_EVENT_ID_REQUIRED = "event_id is required"
ERR_EVENT_NOT_IN_DLQ = "event is not in DLQ"
ERR_EVENT_ALREADY_ACKED = "event already acknowledged"
ERR_EVENT_IN_DLQ = "event already in dead letter queue"
ERR_CONSUMER_ALREADY_CONNECTED = "consumer already connected"
ERR_EVENT_CONFLICT = "event already exists with different content"


def _require_state(app: Any, attr: str) -> Any:
    """Get an attribute from app.state or raise RuntimeError."""
    val = getattr(app.state, attr, None)
    if val is None:
        raise RuntimeError(f"{attr} not initialized")
    return val


# -- HTTP request helpers ----------------------------------------------------


def get_db(request: Request) -> Any:
    """Return the app state DB connection or raise RuntimeError."""
    return _require_state(request.app, "db")


def get_config(request: Request) -> Any:
    """Return the app state config or raise RuntimeError."""
    return _require_state(request.app, "config")


def get_broker(request: Request) -> "EventBroker":
    """Return the app state broker or raise RuntimeError."""
    return cast("EventBroker", _require_state(request.app, "broker"))


# -- Background-task helpers (no Request available) --------------------------


def app_get_db(app: Any) -> Any:
    """Return app.state.db or raise RuntimeError."""
    return _require_state(app, "db")


def app_get_config(app: Any) -> Any:
    """Return app.state.config or raise RuntimeError."""
    return _require_state(app, "config")


def app_get_broker(app: Any) -> "EventBroker":
    """Return app.state.broker or raise RuntimeError."""
    return cast("EventBroker", _require_state(app, "broker"))


# -- Common patterns ---------------------------------------------------------


async def run_with_db_lock(func: Any) -> Any:
    """Execute a function inside get_db_lock() via asyncio.to_thread."""
    from eventbus.db import get_db_lock  # noqa: PLC0415

    def _locked() -> Any:
        """Execute func while holding the DB lock."""
        start_time = time.monotonic()
        try:
            with get_db_lock():
                return func()
        finally:
            elapsed = time.monotonic() - start_time
            _db_query_duration.observe(elapsed)

    start_time = time.monotonic()
    result = await asyncio.to_thread(_locked)
    lock_wait = time.monotonic() - start_time
    _db_lock_wait_time.observe(lock_wait)
    if lock_wait > 0.001:
        _db_lock_contention.inc()
    return result


# -- Event row helpers -------------------------------------------------------


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a SQLite row proxy to a dictionary mapping column names to values."""
    import orjson  # noqa: PLC0415

    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": orjson.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }
