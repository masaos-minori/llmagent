"""scripts/shared/db_maintenance.py

Shared database maintenance utilities."""

from typing import Any


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_count_table__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_count_table__mutmut)
def count_table(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_orig(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_1(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(None)  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_2(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(None)[0]["n"])  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_3(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[1]["n"])  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_4(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["XXnXX"])  # nosec B608 — table is always a hardcoded name, never user input


def x_count_table__mutmut_5(db: Any, table: str) -> int:
    """Return row count for a single table.

    Args:
        db: Database connection (SQLiteHelper context manager result).
        table: Table name (must be a hardcoded identifier, never user input).

    Returns:
        Number of rows in the table.
    """
    return int(db.fetchall(f"SELECT COUNT(*) AS n FROM {table}")[0]["N"])  # nosec B608 — table is always a hardcoded name, never user input

mutants_x_count_table__mutmut['_mutmut_orig'] = x_count_table__mutmut_orig # type: ignore # mutmut generated
mutants_x_count_table__mutmut['x_count_table__mutmut_1'] = x_count_table__mutmut_1 # type: ignore # mutmut generated
mutants_x_count_table__mutmut['x_count_table__mutmut_2'] = x_count_table__mutmut_2 # type: ignore # mutmut generated
mutants_x_count_table__mutmut['x_count_table__mutmut_3'] = x_count_table__mutmut_3 # type: ignore # mutmut generated
mutants_x_count_table__mutmut['x_count_table__mutmut_4'] = x_count_table__mutmut_4 # type: ignore # mutmut generated
mutants_x_count_table__mutmut['x_count_table__mutmut_5'] = x_count_table__mutmut_5 # type: ignore # mutmut generated
