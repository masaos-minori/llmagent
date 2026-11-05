#!/usr/bin/env python3
"""Batch-update Execution Status rows of an implementation procedure document.

Thin wrapper around tools/manage_workitem_stage.py set-step-status so a cycle
can update several rows in one call. Timestamps are stamped automatically:
'In Progress' sets Started, 'Completed' sets Completed (and Started if unset).

Usage:
  uv run python tools/proc_step_status.py PROC --update "STEP:STATUS[:NOTES]"
Example:
  uv run python tools/proc_step_status.py implementations/foo.md \
      --update "1:Completed:changed history.py" --update "3:In Progress"
Statuses: Pending | In Progress | Completed | Blocked (space is written as '_').
Notes text may contain spaces; the third ':'-separated field takes the rest.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys

_STATUSES = {"Pending", "In Progress", "Completed", "Blocked"}


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proc", help="path to the implementation procedure .md")
    parser.add_argument(
        "--update",
        action="append",
        required=True,
        help='STEP:STATUS[:NOTES], e.g. "1:Completed:changed history.py"',
    )
    args = parser.parse_args()

    rc = 0
    for spec in args.update:
        parts = spec.split(":", 2)
        if len(parts) < 2:
            print(f"bad update spec: {spec}", file=sys.stderr)
            rc = 1
            continue
        step, status = parts[0], parts[1].replace("_", " ")
        notes = parts[2].strip() if len(parts) > 2 else ""
        if status not in _STATUSES:
            print(f"invalid status in spec {spec!r}", file=sys.stderr)
            rc = 1
            continue
        ts = _ts()
        cmd = [
            "uv",
            "run",
            "python",
            "tools/manage_workitem_stage.py",
            "set-step-status",
            "implementation-procedure",
            args.proc,
            "--step",
            step,
            status,
        ]
        if notes:
            cmd += ["--notes", notes]
        if status == "In Progress":
            cmd += ["--started", ts]
        elif status == "Completed":
            cmd += ["--completed", ts]
        result = subprocess.run(cmd, capture_output=True, text=True)
        out = (result.stdout or result.stderr).strip().splitlines()
        print(out[-1] if out else f"(no output, exit {result.returncode})")
        if result.returncode != 0:
            rc = result.returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())
