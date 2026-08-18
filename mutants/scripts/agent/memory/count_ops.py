#!/usr/bin/env python3
"""scripts/agent/memory/count_ops.py — Count operations for memory tables."""

from db.helper import SQLiteHelper


def _scalar_count(sql: str, params: tuple[object, ...] = ()) -> int:
    """Run a `COUNT(*)`-style query against the session DB and return the scalar result."""
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall(sql, params)
    return int(rows[0][0]) if rows else 0


def count_by_type() -> dict[str, int]:
    """Return {memory_type: count} for all rows in memories. Diagnostic use only."""
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall(
            "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type",
        )
        return {row[0]: row[1] for row in rows}


def count_by_source_type() -> dict[str, int]:
    """Return {source_type: count} for all rows in memories. Diagnostic use only."""
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall(
            "SELECT source_type, COUNT(*) FROM memories GROUP BY source_type",
        )
        return {row[0]: row[1] for row in rows}


def count_vec() -> int:
    """Return total entry count in memories_vec. Raises sqlite3.OperationalError if unavailable."""
    return _scalar_count("SELECT COUNT(*) FROM memories_vec")


def count_entries() -> int:
    """Return total entry count across all types. Raises sqlite3.OperationalError on DB error."""
    return _scalar_count("SELECT COUNT(*) FROM memories")


def count_prunable(days: int) -> int:
    """Return count of entries older than `days` days. Raises sqlite3.OperationalError on DB error."""
    return _scalar_count(
        "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
        (f"-{days} days",),
    )
