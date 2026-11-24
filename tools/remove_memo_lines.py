#!/usr/bin/env python3
"""tools/remove_memo_lines.py — Remove a completed procedure's line from a work list.

A memo file lists the procedure documents to execute. The instruction in that file is to
remove the line of each document once its work is complete, which is the same operation
repeated once per procedure across a batch, so it is kept as a tool rather than edited by
hand.

- A line is removed when it names one of the given paths as a whole path, so a line about
  a different document with a similar name is not touched.
- A path no line names is reported and nothing is written: the document may have been
  removed already, and a silent skip would hide a typo in the path.
- `--dry-run` prints the diff and writes nothing.

Usage:
    uv run python tools/remove_memo_lines.py memo3.md --path implementations/foo.py.md
    uv run python tools/remove_memo_lines.py memo3.md --dry-run --path implementations/foo.py.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run


def _matches(line: str, path: str) -> bool:
    """True when the line names `path` as a whole path, not as a substring of a longer one."""
    start = line.find(path)
    if start < 0:
        return False
    end = start + len(path)
    prev, nxt = line[start - 1 : start], line[end : end + 1]
    if prev and not prev.isspace():
        return False
    return not nxt or nxt.isspace()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("memo", help="path to the work-list .md file")
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="procedure path whose line is removed (repeatable)",
    )
    add_dry_run_argument(parser)
    args = parser.parse_args(argv)

    memo = Path(args.memo)
    if not memo.is_file():
        print(f"memo file not found: {memo}", file=sys.stderr)
        return 2

    text = memo.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    removed: list[tuple[str, str]] = []
    for line in lines:
        path = next((p for p in args.path if _matches(line, p)), None)
        if path is None:
            kept.append(line)
        else:
            removed.append((path, line))

    for path in args.path:
        if not any(p == path for p, _ in removed):
            print(f"no line names {path}; nothing removed", file=sys.stderr)
            return 1

    new = "".join(kept)
    if args.dry_run:
        print_dry_run(memo, text, new)
        return 0

    atomic_write_text(memo, new)
    for _, line in removed:
        print(f"removed: {line.rstrip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
