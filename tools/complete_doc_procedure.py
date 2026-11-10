#!/usr/bin/env python3
"""tools/complete_doc_procedure.py - Record completion of a docs-wave procedure doc.

One call per documentation procedure document in the batch workflow:
  1. Sets the `### Execution Status` rows to `Done` with timestamps (step 1 = the
     document edit, step 2 = the documentation checkers), filling the Notes cells.
  2. Inserts a `### Verification Findings` table (one row per --vf argument, format
     `ITEM|FINDING|ACTION`) before `### Blocker Log` when any --vf is given and the
     section does not already exist.
  3. With --archive: removes the document's line from MEMO (default memo3.md, matched
     by filename) and moves the procedure doc to `implementations/done/`. Refuses when
     the destination exists.

Usage:
    python tools/complete_doc_procedure.py PROC.md \
        [--step1-note TEXT] [--step2-note TEXT] \
        [--vf "ID|finding|action"]... [--memo PATH] [--no-archive]

Exit 0 on success, 1 on a missing anchor (status table, memo line), 2 on usage error.
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DONE_DIR = REPO / "implementations" / "done"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    proc = REPO / argv[0] if not Path(argv[0]).is_absolute() else Path(argv[0])
    if not proc.is_file():
        print(f"procedure doc not found: {proc}", file=sys.stderr)
        return 2
    step_notes: dict[int, str] = {}
    vfs: list[str] = []
    memo = REPO / "memo3.md"
    archive = True
    i = 1
    while i < len(argv):
        a = argv[i]
        m = re.fullmatch(r"--step(\d+)-note", a)
        if m:
            step_notes[int(m.group(1))] = argv[i + 1]
            i += 2
        elif a == "--vf":
            vfs.append(argv[i + 1])
            i += 2
        elif a == "--memo":
            memo = REPO / argv[i + 1]
            i += 2
        elif a == "--no-archive":
            archive = False
            i += 1
        else:
            print(f"unknown option: {a}", file=sys.stderr)
            return 2

    stamp = time.strftime("%Y%m%d-%H%M%S")
    text = proc.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 1. Execution Status rows.
    try:
        head = next(
            i for i, ln in enumerate(lines) if ln.strip() == "### Execution Status"
        )
    except StopIteration:
        print("anchor not found: ### Execution Status", file=sys.stderr)
        return 1
    changed = 0
    for i in range(head + 2, len(lines)):
        ln = lines[i]
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[2] != "Pending":
            continue
        step_no = int(cells[0]) if cells[0].isdigit() else changed + 1
        note = step_notes.get(step_no, "")
        lines[i] = f"| {cells[0]} | {cells[1]} | Done | {stamp} | {stamp} | {note} |"
        changed += 1
    if changed == 0:
        print("no Pending rows found in Execution Status", file=sys.stderr)
        return 1

    # 2. Verification Findings insertion.
    if vfs and not any(ln.strip() == "### Verification Findings" for ln in lines):
        try:
            blocker = next(
                i for i, ln in enumerate(lines) if ln.strip() == "### Blocker Log"
            )
        except StopIteration:
            print("anchor not found: ### Blocker Log", file=sys.stderr)
            return 1
        table = [
            "### Verification Findings",
            "| Item | Finding | Action taken |",
            "|------|---------|--------------|",
        ]
        for vf in vfs:
            parts = vf.split("|", 2)
            if len(parts) != 3:
                print(f"--vf needs ITEM|FINDING|ACTION: {vf}", file=sys.stderr)
                return 2
            table.append(f"| {parts[0]} | {parts[1]} | {parts[2]} |")
        lines[blocker:blocker] = table + [""]

    proc.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status updated: {changed} row(s); vf rows: {len(vfs)}")

    # 3. Memo line removal + archive.
    if archive:
        if (DONE_DIR / proc.name).exists():
            print(
                f"archive destination exists: {DONE_DIR / proc.name}", file=sys.stderr
            )
            return 1
        if memo.is_file():
            memo_lines = memo.read_text(encoding="utf-8").splitlines()
            kept = [ln for ln in memo_lines if proc.name not in ln]
            if len(kept) == len(memo_lines):
                print(f"no memo line matched: {proc.name}", file=sys.stderr)
                return 1
            memo.write_text("\n".join(kept) + "\n", encoding="utf-8")
            print(f"memo line removed: {proc.name}")
        else:
            print(f"memo not found, skipped: {memo}", file=sys.stderr)
        proc.rename(DONE_DIR / proc.name)
        print(f"archived: implementations/done/{proc.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
