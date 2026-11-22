#!/usr/bin/env python3
"""summarize_pytest_failures.py — Group a pytest report by test file and failure cause.

Plan agentcfg004 RU-2 touches call sites across many test files, so the same read of a
report is repeated while the suite is being brought back to green. This script answers two
questions for a saved pytest output file:

  - which test files have failures, and how many
  - what the distinct `E   ` lines are, so one mechanical cause can be fixed once

It only reads the report; it does not run pytest, and it does not change any file.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ENTRY = re.compile(r"^(FAILED|ERROR) (tests/[^:]+\.py)::")
BLOCK = re.compile(r"^_{5,} [^\n]*_{5,}\n(.*?)(?=^_{5,} |\Z)", re.M | re.S)


def normalize(line: str) -> str:
    """Fold values that vary per run so identical causes group together."""
    line = re.sub(r"id='\w+'", "id=N", line)
    line = re.sub(r"\b\d+\b", "N", line)
    return line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("report", help="saved pytest output file")
    parser.add_argument(
        "--group-by",
        choices=["file", "cause"],
        default="file",
        help="how to order the counts (default: file)",
    )
    parser.add_argument("--limit", type=int, default=40, help="rows to show")
    args = parser.parse_args(argv)

    text = Path(args.report).read_text(errors="replace")
    per_file: Counter[str] = Counter()
    causes: Counter[tuple[str, str]] = Counter()

    for line in text.splitlines():
        m = ENTRY.match(line)
        if m:
            per_file[m.group(2)] += 1

    for match in BLOCK.finditer(text):
        body = match.group(1)
        # The block header does not name the file; the traceback does.
        target = re.search(r"^(tests/[\w/.]+\.py):\d+: in", body, re.M)
        if not target:
            continue
        errors = [
            normalize(line) for line in body.splitlines() if line.startswith("E   ")
        ]
        if not errors:
            continue
        causes[(target.group(1), errors[-1])] += 1

    order = causes if args.group_by == "cause" else None
    if order:
        for (file, cause), count in order.most_common(args.limit):
            print(f"{count:5d}  {file}  {cause[:120]}")
    else:
        for file, count in per_file.most_common(args.limit):
            print(f"{count:5d}  {file}")

    print(f"entries: {sum(per_file.values())} in {len(per_file)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
