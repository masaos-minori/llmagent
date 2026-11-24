#!/usr/bin/env python3
"""scripts/agent/memory/count_ops.py — Count operations for memory tables."""

from db.config import DbConfig
from db.helper import SQLiteHelper


def _scalar_count(
    sql: str, params: tuple[object, ...] = (), *, db_config: DbConfig
) -> int:
    """Run a `COUNT(*)`-style query against the session DB and return the scalar result."""
    with SQLiteHelper("session", db_config=db_config).open() as db:
        return _scalar_count_on(db, sql, params)


def _scalar_count_on(
    db: SQLiteHelper, sql: str, params: tuple[object, ...] = ()
) -> int:
    """Run a `COUNT(*)`-style query on the caller's connection and return the scalar result."""
    rows = db.fetchall(sql, params)
    return int(rows[0][0]) if rows else 0


def count_pinned(db: SQLiteHelper) -> int:
    """Return the number of currently pinned memories on the caller's connection.

    The pin limit is evaluated inside the transaction that writes the pin, so the count
    must come from the same connection rather than a second one (REQ-008).
    """
    return _scalar_count_on(db, "SELECT count(*) FROM memories WHERE pinned = 1")


def count_by_type(*, db_config: DbConfig) -> dict[str, int]:
    """Return {memory_type: count} for all rows in memories. Diagnostic use only."""
    with SQLiteHelper("session", db_config=db_config).open() as db:
        rows = db.fetchall(
            "SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type",
        )
        return {row[0]: row[1] for row in rows}


def count_by_source_type(*, db_config: DbConfig) -> dict[str, int]:
    """Return {source_type: count} for all rows in memories. Diagnostic use only."""
    with SQLiteHelper("session", db_config=db_config).open() as db:
        rows = db.fetchall(
            "SELECT source_type, COUNT(*) FROM memories GROUP BY source_type",
        )
        return {row[0]: row[1] for row in rows}


def count_vec(*, db_config: DbConfig) -> int:
    """Return total entry count in memories_vec. Raises sqlite3.OperationalError if unavailable."""
    return _scalar_count("SELECT COUNT(*) FROM memories_vec", db_config=db_config)


def count_entries(*, db_config: DbConfig) -> int:
    """Return total entry count across all types. Raises sqlite3.OperationalError on DB error."""
    return _scalar_count("SELECT COUNT(*) FROM memories", db_config=db_config)


def count_prunable(days: int, *, db_config: DbConfig) -> int:
    """Return count of entries older than `days` days. Raises sqlite3.OperationalError on DB error."""
    return _scalar_count(
        "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
        (f"-{days} days",),
        db_config=db_config,
    )
