#!/usr/bin/env python3
"""scripts/agent/memory/pin_ops.py — Pin/unpin operations for memories."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shared.config_loader import ConfigLoader
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
    """Set pinned=1 for memory_id; return True when found.

    Emits a ``pin`` change event to the JSONL archive after the SQLite write
    (SQLite-first) on the main path (no injected ``conn``); a no-op of a missing
    id emits nothing. REQ-001.
    """
    ok = _set_pinned(memory_id, 1, conn)
    if ok and conn is None:
        _emit_event("pin", memory_id)
    return ok


def unpin(memory_id: str, conn: sqlite3.Connection | None = None) -> bool:
    """Set pinned=0 for memory_id; return True when found.

    Emits an ``unpin`` change event to the JSONL archive after the SQLite write
    (SQLite-first) on the main path (no injected ``conn``); a no-op of a missing
    id emits nothing. REQ-001.
    """
    ok = _set_pinned(memory_id, 0, conn)
    if ok and conn is None:
        _emit_event("unpin", memory_id)
    return ok


def _emit_event(event: str, memory_id: str) -> None:
    """Append a pin/unpin change event after the SQLite write (SQLite-first).

    The SQLite change stands even if the archive append fails; the error
    propagates so the caller can surface M-07. Mirrors ``write_ops._emit_delete_event``.
    """
    from agent.memory.jsonl_store import JsonlMemoryStore

    cfg = ConfigLoader().load("agent.toml")
    store = JsonlMemoryStore(Path(cfg["memory"]["memory_jsonl_dir"]) / "memories.jsonl")
    store.append_event(event, memory_id)
