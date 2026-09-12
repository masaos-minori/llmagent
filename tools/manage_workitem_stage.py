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

_VALID_STATUSES = frozenset({"Pending", "In Progress", "Blocked", "Completed"})
_KIND_IMPL = "implementation-procedure"


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


def _find_implementation_dir(path: Path) -> Path:
    """Return the implementations/ directory containing `path`."""
    resolved = path.resolve()
    for parent in resolved.parents:
        if parent.name == "implementations":
            return parent
    raise ValueError(f"no 'implementations' ancestor found for {resolved}")


def _find_plan_dir(path: Path) -> Path:
    """Return the plans/ directory containing `path`."""
    resolved = path.resolve()
    for parent in resolved.parents:
        if parent.name == "plans":
            return parent
    raise ValueError(f"no 'plans' ancestor found for {resolved}")


def update_execution_status(
    source: Path,
    kind: str,
    step_number: int | None = None,
    description_match: str | None = None,
    new_status: str = "",
    new_notes: str | None = None,
) -> bool:
    """Update the Execution Status table on an implementation or plan file.

    If ``step_number`` is given, only that row's ``Status`` column is changed.
    If ``description_match`` is given, the first row whose ``Description`` contains
    the substring (case-insensitive) is updated.
    Otherwise every row's ``Status`` column is set to ``new_status``.

    When ``new_notes`` is provided, the Notes column of the matched row(s) is
    appended with the text (a single space separator is inserted before appending).

    Returns ``True`` when at least one row was modified; ``False`` when nothing
    matched or the file could not be written.
    """
    if new_status not in _VALID_STATUSES:
        print(
            f"ERROR: invalid status '{new_status}', must be one of: "
            f"{', '.join(sorted(_VALID_STATUSES))}",
            file=sys.stderr,
        )
        return False

    content = source.read_text(encoding="utf-8")
    heading, header, data_rows = parse_execution_status_table(content)
    if heading is None or header is None or data_rows is None:
        print(
            f"ERROR: '{EXECUTION_STATUS_HEADING}' table missing or malformed "
            f"(no 'Status' column) in {source}",
            file=sys.stderr,
        )
        return False

    status_col_idx = header.index("Status")
    notes_col_idx = header.index("Notes")
    modified = False

    for row in data_rows:
        if step_number is not None:
            try:
                row_step = int(row[header.index("Step")])
            except (ValueError, IndexError):
                continue
            if row_step != step_number:
                continue
        elif description_match is not None:
            desc_col_idx = header.index("Description")
            row_desc = row[desc_col_idx].lower()
            if description_match.lower() not in row_desc:
                continue
        # else: update every row

        row[status_col_idx] = new_status
        modified = True

        if new_notes is not None:
            existing_notes = row[notes_col_idx]
            if existing_notes.strip():
                row[notes_col_idx] = f"{existing_notes} {new_notes}"
            else:
                row[notes_col_idx] = new_notes
            modified = True

    if not modified:
        if step_number is not None:
            print(
                f"ERROR: no row with Step={step_number} found in {source}",
                file=sys.stderr,
            )
        elif description_match is not None:
            print(
                f"ERROR: no row with Description containing '{description_match}' "
                f"found in {source}",
                file=sys.stderr,
            )
        else:
            print(
                f"ERROR: no rows found in {source}",
                file=sys.stderr,
            )
        return False

    # Rebuild the entire table section from modified data_rows
    new_lines: list[str] = []
    in_table = False
    separator_appended = False
    for i, line in enumerate(content.splitlines()):
        if line.strip() == EXECUTION_STATUS_HEADING:
            new_lines.append(line)
            in_table = True
            continue
        if in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r"-+", c) for c in cells):
                # Separator line — keep it
                new_lines.append(line)
                separator_appended = True
                continue
            if len(cells) == len(header):
                # Data row — skip, will be replaced with rebuilt rows
                continue
            # Empty line or non-table line after table — stop tracking
            in_table = False
        new_lines.append(line)

    # Append the rebuilt table rows after the separator line
    if separator_appended:
        for dr in data_rows:
            new_lines.append(build_data_row_line(header, dr))

    # Write back
    new_content = "\n".join(new_lines)
    source.write_text(new_content, encoding="utf-8")
    return True


def _rows_equal(a: list[str], b: list[str], header: list[str]) -> bool:
    """Check whether two rows match on all columns except Status and Notes."""
    status_idx = header.index("Status")
    notes_idx = header.index("Notes")
    for i, col in enumerate(header):
        if i == status_idx or i == notes_idx:
            continue
        if a[i] != b[i]:
            return False
    return True


