#!/usr/bin/env python3
"""Measure the source span and byte size of every top-level node in a module.

Used to size a module's clusters before choosing a split unit, and to confirm the
split after extraction. Reports the 1-based line span and the encoded size of each
top-level node, so a target file's size can be traced to specific clusters.

Usage:
    uv run python tools/measure_module_nodes.py <src> [--min N] [--json]
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def measure(path: Path, min_bytes: int) -> list[dict[str, object]]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("src", type=Path)
    parser.add_argument(
        "--min", type=int, default=0, help="skip nodes smaller than N bytes"
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

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


if __name__ == "__main__":
    sys.exit(main())
