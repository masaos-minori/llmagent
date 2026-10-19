#!/usr/bin/env python3
"""tools/extract_module_nodes.py — Move top-level class/function nodes between modules verbatim.

Moves the exact source ranges of named top-level classes and functions from one Python
module into another (appended to the destination file, created when absent). The moved
code is byte-identical to the original: the tool slices original lines, never rewrites
them. Import cleanup, formatting, and call/test repointing stay with the caller.

Usage:
    uv run python tools/extract_module_nodes.py \
        --src scripts/mcp_servers/mdq/indexer.py \
        --dest scripts/mcp_servers/mdq/index_refresh.py \
        --name RefreshSummary --name _load_index_state ...

Reports moved names, destination order, and post-move line/byte counts. Exit 1 when a
name is not a top-level class or function of --src.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys

_MOVED_NODE = ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


def _node_index(tree: ast.Module) -> dict[str, tuple[int, int]]:
    """Map each top-level class/function name to its 1-based (start, end) line range."""
    index: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, _MOVED_NODE):
            index[node.name] = (node.lineno, node.end_lineno or node.lineno)
    return index


def _extract_lines(src: pathlib.Path, names: list[str]) -> tuple[list[str], list[str]]:
    """Return (kept_lines, moved_segments): src lines without the moved nodes, and each
    moved node's exact original lines, in the order requested."""
    lines = src.read_text().splitlines(keepends=True)
    index = _node_index(ast.parse(src.read_text()))
    missing = [name for name in names if name not in index]
    if missing:
        msg = ", ".join(missing)
        raise SystemExit(f"ERROR: not top-level nodes of {src}: {msg}")
    moved_segments = [
        "".join(lines[index[name][0] - 1 : index[name][1]]) for name in names
    ]
    drop: set[int] = set()
    for name in names:
        start, end = index[name]
        drop.update(range(start, end + 1))
    kept_lines = [line for i, line in enumerate(lines, start=1) if i not in drop]
    return kept_lines, moved_segments


def main(argv: list[str] | None = None) -> int:
    """Move the named nodes from --src into --dest; print post-move file sizes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, type=pathlib.Path)
    parser.add_argument("--dest", required=True, type=pathlib.Path)
    parser.add_argument("--name", action="append", required=True, dest="names")
    args = parser.parse_args(argv)

    kept_lines, moved_segments = _extract_lines(args.src, args.names)

    dest_existing = args.dest.read_text() if args.dest.exists() else ""
    joined = dest_existing.rstrip("\n")
    body = "\n\n\n".join(segment.rstrip("\n") for segment in moved_segments)
    dest_code = f"{joined}\n\n\n{body}\n" if joined else f"{body}\n"
    args.dest.write_text(dest_code)
    args.src.write_text("".join(kept_lines))

    print(f"moved {len(args.names)} nodes -> {args.dest}")
    for name in args.names:
        print(f"  {name}")
    for path in (args.src, args.dest):
        print(
            f"{path}: {len(path.read_text().splitlines())} lines, {path.stat().st_size} B"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
