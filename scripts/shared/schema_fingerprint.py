"""scripts/shared/schema_fingerprint.py — Shared schema shape validator.

Derives a structural fingerprint (tables, views, columns, indexes with partial
predicates, table-level constraints, foreign keys, triggers) from canonical DDL
text applied to a fresh in-memory database and compares it against a target
connection. Any deviation raises RuntimeError naming the first differing object,
and every refusal message carries the archive-and-recreate guidance: automatic
migration and version stamping are not supported. Callers pass the canonical DDL
text of their own database (`db.schema_sql` accessors, `schema.sql`, or module
constants), so this module knows no database path.

Virtual tables (`vec0`, FTS5) are compared by name only: `vec0` needs an extension
this module must not load, and a virtual table's shape and `{base}_*` shadow tables
are module implementation details rather than part of the canonical shape. The base
name is required to exist, its shape is not compared, and its shadow tables are
omitted (UNK-01). The accepted limitation is that a name under a virtual base's
prefix (for example `chunks_vec_backup`) cannot be told apart from a shadow table
and is omitted too. Triggers are unaffected: SQLite resolves a trigger body at
execution time, so a trigger that references a virtual table is created identically
on both sides.

Imports only the standard library so shared-is-leaf stays KEPT.

`assert_matches` is the comparison entry point. `build_fingerprint(conn)` and
`expected_fingerprint(canonical_ddl)` are directly comparable only for DDL that
declares no virtual table; for the others the name-only treatment lives in the
comparison, so compare through `assert_matches`."""

import re
import sqlite3
from sqlite3 import Connection

_COMMENT_RE = re.compile(r"--[^\n]*")
_WS_RE = re.compile(r"\s+")
_CONSTRAINT_RE = re.compile(r"\b(unique|check|primary key)\s*\(")
_INDEX_WHERE_RE = re.compile(r"\bWHERE\s+(.*)$", re.IGNORECASE | re.DOTALL)
_VIRTUAL_TABLE_RE = re.compile(
    r"^\s*create\s+virtual\s+table\s+(?:if\s+not\s+exists\s+)?(\w+)",
    re.IGNORECASE | re.DOTALL,
)

# Refusal guidance every message carries (ADR-008: the operator archives and
# recreates; nothing is migrated, stamped, or repaired automatically).
REFUSAL_MESSAGE = (
    "The database does not match the current schema. Automatic migration and "
    "version stamping are not supported. Stop the service, archive the existing "
    "database if required, remove or rename it, and create a new database using "
    "the current schema."
)

# An object entry is (name, columns, indexes, constraints, foreign_keys, triggers).
TableEntry = tuple[
    str,
    tuple[object, ...],
    tuple[object, ...],
    tuple[str, ...],
    tuple[tuple[str, ...], ...],
    tuple[tuple[str, str], ...],
]
Fingerprint = tuple[TableEntry, ...]


def _normalize_ddl(sql: str) -> str:
    """Normalize DDL text so the same shape compares equal across formatting."""
    return _WS_RE.sub(" ", _COMMENT_RE.sub("", sql)).strip().lower()


def _split_statements(script: str) -> list[str]:
    """Split a DDL script into statements with SQLite's own tokenizer.

    Statement boundaries are found with `sqlite3.complete_statement` rather than
    a regular expression, so the semicolons inside a trigger body, a string
    literal, or a comment do not split a statement.
    """
    found: list[str] = []
    rest = script
    while True:
        rest = rest.lstrip()
        if not rest:
            return found
        end = rest.find(";")
        while end != -1 and not sqlite3.complete_statement(rest[: end + 1]):
            end = rest.find(";", end + 1)
        if end == -1:
            if rest.strip():
                found.append(rest.strip())
            return found
        found.append(rest[: end + 1])
        rest = rest[end + 1 :]


def _strip_virtual_statements(script: str) -> tuple[str, tuple[str, ...]]:
    """Return (script without virtual table statements, virtual base names).

    The virtual statements are removed so the remaining DDL applies to a plain
    in-memory database without loading any extension. Their base names are kept
    for the name-only comparison.
    """
    virtual: list[str] = []
    kept: list[str] = []
    for statement in _split_statements(script):
        match = _VIRTUAL_TABLE_RE.match(_normalize_ddl(statement))
        if match:
            virtual.append(match.group(1))
        else:
            kept.append(statement)
    return "\n".join(kept), tuple(virtual)


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
    """Return (name, unique, partial, key_columns, predicate) per index on the table.

    predicate is the normalized trailing WHERE clause of the index's own DDL,
    or None for non-partial indexes.
    """
    found: list[tuple[str, int, int, tuple[tuple[int, int, str], ...], str | None]] = []
    for row in conn.execute(f'PRAGMA index_list("{table}")'):  # nosec B608 — table name read from sqlite_master
        name = str(row[1])
        keys = tuple(
            (int(k[0]), int(k[1]), str(k[2] or ""))
            for k in conn.execute(f'PRAGMA index_info("{name}")')  # nosec B608 — index name read from index_list
        )
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name=?", (name,)
        ).fetchone()
        predicate: str | None = None
        match = _INDEX_WHERE_RE.search(str(ddl[0] or "")) if ddl else None
        if match:
            predicate = _normalize_ddl(match.group(1))
        found.append((name, int(row[2]), int(row[4]), keys, predicate))
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


