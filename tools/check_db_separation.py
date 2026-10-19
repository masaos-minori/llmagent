#!/usr/bin/env python3
"""check_db_separation.py — Verify the ADR-008 SQLite 4DB separation boundaries.

Statically verifies that the four logical databases (rag, session, workflow,
eventbus) stay physically and logically separated:

  1. Table ownership: the tables created by each database's schema DDL equal the
     canonical ownership inventory below (a table placed in the wrong database, or
     an unregistered table, is reported).
  2. Cross-DB references: no DDL REFERENCES clause targets a table owned by
     another database.
  3. Physical path separation: the four configured/default DB paths are distinct
     files named after their database (`rag.sqlite`, ...), and every `*_db_path`
     key under `config/*.toml` points to the file named after its key.
  4. sqlite-vec scope: `vec0` virtual tables exist only where the inventory
     registers them, `SQLiteHelper` loads the extension by default only for `rag`
     and `session` (the databases that own a vec0 table),
     and an explicit `load_vec=True` appears only in sanctioned call sites.
  5. Cross-DB access in code: no `ATTACH` statement and no schema-qualified
     `FROM`/`JOIN` (`rag.`, `session.`, `workflow.`, `eventbus.`) in `scripts/`.

Rule: ADR-008 INV-01 to INV-05 and INV-08 (docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md).

Usage:
    uv run python tools/check_db_separation.py
    uv run python tools/check_db_separation.py --format json

Exit codes:
    0  No violations found
    1  Violations detected
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import orjson

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
CONFIG_DIR = REPO_ROOT / "config"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Canonical table ownership (ADR-008 Decision #1 to #4). Update together with the
# ADR when a table is added to or moved between databases.
TABLE_OWNERSHIP: dict[str, frozenset[str]] = {
    "rag": frozenset({"documents", "chunks", "chunks_vec", "chunks_fts"}),
    "session": frozenset(
        {
            "sessions",
            "messages",
            "memories",
            "memories_fts",
            "memories_vec",
            "memory_links",
            "session_diagnostics",
        }
    ),
    "workflow": frozenset(
        {
            "tasks",
            "attempts",
            "processed_events",
            "artifacts",
            "workflow_schema_version",
        }
    ),
    "eventbus": frozenset({"events", "consumer_delivery", "consumer_offsets"}),
}

# Virtual tables backed by the sqlite-vec extension, by owning database.
VEC_TABLES: dict[str, frozenset[str]] = {
    "rag": frozenset({"chunks_vec"}),
    "session": frozenset({"memories_vec"}),
}

# Sanctioned explicit `load_vec=True` call sites (path relative to the repo root).
LOAD_VEC_SANCTIONED: frozenset[str] = frozenset({"scripts/db/create_schema.py"})

_CREATE_RE = re.compile(
    r"CREATE\s+(?P<virtual>VIRTUAL\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"(?P<name>\w+)(?P<using>\s+USING\s+(?P<module>\w+))?",
    re.IGNORECASE,
)
_REFERENCES_RE = re.compile(r"\bREFERENCES\s+(?P<name>\w+)", re.IGNORECASE)
_ATTACH_RE = re.compile(r"\bATTACH\s+(?:DATABASE\s+)?\S+\s+AS\s+\w+", re.IGNORECASE)
_QUALIFIED_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+(?:rag|session|workflow|eventbus)\.\w+", re.IGNORECASE
)
_LOAD_VEC_TRUE_RE = re.compile(r"\bload_vec\s*=\s*True\b")
_DEFAULT_LOAD_VEC_RE = re.compile(
    r"self\._default_load_vec\s*=\s*resolved\s+in\s*"
    r"\(\s*[\"']rag[\"']\s*,\s*[\"']session[\"']\s*\)"
)
_DB_PATH_KEY_RE = re.compile(r"^(?P<db>rag|session|workflow|eventbus)_db_path$")


def _schema_ddl() -> dict[str, str]:
    """Return the full schema DDL text per database, migrations included."""
    import db.schema_sql as schema_sql  # noqa: PLC0415

    migrations_workflow = ";\n".join(s for _, s in schema_sql._WORKFLOW_MIGRATIONS)
    migrations_eventbus = ";\n".join(s for _, s in schema_sql._EVENTBUS_MIGRATIONS)
    return {
        "rag": schema_sql.build_rag_schema_sql(8),
        "session": schema_sql.build_session_schema_sql(8),
        "workflow": schema_sql.build_workflow_schema_sql()
        + ";\n"
        + migrations_workflow,
        "eventbus": schema_sql.build_eventbus_schema_sql()
        + ";\n"
        + migrations_eventbus,
    }


def _strip_sql_comments(sql: str) -> str:
    """Remove `--` line comments so commented DDL is not parsed."""
    return re.sub(r"--[^\n]*", "", sql)


def check_table_ownership(ddl: dict[str, str]) -> list[str]:
    """Check 1 and 2: table placement, vec0 scope, and cross-DB REFERENCES."""
    problems: list[str] = []
    created: dict[str, set[str]] = {}
    for db_name, sql in ddl.items():
        sql = _strip_sql_comments(sql)
        tables: set[str] = set()
        for m in _CREATE_RE.finditer(sql):
            tables.add(m.group("name"))
            module = (m.group("module") or "").lower()
            if module == "vec0" and m.group("name") not in VEC_TABLES.get(
                db_name, frozenset()
            ):
                problems.append(
                    f"[vec-scope] vec0 table {m.group('name')!r} is created in "
                    f"{db_name}.sqlite but is not registered in VEC_TABLES"
                )
        created[db_name] = tables
        expected = TABLE_OWNERSHIP[db_name]
        for name in sorted(tables - expected):
            owner = next((d for d, t in TABLE_OWNERSHIP.items() if name in t), None)
            where = f"belongs to {owner}.sqlite" if owner else "is not in the inventory"
            problems.append(
                f"[table-ownership] {db_name}.sqlite creates table {name!r}, which {where}"
            )
        for name in sorted(expected - tables):
            problems.append(
                f"[table-ownership] {db_name}.sqlite no longer creates inventory table {name!r}"
            )
        for m in _REFERENCES_RE.finditer(sql):
            target = m.group("name")
            if target not in tables and target not in expected:
                owner = next(
                    (d for d, t in TABLE_OWNERSHIP.items() if target in t), None
                )
                if owner and owner != db_name:
                    problems.append(
                        f"[cross-db-fk] {db_name}.sqlite REFERENCES {target!r}, "
                        f"owned by {owner}.sqlite"
                    )
    return problems


def _normalize(path: str) -> str:
    return str(Path(path))


def check_db_paths() -> list[str]:
    """Check 3: four distinct physical files named after their database."""
    problems: list[str] = []
    from db.config import DbConfig  # noqa: PLC0415

    defaults = {f.name: f.default for f in dataclasses.fields(DbConfig)}
    paths: dict[str, str] = {
        "rag": "",
        "session": "",
        "workflow": str(defaults["workflow_db_path"]),
        "eventbus": str(defaults["eventbus_db_path"]),
    }
    agent_toml = CONFIG_DIR / "agent.toml"
    if agent_toml.is_file():
        data = tomllib.loads(agent_toml.read_text(encoding="utf-8"))
        flat = _flatten(data)
        for key, value in flat.items():
            m = _DB_PATH_KEY_RE.match(key)
            if m and isinstance(value, str):
                paths[m.group("db")] = value
    for db_name, path in paths.items():
        if not path:
            problems.append(f"[db-path] {db_name}_db_path is not configured")
    configured = {d: _normalize(p) for d, p in paths.items() if p}
    seen: dict[str, str] = {}
    for db_name, path in configured.items():
        if path in seen:
            problems.append(
                f"[db-path] {db_name} and {seen[path]} point to the same file {path}"
            )
        seen[path] = db_name
    for toml_path in sorted(CONFIG_DIR.glob("*.toml")):
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        for key, value in _flatten(data).items():
            m = _DB_PATH_KEY_RE.match(key)
            if m and isinstance(value, str):
                expected_name = f"{m.group('db')}.sqlite"
                if Path(value).name != expected_name:
                    rel = toml_path.relative_to(REPO_ROOT)
                    problems.append(
                        f"[db-path] {rel}: {key} = {value!r} is not named {expected_name}"
                    )
    return problems


def _flatten(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested TOML tables into leaf key -> value (last key wins)."""
    flat: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            flat.update(_flatten(value))
        else:
            flat[key] = value
    return flat


