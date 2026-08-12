#!/usr/bin/env python3
"""scripts/agent/memory/pin_ops.py — Pin/unpin operations for memories."""

from __future__ import annotations

import sqlite3

from shared.json_utils import now_iso


def _set_pinned(
    memory_id: str, value: int, conn: sqlite3.Connection | None = None
) -> bool:
    """Set memories.pinned=value for memory_id; return True when found."""
    if conn is not None:
        cur = conn.execute(
            "UPDATE memories SET pinned=?, updated_at=? WHERE memory_id=?",
            (value, now_iso(), memory_id),
        )
        conn.commit()
        return cur.rowcount > 0

    from db.helper import SQLiteHelper

    with SQLiteHelper("session").open(write_mode=True) as db:
        cur = db.execute(
            "UPDATE memories SET pinned=?, updated_at=? WHERE memory_id=?",
            (value, now_iso(), memory_id),
        )
        db.commit()
    return cur.rowcount > 0


def pin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
    """Set pinned=1 for memory_id; return True when found."""
    return _set_pinned(memory_id, 1, conn)


def unpin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
    """Set pinned=0 for memory_id; return True when found."""
    return _set_pinned(memory_id, 0, conn)
