#!/usr/bin/env python3
"""tools/apply_test_taxonomy_markers.py - Writes the test-taxonomy markers a procedure names.

Reads a records JSON file describing one test module per record: the module-level `pytestmark`
kind, the individual tests that carry `@pytest.mark.characterization` (line numbers as recorded
by the procedure, before any insertion), and whether `import pytest` has to be added. The marker
is placed after the module-level import block. Nothing is written when any record fails
validation: an existing module-level `pytestmark`, a named line that is not a test function
definition, an unregistered kind, or `add_import` on a module that already imports pytest.
Test-file content other than the markers is not changed.

Usage:
    python tools/apply_test_taxonomy_markers.py RECORDS.json [--dry-run]

Exit codes: 0 every record applied, 1 a record that failed validation, 2 a usage error or an
unreadable or malformed records file.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import TypedDict

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text, print_dry_run

KINDS = ("contract", "characterization")


class Record(TypedDict, total=False):
    path: str
    pytestmark: str
    tests: list[int]
    add_import: bool


def _imports(tree: ast.Module) -> list[ast.Import | ast.ImportFrom]:
    """The module-level import statements, in source order."""
    return [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]


def _has_pytestmark(tree: ast.Module) -> bool:
    """Whether the module already assigns `pytestmark` at module level."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "pytestmark"
                for target in node.targets
            ):
                return True
    return False


def _validate(record: Record) -> str | None:
    """The reason a record cannot be applied, or None when it is sound."""
    path = Path(record["path"])
    if not path.is_file():
        return f"{path}: not a file"
    kind = record["pytestmark"]
    if kind not in KINDS:
        return f"{path}: pytestmark must be one of {KINDS}"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    if _has_pytestmark(tree):
        return f"{path}: already carries a module-level pytestmark"
    imports = _imports(tree)
    if not imports:
        return f"{path}: no module-level import to place the marker after"
    if record["add_import"]:
        names = [
            alias.name.split(".")[0]
            for node in imports
            for alias in getattr(node, "names", [])
        ]
        if "pytest" in names:
            return f"{path}: already imports pytest"
    lines = text.splitlines()
    for line in record["tests"]:
        if not 1 <= line <= len(lines):
            return f"{path}: line {line} is out of range"
        definition = lines[line - 1].strip()
        if not definition.startswith("def test_") and not definition.startswith(
            "async def test_"
        ):
            return f"{path}: line {line} is not a test function definition"
    return None


def _apply(record: Record) -> str:
    """The module text with the markers inserted at the recorded positions."""
    path = Path(record["path"])
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    imports = _imports(ast.parse(text))
    insertions: dict[int, list[str]] = {}

    if record["add_import"]:
        first = next(
            node for node in imports if getattr(node, "module", None) != "__future__"
        )
        insertions.setdefault(first.lineno - 1, []).append("import pytest")

    last = (
        imports[-1].lineno if imports[-1].end_lineno is None else imports[-1].end_lineno
    )
    marker = insertions.setdefault(last, [])
    marker.append("")
    marker.append(f"pytestmark = pytest.mark.{record['pytestmark']}")
    if len(lines) <= last or lines[last] != "":
        marker.append("")

    for line in record["tests"]:
        definition = lines[line - 1]
        indent = definition[: len(definition) - len(definition.lstrip())]
        insertions.setdefault(line - 1, []).append(
            f"{indent}@pytest.mark.characterization"
        )

    new: list[str] = []
    for index, source_line in enumerate(lines):
        new.extend(insertions.get(index, []))
        new.append(source_line)
    return "\n".join(new) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("records")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        parsed = json.loads(Path(args.records).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{args.records}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(parsed, list) or not parsed:
        print(f"{args.records}: expected a non-empty array of records", file=sys.stderr)
        return 2

    records: list[Record] = []
    for item in parsed:
        if (
            not isinstance(item, dict)
            or not item.get("path")
            or not item.get("pytestmark")
        ):
            print(
                f"{args.records}: a record needs a path and a pytestmark",
                file=sys.stderr,
            )
            return 2
        records.append(
            {
                "path": str(item["path"]),
                "pytestmark": str(item["pytestmark"]),
                "tests": [int(line) for line in item.get("tests", [])],
                "add_import": bool(item.get("add_import", False)),
            }
        )

    problems = [_validate(record) for record in records]
    if any(problem is not None for problem in problems):
        for problem in problems:
            if problem:
                print(problem, file=sys.stderr)
        return 1

    for record in records:
        path = Path(record["path"])
        old = path.read_text(encoding="utf-8")
        new = _apply(record)
        if args.dry_run:
            print_dry_run(path, old, new)
        else:
            atomic_write_text(path, new)

    if not args.dry_run:
        print(f"Applied markers to {len(records)} module(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
