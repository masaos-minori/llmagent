#!/usr/bin/env python3
"""Run stale_detector.py over a batch of implementation procedure docs.

Loops the single-path stale_detector CLI over the given procedure files,
aggregates per-file results, and prints a summary table plus any file with
unmet dependencies. Exit code 0 if all clean, 1 if any file has unmet deps.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv if not a.startswith("-")]
    if not paths:
        print("usage: batch_stale_detector.py <proc.md> ...", file=sys.stderr)
        return 2

    failures = 0
    for proc in sorted(paths):
        rel = proc.relative_to(REPO_ROOT) if proc.is_absolute() else proc
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "stale_detector.py"), str(rel)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        unmet = "stale_detector:" in result.stdout and "unmet" in result.stdout
        if unmet:
            failures += 1
            print(f"UNMET {rel}")
            print(result.stdout.rstrip())
            if result.stderr:
                print(result.stderr.rstrip())
        elif result.returncode != 0:
            failures += 1
            print(f"ERROR {rel} (exit {result.returncode})")
            print((result.stdout + result.stderr).rstrip())
    total = len(paths)
    print(f"checked={total} unmet_or_error={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