def _is_name_only(entry: TableEntry) -> bool:
    """Return True when an entry carries only its name: a virtual table marker.

    Only a virtual table can have no columns at all, so an entry whose every shape
    component is empty is unambiguously a name-only marker, not a real table.
    """
    return not any(entry[i] for i in range(1, 6))


def _name_only_names(expected: Fingerprint) -> frozenset[str]:
    """Return the names the fingerprint requires by name only (canonical virtual tables)."""
    return frozenset(str(entry[0]) for entry in expected if _is_name_only(entry))


def _drop_shadow_tables(actual: Fingerprint, virtual: frozenset[str]) -> Fingerprint:
    """Return the live entries without the shadow tables of the canonical virtual tables.

    Shadow table names are `{base}_...` and their layout is a module implementation
    detail, so they are omitted from the comparison (UNK-01).
    """
    prefixes = tuple(f"{name}_" for name in virtual)
    return tuple(entry for entry in actual if not str(entry[0]).startswith(prefixes))


def _name_only(name: str) -> TableEntry:
    """Return the entry a virtual table is compared by: its name and nothing else."""
    return (name, (), (), (), (), ())


def apply_ddl_in_memory(canonical_ddl: str) -> Connection:
    """Apply canonical DDL text to a fresh in-memory database.

    Virtual table statements are stripped first (see `_strip_virtual_statements`),
    so no extension is loaded and the caller closes the returned connection.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(_strip_virtual_statements(canonical_ddl)[0])
    return conn


def build_fingerprint(conn: Connection) -> Fingerprint:
    """Derive the structural fingerprint of conn: tables, views, columns, indexes
    (with partial predicates), table-level constraints, foreign keys, and
    triggers-if-any.

    A live virtual table (its sqlite_master sql starts with CREATE VIRTUAL TABLE)
    is recorded by name only: reading a virtual table's PRAGMA shape requires the
    module that defines it, which this module never loads and the caller may not
    have loaded. Shadow tables are returned as-is; omitting them is the
    comparison's job in `_raise_first_difference`.
    """
    objects = [
        (str(r[0]), str(r[1]))
        for r in conn.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view')"
            " AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    entries: list[TableEntry] = []
    for name, _obj_type in objects:
        ddl = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
            (name,),
        ).fetchone()
        sql = str(ddl[0] or "")
        if _VIRTUAL_TABLE_RE.match(_normalize_ddl(sql)):
            entries.append(_name_only(name))
            continue
        entries.append(
            (
                name,
                _columns(conn, name),
                _indexes(conn, name),
                _table_level_constraints(sql),
                _foreign_keys(conn, name),
                _triggers(conn, name),
            )
        )
    return tuple(entries)


def expected_fingerprint(canonical_ddl: str) -> Fingerprint:
    """Build the canonical fingerprint from a fresh in-memory apply of canonical DDL.

    Virtual tables declared by the DDL contribute name-only entries: the comparison
    requires their names and ignores their shape and shadow tables (UNK-01).
    """
    conn = apply_ddl_in_memory(canonical_ddl)
    try:
        entries = list(build_fingerprint(conn))
    finally:
        conn.close()
    virtual = _strip_virtual_statements(canonical_ddl)[1]
    entries.extend(_name_only(name) for name in virtual)
    return tuple(sorted(entries, key=lambda entry: str(entry[0])))


def _raise_first_difference(
    expected: Fingerprint, actual: Fingerprint, label: str
) -> None:
    """Raise RuntimeError naming the first differing table/column/index/constraint.

    The refusal guidance is part of every message so an operator never sees a diff
    without the archive-and-recreate instruction. Only schema structure is quoted,
    never row content.
    """
    virtual = _name_only_names(expected)
    exp = {str(entry[0]): entry for entry in expected}
    act = {str(entry[0]): entry for entry in _drop_shadow_tables(actual, virtual)}
    for name in sorted(set(exp) - set(act)):
        raise RuntimeError(
            f"{label}: missing table '{name}' defined by the canonical schema — "
            f"{REFUSAL_MESSAGE}"
        )
    for name in sorted(set(act) - set(exp)):
        raise RuntimeError(
            f"{label}: unexpected table '{name}' not defined by the canonical "
            f"schema — {REFUSAL_MESSAGE}"
        )
    parts = (
        "columns",
        "indexes",
        "table-level constraints",
        "foreign keys",
        "triggers",
    )
    for name, exp_entry in exp.items():
        if name in virtual:
            continue  # required by name only: virtual shape and shadows are excluded (UNK-01)
        act_entry = act[name]
        for i, part in enumerate(parts, start=1):
            if exp_entry[i] != act_entry[i]:
                raise RuntimeError(
                    f"{label}.{name}: {part} differ from the canonical schema — "
                    f"{REFUSAL_MESSAGE} expected {exp_entry[i]!r}, found "
                    f"{act_entry[i]!r}"
                )


def assert_matches(
    conn: Connection, canonical_ddl: str, *, label: str = "database"
) -> None:
    """Raise RuntimeError on any deviation from the shape of canonical_ddl.

    Compares expected_fingerprint(canonical_ddl) against build_fingerprint(conn)
    and names the first differing object so operators get an actionable message.
    The database is only inspected: nothing is written, stamped, or repaired.
    """
    _raise_first_difference(
        expected_fingerprint(canonical_ddl), build_fingerprint(conn), label
    )
