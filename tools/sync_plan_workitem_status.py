#!/usr/bin/env python3
"""tools/sync_plan_workitem_status.py - Mark Plan Work Items rows Completed for archived procedures.

The batch workflow archives each procedure document to `implementations/done/` after
its own Execution Status is recorded. The owning Plan's `### Work Items Created`
table then still shows the procedure row as `Pending`. This tool reconciles the two:
every Work Items row whose Item ID names a procedure file that already exists under
`implementations/done/` is set to `Completed`. Rows for files still under
`implementations/` are left untouched. It writes no other column and never marks a
row Completed for a file that is not archived.

Usage:
    python tools/sync_plan_workitem_status.py PLAN.md [--dry-run]

Output: one line per changed row, then a summary. Exit 0 when the plan parses.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DONE_DIR = REPO / "implementations" / "done"

WORK_ITEMS_HEADING = "### Work Items Created"


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(
            "usage: sync_plan_workitem_status.py PLAN.md [--dry-run]", file=sys.stderr
        )
        return 2
    plan = Path(args[0])
    if not plan.is_file():
        print(f"plan not found: {plan}", file=sys.stderr)
        return 2

    lines = plan.read_text(encoding="utf-8").splitlines()
    try:
        start = next(
            i for i, ln in enumerate(lines) if ln.strip() == WORK_ITEMS_HEADING
        )
    except StopIteration:
        print(f"heading not found in {plan}: {WORK_ITEMS_HEADING}", file=sys.stderr)
        return 2

    # Locate the Status column from the table header that follows the heading.
    header_idx = next(
        i for i in range(start + 1, len(lines)) if lines[i].startswith("| Item ID")
    )
    header_cells = [c.strip() for c in lines[header_idx].strip().strip("|").split("|")]
    status_col = header_cells.index("Status")

    changed = 0
    for i in range(header_idx + 2, len(lines)):  # skip separator row
        ln = lines[i]
        if not ln.startswith("|"):
            break
        raw_cells = ln.strip().strip("|").split("|")
        if len(raw_cells) <= status_col:
            continue
        cells = [c.strip() for c in raw_cells]
        if cells[status_col] != "Pending":
            continue
        item = cells[0].strip("`").strip()
        name = Path(item).name
        if not (DONE_DIR / name).is_file():
            continue
        raw_cells[status_col] = " Completed "
        lines[i] = "|" + "|".join(raw_cells) + "|"
        changed += 1
        print(f"Completed: {name}")

    print(f"{'dry-run: would change' if dry else 'marked Completed'}: {changed} row(s)")
    if not dry and changed:
        plan.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
