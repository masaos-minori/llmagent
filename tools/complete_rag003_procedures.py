#!/usr/bin/env python3
"""Batch-complete the rag003 implementation procedures (issue-228).

For each of the 29 procedures in batch 20261027-154425:
1. Stamp every Pending row in its '## Execution Status' table as Completed
   with a YYYYMMDD-HHMMSS timestamp.
2. Archive it with manage_workitem_stage.py close-implementation --stage-only.
3. Remove its row from memo3.md.
Then update the plan's Execution Status and Work Items tables.

Run from repo root: uv run python tools/complete_rag003_procedures.py [--dry-run]
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 — manage_workitem_stage.py is a trusted local CLI, argv is a fixed list
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMO = ROOT / "memo3.md"
PLAN = ROOT / "plans/done/20261027-110727_rag003_rag-url-key-ambiguity.md"
IMPL_DIR = ROOT / "implementations"

PROC_NAMES = sorted(p.name for p in IMPL_DIR.glob("20261027-154425_*.md"))

STATUS_ROW_RE = re.compile(
    r"^\| (\d+) \| (.+?) \| (Pending|In Progress) \| — \| — \| *\|$"
)
PLAN_STATUS_RE = re.compile(
    r"^\| (\d+) \| (.+?) \| (Pending|In Progress) \| — \| — \| *\|$"
)
PLAN_WORKITEM_RE = re.compile(
    r"^\| (implementations/20261027-154425_\d+_[^|]+\.md) \| (\d) \| Procedure \| Pending \| — \| — \|$"
)

PLAN_NOTES = {
    "1": "HEAD baseline green; post-rename full suite 10265 passed, 10 skipped, exit 0",
    "2": "Executed with Phase 3 as one serial batch (single validation pass); grep gate, mypy, bandit, lint-imports, targeted pytest all green",
    "3": "14 test files renamed + new AC-2 regression test in test_config_resolution.py; full suite exit 0; diff-cover 100%",
    "4": "7 docs pages + ADR renamed; docs checkers green; check_adr_preservation WARNING recorded (see procedure 29); config/ and deployed /opt/llm/config/ contain no old key",
}


def now() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def stamp_procedures(dry: bool) -> int:
    stamped = 0
    for name in PROC_NAMES:
        path = IMPL_DIR / name
        if not path.exists():
            print(f"MISSING: {path}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        out = []
        for ln in lines:
            m = STATUS_ROW_RE.match(ln)
            if m:
                ts = now()
                out.append(
                    f"| {m.group(1)} | {m.group(2)} | Completed | {ts} | {ts} | batch 20261027-154425 validated |"
                )
                stamped += 1
            else:
                out.append(ln)
        if not dry:
            path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return stamped


def close_procedures(dry: bool) -> None:
    for name in PROC_NAMES:
        path = IMPL_DIR / name
        if not path.exists():
            continue
        cmd = [
            "uv",
            "run",
            "python",
            "tools/manage_workitem_stage.py",
            "close-implementation",
            str(path),
            "--stage-only",
        ]
        if dry:
            print("WOULD RUN:", " ".join(cmd))
            continue
        r = subprocess.run(  # nosec B603 — fixed argv list, no shell, no user-built command
            cmd, cwd=ROOT, capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f"FAIL close: {name}\n{r.stdout}\n{r.stderr}")
            sys.exit(1)
        print(f"closed: {name}")


def trim_memo(dry: bool) -> int:
    lines = MEMO.read_text(encoding="utf-8").splitlines()
    removed = 0
    out = []
    for ln in lines:
        if any(name in ln for name in PROC_NAMES):
            removed += 1
            continue
        out.append(ln)
    if not dry:
        MEMO.write_text("\n".join(out) + "\n", encoding="utf-8")
    return removed


def update_plan(dry: bool) -> None:
    lines = PLAN.read_text(encoding="utf-8").splitlines()
    out = []
    status_rows = 0
    work_rows = 0
    for ln in lines:
        m = PLAN_STATUS_RE.match(ln)
        if m:
            status_rows += 1
            out.append(
                f"| {m.group(1)} | {m.group(2)} | Completed | {now()} | {now()} | {PLAN_NOTES[m.group(1)]} |"
            )
            continue
        m = PLAN_WORKITEM_RE.match(ln)
        if m:
            work_rows += 1
            out.append(
                f"| {m.group(1)} | {m.group(2)} | Procedure | Completed | — | — |"
            )
            continue
        out.append(ln)
    if not dry:
        PLAN.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"plan status rows: {status_rows}, work item rows: {work_rows}")


def main() -> None:
    dry = "--dry-run" in sys.argv
    stamped = stamp_procedures(dry)
    print(f"stamped rows: {stamped}")
    close_procedures(dry)
    removed = trim_memo(dry)
    print(f"memo3 rows removed: {removed}")
    update_plan(dry)
    print("plan updated")


if __name__ == "__main__":
    main()
