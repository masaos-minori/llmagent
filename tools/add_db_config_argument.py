#!/usr/bin/env python3
"""add_db_config_argument.py — Add the typed-configuration parameter and its call-site argument.

Applies the mechanical part of Plan agentcfg004 RU-2 for one file at a time:

  1. `--func NAME[,NAME]` inserts a keyword-only `db_config: DbConfig` parameter into the
     named function or method.
  2. `--call-names NAME[,NAME]` adds `db_config=<expr>` at the call sites of those
     functions in this file.
  3. Every `SQLiteHelper(...)` call in the file that supplies neither `db_config=` nor
     `db_path=` gets `db_config=<expr>`.

`<expr>` (`--expr`) is how this file reaches the configuration: the parameter name, an
instance attribute, or an attribute path through the context it already holds. The script
never invents a source, so it changes no file whose expression is not stated.

Instance assignment (`self._db_config = db_config`) and the docstring contract lines are
manual steps. Use `check_db_config_call_sites.py` to confirm no call site is left, and
`ruff format` to normalize the inserted signatures.

Usage:
    uv run python tools/add_db_config_argument.py --file scripts/agent/memory/store.py \
        --func __init__ --expr self._db_config
    uv run python tools/add_db_config_argument.py --file scripts/agent/commands/memory_data_ops.py \
        --call-names count_entries,delete --expr self._ctx.cfg.db --dry-run

Exit codes:
    0  The changes were applied (or --dry-run reported them)
    1  Nothing matched
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAM_NAME = "db_config"
IMPORT_LINE = "from db.config import DbConfig"


def _param_end(node: ast.FunctionDef) -> tuple[int, int] | None:
    """Position after the last parameter, including its default; None when there are none."""
    args = node.args
    items = list(args.kwonlyargs) or list(args.args)
    if not items:
        return None
    end = items[-1]
    if end.end_lineno is None or end.end_col_offset is None:
        return None
    pos = (end.end_lineno, end.end_col_offset)
    for default in args.defaults or args.kw_defaults:
        if (
            default is None
            or default.end_lineno is None
            or default.end_col_offset is None
        ):
            continue
        if (default.end_lineno, default.end_col_offset) > pos:
            pos = (default.end_lineno, default.end_col_offset)
    return pos


def _insert_params(tree: ast.Module, names: list[str]) -> list[tuple[int, int, str]]:
    """Return insertions for a keyword-only db_config parameter."""
    out: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in names:
            continue
        args = node.args
        if PARAM_NAME in {a.arg for a in args.kwonlyargs} | {a.arg for a in args.args}:
            continue
        indent = " " * node.col_offset
        star = "" if (args.vararg or args.kwonlyargs) else "*, "
        pos = _param_end(node)
        if pos is None:
            # No parameters: place it directly after the opening parenthesis.
            out.append(
                (
                    node.lineno,
                    node.col_offset + len(f"def {node.name}("),
                    f"{star}{PARAM_NAME}: DbConfig",
                )
            )
            continue
        out.append((pos[0], pos[1], f",\n{indent}{star}{PARAM_NAME}: DbConfig"))
    return out


def _insert_assignments(tree: ast.Module, names: list[str]) -> list[tuple[int, str]]:
    """Return whole-line insertions of the instance assignment at the start of the
    named method bodies, after the docstring when the body has one."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name not in names:
            continue
        if not node.body:
            continue
        first = node.body[0]
        indent = " " * first.col_offset
        after_docstring = (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        )
        line = (
            (first.end_lineno or first.lineno) + 1 if after_docstring else first.lineno
        )
        out.append((line, f"{indent}self._db_config = db_config"))
    return out


def _insert_calls(
    tree: ast.Module, names: list[str], expr: str
) -> list[tuple[int, int, str]]:
    """Return insertions of `db_config=<expr>` after the last argument of each named call."""
    out: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else (func.attr if isinstance(func, ast.Attribute) else None)
        )
        if name not in names:
            continue
        keywords = {kw.arg for kw in node.keywords if kw.arg}
        if PARAM_NAME in keywords:
            continue
        last = (
            node.keywords[-1]
            if node.keywords
            else (node.args[-1] if node.args else None)
        )
        if last is None:
            # Position after the opening parenthesis of a zero-argument call.
            out.append(
                (
                    node.lineno,
                    (node.func.end_col_offset or 0) + 1,
                    f"{PARAM_NAME}={expr}",
                )
            )
            continue
        if last.end_lineno is None or last.end_col_offset is None:
            continue
        out.append((last.end_lineno, last.end_col_offset, f", {PARAM_NAME}={expr}"))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--file", required=True)
    parser.add_argument("--func", default="")
    parser.add_argument("--call-names", default="")
    parser.add_argument("--expr", required=True)
    parser.add_argument(
        "--add-import",
        action="store_true",
        help="insert `from db.config import DbConfig` at the top of the import block "
        "when the file does not have it (run ruff check --fix afterwards to order it)",
    )
    parser.add_argument(
        "--assign",
        action="store_true",
        help="insert `self._db_config = db_config` as the first statement of --func bodies",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.file) if Path(args.file).is_absolute() else ROOT / args.file
    funcs = [f for f in args.func.split(",") if f]
    call_names = [c for c in args.call_names.split(",") if c]
    if not funcs and not call_names:
        parser.error("--func or --call-names is required")

    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    if args.add_import and IMPORT_LINE not in text and not args.dry_run:
        lines = text.splitlines(keepends=True)
        first = next(
            (
                i
                for i, line in enumerate(lines)
                if line.startswith("import ") or line.startswith("from ")
            ),
            0,
        )
        lines.insert(first, IMPORT_LINE + "\n")
        path.write_text("".join(lines), encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    insertions = _insert_params(tree, funcs)
    line_insertions = _insert_assignments(tree, funcs) if args.assign else []
    if call_names:
        insertions += _insert_calls(tree, call_names, args.expr)
    if not insertions and not line_insertions:
        print(f"{path.relative_to(ROOT)}: nothing matched")
        return 1

    lines = text.splitlines(keepends=True)
    for lineno, col, snippet in sorted(insertions, key=lambda i: (-i[0], -i[1])):
        idx = lineno - 1
        lines[idx] = lines[idx][:col] + snippet + lines[idx][col:]
    for line, snippet in sorted(line_insertions, key=lambda i: -i[0]):
        lines[line - 1] = snippet + "\n" + lines[line - 1]
    result = "".join(lines)
    if args.dry_run:
        print(result)
    else:
        path.write_text(result, encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(insertions)} insertion(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
