#!/usr/bin/env python3
"""Bulk-rewrite `record_tool_call` call sites in test files so the argument-hash value is
computed with the production helper instead of a bare dict literal.

Usage:
    python tools/normalize_test_args_hash.py <test-file> [--dry-run]

The helper name is `agent.tool_preparation._canonical_args_hash`, the same function the
production write path uses, so the stored value is comparable in the assertions. A call
site that already passes the helper is left unchanged.

Exit codes: 0 pass, 2 usage or environment error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run

HELPER = "_canonical_args_hash"
CALL_SQL = re.compile(r"store\.record_tool_call\((.*?)\)", re.S)
BARE_DICT = re.compile(r"(?<!\w)(\{\"[^\"]*\"[^{}]*\})")


def normalize(text: str) -> tuple[str, int]:
    """Return the rewritten text and the number of call sites wrapped."""
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        args = match.group(1)
        if HELPER in args:
            return match.group(0)
        new_args = BARE_DICT.sub(lambda m: f"{HELPER}({m.group(1)})", args)
        if new_args != args:
            changed += 1
        return f"store.record_tool_call({new_args})"

    return CALL_SQL.sub(repl, text), changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="test file to rewrite")
    add_dry_run_argument(parser)
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        print(f"not a file: {path}")
        return 2

    before = path.read_text()
    after, count = normalize(before)
    if count == 0:
        print(f"{path}: no call site to wrap")
        return 0
    if args.dry_run:
        print_dry_run(path, before, after)
        return 0
    atomic_write_text(path, after)
    print(f"{path}: {count} call sites wrapped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
