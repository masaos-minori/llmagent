#!/usr/bin/env python3
"""tools/close_procedures_batch.py - Verified batch close of executed procedures.

Closing a batch of implementation procedures is a fixed sequence: check that every
step of each procedure was carried out, archive it with the rename staged, mark the
matching `Work Items Created` row of the owning Plan, and mark the Plan steps that the
batch completed. `manage_workitem_stage.py close-batch` does the sequence by setting
every row of every procedure and of the Plan to `Completed`, which overwrites true
statuses, so it is not used for this workflow. This tool verifies first and writes only
what it verified.

Usage:
    python tools/close_procedures_batch.py PROC... [--plan PLAN] [--plan-steps N,M]
        [--complete-rows --note TEXT] [--dry-run]

Behavior:
- Verify (no write): each PROC must be a file directly under `implementations/`, its
  `### Execution Status` table must parse, and every row must be `Completed` or `N/A`
  (the tool never writes `N/A`). A `Pending`, `In Progress`, or `Blocked` row refuses
  the procedure and names the row. The destination in `implementations/done/` must be
  free, and the Plan (`--plan`, else the common `Source plan` of the procedures, looked
  up in `plans/` then `plans/done/`) must exist. A refused procedure is reported and
  left untouched; the others proceed.
- `--complete-rows --note TEXT` additionally lets `Pending` rows pass: only those rows
  are set to `Completed` with TEXT as their Notes. `Blocked`, `In Progress`, and `N/A`
  rows are never overwritten, and a `Pending` row that carries a `Gated:` marker is
  refused because only the owner clears that marker. Rows are never completed
  implicitly; `--note` is required with the option.
- Archive: each verified procedure is moved to `implementations/done/` with the rename
  staged (`move_to_done(..., stage_only=True)`); nothing is committed. A failed archive
  is reported and does not stop the others.
- Plan: the `Work Items Created` row whose Item ID is the procedure's path is set to
  `Completed` when present (a Plan without the row is reported, not failed). With
  `--plan-steps N,M`, step N is set to `Completed` only when the Plan's
  `Implementation steps` item N cites at least one `Implementation Target Files` path
  and every cited path has an archived procedure whose `Source plan` is this Plan
  (this batch's included; a procedure's `Related target files` may be a comma-separated
  list). Otherwise the step is left unchanged and the reason is reported. Without
  `--plan-steps`, the steps whose cited files are all archived are listed as
  candidates and none is changed: a check-only step can cite the same files, so the
  caller decides which steps modify files.
- `--dry-run` prints every intended change and writes nothing.

Exit status: 0 when no procedure was refused and no archive failed, 1 otherwise, 2 on a
usage error. A step left unchanged does not make the exit non-zero.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.manage_workitem_stage import (
    MoveResult,
    move_to_done,
    parse_execution_status_rows,
    update_execution_status,
)
from tools.set_execution_status import ExecutionStatusError, update_document

IMPL_DIR = Path("implementations")
PLAN_DIRS = (Path("plans"), Path("plans/done"))
TERMINAL_STATUSES = frozenset({"Completed", "N/A"})
WORK_ITEMS_HEADING = "### Work Items Created"
GATED_PREFIX = "Gated:"

_BACKTICKED = re.compile(r"`([^`]+)`")
_NUMBERED = re.compile(r"^(\d+)\.\s")
_TRACE_LINE = r"^-\s+\*\*{label}\*\*:\s*(.*)$"


@dataclass(frozen=True)
class ProcedureCheck:
    """Result of verifying one procedure; `refusal` is None when it may proceed."""

    path: Path
    refusal: str | None = None
    pending_steps: tuple[str, ...] = ()
    related: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanStep:
    """One numbered item of a Plan's `Implementation steps`."""

    number: int
    title: str
    cited: tuple[str, ...]


@dataclass
class ApplyResult:
    """Outcome of applying one verified procedure."""

    path: Path
    archived: bool = False
    error: str | None = None
    completed_rows: tuple[str, ...] = ()


@dataclass
class BatchReport:
    """Counts printed on the final line."""

    verified: int = 0
    refused: int = 0
    archived: int = 0
    failed: int = 0
    steps_marked: int = 0
    steps_left: int = 0
    lines: list[str] = field(default_factory=list)


