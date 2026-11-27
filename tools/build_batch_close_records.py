#!/usr/bin/env python3
"""tools/build_batch_close_records.py - Builds the records file for a batch step-status update.

Reads each procedure document's `### Execution Status` table and writes one
`set_step_status_batch.py` record per unfinished row:

- rows 1-3 become `Completed`, keeping the row's existing Notes;
- a row 4 (documentation) becomes `N/A` when no documentation row matched its scope;
- the gates row's Notes gain the end-of-batch full-suite and coverage result passed with
  `--suite`, replacing the `awaiting end-of-batch full suite` placeholder when one is present.

The tool builds a records file only; it applies nothing. `set_step_status_batch.py` is the tool
that writes the work item tables, and `close_procedures_batch.py` stays the tool that gates an
archive on the rows.

Usage:
    python tools/build_batch_close_records.py --out RECORDS.json --suite TEXT PROC.md ...

Exit codes: 0 when every procedure contributed at least one record, 1 when a file is missing or
unreadable or a procedure has no unfinished row, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TypedDict

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text

ROW_RE = r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$"

UNFINISHED = {"Pending", "In Progress", "Blocked"}


class Record(TypedDict):
    """One `set_step_status_batch.py` record."""

    path: str
    kind: str
    step: int
    status: str
    notes: str


def build(path: Path, suite: str) -> list[Record]:
    """The records for one procedure's unfinished Execution Status rows."""
    records: list[Record] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(ROW_RE, line)
        if not m:
            continue
        step, description, status, _started, _completed, notes = m.groups()
        if status not in UNFINISHED:
            continue
        step_no = int(step)
        if step_no == 4:
            records.append(
                {
                    "path": str(path),
                    "kind": "implementation-procedure",
                    "step": step_no,
                    "status": "N/A",
                    "notes": "no documentation row matched this procedure's scope",
                }
            )
            continue
        note = "" if notes == "—" else notes
        if "gate" in description.lower():
            pending = "awaiting end-of-batch full suite"
            if pending in note:
                note = note.replace(f"; {pending}", "").replace(pending, "").strip("; ")
                note = f"{note}; {suite}".strip("; ")
            else:
                note = f"{note}; {suite}".strip("; ")
        records.append(
            {
                "path": str(path),
                "kind": "implementation-procedure",
                "step": step_no,
                "status": "Completed",
                "notes": note,
            }
        )
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--suite", required=True, help="row 3 Notes suffix: the batch suite result"
    )
    ap.add_argument("procedures", nargs="+")
    args = ap.parse_args()

    records: list[Record] = []
    failed = False
    for proc in args.procedures:
        path = Path(proc)
        try:
            found = build(path, args.suite)
        except OSError as exc:
            print(f"{proc}: {exc}", file=sys.stderr)
            failed = True
            continue
        if not found:
            print(f"{proc}: no unfinished row", file=sys.stderr)
            failed = True
            continue
        records.extend(found)

    if not records:
        return 1
    atomic_write_text(
        Path(args.out), json.dumps(records, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Wrote {len(records)} records to {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
