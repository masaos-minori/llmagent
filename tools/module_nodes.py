#!/usr/bin/env python3
"""tools/module_nodes.py — Measure, move, and verify top-level nodes for Path C module splits.

Merged from measure_module_nodes.py, extract_module_nodes.py and compare_moved_nodes.py,
which were three steps of one workflow: size the clusters, move them, prove the move
changed nothing.

Usage:
    uv run python tools/module_nodes.py measure <src> [--min N] [--json]
    uv run python tools/module_nodes.py extract --src SRC --dest DEST \
        [--name NAME ...] [--range START-END ...] [--dedent]
    uv run python tools/module_nodes.py compare --old-src PATH --new-src PATH \
        --name NAME [--name NAME ...] [--old-class CLASS] [--old-rev REV] [--param P ...]

measure: report the 1-based line span and encoded byte size of every top-level node, so a
module's size is traced to specific clusters. Read-only.

extract: move the exact source ranges of named top-level classes and functions, or explicit
line spans, from --src into --dest (appended, created when absent). The moved code is the
original text: the tool slices original lines and never rewrites them. `--range START-END`
is how a method inside a class is moved out as a span; `--dedent` removes one 4-space indent
level from every moved line so a moved method becomes a module-level function (refuses when a
moved line is indented by less than 4 spaces). Import cleanup, `self` removal, formatting and
call/test repointing stay with the caller. Exit 1 when a name is not a top-level class or
function of --src.

compare: normalize the transformations an extraction may make (a method loses `self`, a
private name may drop its leading underscore, an attribute read may become an injected
parameter, docstrings are re-indented) and report whether every named function is identical
to its pre-move source read from git. Parameters are listed but not compared. Exit 1 on any
difference. Read-only.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import subprocess  # nosec B404 — git is a trusted local CLI, argv is a fixed list
import sys

_MOVED_NODE = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


# --- measure ---


def measure(path: pathlib.Path, min_bytes: int) -> list[dict[str, object]]:
    """Return the line span and byte size of each top-level non-import node of `path`."""
    src = path.read_text(encoding="utf-8").splitlines()
    tree = ast.parse("".join(line + "\n" for line in src))
    rows: list[dict[str, object]] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        start = node.lineno
        end = node.end_lineno or start
        size = len("\n".join(src[start - 1 : end]).encode("utf-8"))
        if size < min_bytes:
            continue
        rows.append(
            {
                "name": getattr(node, "name", type(node).__name__),
                "start": start,
                "end": end,
                "span": end - start + 1,
                "bytes": size,
                "kind": type(node).__name__,
            }
        )
    return rows


def _cmd_measure(args: argparse.Namespace) -> int:
    if not args.src.is_file():
        print(f"{args.src}: not found", file=sys.stderr)
        return 1
    rows = measure(args.src, args.min)
    if args.json:
        print(json.dumps(rows))
        return 0
    total = len(args.src.read_bytes())
    for row in rows:
        print(
            f"{row['start']:>5}-{row['end']:<5} {row['bytes']:>6}B  {row['kind']:<14} "
            f"{row['name']}"
        )
    print(f"file total: {total}B")
    return 0


# --- extract ---


def _node_index(tree: ast.Module) -> dict[str, tuple[int, int]]:
    """Map each top-level class/function name to its 1-based (start, end) line range."""
    index: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, _MOVED_NODE):
            index[node.name] = (node.lineno, node.end_lineno or node.lineno)
    return index


def _parse_range(raw: str) -> tuple[int, int]:
    """Parse a `START-END` 1-based inclusive line span."""
    try:
        start_raw, end_raw = raw.split("-", 1)
        start, end = int(start_raw), int(end_raw)
    except ValueError:
        raise SystemExit(f"ERROR: --range expects START-END, got {raw!r}") from None
    if start < 1 or end < start:
        raise SystemExit(f"ERROR: invalid --range {raw!r}")
    return start, end


def _dedent_segment(segment: str, src: pathlib.Path, start: int) -> str:
    """Remove one 4-space indent level from every non-blank line of a moved span."""
    out: list[str] = []
    for offset, line in enumerate(segment.splitlines(keepends=True)):
        text = line.rstrip("\r\n")
        if text.strip() == "":
            out.append(line)
            continue
        if not text.startswith("    ") or text.startswith("\t"):
            msg = f"{src}:{start + offset}: expected a 4-space indent, got {text!r}"
            raise SystemExit(f"ERROR: cannot --dedent {msg}")
        out.append(line[4:])
    return "".join(out)


def _extract_lines(
    src: pathlib.Path,
    names: list[str],
    ranges: list[tuple[int, int]],
    dedent: bool,
) -> tuple[list[str], list[str]]:
    """Return (kept_lines, moved_segments): src lines without the moved nodes, and each
    moved span's exact original lines, in the order requested."""
    lines = src.read_text().splitlines(keepends=True)
    index = _node_index(ast.parse(src.read_text()))
    missing = [name for name in names if name not in index]
    if missing:
        msg = ", ".join(missing)
        raise SystemExit(f"ERROR: not top-level nodes of {src}: {msg}")
    spans = [index[name] for name in names] + list(ranges)
    moved_segments = []
    for start, end in spans:
        segment = "".join(lines[start - 1 : end])
        moved_segments.append(
            _dedent_segment(segment, src, start) if dedent else segment
        )
    drop: set[int] = set()
    for start, end in spans:
        drop.update(range(start, end + 1))
    kept_lines = [line for i, line in enumerate(lines, start=1) if i not in drop]
    return kept_lines, moved_segments


