#!/usr/bin/env python3
"""tools/_detect_unexecuted_archive.py — report recently-archived procedures that
still carry open Execution Status rows.

Read-only companion to ``manage_workitem_stage.py``'s archival moves. Enumerates
``implementations/done/*.md``, computes each file's archive date (the first commit
that added it at its ``implementations/done/`` path), and prints every file archived
within the last ``days`` days whose ``### Execution Status`` table still has a
``Pending`` / ``In Progress`` / ``Blocked`` row. Procedures archived longer ago, or
with no add-commit, are skipped. Never moves or edits a work item; always exits 0.

Kept separate from ``manage_workitem_stage.py`` so that stage stays under the
module-size gate (see ``tools/check_module_size.py``).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._workitem_status_table import (
    _normalize_status,
    parse_execution_status_rows,
)

# Execution Status values that count as "open" for the detector. Matches the
# non-terminal subset of ``_workitem_status_table``'s valid vocabulary;
# ``Completed`` is the only terminal state and never reported.
_UNEXECUTED_ARCHIVE_OPEN_STATUSES = frozenset({"Pending", "In Progress", "Blocked"})

_ADD_DATE_LINE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


def cmd_detect_unexecuted_archive(args: argparse.Namespace) -> int:
    """Report recently-archived procedures that still carry open Execution Status rows.

    Enumerates ``implementations/done/*.md``, computes each file's archive date (the
    first commit that added it at its ``implementations/done/`` path), and prints every
    file archived within the last ``args.days`` days whose ``### Execution Status`` table
    still has a ``Pending`` / ``In Progress`` / ``Blocked`` row. Procedures archived longer
    ago, or with no add-commit, are skipped. Read-only: never moves or edits a work item,
    and always exits 0.
    """
    done_dir = Path("implementations") / "done"
    if not done_dir.exists():
        print(f"No unexecuted archives found (window: {args.days} days)")
        return 0

    window_start = datetime.now(UTC) - timedelta(days=args.days)

    try:
        import git
        import git.exc
    except ImportError:
        # No VCS metadata to date an archive against; nothing to report.
        print(f"No unexecuted archives found (window: {args.days} days)")
        return 0

    try:
        repo = git.Repo(done_dir.resolve(), search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        print(f"No unexecuted archives found (window: {args.days} days)")
        return 0

    # Single pass: every done path added within the window, with its add-commit date.
    # A per-path `git log` would walk full history once per file (~8k files here);
    # `--since` restricts git to the window, keeping this to one cheap scan.
    # `--no-renames` is required: procedures reach `done/` via `git mv`, which git
    # records as a rename (R); `--diff-filter=A` alone would skip every such archive.
    since_ref = f"--since=@{int(window_start.timestamp())}"
    done_glob = done_dir.as_posix() + "/*"
    try:
        log_out = repo.git.log(
            "--no-renames",
            "--diff-filter=A",
            since_ref,
            "--format=%cI",
            "--name-only",
            "--",
            done_glob,
        )
    except git.exc.GitCommandError:
        print(f"No unexecuted archives found (window: {args.days} days)")
        return 0

    added: dict[str, datetime] = {}
    current_date: datetime | None = None
    for line in log_out.splitlines():
        if not line.strip():
            continue
        if _ADD_DATE_LINE_RE.match(line):
            current_date = datetime.fromisoformat(line)
            continue
        if current_date is not None:
            existing = added.get(line)
            if existing is None or current_date < existing:
                added[line] = current_date

    findings: list[tuple[str, str, str]] = []
    for rel in sorted(added):
        fpath = Path(rel)
        if not fpath.exists():
            continue
        rows = parse_execution_status_rows(fpath.read_text(encoding="utf-8"))
        if rows is None:
            continue
        open_statuses: set[str] = set()
        for row in rows:
            status = row.get("Status", "").strip()
            if not status:
                continue
            try:
                status = _normalize_status(status)
            except ValueError:
                continue
            if status in _UNEXECUTED_ARCHIVE_OPEN_STATUSES:
                open_statuses.add(status)
        if open_statuses:
            findings.append(
                (
                    rel,
                    added[rel].isoformat(),
                    "; ".join(sorted(open_statuses)),
                )
            )

    if not findings:
        print(f"No unexecuted archives found (window: {args.days} days)")
        return 0

    print(
        f"Found {len(findings)} recently-archived procedure(s) with open Execution Status rows (window: {args.days} days):"
    )
    for rel, archive_date, statuses in findings:
        print(f"  [unexecuted-archive] {rel}: {statuses} (archived {archive_date})")
    return 0
