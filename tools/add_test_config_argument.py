#!/usr/bin/env python3
"""add_test_config_argument.py — Insert an argument at the call sites in a test file.

Companion of `add_db_config_argument.py` for the test side of Plan agentcfg004 RU-2:
the tests already construct the typed configuration, so the mechanical part is placing it
at the call sites of the named functions.

For every call of `--call-names` in the file:
  - `--position first`        insert it as the first argument (the typed configuration is
                             the first parameter of `rotate_*` and `recover_corruption`).
  - `--position after-first`  insert it after the first argument (`checkpoint_wal`,
                             `purge_corrupt_archives`, `purge_archive_artifacts`).
  - `--keyword NAME`          insert it as keyword `NAME=...` (keyword-only parameters).

`--expr` is the expression the file uses to reach the configuration: a module helper, an
instance attribute set by an autouse fixture, or a fixture value. The script never invents
a source, and it skips calls that already pass the argument by keyword. `--import-module`
adds `from <module> import <expr>` after the last top-level import when the file reaches
the value through an import rather than a local definition.

`--add-param NAME` adds NAME to the signature of every test function that uses NAME as a
fixture value but does not declare it; pytest resolves the name through the existing fixture.

`--accept-param NAME` is the other direction: it adds `NAME=None` to the definition of every
function named in `--call-names` that does not declare it. This is the local fake-factory shape
(`def _make(target): return _FakeSQLiteHelper(conn)` used as `side_effect=_make`), where the
source now passes the typed configuration as a keyword the fake never reads. Lambdas passed as
`side_effect=lambda ...` are the same shape and receive the parameter too. `--definitions-only`
restricts the run to those definitions, so the names in `--call-names` are not also inserted at
call sites.

`--drop-patch TARGET` removes every `patch("<TARGET>", ...)` and `monkeypatch.setattr("<TARGET>", ...)`
usage, because the patched function no longer exists in the source module. A `with` whose only item
was that patch is removed and its body dedented; a patch that was one item of a group is removed
from the group. Call sites inside the affected blocks — and inside the function that held the
setattr — receive the argument. The test already binds the value it patched, so `--expr` names that
binding; only the affected call sites are touched, which is what makes the two options meaningful
together.

`--hoist-into VAR` is for the cases where the value was only bound inside the patch
(`return_value=<expression>`, `lambda: <expression>`): the removed usage becomes an assignment
`VAR = <expression>` at the same indentation, and `--expr VAR` places it at the call sites. An
expression that is already a bare name is not re-bound.

Usage:
    uv run python tools/add_test_config_argument.py --file tests/db/test_db_maintenance.py \
        --call-names recover_corruption --expr self._db_cfg --position first --dry-run
    uv run python tools/add_test_config_argument.py --file tests/db/test_db_recovery.py \
        --call-names recover_corruption --expr mock_db_cfg --add-param mock_db_cfg

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


def _is_patch_of(node: ast.AST, target: str) -> bool:
    """True when the node is patch("<target>", ...)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not (isinstance(func, ast.Name) and func.id == "patch"):
        return False
    return bool(
        node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == target
    )