def _traceability_value(content: str, label: str) -> str | None:
    match = re.search(_TRACE_LINE.format(label=re.escape(label)), content, re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_source_plan(content: str) -> str | None:
    """Return the Traceability `Source plan` path, or None for `N/A` or absent."""
    value = _traceability_value(content, "Source plan")
    if value is None:
        return None
    value = value.strip("`").strip()
    if not value or value.upper().startswith("N/A"):
        return None
    return value.split()[0].strip("`")


def parse_related_targets(content: str) -> list[str]:
    """Return the Traceability `Related target files` as a list of paths.

    The value is a comma-separated list; backticks and any ` - ` or em-dash trailer
    after the list are dropped.
    """
    value = _traceability_value(content, "Related target files")
    if value is None:
        return []
    value = re.split(r"\s+[—-]\s+", value, maxsplit=1)[0]
    paths = [part.strip().strip("`").strip() for part in value.split(",")]
    return [path for path in paths if path and not path.upper().startswith("N/A")]


def resolve_plan(reference: str | Path) -> Path | None:
    """Find a Plan by its file name in `plans/` then `plans/done/`."""
    name = Path(str(reference)).name
    for directory in PLAN_DIRS:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def verify_procedure(
    path: Path, *, complete_rows: bool, plan_path: Path | None
) -> ProcedureCheck:
    """Check one procedure without writing anything."""
    if path.resolve().parent != IMPL_DIR.resolve():
        return ProcedureCheck(
            path, refusal=f"not a file directly under {IMPL_DIR}/: {path}"
        )
    if not path.is_file():
        return ProcedureCheck(path, refusal=f"file not found: {path}")
    content = path.read_text(encoding="utf-8")
    rows = parse_execution_status_rows(content)
    if not rows:
        return ProcedureCheck(
            path, refusal="Execution Status table missing, malformed, or empty"
        )
    pending: list[str] = []
    for row in rows:
        status = row.get("Status", "").strip()
        step = row.get("Step", "?")
        if status in TERMINAL_STATUSES:
            continue
        if status == "Pending" and complete_rows:
            if row.get("Notes", "").strip().startswith(GATED_PREFIX):
                return ProcedureCheck(
                    path,
                    refusal=f"Step {step} carries a Gated marker (owner clears it)",
                )
            pending.append(step)
            continue
        return ProcedureCheck(
            path,
            refusal=f"Step {step} is {status or 'empty'}: {row.get('Description')}",
        )
    destination = IMPL_DIR / "done" / path.name
    if destination.exists():
        return ProcedureCheck(
            path, refusal=f"archive destination exists: {destination}"
        )
    if not destination.parent.is_dir():
        return ProcedureCheck(
            path, refusal=f"archive directory missing: {destination.parent}"
        )
    if plan_path is None or not plan_path.is_file():
        return ProcedureCheck(path, refusal="Plan not found")
    return ProcedureCheck(
        path,
        pending_steps=tuple(pending),
        related=tuple(parse_related_targets(content)),
    )


def _section_lines(text: str, heading: str) -> list[str]:
    """Lines of the `## ` section whose title equals `heading` (case-insensitive)."""
    lines = text.splitlines()
    start = next(
        (
            i
            for i, line in enumerate(lines)
            if line.startswith("## ") and line[3:].strip().lower() == heading.lower()
        ),
        None,
    )
    if start is None:
        return []
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return lines[start + 1 : end]


def parse_target_paths(plan_text: str) -> set[str]:
    """Paths in the first column of the Plan's `Implementation Target Files` table."""
    paths: set[str] = set()
    for line in _section_lines(plan_text, "Implementation Target Files"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        first = stripped.strip("|").split("|")[0]
        paths.update(_BACKTICKED.findall(first))
    return paths


def parse_plan_steps(plan_text: str, target_paths: Iterable[str]) -> list[PlanStep]:
    """Read the numbered `Implementation steps` items and the target paths they cite."""
    targets = set(target_paths)
    items: list[tuple[int, list[str]]] = []
    for line in _section_lines(plan_text, "Implementation steps"):
        match = _NUMBERED.match(line)
        if match:
            items.append((int(match.group(1)), [line]))
        elif items:
            items[-1][1].append(line)
    steps: list[PlanStep] = []
    for number, block in items:
        cited: list[str] = []
        for token in _BACKTICKED.findall("\n".join(block)):
            if token in targets and token not in cited:
                cited.append(token)
        title = re.sub(r"^\d+\.\s*", "", block[0]).strip().strip("*")
        steps.append(PlanStep(number, title, tuple(cited)))
    return steps


def check_step_marking(step: PlanStep, archived_paths: set[str]) -> str | None:
    """Return why `step` cannot be marked `Completed`, or None when it can."""
    if not step.cited:
        return "cites no Implementation Target Files path (cannot map it)"
    missing = [path for path in step.cited if path not in archived_paths]
    if missing:
        return "cited file without an archived procedure: " + ", ".join(missing)
    return None


def archived_targets(plan_path: Path) -> set[str]:
    """Target paths covered by procedures in `implementations/done/` for this Plan."""
    covered: set[str] = set()
    done = IMPL_DIR / "done"
    if not done.is_dir():
        return covered
    for procedure in sorted(done.glob("*.md")):
        content = procedure.read_text(encoding="utf-8")
        source = parse_source_plan(content)
        if source is not None and Path(source).name == plan_path.name:
            covered.update(parse_related_targets(content))
    return covered


def update_work_items(
    plan_text: str, archived: Iterable[str]
) -> tuple[str, list[str], list[str]]:
    """Set the Status of the `Work Items Created` rows of archived procedures.

    A row matches when its Item ID (backticks removed) equals the procedure path.
    Returns (new text, matched paths, unmatched paths); a missing table or row is
    reported through `unmatched`, never raised.
    """
    wanted = list(archived)
    lines = plan_text.split("\n")
    heading = next(
        (i for i, line in enumerate(lines) if line.strip() == WORK_ITEMS_HEADING), None
    )
    if heading is None:
        return plan_text, [], wanted
    matched: list[str] = []
    header: list[str] | None = None
    for index in range(heading + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("|"):
            if header is not None:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if header is None:
            header = cells
            if "Item ID" not in header or "Status" not in header:
                return plan_text, [], wanted
            continue
        if all(re.fullmatch(r"-+", cell) for cell in cells):
            continue
        if len(cells) != len(header):
            continue
        tokens = _BACKTICKED.findall(cells[header.index("Item ID")]) or [
            cells[header.index("Item ID")]
        ]
        hit = next((path for path in wanted if path in tokens), None)
        if hit is None:
            continue
        cells[header.index("Status")] = "Completed"
        lines[index] = "| " + " | ".join(cells) + " |"
        matched.append(hit)
    unmatched = [path for path in wanted if path not in matched]
    return "\n".join(lines), matched, unmatched


def apply_procedure(check: ProcedureCheck, *, note: str, stamp: str) -> ApplyResult:
    """Complete the permitted rows, then archive with the rename staged."""
    result = ApplyResult(check.path)
    try:
        if check.pending_steps:
            update_document(
                check.path,
                set(check.pending_steps),
                dict.fromkeys(check.pending_steps, note),
                stamp,
            )
            result.completed_rows = check.pending_steps
    except (ExecutionStatusError, OSError) as exc:
        result.error = f"row completion failed: {exc}"
        return result
    moved: MoveResult = move_to_done(
        check.path, kind="implementation procedure", stage_only=True
    )
    if moved.success:
        result.archived = True
    else:
        suffix = (
            " (rows stay Completed in the unarchived file)"
            if (result.completed_rows)
            else ""
        )
        result.error = f"archive failed: {moved.error}{suffix}"
    return result


def _relative(path: Path) -> Path:
    """Express an absolute path under the working directory as a relative one."""
    try:
        return (
            path.resolve().relative_to(Path.cwd().resolve())
            if path.is_absolute()
            else path
        )
    except ValueError:
        return path


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _parse_steps(raw: str) -> list[int]:
    try:
        steps = sorted({int(part) for part in raw.split(",") if part.strip()})
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--plan-steps needs integers: N,M") from exc
    if not steps:
        raise argparse.ArgumentTypeError("--plan-steps needs at least one number")
    return steps


def _note_text(raw: str) -> str:
    if not raw.strip() or "|" in raw or "\n" in raw:
        raise argparse.ArgumentTypeError("--note must be non-empty, one line, no '|'")
    return raw.strip()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("procedures", nargs="+", type=Path)
    parser.add_argument("--plan", type=Path, help="owning Plan (default: Source plan)")
    parser.add_argument("--plan-steps", type=_parse_steps, default=None)
    parser.add_argument("--complete-rows", action="store_true")
    parser.add_argument("--note", type=_note_text, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _find_plan(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> Path | None:
    if args.plan is not None:
        return resolve_plan(args.plan)
    sources: set[str] = set()
    for path in args.procedures:
        if path.is_file():
            source = parse_source_plan(path.read_text(encoding="utf-8"))
            if source:
                sources.add(Path(source).name)
    if len(sources) > 1:
        parser.error(f"procedures name different Source plans: {sorted(sources)}")
    return resolve_plan(next(iter(sources))) if sources else None


def _plan_step_report(
    plan_path: Path,
    steps: list[PlanStep],
    named: list[int] | None,
    covered: set[str],
    *,
    dry_run: bool,
    report: BatchReport,
    stamp: str,
) -> None:
    status_rows = parse_execution_status_rows(plan_path.read_text(encoding="utf-8"))
    status_of = {
        row.get("Step", ""): row.get("Status", "") for row in status_rows or []
    }
    by_number = {step.number: step for step in steps}
    if named is None:
        candidates = [
            step.number
            for step in steps
            if check_step_marking(step, covered) is None
            and status_of.get(str(step.number)) != "Completed"
        ]
        report.lines.append(
            "candidate steps (none changed; pass --plan-steps): "
            + (", ".join(map(str, candidates)) or "none")
        )
        return
    for number in named:
        step = by_number.get(number)
        reason: str | None
        if step is None:
            reason = "no such Implementation steps item"
        elif str(number) not in status_of:
            reason = "no Execution Status row for this step"
        elif status_of[str(number)] == "Completed":
            reason = "already Completed"
        else:
            reason = check_step_marking(step, covered)
        if reason is not None:
            report.steps_left += 1
            report.lines.append(f"step {number}: left unchanged - {reason}")
            continue
        if not dry_run and not update_execution_status(
            plan_path,
            "plan",
            step_number=number,
            new_status="Completed",
            new_completed=stamp,
        ):
            report.steps_left += 1
            report.lines.append(f"step {number}: left unchanged - status update failed")
            continue
        report.steps_marked += 1
        verb = "would mark" if dry_run else "marked"
        report.lines.append(f"step {number}: {verb} Completed")


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: verify, then archive, then update the Plan."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.procedures = [_relative(path) for path in args.procedures]
    if args.complete_rows and not args.note:
        parser.error("--complete-rows requires --note")
    if args.note and not args.complete_rows:
        parser.error("--note is only used with --complete-rows")
    plan_path = _find_plan(args, parser)
    stamp = _stamp()
    report = BatchReport()
    checks = [
        verify_procedure(path, complete_rows=args.complete_rows, plan_path=plan_path)
        for path in args.procedures
    ]
    verified = [check for check in checks if check.refusal is None]
    report.verified = len(verified)
    report.refused = len(checks) - len(verified)
    for check in checks:
        if check.refusal is not None:
            report.lines.append(f"refused {check.path}: {check.refusal}")
    archived: list[ProcedureCheck] = []
    for check in verified:
        rows = (
            f" (complete rows: {', '.join(check.pending_steps)})"
            if check.pending_steps
            else ""
        )
        if args.dry_run:
            report.lines.append(f"would archive {check.path}{rows}")
            archived.append(check)
            continue
        result = apply_procedure(check, note=args.note or "", stamp=stamp)
        if result.archived:
            report.archived += 1
            archived.append(check)
            report.lines.append(f"archived {check.path}{rows}")
        else:
            report.failed += 1
            report.lines.append(f"failed {check.path}: {result.error}")
    if args.dry_run:
        report.archived = len(archived)
    if plan_path is not None:
        _update_plan(plan_path, archived, args, report, stamp)
    print("\n".join(report.lines))
    prefix = "dry run: " if args.dry_run else ""
    print(
        f"{prefix}verified={report.verified} refused={report.refused} "
        f"archived={report.archived} failed={report.failed} "
        f"steps_marked={report.steps_marked} steps_left={report.steps_left}"
    )
    return 1 if report.refused or report.failed else 0


def _update_plan(
    plan_path: Path,
    archived: list[ProcedureCheck],
    args: argparse.Namespace,
    report: BatchReport,
    stamp: str,
) -> None:
    text = plan_path.read_text(encoding="utf-8")
    paths = [check.path.as_posix() for check in archived]
    new_text, matched, unmatched = update_work_items(text, paths)
    for path in matched:
        verb = "would set" if args.dry_run else "set"
        report.lines.append(f"work item {path}: {verb} Completed in {plan_path}")
    for path in unmatched:
        report.lines.append(f"work item {path}: no row in {plan_path} (not failed)")
    if new_text != text and not args.dry_run:
        plan_path.write_text(new_text, encoding="utf-8")
    covered = archived_targets(plan_path)
    for check in archived:
        covered.update(check.related)
    steps = parse_plan_steps(new_text, parse_target_paths(new_text))
    _plan_step_report(
        plan_path,
        steps,
        args.plan_steps,
        covered,
        dry_run=args.dry_run,
        report=report,
        stamp=stamp,
    )
    if not args.dry_run and not plan_path.read_text(encoding="utf-8").endswith("\n"):
        with plan_path.open("a", encoding="utf-8") as handle:
            handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