def parse_execution_status_table(
    content: str,
) -> tuple[str | None, list[str] | None, list[list[str]] | None]:
    """Parse the `### Execution Status` table into components.

    Returns (heading_line, header_cells, data_rows) where each data row is a list of
    cell strings matching the header length. Returns None for any component if parsing
    fails.
    """
    lines = content.splitlines()
    heading_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == EXECUTION_STATUS_HEADING),
        None,
    )
    if heading_idx is None:
        return None, None, None

    header: list[str] | None = None
    separator_seen = False
    data_rows: list[list[str]] = []
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
                return None, None, None
            continue
        if not separator_seen:
            separator_seen = True
            if all(re.fullmatch(r"-+", cell) for cell in cells):
                continue
        if len(cells) != len(header):
            continue
        data_rows.append(cells)
    return EXECUTION_STATUS_HEADING, header, data_rows


def build_table_header_line(header: list[str]) -> str:
    """Rebuild a Markdown table header line from header cells."""
    return "| " + " | ".join(header) + " |"


def build_table_separator_line(header_len: int) -> str:
    """Rebuild a Markdown table separator line."""
    return "|" + "|".join(["------"] * header_len) + "|"


def build_data_row_line(header: list[str], cells: list[str]) -> str:
    """Rebuild a Markdown table data row line."""
    return "| " + " | ".join(cells) + " |"


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

    # set-status: update all rows' Status column
    set_status_parser = subparsers.add_parser(
        "set-status",
        help="Update the Execution Status table on an implementation-procedure or plan file",
    )
    set_status_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    set_status_parser.add_argument("path", help="Path to the file")
    set_status_parser.add_argument(
        "status",
        choices=sorted(_VALID_STATUSES),
        help="New status value for all rows",
    )
    set_status_parser.add_argument(
        "--notes",
        default=None,
        help="Optional notes text to append to each row's Notes column",
    )

    # set-step-status: update a single step's Status column
    set_step_parser = subparsers.add_parser(
        "set-step-status",
        help="Update the Status column of a specific step in the Execution Status table",
    )
    set_step_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    set_step_parser.add_argument("path", help="Path to the file")
    set_step_parser.add_argument(
        "--step",
        type=int,
        default=None,
        help="Step number to update (mutually exclusive with --description)",
    )
    set_step_parser.add_argument(
        "--description",
        default=None,
        help="Substring match against Description column (mutually exclusive with --step)",
    )
    set_step_parser.add_argument(
        "status",
        choices=sorted(_VALID_STATUSES),
        help="New status value for the matched row",
    )
    set_step_parser.add_argument(
        "--notes",
        default=None,
        help="Optional notes text to append to the matched row's Notes column",
    )

    # detect-stale: find stale workitems
    detect_parser = subparsers.add_parser(
        "detect-stale",
        help="Detect stale in-progress or pending workitems",
    )
    detect_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days since last modification to consider stale (default: 7)",
    )

    # list: list workitems by status/kind
    list_parser = subparsers.add_parser(
        "list",
        help="List workitems filtered by kind and/or status",
    )
    list_parser.add_argument(
        "--kind",
        choices=["implementation-procedure", "plan"],
        default=None,
        help="Filter by kind (omit to show both)",
    )
    list_parser.add_argument(
        "--status",
        choices=sorted(_VALID_STATUSES),
        default=None,
        help="Filter by status (omit to show all statuses)",
    )

    # show: display Execution Status table
    show_parser = subparsers.add_parser(
        "show",
        help="Display the Execution Status table from a workitem file",
    )
    show_parser.add_argument(
        "kind",
        choices=["implementation-procedure", "plan"],
        help="Kind of workitem file",
    )
    show_parser.add_argument("path", help="Path to the file")

    return parser


def cmd_set_status(args):
    """Set the same status on all rows of the Execution Status table."""
    source = Path(args.path)
    if not source.is_file():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return 1

    modified = update_execution_status(
        source=source,
        kind=args.kind,
        new_status=args.status,
        new_notes=args.notes,
    )
    if not modified:
        return 1
    msg_parts = [f"OK: updated all rows to '{args.status}' in {source}"]
    if args.notes is not None:
        msg_parts.append(f"Notes appended: '{args.notes}'")
    print(" ".join(msg_parts))
    return 0


