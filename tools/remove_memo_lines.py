#!/usr/bin/env python3
"""tools/remove_memo_lines.py - Removes the completed procedure lines from a memo file list.

The memo lists the implementation procedures to process and says that a procedure's filename is
removed from the list once the procedure is complete. This tool removes the lines whose path
matches `--prefix`, and it refuses a line whose procedure is not archived: the path must exist
under `implementations/done/` and no longer exist under `implementations/`. Nothing is removed
when any matched line is not archived.

Usage:
    python tools/remove_memo_lines.py MEMO.md --prefix implementations/PLAN_ID_ [--dry-run]

Exit codes: 0 when every matched line was archived and removed, 1 when a matched procedure is
not archived or the memo has no matching line, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text, print_dry_run

DONE_DIR = "implementations/done"


def _archived(path: str) -> bool:
    """Whether a procedure path is archived and no longer pending."""
    return Path(DONE_DIR, Path(path).name).exists() and not Path(path).exists()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("memo")
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    memo = Path(args.memo)
    try:
        text = memo.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"{memo}: {exc}", file=sys.stderr)
        return 1

    matched = [line for line in text.splitlines() if args.prefix in line]
    if not matched:
        print(f"{memo}: no line matches {args.prefix}", file=sys.stderr)
        return 1

    blocked = [
        line for line in matched if not _archived(line.removeprefix("- ").strip())
    ]
    if blocked:
        for line in blocked:
            print(f"not archived: {line}", file=sys.stderr)
        return 1

    new = (
        "\n".join(line for line in text.splitlines() if args.prefix not in line) + "\n"
    )
    if args.dry_run:
        print_dry_run(memo, text, new)
        return 0

    atomic_write_text(memo, new)
    print(f"Removed {len(matched)} lines from {memo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
