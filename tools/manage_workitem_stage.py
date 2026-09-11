#!/usr/bin/env python3
"""tools/manage_workitem_stage.py — Archive workflow-stage transitions via git mv.

Performs the `issues/` -> `issues/done/`, `plans/` -> `plans/done/`, and
`implementations/` -> `implementations/done/` archival move for one workitem file at
a time, using GitPython so the move is recorded as a Git rename.

Every subcommand shares these pre-move safety checks (`move_to_done()`): the source
file must exist, the destination must not already exist, the destination's `done/`
directory must already exist, and the source file itself must have no uncommitted
local changes (untracked, staged, or modified-since-commit — other files' uncommitted
changes elsewhere in the repository are ignored). If `origin` is configured as a
remote, the move also fetches it and refuses when the destination path already exists
on the remote-tracking branch (a concurrent session likely already archived this file
there); a fetch failure (no network, no `origin`, detached HEAD) degrades to a no-op
rather than blocking the move. `git status`/`git mv` invocations retry a bounded
number of times on `.git/index.lock` contention from a concurrent git process.

`close-implementation` additionally parses the target file's `### Execution Status`
table (see `templates/execution-status.md`) and refuses the move while any row's
`Status` column is `Pending`, unless both `--force` and `--reason` are supplied.

Subcommands:
  close-issue           issues/{file}.md -> issues/done/{file}.md
  close-plan            plans/{file}.md -> plans/done/{file}.md
  close-implementation  implementations/{file}.md -> implementations/done/{file}.md

Usage:
    python tools/manage_workitem_stage.py close-issue issues/20260101_foo.md
    python tools/manage_workitem_stage.py close-plan plans/20260101_plan.md
    python tools/manage_workitem_stage.py close-plan plans/20260101_plan.md --allow-uncommitted
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md --force --reason "manually verified complete"
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import git

EXECUTION_STATUS_HEADING = "### Execution Status"

# `.git/index.lock` contention markers seen in GitCommandError messages when a
# concurrent git process (e.g. another session) holds the index lock.
_LOCK_CONTENTION_MARKERS = ("index.lock", "Unable to create")
_LOCK_RETRY_ATTEMPTS = 3
_LOCK_RETRY_DELAY_SECONDS = 0.2


@dataclass(frozen=True)
class MoveResult:
    """Result of an archival move attempt."""

    success: bool
    destination: Path | None = None
    error: str | None = None


def _run_with_lock_retry[T](operation: Callable[[], T]) -> T:
    """Retry `operation` when it fails on git index-lock contention.

    Concurrent git invocations against the same working tree (e.g. two sessions
    archiving different files at once) can race on `.git/index.lock`. Retries a
    bounded number of times with a short delay before propagating the last error.
    Any other `GitCommandError` is propagated immediately, without retrying.
    """
    import git.exc

    for attempt in range(_LOCK_RETRY_ATTEMPTS):
        try:
            return operation()
        except git.exc.GitCommandError as e:
            if not any(marker in str(e) for marker in _LOCK_CONTENTION_MARKERS):
                raise
            if attempt == _LOCK_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(_LOCK_RETRY_DELAY_SECONDS * (attempt + 1))
    raise AssertionError("unreachable: loop above always returns or raises")


def _find_remote_conflict(repo: git.Repo, destination_abs: Path) -> str | None:
    """Check whether `destination_abs` already exists on `origin`'s tracking branch.

    A hit means another session likely already archived this file there. Returns a
    conflict description, or `None` when: no remote is configured, the remote cannot
    be reached (network/auth unavailable — the check degrades to a no-op rather than
    blocking the move), the repository is in a detached-HEAD state, or no conflict was
    found.
    """
    import git.exc

    if not repo.remotes:
        return None
    try:
        remote = repo.remote("origin")
    except ValueError:
        return None

    try:
        remote.fetch()
    except git.exc.GitCommandError:
        return None

    try:
        branch = repo.active_branch.name
    except TypeError:
        return None

    if repo.working_tree_dir is None:
        return None  # bare repository — no working tree to relativize against

    tracking_ref = f"{remote.name}/{branch}"
    try:
        rel_path = destination_abs.relative_to(
            Path(repo.working_tree_dir).resolve()
        ).as_posix()
    except ValueError:
        return None

    try:
        repo.git.cat_file("-e", f"{tracking_ref}:{rel_path}")
    except git.exc.GitCommandError:
        return None

    return (
        f"destination already exists on {tracking_ref}: {rel_path} — another "
        "session may have already archived this file; fetch and reconcile before "
        "retrying"
    )


def move_to_done(source: Path, allow_uncommitted: bool = False) -> MoveResult:
    """Move `source` into its sibling `done/` directory as a Git rename.

    Refuses (returns a failure `MoveResult`, performs no move) when the source is
    missing, the destination already exists, the destination's `done/` directory
    does not exist, the source is outside a Git repository, the source has
    uncommitted local changes, or the destination already exists on `origin`'s
    remote-tracking branch (see `_find_remote_conflict`).

    Set `allow_uncommitted=True` to bypass the uncommitted-changes check.
    """
    if not source.is_file():
        return MoveResult(success=False, error=f"source file not found: {source}")

    destination = source.parent / "done" / source.name
    if destination.exists():
        return MoveResult(
            success=False, error=f"destination already exists: {destination}"
        )
    if not destination.parent.is_dir():
        return MoveResult(
            success=False,
            error=f"archive directory does not exist: {destination.parent}",
        )

    try:
        import git  # lazy import keeps startup fast when gitpython is unused
        import git.exc
    except ImportError:
        return MoveResult(success=False, error="GitPython is not installed")

    source_abs = source.resolve()
    destination_abs = destination.resolve()

    try:
        repo = git.Repo(source_abs.parent, search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        return MoveResult(success=False, error=f"not inside a git repository: {source}")

    try:
        status = _run_with_lock_retry(
            lambda: repo.git.status("--porcelain", str(source_abs))
        )
    except git.exc.GitCommandError as e:
        return MoveResult(success=False, error=f"git status failed: {e}")

    if status.strip() and not allow_uncommitted:
        if status.strip().startswith("??"):
            # An untracked file has no HEAD entry to diff against — `git
            # diff` (staged or not) always reports empty for it.
            diff_output = (
                "(untracked file -- no committed version exists yet, so "
                "there is nothing to diff; the whole file is new)"
            )
        else:
            # `git diff --cached` only covers staged changes -- the routine
            # case this hint exists for (an unstaged working-tree edit, e.g.
            # a Plan self-correction) would otherwise print an empty diff.
            # `diff HEAD` covers staged and unstaged changes together.
            diff_output = _run_with_lock_retry(
                lambda: repo.git.diff("HEAD", "--", str(source_abs))
            )
        error_msg = (
            f"source file has uncommitted changes, refusing to move: {source}\n"
            f"HINT: Commit the changes first, or use --allow-uncommitted to proceed anyway.\n"
            f"Changes:\n{diff_output}"
        )
        return MoveResult(success=False, error=error_msg)

    conflict = _find_remote_conflict(repo, destination_abs)
    if conflict:
        return MoveResult(success=False, error=conflict)

    try:
        _run_with_lock_retry(lambda: repo.git.mv(str(source_abs), str(destination_abs)))
    except git.exc.GitCommandError as e:
        return MoveResult(success=False, error=f"git mv failed: {e}")

    return MoveResult(success=True, destination=destination)


def parse_execution_status_rows(content: str) -> list[dict[str, str]] | None:
    """Parse the `### Execution Status` Markdown table's data rows.

    Returns `None` when the heading itself cannot be found, or when the table's
    header row does not include a `Status` column (both a structural problem,
    distinct from an empty table) — a renamed or missing `Status` column would
    otherwise silently disable `close-implementation`'s Pending-row block instead
    of surfacing an error. Each returned row maps the header's column names
    (`Step`, `Description`, `Status`, `Started`, `Completed`, `Notes`) to that
    row's cell values.
    """
    lines = content.splitlines()
    heading_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == EXECUTION_STATUS_HEADING),
        None,
    )
    if heading_idx is None:
        return None

    header: list[str] | None = None
    separator_seen = False
    rows: list[dict[str, str]] = []
    for line in lines[heading_idx + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header is not None:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            if "Status" not in header:
                return None
            continue
        if not separator_seen:
            separator_seen = True
            if all(re.fullmatch(r"-+", cell) for cell in cells):
                continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def _pending_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("Status", "").strip() == "Pending"]


def _describe_rows(rows: list[dict[str, str]]) -> str:
    return "; ".join(
        f"Step {row.get('Step', '?')}: {row.get('Description', '?')}" for row in rows
    )


def cmd_close_issue(args: argparse.Namespace) -> int:
    """Move an `issues/*.md` file to `issues/done/`."""
    return _run_simple_move(Path(args.issue_path))


def cmd_close_plan(args: argparse.Namespace) -> int:
    """Move a `plans/*.md` file to `plans/done/`."""
    result = move_to_done(
        Path(args.plan_path), allow_uncommitted=args.allow_uncommitted
    )
    if not result.success:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 1
    print(f"OK: moved {args.plan_path} -> {result.destination}")
    return 0


def _run_simple_move(source: Path) -> int:
    result = move_to_done(source)
    if not result.success:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 1
    print(f"OK: moved {source} -> {result.destination}")
    return 0


def cmd_close_implementation(args: argparse.Namespace) -> int:
    """Move an `implementations/*.md` file to `implementations/done/`.

    Refuses when the file's Execution Status table has any `Pending` row,
    unless both `--force` and `--reason` are supplied.
    """
    if args.force and not args.reason:
        print("ERROR: --force requires --reason", file=sys.stderr)
        return 1

    source = Path(args.implementation_path)
    if not source.is_file():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return 1

    rows = parse_execution_status_rows(source.read_text(encoding="utf-8"))
    if rows is None:
        print(
            f"ERROR: '{EXECUTION_STATUS_HEADING}' table missing or malformed "
            f"(no 'Status' column) in {source}",
            file=sys.stderr,
        )
        return 1

    pending = _pending_rows(rows)
    overridden = bool(args.force and args.reason)
    if pending and not overridden:
        print(
            f"ERROR: blocked by Pending Execution Status row(s): {_describe_rows(pending)}",
            file=sys.stderr,
        )
        return 1

    result = move_to_done(source)
    if not result.success:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 1

    if pending:
        print(
            f"OK: moved {source} -> {result.destination} "
            f"(forced past Pending row(s); reason: {args.reason})"
        )
    else:
        print(f"OK: moved {source} -> {result.destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive workflow-stage transitions via git mv",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    issue_parser = subparsers.add_parser(
        "close-issue", help="Move an issues/*.md file to issues/done/"
    )
    issue_parser.add_argument("issue_path", help="Path to the issue file")

    plan_parser = subparsers.add_parser(
        "close-plan", help="Move a plans/*.md file to plans/done/"
    )
    plan_parser.add_argument("plan_path", help="Path to the plan file")
    plan_parser.add_argument(
        "--allow-uncommitted",
        action="store_true",
        help="Allow moving files with uncommitted changes (not recommended without review)",
    )

    impl_parser = subparsers.add_parser(
        "close-implementation",
        help="Move an implementations/*.md file to implementations/done/",
    )
    impl_parser.add_argument(
        "implementation_path", help="Path to the implementation procedure file"
    )
    impl_parser.add_argument(
        "--force",
        action="store_true",
        help="Override a Pending Execution Status block (requires --reason)",
    )
    impl_parser.add_argument(
        "--reason", help="Justification for --force (required alongside --force)"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "close-issue":
        return cmd_close_issue(args)
    elif args.subcommand == "close-plan":
        return cmd_close_plan(args)
    elif args.subcommand == "close-implementation":
        return cmd_close_implementation(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
