"""scripts/eventbus/db_conn.py — Connection layer: SQLite connection lifecycle, locking, pragma application."""

from __future__ import annotations

import logging
import sqlite3
import threading

logger = logging.getLogger(__name__)

_DEFAULT_BUSY_TIMEOUT_MS = 30_000

_db_lock = threading.Lock()

_shutting_down = False
_active_db_users = 0

# Import schema functions — open_db depends on them
from eventbus.schema import (  # noqa: PLC0415 — deferred import avoids a circular import with eventbus.schema
    _apply_eventbus_pragmas,
    _init_schema,
)


def get_db_lock() -> threading.Lock:
    """Return the lock that must be held for all DB operations.

    All asyncio.to_thread callables in app.py must acquire this lock before
    executing any sqlite3 operation on the shared connection.
    """
    return _db_lock


def set_shutdown_flag() -> None:
    """Mark shutdown as begun.

    Called by the shared cleanup helper (app.py) before closing the shared
    connection. Makes run_with_db_lock() refuse new work for any thread still queued
    on the lock (REQ-004). Idempotent.

    run_with_db_lock() refuses twice: before queueing, and again after a queued
    worker acquires the lock. Shutdown serializes behind any running worker by
    acquiring the same lock before it closes the connection.
    """
    global _shutting_down
    _shutting_down = True


def is_shutting_down() -> bool:
    """Return True once shutdown has begun."""
    return _shutting_down


def clear_shutdown_flag() -> None:
    """Reset the shutdown flag at the start of a fresh app lifecycle.

    Called by lifespan() startup so a restarted app (or a second TestClient
    context in tests) does not inherit a previous shutdown's flag.
    """
    global _shutting_down
    _shutting_down = False


def bump_active_db_user() -> None:
    """Increment the count of live DB users (called by run_with_db_lock()).

    The counter is observability only; shutdown does not consult it.
    """
    global _active_db_users
    _active_db_users += 1


def release_active_db_user() -> None:
    """Decrement the count of live DB users after the locked critical section.

    The counter is observability only; shutdown does not consult it.
    """
    global _active_db_users
    if _active_db_users > 0:
        _active_db_users -= 1


def open_db(db_path: str) -> sqlite3.Connection:
    """Return a shared SQLite connection for the Event Bus.

    Uses check_same_thread=False. Concurrent access from asyncio.to_thread()
    calls is serialized by the module-level _db_lock (retrieve via get_db_lock()).
    WAL mode additionally serializes concurrent writers at the SQLite level.
    A single shared connection avoids per-request connection churn.
    """
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _apply_eventbus_pragmas(conn)
        _init_schema(conn)
        return conn
    except sqlite3.Error as exc:
        logger.error(
            "eventbus: failed to open SQLite connection: path=%s err=%s", db_path, exc
        )
        raise


def check_db(conn: sqlite3.Connection) -> bool:
    """Return True if the DB connection is usable."""
    try:
        conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False
