#!/usr/bin/env python3
"""tools/manage_workitem_stage.py — Archive workflow-stage transitions via git mv.

Performs the `issues/` -> `issues/done/`, `plans/` -> `plans/done/`, and
`implementations/` -> `implementations/done/` archival move for one workitem file at
a time, using GitPython so the move is recorded as a Git rename.

Every subcommand shares these pre-move safety checks (`move_to_done()`): the source
file must exist, the destination must not already exist, and the destination's `done/`
directory must already exist. If the source file itself has uncommitted local changes
(untracked, staged, or modified-since-commit — other files' uncommitted changes
elsewhere in the repository are ignored), it is staged and committed automatically
(via the real `git add`/`git commit` commands, so any configured pre-commit hooks
still run) before the move proceeds — there is no flag to bypass this with an
uncommitted move; auto-commit is the only path. If `origin` is configured as a
remote, the move also fetches it and refuses when the destination path already exists
on the remote-tracking branch (a concurrent session likely already archived this file
there); a fetch failure (no network, no `origin`, detached HEAD) degrades to a no-op
rather than blocking the move. `git status`/`git mv`/auto-commit invocations retry a
bounded number of times on `.git/index.lock` contention from a concurrent git process.

Every `close-*` subcommand accepts `--stage-only`: the dirty source is staged
(`git add`) instead of committed before the move, so the rename lands in the next
real commit together with the work it belongs to and no `chore: auto-commit ...`
commit is created. Default behavior (auto-commit) is unchanged; pre-commit hooks
then run at that later commit rather than at the move.

`close-issue` additionally refuses the move while a Plan in `plans/` (not `plans/done/`)
names the issue in its `- **Source issue**:` line and that Plan's `Freeze status` is not
`Frozen` (a `Draft` Plan, or a missing/malformed Freeze status line), unless both
`--force` and `--reason` are supplied. An issue with no matching Plan (e.g. already
resolved) moves as before.

`close-implementation` additionally parses the target file's `### Execution Status`
table (see `templates/execution-status.md`) and refuses the move while any row's
`Status` column is `Pending`, unless both `--force` and `--reason` are supplied.

Subcommands:
  close-issue           issues/{file}.md -> issues/done/{file}.md
  close-plan            plans/{file}.md -> plans/done/{file}.md
  close-implementation  implementations/{file}.md -> implementations/done/{file}.md
  close-batch           archive every procedure of a batch (plan path or timestamp
                          prefix), marking each Completed and its plan Completed
  set-status            set every row's Status (+ optional Started/Completed/Notes)
                         in a plan's or implementation procedure's Execution Status table
  set-step-status       same, but only for one row (--step N or --description text)
  detect-stale          list plans/implementations not modified in --days (default 7)
                         that are still In Progress or Pending
  list                  list plans/implementations, optionally filtered by --kind/--status
                         or, with --plan PLAN --order, one Plan's procedures in phase order
  show                  print a plan's or implementation procedure's Execution Status table

Usage:
    python tools/manage_workitem_stage.py close-issue issues/20260101_foo.md
    python tools/manage_workitem_stage.py close-plan plans/20260101_plan.md
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md
    python tools/manage_workitem_stage.py close-implementation \\
        implementations/20260101_x.md --force --reason "manually verified complete"
    python tools/manage_workitem_stage.py set-step-status implementation-procedure \\
        implementations/20260101_x.md --step 3 Completed \\
        --started 20260101-090000 --completed 20260101-091500
    python tools/manage_workitem_stage.py set-status plan plans/20260101_plan.md Completed
    python tools/manage_workitem_stage.py detect-stale --days 14
    python tools/manage_workitem_stage.py list --kind implementation-procedure --status "In Progress"
    python tools/manage_workitem_stage.py list --plan plans/20260101_plan.md --order
    python tools/manage_workitem_stage.py show plan plans/20260101_plan.md
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import TYPE_CHECKING

from tools._workitem_stage_parser import build_parser
from tools._workitem_status_table import (
    EXECUTION_STATUS_HEADING,
    build_data_row_line,
    build_table_header_line,
    build_table_separator_line,
    parse_execution_status_rows,
    parse_execution_status_table,
    update_execution_status,
)

if TYPE_CHECKING:
    import git

_FREEZE_STATUS_PATTERN = re.compile(r"^\*\*Freeze status\*\*:\s*(\S+)", re.MULTILINE)

# `.git/index.lock` contention markers seen in GitCommandError messages when a
# concurrent git process (e.g. another session) holds the index lock.
_LOCK_CONTENTION_MARKERS = ("index.lock", "Unable to create")
_LOCK_RETRY_ATTEMPTS = 3
_LOCK_RETRY_DELAY_SECONDS = 0.2

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


def _auto_commit(
    repo: git.Repo,
    source_abs: Path,
    kind: str,
    exc_class: type[Exception],
    *,
    stage_only: bool = False,
) -> str | None:
    """Stage and commit `source_abs` so the subsequent move never runs against an
    uncommitted file. Returns an error string on failure, or `None` on success.

    Runs the real `git add`/`git commit` commands (not GitPython's index API)
    so any configured pre-commit hooks still apply — this must not become a
    silent way to bypass them. The commit is limited to `source_abs` by pathspec:
    changes the caller had already staged for other paths stay staged and out of
    this commit. With `stage_only`, only `git add` runs: the file is left staged
    for the caller's next commit (hooks run then).
    """
    message = f"chore: auto-commit {kind} before archival move ({source_abs.name})"
    try:
        _run_with_lock_retry(lambda: repo.git.add(str(source_abs)))
        if not stage_only:
            _run_with_lock_retry(
                lambda: repo.git.commit("-m", message, "--", str(source_abs))
            )
    except exc_class as e:
        return f"auto-commit failed: {e}"
    return None


def move_to_done(
    source: Path, *, kind: str = "workitem", stage_only: bool = False
) -> MoveResult:
    """Move `source` into its sibling `done/` directory as a Git rename.

    Refuses (returns a failure `MoveResult`, performs no move) when the source is
    missing, the destination already exists, the destination's `done/` directory
    does not exist, the source is outside a Git repository, or the destination
    already exists on `origin`'s remote-tracking branch (see
    `_find_remote_conflict`).

    If `source` has uncommitted local changes (untracked, staged, or modified
    since its last commit), it is staged and committed automatically before the
    move proceeds — there is no bypass flag; auto-commit replaces the previous
    refuse-and-hint behavior entirely. `kind` (e.g. `"issue"`, `"plan"`,
    `"implementation procedure"`) only labels the auto-commit message; pass it
    from the calling subcommand for a clearer commit history. With `stage_only`,
    the uncommitted source is staged but not committed (see `_auto_commit`).
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

    if status.strip():
        commit_error = _auto_commit(
            repo, source_abs, kind, git.exc.GitCommandError, stage_only=stage_only
        )
        if commit_error:
            return MoveResult(success=False, error=commit_error)

    conflict = _find_remote_conflict(repo, destination_abs)
    if conflict:
        return MoveResult(success=False, error=conflict)

    try:
        _run_with_lock_retry(lambda: repo.git.mv(str(source_abs), str(destination_abs)))
    except git.exc.GitCommandError as e:
        return MoveResult(success=False, error=f"git mv failed: {e}")

    return MoveResult(success=True, destination=destination)


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


