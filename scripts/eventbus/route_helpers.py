#!/usr/bin/env python3
"""eventbus/route_helpers.py — Shared helpers for route handlers."""

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import Request

if TYPE_CHECKING:
    from eventbus.broker import EventBroker  # noqa: F401

# -- Reusable error messages -------------------------------------------------

ERR_EVENT_NOT_FOUND = "event not found"
ERR_EVENT_ID_REQUIRED = "event_id is required"
ERR_EVENT_NOT_IN_DLQ = "event is not in DLQ"


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
    return _require_state(request.app, "broker")


# -- Background-task helpers (no Request available) --------------------------


def app_get_db(app: Any) -> Any:
    """Return app.state.db or raise RuntimeError."""
    return _require_state(app, "db")


def app_get_config(app: Any) -> Any:
    """Return app.state.config or raise RuntimeError."""
    return _require_state(app, "config")


def app_get_broker(app: Any) -> "EventBroker":
    """Return app.state.broker or raise RuntimeError."""
    return _require_state(app, "broker")


# -- Common patterns ---------------------------------------------------------


async def run_with_db_lock(func: Any) -> Any:
    """Execute a function inside get_db_lock() via asyncio.to_thread."""
    from eventbus.db import get_db_lock  # noqa: PLC0415

    def _locked() -> Any:
        with get_db_lock():
            return func()

    return await asyncio.to_thread(_locked)


# -- Event row helpers -------------------------------------------------------


def _row_to_dict(row: Any) -> dict[str, Any]:
    import orjson  # noqa: PLC0415

    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "topic": row["topic"],
        "payload": orjson.loads(row["payload"]),
        "producer": row["producer"],
        "published_at": row["published_at"],
    }