def _is_setattr_of(node: ast.AST, target: str) -> bool:
    """True when the node is monkeypatch.setattr("<target>", ...)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not (isinstance(func, ast.Attribute) and func.attr == "setattr"):
        return False
    return bool(
        node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == target
    )


def _patch_value_source(source: str, node: ast.AST) -> str:
    """The expression the patch supplies: return_value=, or the lambda body of a setattr."""
    if not isinstance(node, ast.Call):
        return ""
    for kw in node.keywords:
        if kw.arg == "return_value":
            return ast.get_source_segment(source, kw.value) or ""
    if len(node.args) >= 2:
        value = node.args[1]
        if isinstance(value, ast.Lambda):
            return ast.get_source_segment(source, value.body) or ""
        return ast.get_source_segment(source, value) or ""
    return ""


def _affected_blocks(
    tree: ast.Module, target: str
) -> list[tuple[ast.AST, bool, list[ast.stmt | ast.expr]]]:
    """The `with` blocks whose patch usage must be removed.

    The bool says whether the whole `with` disappears (its only item was the patch), in which
    case the body is dedented; otherwise only the patch item is taken out of the group.
    `monkeypatch.setattr("<target>", ...)` statements are reported as single entries, with the
    statement itself as the only item.
    """
    out: list[tuple[ast.AST, bool, list[ast.stmt | ast.expr]]] = []
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            items: list[ast.stmt | ast.expr] = [
                item.context_expr
                for item in node.items
                if _is_patch_of(item.context_expr, target)
            ]
            if items:
                out.append((node, len(items) == len(node.items), items))
        elif isinstance(node, ast.Call) and _is_setattr_of(node, target):
            scope = parents.get(node, node)
            out.append((scope, True, [node]))
    return out


def _insertions(
    tree: ast.Module,
    names: list[str],
    expr: str,
    position: str,
    keyword: str,
    only_in: list[ast.AST] | None = None,
) -> list[tuple[int, int, str]]:
    inside = {id(block) for block in only_in} if only_in is not None else None
    out: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if inside is not None:
            enclosing = None
            for block in only_in or []:
                if any(sub is node for sub in ast.walk(block)):
                    enclosing = block
                    break
            if enclosing is None or id(enclosing) not in inside:
                continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else (func.attr if isinstance(func, ast.Attribute) else None)
        )
        if name not in names:
            continue
        if keyword and any(kw.arg == keyword for kw in node.keywords):
            continue
        if keyword:
            last = (
                node.keywords[-1]
                if node.keywords
                else (node.args[-1] if node.args else None)
            )
            snippet = f", {keyword}={expr}" if last else f"{keyword}={expr}"
            pos = (
                (last.end_lineno or 0, last.end_col_offset or 0)
                if last
                else (
                    node.lineno,
                    (node.func.end_col_offset or 0) + 1,
                )
            )
        elif node.args and position == "after-first":
            first = node.args[0]
            pos = (first.end_lineno or 0, first.end_col_offset or 0)
            snippet = f", {expr}"
        else:
            pos = (node.lineno, (node.func.end_col_offset or 0) + 1)
            snippet = expr if not (node.args or node.keywords) else f"{expr}, "
        out.append((pos[0], pos[1], snippet))
    return out


def _param_insertions(tree: ast.Module, param: str) -> list[tuple[int, int, str]]:
    """Positions where `param` must be added to a test function that uses it."""
    out: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        declared = {a.arg for a in node.args.args + node.args.kwonlyargs}
        if param in declared:
            continue
        used = any(isinstance(n, ast.Name) and n.id == param for n in ast.walk(node))
        if not used:
            continue
        out.append(_signature_position(node, param))
    return out


def _signature_position(
    node: ast.FunctionDef | ast.Lambda, snippet: str
) -> tuple[int, int, str]:
    """Where `param` is appended to a function signature.

    The insertion point is the end of the last declared parameter, including its default when
    it has one; `ast.arg.end_col_offset` stops at the annotation, so the default is read from
    the matching entry of `arguments.defaults` / `arguments.kw_defaults`.
    """
    args = node.args
    positional = args.args
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults))
    defaults += list(args.defaults)
    entries: list[tuple[ast.arg, ast.expr | None]] = list(
        zip(positional, defaults, strict=True)
    )
    entries += list(zip(args.kwonlyargs, args.kw_defaults, strict=True))
    if not entries:
        if isinstance(node, ast.FunctionDef):
            head = len("def ") + len(node.name)
        else:
            head = len("lambda")
        return (node.lineno, node.col_offset + head, f"({snippet})")
    target, default = entries[-1]
    pos = (target.end_lineno or 0, target.end_col_offset or 0)
    if default and default.end_col_offset:
        if (default.lineno, default.end_col_offset) > pos:
            pos = (default.lineno, default.end_col_offset)
    return (pos[0], pos[1], f", {snippet}")


def _side_effect_lambdas(tree: ast.Module) -> set[int]:
    """The ids of lambdas used as `side_effect=` of a patch() call.

    Direct `side_effect=lambda ...` is the common shape; a lambda first bound to a name and
    then named in `side_effect=<name>` is the same case, so both are matched.
    """
    bound: dict[str, ast.Lambda] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bound[target.id] = node.value
    out: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "patch"):
            continue
        for kw in node.keywords:
            if kw.arg != "side_effect":
                continue
            if isinstance(kw.value, ast.Lambda):
                out.add(id(kw.value))
            elif isinstance(kw.value, ast.Name) and kw.value.id in bound:
                out.add(id(bound[kw.value.id]))
    return out


def _accept_param_insertions(
    tree: ast.Module, param: str, names: list[str]
) -> list[tuple[int, int, str]]:
    """Positions where `param=None` must be added to a named function that does not take it.

    Named functions are matched by `--call-names`; the anonymous lambdas passed as
    `side_effect=lambda ...` are matched by position, because they are the same shape: the
    patched callable now receives the typed configuration as an extra keyword the stub ignores.
    """
    out: list[tuple[int, int, str]] = []
    side_effects = _side_effect_lambdas(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.Lambda)):
            continue
        declared = {a.arg for a in node.args.args + node.args.kwonlyargs}
        if param in declared:
            continue
        if isinstance(node, ast.FunctionDef):
            if node.name not in names:
                continue
            out.append(_signature_position(node, f"{param}=None"))
        elif isinstance(node, ast.Lambda) and id(node) in side_effects:
            if node.args.args or node.args.kwonlyargs:
                out.append(_signature_position(node, f"{param}=None"))
            else:
                out.append(
                    (node.lineno, node.col_offset + len("lambda"), f"({param}=None)")
                )
    return out


def _last_import_line(tree: ast.Module) -> int:
    """The last line of the last top-level import block (1-based)."""
    last = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last = max(last, node.end_lineno or node.lineno)
    return last


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--file", required=True)
    parser.add_argument("--call-names", required=True)
    parser.add_argument("--expr", required=True)
    parser.add_argument("--position", choices=["first", "after-first"], default="first")
    parser.add_argument("--keyword", default="", help="insert as this keyword instead")
    parser.add_argument(
        "--add-param",
        default="",
        help="declare this fixture name on the test functions that use it",
    )
    parser.add_argument(
        "--accept-param",
        default="",
        help="declare `NAME=None` on the functions named by --call-names that do not take it",
    )
    parser.add_argument(
        "--definitions-only",
        action="store_true",
        help="apply the change only to function definitions, not to call sites",
    )
    parser.add_argument(
        "--drop-patch",
        default="",
        help='remove every patch("<TARGET>") usage, e.g. db.helper.build_db_config',
    )
    parser.add_argument(
        "--hoist-into",
        default="",
        help="bind the patched expression to this name instead of dropping the patch",
    )
    parser.add_argument(
        "--import-module",
        default="",
        help="also add `from <module> import <expr>` after the last top-level import",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.file) if Path(args.file).is_absolute() else ROOT / args.file
    names = [c for c in args.call_names.split(",") if c]
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    blocks = _affected_blocks(tree, args.drop_patch) if args.drop_patch else []
    insertions = (
        _insertions(
            tree,
            names,
            args.expr,
            args.position,
            args.keyword,
            only_in=[block for block, _, _ in blocks] or None,
        )
        if not args.definitions_only
        else []
    )
    if args.add_param:
        insertions += _param_insertions(tree, args.add_param)
    if args.accept_param:
        insertions += _accept_param_insertions(tree, args.accept_param, names)
    if not insertions and not blocks:
        print(f"{path.relative_to(ROOT)}: nothing matched")
        return 1

    lines = text.splitlines(keepends=True)
    for lineno, col, snippet in sorted(insertions, key=lambda i: (-i[0], -i[1])):
        idx = lineno - 1
        lines[idx] = lines[idx][:col] + snippet + lines[idx][col:]

    drop = [False] * len(lines)
    dedent: set[int] = set()
    hoist: dict[int, str] = {}
    for block, whole, items in blocks:
        for item in items:
            if args.hoist_into:
                value = _patch_value_source(text, item)
                if value and not value.isidentifier():
                    hoist[item.lineno - 1] = (
                        " " * getattr(block, "col_offset", 0)
                        + f"{args.hoist_into} = {value}\n"
                    )
            for idx in range(item.lineno - 1, item.end_lineno or item.lineno):
                drop[idx] = True
        if whole and isinstance(block, ast.With):
            for idx in range(block.lineno - 1, block.body[0].lineno - 1):
                drop[idx] = True
            end = max(
                stmt.end_lineno or stmt.lineno
                for stmt in block.body
                if hasattr(stmt, "end_lineno")
            )
            dedent.update(range(block.body[0].lineno - 1, end))

    out = []
    import_after = _last_import_line(tree) if args.import_module else -1
    for idx, line in enumerate(lines):
        if idx in hoist:
            out.append(hoist[idx])
        if drop[idx]:
            continue
        if idx in dedent:
            line = line[4:] if line.startswith("    ") else line
        out.append(line)
        if args.import_module and idx == import_after:
            out.append(f"\nfrom {args.import_module} import {args.expr}\n")
    result = "".join(out)
    if args.dry_run:
        print(result)
    else:
        path.write_text(result, encoding="utf-8")
    print(
        f"{path.relative_to(ROOT)}: {len(insertions)} insertion(s), "
        f"{sum(drop)} line(s) removed, {len(hoist)} hoisted",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
