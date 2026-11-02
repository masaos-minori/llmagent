#!/usr/bin/env python3
"""tools/amend_plan.py
Append one target file to a Frozen Plan in `plans/` consistently.

The tool does the mechanics of a post-freeze amendment and leaves the decision
(whether the amendment is allowed) to the caller, who states its class:

- `fallout`: a file added only to keep existing behavior, tests, inventories, or
  checkers working.
- `scope`: a change to scope or behavior.

Each edit is located by its own section heading or line prefix, never by a global
search for a path string, so a similar path elsewhere in the Plan is not touched:

1. the new row is appended after the last row of `Implementation Target Files`;
2. a dated `Amended ...` line is added after the `Freeze status` note;
3. a row is added to `### Requirement Traceability`;
4. the path is appended to the `Related target files` line;
5. a row is added to `Affected areas`;
6. a checkbox naming the file is appended to the named step of
   `Implementation steps`;
7. a row is added to `### Work Items Created` when `--procedure` is given.

The four Plan Freeze criteria are re-checked for the new row (see
`rules/workflow-lifecycle.md`): the file exists or is declared `New file` with an
existing directory, the reason is stated, evidence is stated, and the requirement
exists in the Plan. All pass: the row is `Verified` and `Frozen` is kept.
Otherwise the row is `Needs confirmation`, the first Freeze status token becomes
`Draft`, and the failed criteria are printed.

After a real run the tool runs `check_workitem_structure.py`,
`audit_plan_target_paths.py`, and `check_plan_target_overlaps.py` and prints
their results (overlap lines are filtered to those naming the amended Plan).
A dry run prints every intended edit and the checks it would run, and writes
nothing. All edits land in one write, so any refusal leaves the Plan unchanged.

Usage:
    python tools/amend_plan.py plans/<plan>.md --file <path> \\
        --responsibility <text> --reason <text> --requirement REQ-001 \\
        --evidence <text> --tests <text> --step 1 --class fallout|scope \\
        [--procedure implementations/<doc>.md] [--dry-run]

Exit codes: 0 success (a dry run, or a reported `Draft` outcome, included);
1 refusal or failed check; 2 usage error.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess  # nosec B404 — fixed argv built from sys.executable and repo scripts, no shell
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PLANS_DIR = ROOT_DIR / "plans"
TOOLS_DIR = Path(__file__).resolve().parent

CLASSES = ("fallout", "scope")
REQUIRED_HEADINGS = (
    "## Requirements",
    "## Implementation Target Files",
    "## Reference Files",
    "## Affected areas",
    "## Implementation steps",
    "## Traceability",
    "### Requirement Traceability",
)
_FREEZE_RE = re.compile(r"^(\*\*Freeze status\*\*:\s*)(\S+)")
_PLACEHOLDER_CELLS = {"", "—", "-", "–"}


class Refusal(Exception):
    """A reason the amendment is refused; the Plan is left unchanged."""


@dataclass
class Amendment:
    plan_path: str
    file: str
    responsibility: str
    reason: str
    requirement: str
    evidence: str
    tests: str
    step: int
    amend_class: str
    procedure: str | None = None


@dataclass
class EditRecord:
    label: str
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)


def _today() -> str:
    return datetime.date.today().isoformat()


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _row(*cells: str) -> str:
    return "| " + " | ".join(cells) + " |"


def _first_cell(line: str) -> str:
    inner = line.strip().strip("|")
    return inner.split("|")[0].strip().strip("`").strip()


def _find_line(lines: list[str], heading: str) -> int | None:
    for idx, line in enumerate(lines):
        if line.rstrip() == heading:
            return idx
    return None


def _section(lines: list[str], heading: str) -> tuple[int, int]:
    """Return [start, end) of a section: heading line to the next heading of the
    same or a higher level."""
    start = _find_line(lines, heading)
    if start is None:
        raise Refusal(f"required section missing: {heading}")
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx]
        if stripped.startswith("#"):
            marks = len(stripped) - len(stripped.lstrip("#"))
            if marks <= level and stripped[marks : marks + 1] == " ":
                end = idx
                break
    return start, end


def _table(lines: list[str], start: int, end: int, name: str) -> tuple[int, int]:
    """Return [first, last] line indexes of the first `|` table in [start, end)."""
    first = next((i for i in range(start, end) if lines[i].startswith("|")), None)
    if first is None:
        raise Refusal(f"no table found in {name}")
    last = first
    while last + 1 < end and lines[last + 1].startswith("|"):
        last += 1
    if last - first < 1:
        raise Refusal(f"table in {name} has no header separator row")
    return first, last


def _table_first_cells(lines: list[str], first: int, last: int) -> list[str]:
    cells = [_first_cell(lines[i]) for i in range(first + 2, last + 1)]
    return [c for c in cells if c not in _PLACEHOLDER_CELLS]


def _acceptance_criteria_for(lines: list[str], requirement: str) -> list[str]:
    try:
        start, end = _section(lines, "## Acceptance Criteria")
    except Refusal:
        return []
    found: list[str] = []
    for line in lines[start:end]:
        m = re.match(r"^\s*[-*]\s*(AC-\d+)\b", line)
        if m and re.search(rf"(?<![\w-]){re.escape(requirement)}(?![\w-])", line):
            found.append(m.group(1))
    return found


def _requirement_defined(lines: list[str], requirement: str) -> bool:
    try:
        start, end = _section(lines, "## Requirements")
    except Refusal:
        return False
    pattern = re.compile(rf"(?<![\w-]){re.escape(requirement)}(?![\w-])")
    return any(pattern.search(line) for line in lines[start + 1 : end])


def _is_new_declared(am: Amendment) -> bool:
    return any(
        text.strip().lower().startswith("new file")
        for text in (am.responsibility, am.reason)
    )


def check_freeze_criteria(am: Amendment, lines: list[str], root: Path) -> list[str]:
    """Return the failed Plan Freeze criteria for the new row (empty when all pass)."""
    failed: list[str] = []
    target = root / am.file
    if not target.exists():
        if not _is_new_declared(am):
            failed.append(
                "exists: path does not exist and the row is not declared 'New file'"
            )
        elif not target.parent.is_dir():
            failed.append(
                "exists: declared 'New file' but its containing directory "
                f"does not exist ({Path(am.file).parent.as_posix()})"
            )
    if not am.reason.strip():
        failed.append("requires modification: reason for modification is empty")
    if not am.evidence.strip():
        failed.append("supporting evidence: repository evidence is empty")
    if not _requirement_defined(lines, am.requirement):
        failed.append(
            f"linked to a requirement: {am.requirement} is not defined in the "
            "Plan's Requirements"
        )
    return failed


def _validate_args(am: Amendment) -> None:
    path = am.file
    if (
        not path
        or path.startswith(("/", "./", "../"))
        or path.endswith("/")
        or any(ch in path for ch in "*?[]{}")
        or " " in path
    ):
        raise Refusal(
            f"--file must be one exact repository-relative file path, got {path!r}"
        )
    if am.amend_class not in CLASSES:
        raise Refusal(f"--class must be one of {', '.join(CLASSES)}")
    if am.step < 1:
        raise Refusal("--step must be a positive step number")


def _check_plan_location(plan: Path, plans_dir: Path) -> None:
    if plan.suffix != ".md":
        raise Refusal(f"not a Markdown Plan: {plan}")
    resolved = plan.resolve()
    if not plan.is_file():
        raise Refusal(f"Plan not found: {plan}")
    if resolved.parent == (plans_dir / "done").resolve():
        raise Refusal(f"archived Plan (plans/done/) cannot be amended: {plan}")
    if resolved.parent != plans_dir.resolve():
        raise Refusal(f"Plan must be directly under plans/: {plan}")


def _edit_target_row(
    lines: list[str], am: Amendment, failed: list[str], root: Path
) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "## Implementation Target Files")
    first, last = _table(lines, start, end, "Implementation Target Files")
    targets = _table_first_cells(lines, first, last)
    if am.file in targets:
        raise Refusal(f"{am.file} is already an Implementation Target Files row")
    ref_start, ref_end = _section(lines, "## Reference Files")
    ref_table = [i for i in range(ref_start, ref_end) if lines[i].startswith("|")]
    if ref_table:
        ref_cells = _table_first_cells(lines, ref_table[0], ref_table[-1])
        if am.file in ref_cells:
            raise Refusal(
                f"{am.file} is already a Reference Files row; it is read-only "
                "evidence, move it deliberately instead of amending"
            )
    responsibility = am.responsibility.strip()
    if (
        not (root / am.file).exists()
        and _is_new_declared(am)
        and not responsibility.lower().startswith("new file")
    ):
        responsibility = f"New file: {responsibility}"
    status = "Needs confirmation" if failed else "Verified"
    row = _row(
        f"`{am.file}`",
        _cell(responsibility),
        _cell(am.reason),
        _cell(_requirement_cell(lines, am)),
        _cell(am.evidence),
        _cell(am.tests),
        status,
    )
    record = EditRecord("Implementation Target Files: append row", added=[row])
    return lines[: last + 1] + [row] + lines[last + 1 :], record


def _requirement_cell(lines: list[str], am: Amendment) -> str:
    acs = _acceptance_criteria_for(lines, am.requirement)
    return f"{am.requirement} / {', '.join(acs) if acs else f'N/A: none cites {am.requirement}'}"


def _edit_freeze_note(
    lines: list[str], am: Amendment, failed: list[str]
) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "## Implementation Target Files")
    note = next((i for i in range(start, end) if _FREEZE_RE.match(lines[i])), None)
    if note is None:
        raise Refusal("Freeze status line missing in Implementation Target Files")
    prefix = f"Amended {_today()} ({am.amend_class}): added {am.file}"
    dup = re.compile(rf"^Amended \S+ \(\w+\): added {re.escape(am.file)}( |$)")
    if any(dup.match(lines[i]) for i in range(start, end)):
        raise Refusal(f"an amendment line for {am.file} already exists")
    amendment = f"{prefix} — {_cell(am.reason)}"
    out = list(lines)
    record = EditRecord("Freeze status: dated amendment line")
    if failed:
        m = _FREEZE_RE.match(out[note])
        if m is not None and m.group(2) != "Draft":
            before = out[note]
            out[note] = f"{m.group(1)}Draft{out[note][m.end() :]}"
            record.removed.append(before)
            record.added.append(out[note])
        amendment += " [freeze check failed: " + "; ".join(failed) + "]"
    insert_at = note + 1
    while (
        insert_at < end
        and out[insert_at].strip()
        and not out[insert_at].startswith(("|", "#"))
    ):
        insert_at += 1
    out.insert(insert_at, amendment)
    record.added.append(amendment)
    return out, record


def _edit_requirement_traceability(
    lines: list[str], am: Amendment, failed: list[str]
) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "### Requirement Traceability")
    _first, last = _table(lines, start, end, "Requirement Traceability")
    acs = _acceptance_criteria_for(lines, am.requirement)
    row = _row(
        am.requirement,
        _cell(f"Amendment {_today()}: {am.reason}"),
        _cell(am.file),
        f"Phase {am.step}",
        ", ".join(acs) if acs else f"N/A: none cites {am.requirement}",
        _cell(am.tests),
        "Needs confirmation" if failed else "Confirmed by repository evidence",
    )
    record = EditRecord("Requirement Traceability: append row", added=[row])
    return lines[: last + 1] + [row] + lines[last + 1 :], record


def _edit_related_target_files(
    lines: list[str], am: Amendment
) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "## Traceability")
    idx = next(
        (
            i
            for i in range(start, end)
            if lines[i].startswith("- **Related target files**:")
        ),
        None,
    )
    if idx is None:
        raise Refusal("Related target files line missing in Traceability")
    line = lines[idx]
    head, sep, tail = line.partition(" — ")
    entry = f"`{am.file}`" if "`" in head else am.file
    new_line = f"{head.rstrip()}, {entry}{sep}{tail}"
    out = list(lines)
    out[idx] = new_line
    return out, EditRecord(
        "Traceability: append to Related target files", [line], [new_line]
    )


def _edit_affected_areas(
    lines: list[str], am: Amendment, root: Path
) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "## Affected areas")
    first, last = _table(lines, start, end, "Affected areas")
    date = _today()
    change = "Modify" if (root / am.file).exists() else "Create"
    row = _row(
        f"`{am.file}`",
        change,
        f"Not assessed (amendment {date})",
        "N/A",
        "N/A",
        f"Not assessed (amendment {date})",
    )
    record = EditRecord("Affected areas: append row", added=[row])
    if _first_cell(lines[last]) in _PLACEHOLDER_CELLS:
        return lines[:last] + [row] + lines[last + 1 :], EditRecord(
            record.label, [lines[last]], [row]
        )
    return lines[: last + 1] + [row] + lines[last + 1 :], record


def _edit_step(lines: list[str], am: Amendment) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "## Implementation steps")
    item = next(
        (i for i in range(start, end) if re.match(rf"^{am.step}\. \*\*", lines[i])),
        None,
    )
    if item is None:
        raise Refusal(f"step {am.step} not found in Implementation steps")
    block_end = end
    for i in range(item + 1, end):
        if re.match(r"^\d+\. ", lines[i]) or lines[i].startswith("#"):
            block_end = i
            break
    checkbox = re.compile(r"^(\s+)- \[[ xX]\]")
    last_box = None
    indent = "   "
    for i in range(item + 1, block_end):
        m = checkbox.match(lines[i])
        if m:
            last_box, indent = i, m.group(1)
    insert_at = (last_box if last_box is not None else item) + 1
    if last_box is not None:
        while (
            insert_at < block_end
            and lines[insert_at].strip()
            and not checkbox.match(lines[insert_at])
            and len(lines[insert_at]) - len(lines[insert_at].lstrip()) > len(indent)
        ):
            insert_at += 1
    text = (
        f"{indent}- [ ] {_cell(am.responsibility)} "
        f"({am.requirement}; `{am.file}`) — amendment {_today()}"
    )
    out = lines[:insert_at] + [text] + lines[insert_at:]
    return out, EditRecord(f"Implementation steps: step {am.step} checkbox", [], [text])


def _edit_work_items(lines: list[str], am: Amendment) -> tuple[list[str], EditRecord]:
    start, end = _section(lines, "### Work Items Created")
    _first, last = _table(lines, start, end, "Work Items Created")
    row = _row(
        _cell(am.procedure or ""), str(am.step), "Procedure", "Pending", "—", "—"
    )
    if _first_cell(lines[last]) in _PLACEHOLDER_CELLS:
        return lines[:last] + [row] + lines[last + 1 :], EditRecord(
            "Work Items Created: replace placeholder row", [lines[last]], [row]
        )
    return lines[: last + 1] + [row] + lines[last + 1 :], EditRecord(
        "Work Items Created: append row", added=[row]
    )


def build_amendment(
    text: str, am: Amendment, root: Path
) -> tuple[str, list[EditRecord], list[str], list[str]]:
    """Return (new_text, edits, failed_criteria, skipped_notes) or raise Refusal."""
    lines = text.split("\n")
    missing = [h for h in REQUIRED_HEADINGS if _find_line(lines, h) is None]
    if missing:
        raise Refusal("Plan lacks required section(s): " + ", ".join(missing))
    if am.procedure is not None and _find_line(lines, "### Work Items Created") is None:
        raise Refusal("Plan lacks required section: ### Work Items Created")
    failed = check_freeze_criteria(am, lines, root)
    records: list[EditRecord] = []
    skipped: list[str] = []
    steps = [
        lambda ls: _edit_target_row(ls, am, failed, root),
        lambda ls: _edit_freeze_note(ls, am, failed),
        lambda ls: _edit_requirement_traceability(ls, am, failed),
        lambda ls: _edit_related_target_files(ls, am),
        lambda ls: _edit_affected_areas(ls, am, root),
        lambda ls: _edit_step(ls, am),
    ]
    for step in steps:
        lines, record = step(lines)
        records.append(record)
    if am.procedure is not None:
        lines, record = _edit_work_items(lines, am)
        records.append(record)
    else:
        skipped.append(
            "Work Items Created: skipped (no --procedure given; the procedure "
            "does not exist at amendment time)"
        )
    return "\n".join(lines), records, failed, skipped


def _print_edits(records: list[EditRecord]) -> None:
    for record in records:
        print(f"- {record.label}")
        for line in record.removed:
            print(f"    - {line}")
        for line in record.added:
            print(f"    + {line}")


def _run_check(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(  # nosec B603 — fixed argv from sys.executable and repo scripts, no shell
        [sys.executable, *argv],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def _plan_rel(plan: Path) -> str:
    try:
        return plan.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError:
        return plan.as_posix()


def _planned_checks(plan: Path) -> list[tuple[str, list[str]]]:
    rel = _plan_rel(plan)
    return [
        (
            "check_workitem_structure",
            [str(TOOLS_DIR / "check_workitem_structure.py"), "--file", rel],
        ),
        (
            "audit_plan_target_paths",
            [str(TOOLS_DIR / "audit_plan_target_paths.py"), rel],
        ),
        (
            "check_plan_target_overlaps",
            [str(TOOLS_DIR / "check_plan_target_overlaps.py")],
        ),
    ]


def run_checks(plan: Path) -> int:
    rel = _plan_rel(plan)
    exit_code = 0
    for name, argv in _planned_checks(plan):
        code, output = _run_check(argv)
        if name == "check_plan_target_overlaps":
            lines = [ln for ln in output.splitlines() if rel in ln or plan.name in ln]
            output = "\n".join(lines) or f"no overlap finding names {rel}"
        elif name == "audit_plan_target_paths" or name == "check_workitem_structure":
            if code != 0:
                exit_code = 1
        print(f"[{name}] exit {code}")
        if output:
            print("\n".join(f"    {ln}" for ln in output.splitlines()))
    return exit_code


def amend(am: Amendment, dry_run: bool) -> int:
    plans_dir, root = PLANS_DIR, ROOT_DIR
    plan = Path(am.plan_path)
    try:
        _validate_args(am)
        _check_plan_location(plan, plans_dir)
        text = plan.read_text(encoding="utf-8")
        new_text, records, failed, skipped = build_amendment(text, am, root)
    except Refusal as exc:
        print(f"Refused: {exc}")
        return 1
    mode = "Dry run" if dry_run else "Amending"
    print(f"{mode}: {am.plan_path} (+ {am.file}, class {am.amend_class})")
    _print_edits(records)
    for note in skipped:
        print(f"- {note}")
    if failed:
        print("Freeze re-check: FAILED, Freeze status set to Draft")
        for item in failed:
            print(f"    - {item}")
    else:
        print("Freeze re-check: passed, Frozen kept, row Verified")
    if dry_run:
        print("Dry run: nothing written. Checks that would run after a real run:")
        for name, _argv in _planned_checks(plan):
            print(f"    {name}")
        return 0
    tmp = plan.with_name(f".{plan.name}.amend.tmp")
    try:
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, plan)
    finally:
        if tmp.exists():
            tmp.unlink()
    return run_checks(plan)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Append one target file to a Frozen Plan in plans/ consistently, "
            "re-check the Plan Freeze criteria for the new row, and run the "
            "structure, path-audit, and overlap checks."
        )
    )
    parser.add_argument("plan", help="plans/<plan>.md (archived Plans are refused)")
    parser.add_argument("--file", required=True, help="repository-relative path")
    parser.add_argument("--responsibility", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--requirement", required=True, help="e.g. REQ-001")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--step", required=True, type=int)
    parser.add_argument("--class", dest="amend_class", required=True, choices=CLASSES)
    parser.add_argument("--procedure", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    am = Amendment(
        plan_path=args.plan,
        file=args.file.strip(),
        responsibility=args.responsibility,
        reason=args.reason,
        requirement=args.requirement.strip(),
        evidence=args.evidence,
        tests=args.tests,
        step=args.step,
        amend_class=args.amend_class,
        procedure=args.procedure,
    )
    return amend(am, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
