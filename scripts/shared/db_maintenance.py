"""Shared database maintenance utilities."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


def count_table(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input
