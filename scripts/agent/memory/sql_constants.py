#!/usr/bin/env python3
"""agent/memory/sql_constants.py — SQL constants and helpers for memory tables."""

import sqlite3

from db.helper import SQLiteHelper

from agent.memory.exceptions import MemoryConsistencyError


def _count_fts(db: SQLiteHelper) -> int:
    """Return row count in memories_fts; try MATCH predicate, fall back to plain COUNT.

    Raises MemoryConsistencyError when neither query succeeds.
    """
    try:
        rows = db.fetchall(
            "SELECT COUNT(*) FROM memories_fts WHERE memories_fts MATCH '*'"
        )
        return int(rows[0][0]) if rows else 0
    except sqlite3.OperationalError:
        pass
    try:
        rows = db.fetchall("SELECT COUNT(*) FROM memories_fts")
        return int(rows[0][0]) if rows else 0
    except sqlite3.OperationalError as e:
        raise MemoryConsistencyError(f"Cannot count memories_fts: {e}") from e


_INSERT_SQL = (
    "INSERT INTO memories"
    " (memory_id, memory_type, source_type, session_id, turn_id,"
    "  project, repo, branch, content, summary, tags,"
    "  importance, pinned, created_at, updated_at)"
    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)

_UPSERT_SQL = (
    "INSERT INTO memories"
    " (memory_id, memory_type, source_type, session_id, turn_id,"
    "  project, repo, branch, content, summary, tags,"
    "  importance, pinned, created_at, updated_at)"
    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    " ON CONFLICT(memory_id) DO UPDATE SET"
    "   memory_type=excluded.memory_type,"
    "   source_type=excluded.source_type,"
    "   content=excluded.content,"
    "   summary=excluded.summary,"
    "   tags=excluded.tags,"
    "   importance=excluded.importance,"
    "   pinned=excluded.pinned,"
    "   updated_at=excluded.updated_at"
)
