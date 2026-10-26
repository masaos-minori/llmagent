"""scripts/shared/eventbus_schema_fingerprint.py — Shared EventBus schema shape validator.

Derives a structural fingerprint
(tables, columns, indexes, table-level constraints, foreign keys, triggers)
from scripts/eventbus/schema.sql via a fresh in-memory apply and compares it
against a target connection. Raises RuntimeError on any deviation, even when
PRAGMA user_version matches (REQ-001). Imports only the standard library so
shared-is-leaf and eventbus-is-isolated stay KEPT."""

import re
import sqlite3
from pathlib import Path
from sqlite3 import Connection

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "eventbus" / "schema.sql"

_COMMENT_RE = re.compile(r"--[^\n]*")
_WS_RE = re.compile(r"\s+")
_CONSTRAINT_RE = re.compile(r"\b(unique|check|primary key)\s*\(")

# A table entry is (table, columns, indexes, constraints, foreign_keys, triggers).
TableEntry = tuple[
    str,
    tuple[object, ...],
    tuple[object, ...],
    tuple[str, ...],
    tuple[tuple[str, ...], ...],
    tuple[tuple[str, str], ...],
]
Fingerprint = tuple[TableEntry, ...]


def _schema_sql() -> str:
    """Return the canonical EventBus DDL text from scripts/eventbus/schema.sql."""
    return _SCHEMA_PATH.read_text()


def _normalize_ddl(sql: str) -> str:
    """Normalize DDL text so the same shape compares equal across formatting."""
    return _WS_RE.sub(" ", _COMMENT_RE.sub("", sql)).strip().lower()


def _table_level_constraints(ddl: str) -> tuple[str, ...]:
    """Extract normalized table-level UNIQUE/PRIMARY KEY/CHECK clauses from DDL text."""
    norm = _normalize_ddl(ddl)
    found: list[str] = []
    for match in _CONSTRAINT_RE.finditer(norm):
        depth = 0
        for i in range(match.end() - 1, len(norm)):
            if norm[i] == "(":
                depth += 1
            elif norm[i] == ")":
                depth -= 1
                if depth == 0:
                    found.append(norm[match.start() : i + 1])
                    break
    return tuple(sorted(found))


def _columns(
    conn: Connection, table: str
) -> tuple[tuple[str, str, int, object, int], ...]:
    """Return (name, type.lower(), notnull, dflt_value, pk) per column."""
    rows = conn.execute(f'PRAGMA table_info("{table}")')  # nosec B608 — table name read from sqlite_master
    return tuple(
        (str(r[1]), str(r[2]).lower(), int(r[3]), r[4], int(r[5])) for r in rows
    )


def _indexes(conn: Connection, table: str) -> tuple[object, ...]:
    """Return (name, unique, partial, key_columns) per index on the table."""
    found: list[tuple[str, int, int, tuple[tuple[int, int, str], ...]]] = []
    for row in conn.execute(f'PRAGMA index_list("{table}")'):  # nosec B608 — table name read from sqlite_master
        name = str(row[1])
        keys = tuple(
            (int(k[0]), int(k[1]), str(k[2] or ""))
            for k in conn.execute(f'PRAGMA index_info("{name}")')  # nosec B608 — index name read from index_list
        )
        found.append((name, int(row[2]), int(row[4]), keys))
    return tuple(sorted(found, key=lambda item: str(item[0])))


def _foreign_keys(conn: Connection, table: str) -> tuple[tuple[str, ...], ...]:
    """Return normalized PRAGMA foreign_key_list rows for the table."""
    rows = conn.execute(f'PRAGMA foreign_key_list("{table}")')  # nosec B608 — table name read from sqlite_master
    return tuple(
        sorted(tuple("" if v is None else str(v) for v in row) for row in rows)
    )


def _triggers(conn: Connection, table: str) -> tuple[tuple[str, str], ...]:
    """Return (name, normalized sql) per trigger on the table.

    Triggers come from sqlite_master rows: PRAGMA trigger_list is not a valid
    SQLite pragma and unknown pragmas silently return an empty result.
    """
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
        (table,),
    )
    return tuple(sorted((str(r[0]), _normalize_ddl(str(r[1] or ""))) for r in rows))


def apply_schema_in_memory() -> Connection:
    """Apply scripts/eventbus/schema.sql to a fresh in-memory database."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_schema_sql())
    return conn


def build_fingerprint(conn: Connection) -> Fingerprint:
    """Derive the structural fingerprint of conn: tables, columns, indexes,
    table-level constraints, foreign keys, and triggers-if-any."""
    tables = [
        str(r[0])
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE"
            " 'sqlite_%' ORDER BY name"
        )
    ]
    entries: list[TableEntry] = []
    for table in tables:
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        entries.append(
            (
                table,
                _columns(conn, table),
                _indexes(conn, table),
                _table_level_constraints(str(ddl[0] or "")),
                _foreign_keys(conn, table),
                _triggers(conn, table),
            )
        )
    return tuple(entries)


def expected_fingerprint() -> Fingerprint:
    """Build the canonical fingerprint from a fresh in-memory apply of schema.sql."""
    conn = apply_schema_in_memory()
    try:
        return build_fingerprint(conn)
    finally:
        conn.close()


def _raise_first_difference(
    expected: Fingerprint, actual: Fingerprint, label: str
) -> None:
    """Raise RuntimeError naming the first differing table/column/index/constraint."""
    exp = {str(entry[0]): entry for entry in expected}
    act = {str(entry[0]): entry for entry in actual}
    for name in sorted(set(exp) - set(act)):
        raise RuntimeError(f"{label}: missing table '{name}' defined by schema.sql")
    for name in sorted(set(act) - set(exp)):
        raise RuntimeError(
            f"{label}: unexpected table '{name}' not defined by schema.sql"
        )
    parts = (
        "columns",
        "indexes",
        "table-level constraints",
        "foreign keys",
        "triggers",
    )
    for name, exp_entry in exp.items():
        act_entry = act[name]
        for i, part in enumerate(parts, start=1):
            if exp_entry[i] != act_entry[i]:
                raise RuntimeError(
                    f"{label}.{name}: {part} differ from schema.sql — "
                    f"expected {exp_entry[i]!r}, found {act_entry[i]!r}"
                )


def assert_matches(conn: Connection, *, label: str = "eventbus.sqlite") -> None:
    """Raise RuntimeError on any deviation from the canonical EventBus shape.

    Compares expected_fingerprint() against build_fingerprint(conn) and names
    the first differing object so operators get an actionable message.
    """
    _raise_first_difference(expected_fingerprint(), build_fingerprint(conn), label)