def cmd_set_step_status(args):
    """Update the Status column of a specific step in the Execution Status table."""
    if args.step is None and args.description is None:
        print("ERROR: --step or --description is required", file=sys.stderr)
        return 1
    if args.step is not None and args.description is not None:
        print("ERROR: --step and --description are mutually exclusive", file=sys.stderr)
        return 1

    source = Path(args.path)
    if not source.is_file():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return 1

    modified = update_execution_status(
        source=source,
        kind=args.kind,
        step_number=args.step,
        description_match=args.description,
        new_status=args.status,
        new_notes=args.notes,
    )
    if not modified:
        return 1
    msg_parts = []
    if args.step is not None:
        msg_parts.append(f"Step={args.step}")
    elif args.description is not None:
        msg_parts.append(f"'{args.description}'")
    msg_parts.append(f"to '{args.status}' in {source}")
    output_msg = f"OK: updated {' '.join(msg_parts)}"
    if args.notes is not None:
        output_msg += f"; Notes appended: '{args.notes}'"
    print(output_msg)
    return 0


def _get_workitem_files(kind):
    """Get list of workitem files for the given kind (excluding done/)."""
    if kind == "implementation-procedure":
        base = Path("implementations")
    else:
        base = Path("plans")
    if not base.exists():
        return []
    return sorted(base.glob("*.md"))


def _get_status_from_file(path):
    """Extract status from Execution Status table of a workitem file."""
    content = path.read_text(encoding="utf-8")
    rows = parse_execution_status_rows(content)
    if rows is None:
        return None
    statuses = set()
    for row in rows:
        s = row.get("Status", "").strip()
        if s:
            statuses.add(s)
    return "; ".join(sorted(statuses)) if statuses else None


def cmd_detect_stale(args):
    """Detect stale in-progress or pending workitems."""
    days = args.days
    threshold = __import__("datetime").datetime.now() - __import__(
        "datetime"
    ).timedelta(days=days)
    stale_items = []

    for kind in ["implementation-procedure", "plan"]:
        for fpath in _get_workitem_files(kind):
            mtime = __import__("os").stat(str(fpath)).st_mtime
            if __import__("datetime").datetime.fromtimestamp(mtime) < threshold:
                status = _get_status_from_file(fpath)
                if status and ("In Progress" in status or "Pending" in status):
                    stale_items.append((fpath, status, kind))

    if not stale_items:
        print(f"No stale items found (threshold: {days} days)")
        return 0

    print(f"Found {len(stale_items)} stale item(s) (threshold: {days} days):")
    for fpath, status, kind in stale_items:
        print(f"  [{kind}] {fpath}: {status}")
    return 0


def cmd_list(args):
    """List workitems filtered by kind and/or status."""
    kinds = [args.kind] if args.kind else ["implementation-procedure", "plan"]
    results = {}

    for kind in kinds:
        for fpath in _get_workitem_files(kind):
            status = _get_status_from_file(fpath)
            if status is None:
                continue
            if args.status and args.status not in status:
                continue
            results.setdefault(status, []).append((fpath, kind))

    if not results:
        print("No items found")
        return 0

    for status in sorted(results.keys()):
        print(f"\nStatus: {status}")
        for fpath, kind in results[status]:
            print(f"  [{kind}] {fpath}")
    return 0


def cmd_show(args):
    """Display the Execution Status table from a workitem file."""
    source = Path(args.path)
    if not source.is_file():
        print(f"ERROR: source file not found: {source}", file=sys.stderr)
        return 1

    content = source.read_text(encoding="utf-8")
    heading, header, data_rows = parse_execution_status_table(content)
    if heading is None or header is None or data_rows is None:
        print(
            f"ERROR: '{EXECUTION_STATUS_HEADING}' table missing or malformed in {source}",
            file=sys.stderr,
        )
        return 1

    print(heading)
    print(build_table_header_line(header))
    print(build_table_separator_line(len(header)))
    for row in data_rows:
        print(build_data_row_line(header, row))
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "close-issue":
        return cmd_close_issue(args)
    elif args.subcommand == "close-plan":
        return cmd_close_plan(args)
    elif args.subcommand == "close-implementation":
        return cmd_close_implementation(args)
    elif args.subcommand == "set-status":
        return cmd_set_status(args)
    elif args.subcommand == "set-step-status":
        return cmd_set_step_status(args)
    elif args.subcommand == "detect-stale":
        return cmd_detect_stale(args)
    elif args.subcommand == "list":
        return cmd_list(args)
    elif args.subcommand == "show":
        return cmd_show(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
