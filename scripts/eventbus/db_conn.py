"""Connection layer: SQLite connection lifecycle, locking, pragma application."""

from __future__ import annotations

import logging
import sqlite3
import threading

logger = logging.getLogger(__name__)

_DEFAULT_BUSY_TIMEOUT_MS = 30_000

_db_lock = threading.Lock()

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