def _report_move_result(
    source: Path, result: MoveResult, extra_note: str | None = None
) -> int:
    """Print the ERROR/OK message for a `move_to_done()` result and return the
    process exit code. Shared by all three `close-*` subcommands."""
    if not result.success:
        print(f"ERROR: {result.error}", file=sys.stderr)
        return 1
    message = f"OK: moved {source} -> {result.destination}"
    if extra_note:
        message += f" ({extra_note})"
    print(message)
    return 0


def _find_unfrozen_plans(issue: Path) -> list[tuple[Path, str]]:
    """Return `(plan_path, freeze_status)` for each non-`Frozen` Plan of `issue`.

    Only `plans/*.md` (not `plans/done/`) is searched, for a Plan whose
    `- **Source issue**: {stage_dir}/{filename}` line names `issue`, matching the
    content-based lookup in `skills/issue-to-plan/workflow.md` Step 1b. A Plan whose
    Freeze status line is missing is reported as `"missing"`.
    """
    plans_dir = issue.resolve().parent.parent / "plans"
    if not plans_dir.is_dir():
        return []
    marker = f"- **Source issue**: {issue.resolve().parent.name}/{issue.name}"
    unfrozen: list[tuple[Path, str]] = []
    for plan in sorted(plans_dir.glob("*.md")):
        content = plan.read_text(encoding="utf-8")
        if marker not in content.splitlines():
            continue
        match = _FREEZE_STATUS_PATTERN.search(content)
        status = match.group(1) if match else "missing"
        if status != "Frozen":
            unfrozen.append((plan, status))
    return unfrozen


