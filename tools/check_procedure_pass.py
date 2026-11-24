#!/usr/bin/env python3
"""Run the per-document validation gates for one procedure pass.

Takes a pass timestamp (the prefix of the generated file names) and runs, for
every `implementations/` document whose name starts with it:

  1. `tools/stale_detector.py` — cited lines and symbols still resolve in source.
  2. `tools/check_workitem_structure.py --file` — required template sections.

Both gates are run per document by `skills/plan-to-implementation-procedure/`
Step 3; this script applies them to a whole pass in one call so a pass with many
rows is not validated one file at a time. Findings are reported per file; the
script is read-only and changes nothing.

Usage:
    uv run python tools/check_procedure_pass.py 20261124-122732
    uv run python tools/check_procedure_pass.py 20261124-122732 --mark-new

Exit codes:
    0  Every document passes both gates
    1  Any document reports a finding
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"

STALE_DETECTOR = TOOLS_DIR / "stale_detector.py"
STRUCTURE_CHECKER = TOOLS_DIR / "check_workitem_structure.py"
MARKER = TOOLS_DIR / "mark_procedure_new_symbols.py"


def collect_pass_files(timestamp: str) -> list[Path]:
    """Return the pass's procedure documents, ordered by their sequence number."""
    files = sorted(
        (p for p in (REPO_ROOT / "implementations").glob(f"{timestamp}_*.md")),
        key=lambda p: int(p.name.split("_")[1]),
    )
    return files


def run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    out = result.stdout
    if result.stderr:
        out += result.stderr
    return result.returncode, out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run stale_detector and check_workitem_structure for every "
        "document of one procedure pass."
    )
    parser.add_argument("timestamp", help="Pass timestamp prefix, e.g. 20261124-122732")
    parser.add_argument(
        "--mark-new",
        action="store_true",
        help="Run tools/mark_procedure_new_symbols.py on each document before the gates",
    )
    args = parser.parse_args(argv)

    files = collect_pass_files(args.timestamp)
    if not files:
        print(f"No documents found for pass {args.timestamp}.")
        return 1

    failed: list[str] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT)
        if args.mark_new:
            code, out = run([sys.executable, str(MARKER), "mark", str(path), "--all"])
            if code != 0:
                failed.append(f"{rel}: mark_procedure_new_symbols\n{out}")
                continue
        code, out = run([sys.executable, str(STALE_DETECTOR), str(path)])
        if code != 0:
            failed.append(f"{rel}: stale_detector\n{out}")
        code, out = run([sys.executable, str(STRUCTURE_CHECKER), "--file", str(path)])
        if code != 0:
            failed.append(f"{rel}: check_workitem_structure\n{out}")

    if failed:
        print(f"{len(files)} documents checked, {len(failed)} with findings:")
        for finding in failed:
            print(finding)
        return 1

    print(f"{len(files)} documents checked, 0 findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
