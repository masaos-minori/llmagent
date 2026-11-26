#!/usr/bin/env python3
"""tools/backtick_plan_related_tests.py

Backtick the path citations of a Plan: the `File Path` cells and the `tests/...py` paths of
the `Related Tests` cells of `Implementation Target Files`, and the target paths cited in
`Implementation steps`. tools/close_procedures_batch.py and
tools/check_workitem_traceability.py read those places through a backtick regular
expression, so a plain path is silently ignored. No other text of the Plan changes (other
tables, headers, and prose cells are left alone), a second run changes nothing, and the
file is written only when a citation was wrapped. The rule lives in
tools/_workitem_citation_check.py, which tools/check_workitem_structure.py reports as
`plain-path-citation`.

Usage: uv run python tools/backtick_plan_related_tests.py plans/<plan>.md [--dry-run]

Exit codes: 0 done (or nothing to do), 2 the Plan cannot be read.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import _workitem_citation_check as wcc
from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backtick the path citations of a Plan."
    )
    parser.add_argument("plan", type=Path, help="plans/<plan>.md")
    add_dry_run_argument(parser)
    args = parser.parse_args(argv)
    try:
        old = args.plan.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.plan} ({exc})", file=sys.stderr)
        return 2
    count = len(wcc.find_plain_citations(old))
    if count == 0:
        print(f"no plain citations in {args.plan}")
        return 0
    new = wcc.wrap_plain_citations(old)
    if args.dry_run:
        print_dry_run(args.plan, old, new)
    else:
        atomic_write_text(args.plan, new)
    print(f"backticked {count} citation(s) in {args.plan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