def check_vec_loading() -> list[str]:
    """Check 4: sqlite-vec default scope and explicit load_vec=True call sites."""
    problems: list[str] = []
    helper = SCRIPTS_DIR / "db" / "helper.py"
    if not _DEFAULT_LOAD_VEC_RE.search(helper.read_text(encoding="utf-8")):
        problems.append(
            "[vec-scope] scripts/db/helper.py no longer sets "
            '`self._default_load_vec = resolved in ("rag", "session")`'
        )
    for py in sorted(SCRIPTS_DIR.rglob("*.py")):
        rel = py.relative_to(REPO_ROOT).as_posix()
        if rel in LOAD_VEC_SANCTIONED or rel == "scripts/db/helper.py":
            continue
        for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if _LOAD_VEC_TRUE_RE.search(line):
                problems.append(
                    f"[vec-scope] {rel}:{lineno}: explicit load_vec=True outside "
                    "LOAD_VEC_SANCTIONED"
                )
    return problems


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Return ids of the Constant nodes that are module/class/function docstrings."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                ids.add(id(first.value))
    return ids


def check_cross_db_access() -> list[str]:
    """Check 5: ATTACH and schema-qualified FROM/JOIN inside SQL string literals."""
    problems: list[str] = []
    for py in sorted(SCRIPTS_DIR.rglob("*.py")):
        rel = py.relative_to(REPO_ROOT).as_posix()
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if id(node) in docstrings:
                continue
            if _ATTACH_RE.search(node.value):
                problems.append(
                    f"[cross-db-access] {rel}:{node.lineno}: ATTACH statement"
                )
            if _QUALIFIED_RE.search(node.value):
                problems.append(
                    f"[cross-db-access] {rel}:{node.lineno}: schema-qualified table access"
                )
    return problems


def run_checks() -> list[str]:
    """Run every check and return the combined problem list."""
    return (
        check_table_ownership(_schema_ddl())
        + check_db_paths()
        + check_vec_loading()
        + check_cross_db_access()
    )


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    problems = run_checks()
    if args.format == "json":
        sys.stdout.write(orjson.dumps({"violations": problems}).decode() + "\n")
    elif problems:
        for p in problems:
            sys.stdout.write(p + "\n")
        sys.stdout.write(f"{len(problems)} violation(s) found\n")
    else:
        sys.stdout.write("No violations found\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
