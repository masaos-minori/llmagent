#!/usr/bin/env python3
"""agent/memory/count_ops.py — Count operations for memory tables."""

from db.helper import SQLiteHelper


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
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories_vec")
        return int(rows[0][0]) if rows else 0


def count_entries() -> int:
    """Return total entry count across all types. Raises sqlite3.OperationalError on DB error."""
    with SQLiteHelper("session").open() as db:
        rows = db.fetchall("SELECT COUNT(*) FROM memories")
    return int(rows[0][0]) if rows else 0


def count_prunable(days: int) -> int:
    """Return count of entries older than `days` days. Raises sqlite3.OperationalError on DB error."""
    with SQLiteHelper("session").open() as db:
        row = db.fetchall(
            "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        return int(row[0][0]) if row else 0