def cmd_close_issue(args: argparse.Namespace) -> int:
    """Move an `issues/*.md` file to `issues/done/`.

    Refuses when a Plan in `plans/` for this issue is not `Frozen`, unless both
    `--force` and `--reason` are supplied.
    """
    if args.force and not args.reason:
        print("ERROR: --force requires --reason", file=sys.stderr)
        return 1

    source = Path(args.issue_path)
    unfrozen = _find_unfrozen_plans(source) if source.is_file() else []
    if unfrozen and not args.force:
        described = "; ".join(f"{plan} (Freeze status: {st})" for plan, st in unfrozen)
        print(
            f"ERROR: blocked by non-Frozen Plan(s): {described}. "
            "Re-run issue-to-plan Step 8 until the Plan is Frozen.",
            file=sys.stderr,
        )
        return 1

    result = move_to_done(source, kind="issue", stage_only=args.stage_only)
    extra_note = (
        f"forced past non-Frozen Plan; reason: {args.reason}" if unfrozen else None
    )
    return _report_move_result(source, result, extra_note)


def cmd_close_plan(args: argparse.Namespace) -> int:
    """Move a `plans/*.md` file to `plans/done/`."""
    source = Path(args.plan_path)
    result = move_to_done(source, kind="plan", stage_only=args.stage_only)
    return _report_move_result(source, result)


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

    result = move_to_done(
        source, kind="implementation procedure", stage_only=args.stage_only
    )
    extra_note = (
        f"forced past Pending row(s); reason: {args.reason}" if pending else None
    )
    return _report_move_result(source, result, extra_note)


class BatchResolutionError(Exception):
    """Raised when a batch id resolves to zero live procedures (unknown batch)."""


class AlreadyClosedBatch(Exception):
    """Raised when a batch id resolves to zero live procedures because it was
    already archived into `implementations/done/`."""

    def __init__(self, archived: list[Path]) -> None:
        super().__init__(
            "batch already archived: " + ", ".join(str(p) for p in archived)
        )
        self.files = archived


def _impl_root() -> Path:
    """Return the repository's `implementations/` directory (relative to cwd)."""
    return Path("implementations")


def _prefix_from_plan_path(plan: Path) -> str:
    """Derive a batch's timestamp prefix from a plan file's name.

    A plan is named `<timestamp>_plan.md`; the prefix is the `<timestamp>`
    (`YYYYMMDD-HHMMSS`) that also leads its procedures' filenames. Falls back to the
    leading `YYYYMMDD-HHMMSS` token when the name does not end in `_plan.md`.
    """
    name = plan.name
    if name.endswith("_plan.md"):
        return name[: -len("_plan.md")]
    match = re.match(r"(\d{8}-\d{6})", name)
    if match:
        return match.group(1)
    raise ValueError(f"cannot derive a batch prefix from plan filename: {name}")


def _batch_prefix(batch_id: str) -> str:
    """Resolve a batch id (plan path or bare prefix) to its timestamp prefix."""
    candidate = Path(batch_id)
    if candidate.is_file():
        return _prefix_from_plan_path(candidate)
    return batch_id.strip("/")


def _discover_batch(batch_id: str, prefix: str) -> list[Path]:
    """Return the sorted live procedure paths of the batch identified by `prefix`.

    When no live procedure matches but the files exist under `implementations/done/`,
    raise `AlreadyClosedBatch`; otherwise raise `BatchResolutionError`.
    """
    impl_root = _impl_root()
    live = sorted(impl_root.glob(f"{prefix}_*.md"))
    if live:
        return live

    archived = sorted((impl_root / "done").glob(f"{prefix}_*.md"))
    if archived:
        raise AlreadyClosedBatch(archived)
    raise BatchResolutionError(
        f"batch '{batch_id}' (prefix '{prefix}') resolved to no procedures under "
        f"{impl_root}/ (no implementations/{prefix}_*.md)"
    )


def _extract_source_issue(content: str) -> str | None:
    r"""Return the `Source issue` path cited in a workitem's Traceability section.

    Matches both the plan form (`- **Source issue**: \`issues/...\``) and the
    implementation-procedure form (`**Source issue**: \`issues/...\``); returns the
    bare `issues/<path>` token without surrounding backticks.
    """
    match = re.search(r"\*\*Source issue\*\*:\s*`?([^`\s]+)`?", content)
    return match.group(1) if match else None


