#!/usr/bin/env python3
"""tools/coverage_xml_changed.py

Write `coverage.xml` for the changed `scripts/**/*.py` files only.

`coverage xml` re-parses every measured source file on each run (about 75% of
its 3.5 s on 428 files). `diff-cover` only reads changed lines, so restricting
the report with `--include` to the files changed against the base branch cuts
the run to about 0.3 s. When no `scripts/` file changed, the full report is
written instead so `coverage.xml` always exists for `diff-cover`.

Usage:
    uv run python tools/coverage_xml_changed.py [--base master] [--all] [--dry-run]

Exit codes: 0 report written (or dry-run), 2 git or coverage failure.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 — coverage is a trusted local CLI, argv is a fixed list
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._tool_common import EXIT_ERROR, EXIT_OK, REPO_ROOT, run_git

SCOPE_PREFIX = "scripts/"


def changed_source_files(base: str, *, cwd: Path = REPO_ROOT) -> list[str]:
    """Return existing `scripts/**/*.py` paths changed since the merge base of `base` and HEAD.

    Covers committed, staged, unstaged and untracked changes, matching what
    `diff-cover --compare-branch` inspects. Deleted files are excluded.
    """
    merge_base = run_git("merge-base", base, "HEAD", cwd=cwd)
    if merge_base.returncode != 0:
        raise RuntimeError(
            f"git merge-base {base} HEAD failed: {merge_base.stderr.strip()}"
        )
    diff = run_git(
        "diff", "--name-only", "--diff-filter=ACMR", merge_base.stdout.strip(), cwd=cwd
    )
    untracked = run_git("ls-files", "--others", "--exclude-standard", cwd=cwd)
    for proc in (diff, untracked):
        if proc.returncode != 0:
            raise RuntimeError(f"git failed: {proc.stderr.strip()}")
    names = set(diff.stdout.splitlines()) | set(untracked.stdout.splitlines())
    return sorted(
        n
        for n in names
        if n.startswith(SCOPE_PREFIX) and n.endswith(".py") and (cwd / n).is_file()
    )


def build_command(files: list[str]) -> list[str]:
    """Build the `coverage xml` argv; no files means the full report."""
    cmd = [sys.executable, "-m", "coverage", "xml", "-q"]
    if files:
        cmd.append("--include=" + ",".join(files))
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--base", default="master", help="base branch (default: master)"
    )
    parser.add_argument("--all", action="store_true", help="write the full report")
    parser.add_argument("--dry-run", action="store_true", help="print the command only")
    args = parser.parse_args(argv)

    try:
        files = [] if args.all else changed_source_files(args.base)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    cmd = build_command(files)
    scope = f"{len(files)} changed file(s)" if files else "full report"
    print(f"coverage_xml_changed: {scope}")
    if args.dry_run:
        print(" ".join(cmd))
        return EXIT_OK
    proc = subprocess.run(cmd, cwd=REPO_ROOT, check=False)  # nosec B603 — fixed argv, no shell
    return EXIT_OK if proc.returncode == 0 else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
