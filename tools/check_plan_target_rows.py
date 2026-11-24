#!/usr/bin/env python
"""Report companion-test coverage and duplicate rows in a Plan's target table.

Reads a plan's `Implementation Target Files` table and reports, per row:
- its position (seq), file path, and Related Tests cell,
- whether the test row qualifies as a companion of exactly one code row
  (`plan-to-implementation-procedure` Core Execution Rules),
- rows that name the same file more than once.

Read-only analysis tool for plan-to-implementation-procedure Step 3.

Usage:
    uv run python tools/check_plan_target_rows.py plans/<plan>.md
"""

from __future__ import annotations

import sys
from pathlib import Path


def parse_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("## Implementation Target Files"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 7 or cells[0] == "File Path" or set(cells[0]) <= {"-"}:
            continue
        rows.append(
            {
                "seq": str(len(rows)),
                "path": cells[0],
                "tests": cells[5],
                "requirement": cells[3],
            }
        )
    return rows


def main() -> int:
    rows = parse_rows(Path(sys.argv[1]).read_text(encoding="utf-8"))
    named_by: dict[str, list[str]] = {}
    for row in rows:
        for test in [t.strip().strip("`") for t in row["tests"].split(",")]:
            if test and test != "itself" and test.startswith("tests/"):
                named_by.setdefault(test, []).append(row["seq"])

    print(f"rows: {len(rows)}")
    duplicates: dict[str, list[str]] = {}
    for row in rows:
        duplicates.setdefault(row["path"], []).append(row["seq"])

    companion_count = 0
    for row in rows:
        if not row["path"].startswith("tests/"):
            continue
        refs = named_by.get(row["path"], [])
        if len(refs) == 1:
            companion_count += 1
            print(f"companion: seq {row['seq']} {row['path']} <- row {refs[0]}")
    print(f"companion test rows: {companion_count}")
    print(f"documents to generate: {len(rows) - companion_count}")
    for path, seqs in duplicates.items():
        if len(seqs) > 1:
            print(f"duplicate rows: {path} at {', '.join(seqs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