def _find_owning_plan(procedures: list[Path], prefix: str) -> Path | None:
    """Return the plan that owns the discovered batch, or `None`.

    Two signals are tried, in order:

    1. A plan whose content references this batch's procedures
       (`implementations/<prefix>_`) — the deterministic case used by tests.
    2. A plan sharing the batch's `Source issue` — the real-world link between a plan
       and the procedures its `plan-to-implementation-procedure` run generated (their
       timestamps differ, so the prefix is not derivable from the plan filename).

    Searches both `plans/*.md` and `plans/done/*.md` (a plan may already be archived).
    Returns the first match, or `None` when no plan owns the batch.
    """
    plan_dirs = [Path("plans"), Path("plans") / "done"]
    candidates: list[Path] = []

    for plan_dir in plan_dirs:
        if not plan_dir.is_dir():
            continue
        for plan in sorted(plan_dir.glob("*.md")):
            if f"implementations/{prefix}_" in plan.read_text(encoding="utf-8"):
                candidates.append(plan)
    if candidates:
        return candidates[0]

    issue_tokens: set[str] = set()
    for proc in procedures:
        token = _extract_source_issue(proc.read_text(encoding="utf-8"))
        if token:
            issue_tokens.add(token)

    for plan_dir in plan_dirs:
        if not plan_dir.is_dir():
            continue
        for plan in sorted(plan_dir.glob("*.md")):
            content = plan.read_text(encoding="utf-8")
            if any(token in content for token in issue_tokens):
                candidates.append(plan)

    return candidates[0] if candidates else None