def _cmd_extract(args: argparse.Namespace) -> int:
    if not args.names and not args.range_args:
        raise SystemExit("ERROR: pass at least one --name or --range")
    ranges = [_parse_range(raw) for raw in args.range_args]

    kept_lines, moved_segments = _extract_lines(
        args.src, args.names, ranges, args.dedent
    )

    dest_existing = args.dest.read_text() if args.dest.exists() else ""
    joined = dest_existing.rstrip("\n")
    body = "\n\n\n".join(segment.rstrip("\n") for segment in moved_segments)
    dest_code = f"{joined}\n\n\n{body}\n" if joined else f"{body}\n"
    args.dest.write_text(dest_code)
    args.src.write_text("".join(kept_lines))

    moved = args.names + [f"lines {start}-{end}" for start, end in ranges]
    print(f"moved {len(moved)} nodes -> {args.dest}")
    for label in moved:
        print(f"  {label}")
    for path in (args.src, args.dest):
        print(
            f"{path}: {len(path.read_text().splitlines())} lines, {path.stat().st_size} B"
        )
    return 0


# --- compare ---


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


def _cmd_compare(args: argparse.Namespace) -> int:
    old_src = subprocess.run(  # nosec B603 B607 — fixed argv, git is a trusted local CLI
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
    for name in args.names:
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
    print(f"moved functions compared: {len(args.names)}, differing: {failed}")
    return 1 if failed else 0


# --- CLI ---


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_measure = sub.add_parser("measure", help="line span and byte size per node")
    p_measure.add_argument("src", type=pathlib.Path)
    p_measure.add_argument(
        "--min", type=int, default=0, help="skip nodes smaller than N bytes"
    )
    p_measure.add_argument("--json", action="store_true", help="emit JSON")
    p_measure.set_defaults(func=_cmd_measure)

    p_extract = sub.add_parser("extract", help="move nodes between modules verbatim")
    p_extract.add_argument("--src", required=True, type=pathlib.Path)
    p_extract.add_argument("--dest", required=True, type=pathlib.Path)
    p_extract.add_argument("--name", action="append", default=[], dest="names")
    p_extract.add_argument("--range", action="append", default=[], dest="range_args")
    p_extract.add_argument(
        "--dedent",
        action="store_true",
        help="remove one 4-space indent level from the moved lines",
    )
    p_extract.set_defaults(func=_cmd_extract)

    p_compare = sub.add_parser("compare", help="verify moved functions are unchanged")
    p_compare.add_argument(
        "--old-rev", default="HEAD", help="git revision to read --old-src from"
    )
    p_compare.add_argument("--old-src", required=True)
    p_compare.add_argument(
        "--old-class", default=None, help="class the moved methods lived in"
    )
    p_compare.add_argument("--new-src", required=True)
    p_compare.add_argument(
        "--name", action="append", required=True, dest="names", help="moved function"
    )
    p_compare.add_argument(
        "--param",
        action="append",
        default=[],
        help="configuration the method read from self, now passed by the caller",
    )
    p_compare.set_defaults(func=_cmd_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch to the measure / extract / compare subcommand."""
    args = _build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
