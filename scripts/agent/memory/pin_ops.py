#!/usr/bin/env python3
"""scripts/agent/memory/pin_ops.py — Pin/unpin operations for memories."""

from __future__ import annotations

import sqlite3
import threading

from db.config import DbConfig
from db.helper import SQLiteHelper
from shared.json_utils import now_iso

from agent.memory.count_ops import count_pinned
from agent.memory.models import MemoryMaintenanceResult

_PIN_SQL = "UPDATE memories SET pinned=?, updated_at=? WHERE memory_id=?"


def _postcondition(db: SQLiteHelper, memory_id: str, value: int) -> bool:
    """Measure the committed pinned state for the row the run wrote."""
    rows = db.fetchall("SELECT pinned FROM memories WHERE memory_id=?", (memory_id,))
    return bool(rows) and int(rows[0][0]) == value


def _run(
    db: SQLiteHelper, memory_id: str, value: int, max_pinned: int | None, operation: str
) -> MemoryMaintenanceResult:
    """Pin or unpin inside one transaction on the caller's connection.

    The limit is evaluated on this connection inside the transaction, so it is checked
    against the state the transaction will commit rather than a count read earlier on a
    second connection (REQ-008). The change event is appended only after the commit, so
    an interrupted run emits nothing.
    """
    try:
        with db.begin_immediate():
            if max_pinned is not None and count_pinned(db) >= max_pinned:
                return MemoryMaintenanceResult(operation=operation, refused=True)
            cur = db.execute(_PIN_SQL, (value, now_iso(), memory_id))
            count = cur.rowcount
    except sqlite3.Error:
        # The transaction rolled back, so nothing changed and nothing is verified.
        return MemoryMaintenanceResult(operation=operation, interrupted=True)

    verified = count > 0 and _postcondition(db, memory_id, value)
    result = MemoryMaintenanceResult(
        operation=operation,
        count=count,
        verified=verified,
        ids=(memory_id,) if count else (),
    )
    if verified:
        _emit_event(operation, memory_id)
    return result


def pin(
    memory_id: str,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
    stop: threading.Event | None = None,
    max_pinned: int | None = None,
) -> MemoryMaintenanceResult:
    """Set pinned=1 for memory_id and return the measured outcome.

    `db` is the connection the `MemoryStore` accessor opened for the run; when it is not
    supplied this module opens its own. `max_pinned` is the limit the caller declares
    (`config/agent.toml` `memory_max_pinned`); a run that would exceed it is refused inside
    the transaction and changes nothing. A no-op of a missing id reports count 0 and emits
    nothing.
    """
    if db is not None:
        # The store owns the connection and the cancellation handler for the run.
        return _run(db, memory_id, 1, max_pinned, "pin")

    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        own.interrupt_when(stop)
        return _run(own, memory_id, 1, max_pinned, "pin")


def unpin(
    memory_id: str,
    *,
    db_config: DbConfig,
    db: SQLiteHelper | None = None,
    stop: threading.Event | None = None,
) -> MemoryMaintenanceResult:
    """Set pinned=0 for memory_id and return the measured outcome.

    The pin limit does not apply to a release, so the run is the same transaction shape as
    `pin()` with no limit.
    """
    if db is not None:
        db.interrupt_when(stop)
        return _run(db, memory_id, 0, None, "unpin")

    with SQLiteHelper("session", db_config=db_config).open(write_mode=True) as own:
        own.interrupt_when(stop)
        return _run(own, memory_id, 0, None, "unpin")


def _emit_event(event: str, memory_id: str) -> None:
    """Append a pin/unpin change event after the SQLite write (SQLite-first).

    The SQLite change stands even if the archive append fails; the error
    propagates so the caller can surface M-07. Mirrors ``write_ops._emit_delete_event``.
    """
    from agent.memory.jsonl_store import _emit_change_event

    _emit_change_event(event, memory_id)
