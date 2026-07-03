#!/usr/bin/env python3
"""agent/memory/pin_ops.py — Pin/unpin operations for memories."""

from __future__ import annotations

import sqlite3

from agent.memory.mapper import _now_iso


def pin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
    """Set pinned=1 for memory_id; return True when found."""
    if conn is not None:
        cur = conn.execute(
            "UPDATE memories SET pinned=1, updated_at=? WHERE memory_id=?",
            (_now_iso(), memory_id),
        )
        conn.commit()
        return cur.rowcount > 0

    from db.helper import SQLiteHelper

    with SQLiteHelper("session").open(write_mode=True) as db:
        cur = db.execute(
            "UPDATE memories SET pinned=1, updated_at=? WHERE memory_id=?",
            (_now_iso(), memory_id),
        )
        db.commit()
    return cur.rowcount > 0


def unpin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
    """Set pinned=0 for memory_id; return True when found."""
    if conn is not None:
        cur = conn.execute(
            "UPDATE memories SET pinned=0, updated_at=? WHERE memory_id=?",
            (_now_iso(), memory_id),
        )
        conn.commit()
        return cur.rowcount > 0

    from db.helper import SQLiteHelper

    with SQLiteHelper("session").open(write_mode=True) as db:
        cur = db.execute(
            "UPDATE memories SET pinned=0, updated_at=? WHERE memory_id=?",
            (_now_iso(), memory_id),
        )
        db.commit()
    return cur.rowcount > 0
