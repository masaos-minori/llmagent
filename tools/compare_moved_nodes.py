#!/usr/bin/env python3
"""Compare an extracted module's moved functions against their pre-move source.

Normalizes the transformations a module extraction is allowed to make — a method loses
`self`, a private name may drop its leading underscore, an attribute read may become an
injected parameter, and docstrings are re-indented — then reports whether every remaining
node is identical. Parameters are listed but not compared: an extracted guard takes the
configuration its caller used to read from `self`.

Usage:
    python tools/compare_moved_nodes.py --old-src PATH --new-src PATH --name NAME \
        [--name NAME ...] [--old-class CLASS] [--old-rev REV]
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys


def _norm_name(name: str) -> str:
    return name.lstrip("_")


class _SelfToName(ast.NodeTransformer):
    """Rewrite `self._attr` reads as bare `attr` names.

    Covers both cases an extraction produces: a `self._method()` call that becomes a
    module-level call, and a `self._config` read that becomes an injected parameter.
    """

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            new = ast.Name(id=node.attr.lstrip("_"), ctx=node.ctx)
            return ast.copy_location(new, node)
        return node


class _DropInjectedArgs(ast.NodeTransformer):
    """Drop call arguments named after an injected configuration parameter.

    The extracted function reads what the method read from `self`, so the caller now
    passes it. Those arguments are the intended change, not a behavior change.
    """

    def __init__(self, names: set[str]) -> None:
        self._names = names

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        node.args = [
            a
            for a in node.args
            if not (isinstance(a, ast.Name) and _norm_name(a.id) in self._names)
        ]
        node.keywords = [
            k for k in node.keywords if not (k.arg and _norm_name(k.arg) in self._names)
        ]
        return node


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
    ):
        if isinstance(body[0].value.value, str):
            return body[1:]
    return body


def _params(node: ast.FunctionDef) -> str:
    args = [
        a.arg for a in node.args.args + node.args.posonlyargs + node.args.kwonlyargs
    ]
    return ", ".join(a for a in args if a != "self")


def _normalize(node: ast.FunctionDef, injected: set[str]) -> str:
    node.args.args = [a for a in node.args.args if a.arg != "self"]
    node.body = _strip_docstring(node.body)
    node.decorator_list = []
    for stmt in node.body:
        _SelfToName().visit(stmt)
        if injected:
            _DropInjectedArgs(injected).visit(stmt)
    ast.fix_missing_locations(node)
    return ast.dump(ast.Module(body=node.body, type_ignores=[]), indent=1)


def _functions(src: str, class_name: str | None) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(src)
    scopes: list[list[ast.stmt]] = [tree.body]
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and (
            class_name is None or node.name == class_name
        ):
            scopes.append(node.body)
    out: dict[str, ast.FunctionDef] = {}
    for scope in scopes:
        for node in scope:
            if isinstance(node, ast.FunctionDef):
                out.setdefault(_norm_name(node.name), node)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--old-rev", default="HEAD", help="git revision to read --old-src from"
    )
    ap.add_argument("--old-src", required=True)
    ap.add_argument(
        "--old-class", default=None, help="class the moved methods lived in"
    )
    ap.add_argument("--new-src", required=True)
    ap.add_argument(
        "--name", action="append", required=True, help="moved function name"
    )
    ap.add_argument(
        "--param",
        action="append",
        default=[],
        help="configuration the method read from self, now passed by the caller",
    )
    args = ap.parse_args()

    old_src = subprocess.run(
        ["git", "show", f"{args.old_rev}:{args.old_src}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    with open(args.new_src, encoding="utf-8") as f:
        new_src = f.read()

    old_funcs = _functions(old_src, args.old_class)
    new_funcs = _functions(new_src, None)
    injected = set(args.param)

    failed = 0
    for name in args.name:
        key = _norm_name(name)
        old, new = old_funcs.get(key), new_funcs.get(key)
        if old is None or new is None:
            print(f"{key:<26} MISSING (old={old is not None}, new={new is not None})")
            failed += 1
            continue
        a, b = _normalize(old, injected), _normalize(new, injected)
        status = "identical" if a == b else "DIFFERS"
        print(f"{key:<26} {status:<9} params: ({_params(old)}) -> ({_params(new)})")
        if a != b:
            failed += 1
            for line_a, line_b in zip(a.splitlines(), b.splitlines()):
                if line_a != line_b:
                    print(f"  old: {line_a.strip()[:150]}")
                    print(f"  new: {line_b.strip()[:150]}")
    print(f"moved functions compared: {len(args.name)}, differing: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
