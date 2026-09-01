#!/usr/bin/env python3
"""tools/manage_workitem_stage.py — Archive workflow-stage transitions via git mv.

Performs the `issues/` -> `issues/done/`, `plans/` -> `plans/done/`, and
`implementations/` -> `implementations/done/` archival move for one workitem file at
a time, using GitPython so the move is recorded as a Git rename.

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
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md --force --reason "manually verified complete"
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

EXECUTION_STATUS_HEADING = "### Execution Status"


@dataclass(frozen=True)
class MoveResult:
    """Result of an archival move attempt."""

    success: bool
    destination: Path | None = None
    error: str | None = None


def move_to_done(source: Path) -> MoveResult:
    """Move `source` into its sibling `done/` directory as a Git rename.

    Refuses (returns a failure `MoveResult`, performs no move) when the source is
    missing, the destination already exists, the source is outside a Git
    repository, or the source has uncommitted local changes.
    """
    if not source.is_file():
        return MoveResult(success=False, error=f"source file not found: {source}")

    destination = source.parent / "done" / source.name
    if destination.exists():
        return MoveResult(
            success=False, error=f"destination already exists: {destination}"
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
        status = repo.git.status("--porcelain", str(source_abs))
    except git.exc.GitCommandError as e:
        return MoveResult(success=False, error=f"git status failed: {e}")

    if status.strip():
        return MoveResult(
            success=False,
            error=f"source file has uncommitted changes, refusing to move: {source}",
        )

    try:
        repo.git.mv(str(source_abs), str(destination_abs))
    except git.exc.GitCommandError as e:
        return MoveResult(success=False, error=f"git mv failed: {e}")

    return MoveResult(success=True, destination=destination)


def parse_execution_status_rows(content: str) -> list[dict[str, str]] | None:
    """Parse the `### Execution Status` Markdown table's data rows.

    Returns `None` when the heading itself cannot be found (a structural
    problem, distinct from an empty table). Each returned row maps the header's
    column names (`Step`, `Description`, `Status`, `Started`, `Completed`,
    `Notes`) to that row's cell values.
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
    return _run_simple_move(Path(args.plan_path))


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
            f"ERROR: no '{EXECUTION_STATUS_HEADING}' table found in {source}",
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
