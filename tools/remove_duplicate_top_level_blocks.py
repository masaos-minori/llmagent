#!/usr/bin/env python3
"""remove_duplicate_top_level_blocks.py — Delete a duplicated top-level definition.

`restore_test_preamble.py` inserts HEAD's top-level statements into a test file. A definition the
task rewrote instead of deleting is then present twice: HEAD's version and the task's version. For
every top-level name defined more than once in the given test file, this tool removes the occurrence
whose source matches HEAD's after whitespace collapsing — the inserted one — and keeps the file's own
version. When no occurrence matches exactly, a single near-identical one (95% similar) is treated as
the inserted block, because an earlier formatting pass can differ from HEAD only in layout.

`--dry-run` prints the removed blocks.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def head_text(path: Path) -> str:
    return subprocess.run(
        ["git", "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def name_of(node: ast.stmt) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def segment(source: str, node: ast.AST) -> str:
    """Source text of a node; get_source_segment is Optional in the type stubs."""
    return ast.get_source_segment(source, node) or ""


def block_range(node: ast.stmt) -> tuple[int, int]:
    """Line span of a top-level definition, including its decorators."""
    decorators: list[ast.expr] = getattr(node, "decorator_list", [])
    start = min([node.lineno] + [dec.lineno for dec in decorators])
    return start - 1, node.end_lineno or node.lineno


def normalized(segment: str) -> str:
    """Whitespace-collapsed source, so a reformat is not read as a different definition."""
    return "".join(segment.split())


def duplicate_blocks(text: str, original: str) -> list[tuple[int, int]]:
    """Span of the occurrence that matches HEAD, for every top-level name defined twice."""
    head_sources: dict[str, str] = {}
    head_tree = ast.parse(original)
    for node in head_tree.body:
        name = name_of(node)
        if name:
            head_sources[name] = normalized(segment(original, node))

    tree = ast.parse(text)
    by_name: dict[str, list[ast.stmt]] = defaultdict(list)
    for node in tree.body:
        name = name_of(node)
        if name:
            by_name[name].append(node)

    out: list[tuple[int, int]] = []
    for name, nodes in by_name.items():
        if len(nodes) < 2:
            continue
        head = head_sources.get(name)
        if head is None:
            continue
        exact = [node for node in nodes if normalized(segment(text, node)) == head]
        if exact:
            out.append(block_range(exact[0]))
            continue
        # The inserted copy can differ from HEAD only by the formatting an earlier pass applied,
        # so a near-identical occurrence is the inserted one when the other is the file's own rewrite.
        fuzzy = [
            node
            for node in nodes
            if SequenceMatcher(None, head, normalized(segment(text, node))).ratio()
            >= 0.95
        ]
        if len(fuzzy) == 1:
            out.append(block_range(fuzzy[0]))
    return out


def remove(text: str, original: str) -> tuple[str, int]:
    blocks = duplicate_blocks(text, original)
    if not blocks:
        return text, 0
    lines = text.splitlines(keepends=True)
    out = [
        line
        for idx, line in enumerate(lines)
        if not any(start <= idx < end for start, end in blocks)
    ]
    return "".join(out), len(blocks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total = 0
    for name in args.files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        text = path.read_text(encoding="utf-8")
        try:
            result, removed = remove(text, head_text(path))
        except SyntaxError as exc:
            print(f"{path.relative_to(ROOT)}: skipped ({exc})", file=sys.stderr)
            continue
        if not removed:
            print(f"{path.relative_to(ROOT)}: no duplicate definition")
            continue
        if not args.dry_run:
            path.write_text(result, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {removed} block(s) removed", file=sys.stderr)
        total += removed
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
