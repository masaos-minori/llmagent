#!/usr/bin/env python3
"""Normalize a Plan's Implementation Target Files Related Tests cells to backticked paths.

tools/check_workitem_traceability.py reads Related Tests cells through a backticked-path
regex, so companion eligibility requires each named test path to be backticked. This
script adds backticks around test paths in Related Tests cells without changing the
cell's content (Plan Freeze content is unchanged; only the delimiter is added).

Usage: uv run python tools/backtick_plan_related_tests.py plans/<plan>.md
"""

import re
import sys
from pathlib import Path

ROW_RE = re.compile(r"^\| (?P<path>[^|]+) \|")


def main() -> int:
    plan = Path(sys.argv[1])
    lines = plan.read_text(encoding="utf-8").split("\n")
    changed = 0
    for i, line in enumerate(lines):
        if not ROW_RE.match(line):
            continue
        cells = line.split("|")
        if len(cells) < 8:
            continue
        tests = cells[6]
        if tests.strip() == "—" or "`" in tests:
            continue
        backticked = ", ".join(
            "`" + t.strip() + "`" for t in tests.split(",") if t.strip() != "—"
        )
        if not backticked:
            continue
        cells[6] = f" {backticked} "
        lines[i] = "|".join(cells)
        changed += 1
    plan.write_text("\n".join(lines), encoding="utf-8")
    print(f"backticked Related Tests cells in {changed} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
