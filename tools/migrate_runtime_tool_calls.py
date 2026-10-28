#!/usr/bin/env python3
"""tools/migrate_runtime_tool_calls.py
Rename default-reliant `build_runtime_tool(` call sites in test files to
`build_fixture_runtime_tool(` (tests/shared/runtime_tool_factory.py) and fix
the imports of the affected files.

Semantics (rtool008 batch, rows 03-08):
- A call counts as default-reliant when it omits any of `is_write`,
  `requires_serial`, `resource_scope_kind` or `resource_scope_keys`
  (keyword or positional coverage per the current builder signature).
- Only the identified call-start lines are renamed; all other text is untouched.
- The `shared.runtime_tool` import loses `build_runtime_tool` only when no
  calls remain in the file; otherwise it is kept for the strict calls.
- `from tests.shared.runtime_tool_factory import build_fixture_runtime_tool`
  is inserted after the last module-level import (or after the module docstring);
  run `uv run ruff check --select I --fix` afterwards to finalize import order.
- Import edits preserve indentation for function-local imports, and the rewritten
  source must pass `compile()` before the file is written.

Usage: uv run python tools/migrate_runtime_tool_calls.py <test-file>...
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

FIELDS = {"is_write", "requires_serial", "resource_scope_kind", "resource_scope_keys"}
POS = {
    7: "is_write",
    8: "requires_serial",
    9: "resource_scope_kind",
    10: "resource_scope_keys",
}


def _find_default_reliant_calls(tree: ast.AST) -> tuple[int, list[int]]:
    total = 0
    omit_lines: list[int] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "build_runtime_tool"
        ):
            total += 1
            kw = {k.arg for k in node.keywords if k.arg}
            covered = {POS[i] for i in range(len(node.args)) if i in POS}
            if not FIELDS <= kw | covered:
                omit_lines.append(node.lineno)
    return total, omit_lines


def _migrate(path: Path) -> int:
    src = path.read_text()
    total, omit_lines = _find_default_reliant_calls(ast.parse(src))
    lines = src.splitlines(keepends=True)
    renamed = 0
    for ln in sorted(omit_lines):
        line = lines[ln - 1]
        idx = line.find("build_runtime_tool(")
        if idx == -1:
            print(
                f"{path}:{ln}: call-start line lacks 'build_runtime_tool('",
                file=sys.stderr,
            )
            return 1
        lines[ln - 1] = (
            line[:idx]
            + "build_fixture_runtime_tool("
            + line[idx + len("build_runtime_tool(") :]
        )
        renamed += 1
    new_src = "".join(lines)

    remaining = total - renamed
    if remaining == 0 and "build_runtime_tool" in new_src:
        for node in ast.walk(ast.parse(new_src)):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "shared.runtime_tool"
                and any(a.name == "build_runtime_tool" for a in node.names)
            ):
                names = [a.name for a in node.names if a.name != "build_runtime_tool"]
                start, end = node.lineno - 1, node.end_lineno
                indent = " " * node.col_offset
                replacement = (
                    f"{indent}from {node.module} import {', '.join(names)}\n"
                    if names
                    else ""
                )
                body = new_src.splitlines(keepends=True)
                body[start:end] = [replacement] if replacement else []
                new_src = "".join(body)
                break

    if renamed and "tests.shared.runtime_tool_factory" not in new_src:
        body = new_src.splitlines(keepends=True)
        mod_tree = ast.parse(new_src)
        insert_at = max(
            (
                node.end_lineno
                for node in mod_tree.body
                if isinstance(node, (ast.Import, ast.ImportFrom))
                and node.end_lineno is not None
            ),
            default=0,
        )
        if insert_at == 0 and ast.get_docstring(mod_tree):
            insert_at = mod_tree.body[0].end_lineno or 0
        body.insert(
            insert_at,
            "from tests.shared.runtime_tool_factory import build_fixture_runtime_tool\n",
        )
        new_src = "".join(body)

    try:
        compile(new_src, str(path), "exec")
    except SyntaxError as exc:
        print(f"{path}: refusing to write (syntax error: {exc})", file=sys.stderr)
        return 1

    path.write_text(new_src)
    print(f"{path}: calls={total} renamed={renamed} kept_strict={remaining}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Test files to migrate")
    args = parser.parse_args()
    for raw in args.paths:
        if _migrate(Path(raw)) != 0:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