def _current_stamp() -> str:
    """Return the current local time as `YYYYMMDD-HHMMSS` (per templates/execution-status.md)."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def cmd_close_batch(args: argparse.Namespace) -> int:
    """Archive every procedure of a batch and mark its owning plan `Completed`.

    Discovers the batch, runs an atomic `Pending` pre-check across all procedures
    (refusing with no file moved when any row is `Pending`), marks each procedure's
    rows `Completed`, archives each via `move_to_done()`, then updates the owning
    plan's rows. A batch's renames always stage (never auto-commit mid-batch) so they
    land in one real commit. `--dry-run` prints the planned moves and edits without
    touching files. A second run on an already-closed batch is a no-op (exit 0).
    """
    try:
        prefix = _batch_prefix(args.batch_id)
        files = _discover_batch(args.batch_id, prefix)
    except AlreadyClosedBatch as exc:
        print(
            f"OK: batch already closed ({len(exc.files)} file(s) already archived); "
            f"nothing to do"
        )
        return 0
    except BatchResolutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Atomic Pending pre-check across every procedure (runs even in --dry-run).
    pending_by_file: dict[Path, list[dict[str, str]]] = {}
    for proc in files:
        rows = parse_execution_status_rows(proc.read_text(encoding="utf-8"))
        if rows is None:
            print(
                f"ERROR: '{EXECUTION_STATUS_HEADING}' table missing or malformed "
                f"(no 'Status' column) in {proc}",
                file=sys.stderr,
            )
            return 1
        pending = _pending_rows(rows)
        if pending:
            pending_by_file[proc] = pending

    if pending_by_file:
        described = "; ".join(
            f"{proc}: {_describe_rows(pending_by_file[proc])}"
            for proc in pending_by_file
        )
        print(
            f"ERROR: blocked by Pending Execution Status row(s): {described}",
            file=sys.stderr,
        )
        return 1

    owning_plan = _find_owning_plan(files, prefix)

    if args.dry_run:
        print(f"[dry-run] batch {args.batch_id}: {len(files)} procedure(s)")
        for proc in files:
            destination = proc.parent / "done" / proc.name
            print(f"[dry-run]   move {proc} -> {destination}")
            print(f"[dry-run]   edit  {proc}: mark rows Completed")
        if owning_plan is not None:
            print(f"[dry-run]   edit  {owning_plan}: mark rows Completed")
        else:
            print("[dry-run]   owning plan: not found (skipped)")
        return 0

    stamp = _current_stamp()
    # A batch's renames must land in one real commit, so we always stage rather than
    # auto-commit each file mid-batch (the archival move still runs its hooks later).
    stage_only = True

    for proc in files:
        if not update_execution_status(
            source=proc,
            kind="implementation-procedure",
            new_status="Completed",
            new_started=stamp,
            new_completed=stamp,
        ):
            print(f"ERROR: failed to mark rows Completed in {proc}", file=sys.stderr)
            return 1
        result = move_to_done(
            proc, kind="implementation procedure", stage_only=stage_only
        )
        if not result.success:
            print(
                f"ERROR: failed to archive {proc}: {result.error}",
                file=sys.stderr,
            )
            return 1

    if owning_plan is not None:
        plan_rows = parse_execution_status_rows(owning_plan.read_text(encoding="utf-8"))
        already_all_completed = bool(
            plan_rows
            and all(row.get("Status", "").strip() == "Completed" for row in plan_rows)
        )
        if already_all_completed:
            # Idempotency guard (REQ-007): never re-stamp already-Completed rows.
            print(f"OK: plan {owning_plan} already Closed; rows not re-stamped")
        elif not update_execution_status(
            source=owning_plan,
            kind="plan",
            new_status="Completed",
            new_started=stamp,
            new_completed=stamp,
        ):
            print(
                f"ERROR: failed to mark plan rows Completed in {owning_plan}",
                file=sys.stderr,
            )
            return 1
        else:
            print(f"OK: plan {owning_plan} marked Completed")
    else:
        print(
            f"NOTE: owning plan for batch {args.batch_id} not found; "
            f"plan status not updated"
        )

    detail = f"{len(files)} procedure(s) archived"
    if owning_plan is not None:
        detail += f", plan {owning_plan} marked Completed"
    print(f"OK: closed batch {args.batch_id}: {detail}")
    return 0


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
        new_started=args.started,
        new_completed=args.completed,
    )
    if not modified:
        return 1
    msg_parts = [f"OK: updated all rows to '{args.status}' in {source}"]
    if args.started is not None:
        msg_parts.append(f"Started set: '{args.started}'")
    if args.completed is not None:
        msg_parts.append(f"Completed set: '{args.completed}'")
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
        new_started=args.started,
        new_completed=args.completed,
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
    if args.started is not None:
        output_msg += f"; Started set: '{args.started}'"
    if args.completed is not None:
        output_msg += f"; Completed set: '{args.completed}'"
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


_PHASE_LINE_RE = re.compile(r"^(\d+)\.\s")
_NO_PHASE = float("inf")


def _extract_traceability_field(content: str, label: str) -> str | None:
    """Return the text after a `**{label}**:` Traceability field, backticks removed."""
    match = re.search(rf"\*\*{re.escape(label)}\*\*:[ \t]*(.+)", content)
    if match is None:
        return None
    return match.group(1).strip().replace("`", "")


def _plan_phase_map(plan_text: str) -> list[tuple[int, str]]:
    """Return `(phase number, item text)` for each `## Implementation steps` item.

    An item opens at a line starting `N. ` and runs through its sub-bullets.
    """
    match = re.search(r"(?m)^## Implementation steps\s*$", plan_text)
    if match is None:
        return []
    following = re.compile(r"(?m)^## ").search(plan_text, match.end())
    section = plan_text[match.end() : following.start() if following else None]
    phases: list[tuple[int, list[str]]] = []
    for line in section.splitlines():
        opener = _PHASE_LINE_RE.match(line)
        if opener is not None:
            phases.append((int(opener.group(1)), [line]))
        elif phases:
            phases[-1][1].append(line)
    return [(number, "\n".join(lines)) for number, lines in phases]


def _phase_of_targets(targets: list[str], phases: list[tuple[int, str]]) -> int | float:
    """Return the first Plan phase citing any of `targets`, or `_NO_PHASE`."""
    for number, text in phases:
        for target in targets:
            if re.search(rf"(?<![\w/.-]){re.escape(target)}(?![\w/-])", text):
                return number
    return _NO_PHASE


def _normalize_plan_path(path: str) -> str:
    """Treat `plans/done/x.md` and `plans/x.md` as the same Plan."""
    return path.replace("plans/done/", "plans/", 1)


def _resolve_plan_file(plan_arg: str) -> Path | None:
    """Return the Plan file at `plan_arg`, or its `plans/` / `plans/done/` twin."""
    plan = Path(plan_arg)
    if plan.is_file():
        return plan
    normalized = _normalize_plan_path(plan.as_posix())
    for candidate in (Path(normalized), Path(normalized).parent / "done" / plan.name):
        if candidate.is_file():
            return candidate
    return None


def _procedure_is_gated(content: str) -> bool:
    rows = parse_execution_status_rows(content) or []
    return any(row.get("Notes", "").startswith("Gated:") for row in rows)


def _release_unit_name(content: str) -> str | None:
    """Return the unit named by a procedure's `**Release unit**` line, or None.

    `None` when the line is absent or its value starts with `N/A` (no unit).
    """
    match = re.search(
        r"(?m)^[ \t]*(?:- )?\*\*Release unit\*\*:[ \t]*(.+?)[ \t]*$", content
    )
    if match is None:
        return None
    name = match.group(1).replace("`", "").strip()
    return None if not name or name.startswith("N/A") else name


def _source_plan_path(content: str) -> str | None:
    """Return the normalized `**Source plan**` path, or None when absent or `N/A`."""
    value = _extract_traceability_field(content, "Source plan")
    if value is None or value.startswith("N/A"):
        return None
    return _normalize_plan_path(value)


def cmd_list_order(args):
    """List the procedures of one Plan grouped by Plan phase order (read-only)."""
    plan = _resolve_plan_file(args.plan)
    if plan is None:
        print(f"ERROR: plan not found: {args.plan}", file=sys.stderr)
        return 1
    plan_key = _normalize_plan_path(plan.as_posix())
    phases = _plan_phase_map(plan.read_text(encoding="utf-8"))

    entries: list[tuple[int | float, int, Path, str]] = []
    for fpath in _get_workitem_files("implementation-procedure"):
        content = fpath.read_text(encoding="utf-8")
        source = _extract_traceability_field(content, "Source plan")
        if source is None or _normalize_plan_path(source) != plan_key:
            continue
        related = _extract_traceability_field(content, "Related target files") or ""
        targets = [item.strip() for item in related.split(",") if item.strip()]
        seq_match = re.match(r"\d{8}-\d{6}_(\d+)_", fpath.name)
        seq = int(seq_match.group(1)) if seq_match else 0
        entries.append((_phase_of_targets(targets, phases), seq, fpath, content))

    if not entries:
        print(f"No procedures found for plan {args.plan}")
        return 0

    print(f"Plan: {args.plan}")
    current: int | float | None = None
    for phase, _seq, fpath, content in sorted(entries, key=lambda e: (e[0], e[1])):
        if phase != current:
            current = phase
            print("  Phase (unmatched)" if phase == _NO_PHASE else f"  Phase {phase}")
        status = _get_status_from_file(fpath) or "no status"
        gated = " [gated]" if _procedure_is_gated(content) else ""
        print(f"    {fpath} [{status}]{gated}")
        if phase == _NO_PHASE:
            print(f"WARNING: no Plan step cites {fpath}", file=sys.stderr)
    return 0


def cmd_list(args):
    """List workitems filtered by kind and/or status."""
    if args.order and not args.plan:
        print("ERROR: --order requires --plan", file=sys.stderr)
        return 2
    if args.plan and not args.order:
        print("ERROR: --plan requires --order", file=sys.stderr)
        return 2
    if args.order:
        return cmd_list_order(args)
    kinds = [args.kind] if args.kind else ["implementation-procedure", "plan"]
    results = {}

    for kind in kinds:
        for fpath in _get_workitem_files(kind):
            status = _get_status_from_file(fpath)
            if status is None:
                continue
            if args.status and args.status not in status:
                continue
            unit_key = None
            if kind == "implementation-procedure":
                content = fpath.read_text(encoding="utf-8")
                unit = _release_unit_name(content)
                if unit is not None:
                    unit_key = (_source_plan_path(content) or "N/A", unit)
            results.setdefault(status, []).append((fpath, kind, unit_key))

    if not results:
        print("No items found")
        return 0

    for status in sorted(results.keys()):
        print(f"\nStatus: {status}")
        groups = {}
        for fpath, kind, unit_key in results[status]:
            if unit_key is None:
                print(f"  [{kind}] {fpath}")
            else:
                groups.setdefault(unit_key, []).append(fpath)
        for (source_plan, unit), members in sorted(groups.items()):
            print(f"  Unit: {unit} ({source_plan})")
            for fpath in members:
                print(f"    [implementation-procedure] {fpath}")
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
    unit = _release_unit_name(content)
    if unit is not None:
        print(f"Release unit: {unit}")
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
    elif args.subcommand == "close-batch":
        return cmd_close_batch(args)
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
