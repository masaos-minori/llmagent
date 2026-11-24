#!/usr/bin/env python
"""Adversarial verification helper: print cited source lines from a Plan.

Extracts `path:LINE` and `path:LINE-LINE` citations from a plan document and
prints the corresponding lines from the current repository state so each claim
can be compared against the source. Read-only tool; run at
plan-to-implementation-procedure Step 3a.

Usage:
    uv run python tools/check_plan_citations.py plans/<plan>.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CITE = re.compile(
    r"`([A-Za-z0-9_./-]+\.(?:py|json|toml|md|yaml|sql)):(\d+)(?:-(\d+))?`"
)


def main() -> int:
    plan = Path(sys.argv[1])
    text = plan.read_text(encoding="utf-8")
    seen: set[tuple[str, str]] = set()
    findings = 0
    for match in CITE.finditer(text):
        path, start, end = match.group(1), int(match.group(2)), match.group(3)
        key = (path, match.group(0))
        if key in seen:
            continue
        seen.add(key)
        src = Path(path)
        if not src.exists():
            print(f"MISSING FILE: {path}")
            findings += 1
            continue
        lines = src.read_text(encoding="utf-8").splitlines()
        if start > len(lines):
            print(f"OUT OF RANGE: {path}:{start} (file has {len(lines)} lines)")
            findings += 1
            continue
        stop = min(int(end) if end else start, len(lines))
        print(f"--- {path}:{start}-{stop} ({len(lines)} lines total)")
        for n in range(start, stop + 1):
            print(f"  {n}: {lines[n - 1]}")
    return findings


if __name__ == "__main__":
    sys.exit(main())
