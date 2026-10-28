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


def get_histogram_avg(hist: Histogram) -> float:
    """Return the average observation for a Histogram via the public API.

    Returns 0.0 if the histogram has no observations or if the API is unavailable.
    """
    try:
        metrics = list(hist.collect())
        if not metrics:
            return 0.0
        total_sum = 0.0
        total_count = 0
        for metric in metrics:
            for sample in metric.samples:
                if sample.name.endswith("_sum"):
                    total_sum += sample.value
                elif sample.name.endswith("_count"):
                    total_count += int(sample.value)
        return total_sum / total_count if total_count > 0 else 0.0
    except (AttributeError, TypeError, ZeroDivisionError, ValueError):
        return 0.0


def get_counter_value(counter: Counter) -> int:
    """Return the current value of a Counter via the public API.

    Returns 0 if the counter has no value or if the API is unavailable.
    """
    try:
        metrics = list(counter.collect())
        if not metrics:
            return 0
        for metric in metrics:
            for sample in metric.samples:
                if sample.name == counter._name + "_total":
                    return int(sample.value)
        return 0
    except (AttributeError, TypeError, ValueError):
        return 0


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
    from eventbus.db_conn import (  # noqa: PLC0415
        bump_active_db_user,
        is_shutting_down,
        release_active_db_user,
    )

    def _locked() -> Any:
        """Execute func while holding the DB lock.

        Lock wait is the time from submit to acquisition; query duration is the time
        func runs while the lock is held, recorded even when func raises.
        """
        start_time = time.monotonic()
        with get_db_lock():
            acquired = time.monotonic()
            lock_wait = acquired - start_time
            _db_lock_wait_time.observe(lock_wait)
            if lock_wait > 0.001:
                _db_lock_contention.inc()
            # A worker admitted before shutdown can reach the lock after the
            # connection was closed; refuse before it touches SQL or the counter.
            if is_shutting_down():
                raise RuntimeError("eventbus shutting down: refusing new DB work")
            bump_active_db_user()
            try:
                return func()
            finally:
                release_active_db_user()
                _db_query_duration.observe(time.monotonic() - acquired)

    # REQ-004 fail-fast: refuse new work once shutdown has begun so a thread
    # queued on the lock never runs SQL against the closed connection.
    if is_shutting_down():
        raise RuntimeError("eventbus shutting down: refusing new DB work")

    total_start = time.monotonic()
    result = await asyncio.to_thread(_locked)
    total_elapsed = time.monotonic() - total_start
    logger.debug("run_with_db_lock total=%.4fs", total_elapsed)
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
