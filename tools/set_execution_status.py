#!/usr/bin/env python3
"""tools/set_execution_status.py — Mark Execution Status table rows Completed.

`templates/execution-status.md` gives every implementation procedure a `### Execution
Status` table whose `Status` column starts as `Pending`. `manage_workitem_stage.py
close-implementation` refuses to archive a procedure while any row is still `Pending`,
so the column has to be updated as each step lands. Doing it by hand means editing a
Markdown table cell for every step of every procedure, which is the same operation
repeated across a batch of procedures.

This tool updates the table in place:

- It selects the data rows of the `### Execution Status` table (the first Markdown
  table after that heading) and rewrites only the `Status`, `Started`, `Completed`,
  and `Notes` columns. `Step` and `Description` are never touched, because the
  `Description` column is what the procedure's own `## Implementation` section is
  traced against.
- `--all` selects every data row; `--step 1,4` selects specific rows. A selected step
  that the table does not contain is an error, so a typo cannot silently skip a step.
- `--note STEP:TEXT` sets that row's `Notes` cell. Notes are how a row records a
  deviation or a validation gate that was satisfied by a sibling row, so the text is
  supplied by the operator and never invented here.

Usage:
    python -m tools.set_execution_status.py <procedure.md> --all [--date YYYY-MM-DD]
    python -m tools.set_execution_status.py <procedure.md> --step 1,4 --note 4:landed with row 22
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

HEADING = "### Execution Status"
DONE_STATUS = "Completed"
EMPTY_CELL = "\u2014"

# Columns of the Execution Status table, in file order.
COLUMNS = ("step", "description", "status", "started", "completed", "notes")


class ExecutionStatusError(Exception):
    """Raised when the procedure document does not carry a parseable Execution Status table."""


def split_row(line: str) -> list[str]:
    """Split one Markdown table row into its trimmed cells."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    """True for the `|---|---|` line that follows a table header row."""
    body = line.strip().strip("|")
    return bool(body) and all(set(cell.strip()) <= {"-"} for cell in body.split("|"))


def find_table(lines: list[str]) -> tuple[int, int]:
    """Return the half-open line range of the Execution Status table's data rows.

    Raises `ExecutionStatusError` when the heading, the header row, or the separator is
    missing, because a procedure whose table cannot be located cannot be closed.
    """
    try:
        heading_at = next(i for i, line in enumerate(lines) if line.strip() == HEADING)
    except StopIteration as exc:
        raise ExecutionStatusError(f"no {HEADING!r} heading found") from exc

    header_at = next(
        (
            i
            for i in range(heading_at + 1, len(lines))
            if lines[i].lstrip().startswith("|")
        ),
        None,
    )
    if (
        header_at is None
        or header_at + 1 >= len(lines)
        or not _is_separator(lines[header_at + 1])
    ):
        raise ExecutionStatusError(f"{HEADING} heading is not followed by a table")

    start = header_at + 2
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    if end == start:
        raise ExecutionStatusError("the Execution Status table has no data rows")
    return start, end


def parse_rows(lines: list[str], start: int, end: int) -> list[dict[str, str]]:
    """Parse the data rows of the table into column-name keyed dicts."""
    rows: list[dict[str, str]] = []
    for index in range(start, end):
        cells = split_row(lines[index])
        if len(cells) != len(COLUMNS):
            raise ExecutionStatusError(
                f"line {index + 1} has {len(cells)} cells, expected {len(COLUMNS)}"
            )
        rows.append(dict(zip(COLUMNS, cells)))
    return rows


def apply_updates(
    rows: list[dict[str, str]],
    steps: set[str] | None,
    notes: dict[str, str],
    date: str,
) -> list[str]:
    """Mutate the selected rows and return one report line per changed row.

    `steps` of None selects every row. A step named in `notes` but not selected is an
    error, because the operator intended to record something against it.
    """
    selected = [row for row in rows if steps is None or row["step"] in steps]
    if steps is not None:
        missing = steps - {row["step"] for row in selected}
        if missing:
            raise ExecutionStatusError(
                f"no table row for step(s): {', '.join(sorted(missing))}"
            )
    unknown = set(notes) - {row["step"] for row in selected}
    if unknown:
        raise ExecutionStatusError(
            f"--note names unselected or missing step(s): {', '.join(sorted(unknown))}"
        )

    reports: list[str] = []
    for row in selected:
        before = row["status"]
        row["status"] = DONE_STATUS
        if row["started"] in ("", EMPTY_CELL):
            row["started"] = date
        row["completed"] = date
        if row["step"] in notes:
            row["notes"] = notes[row["step"]]
        reports.append(f"step {row['step']}: {before} -> {DONE_STATUS}")
    return reports


def render_rows(rows: list[dict[str, str]]) -> list[str]:
    """Render parsed rows back into Markdown data rows; header and separator stay in place."""
    return [
        "| " + " | ".join(row[col] or EMPTY_CELL for col in COLUMNS) + " |"
        for row in rows
    ]


def update_document(
    path: Path, steps: set[str] | None, notes: dict[str, str], date: str
) -> list[str]:
    """Rewrite one procedure document's Execution Status table and return the report lines."""
    lines = path.read_text().splitlines()
    start, end = find_table(lines)
    rows = parse_rows(lines, start, end)
    reports = apply_updates(rows, steps, notes, date)
    rebuilt = lines[:start] + render_rows(rows) + lines[end:]
    path.write_text("\n".join(rebuilt) + "\n")
    return reports


def parse_steps(raw: str) -> set[str]:
    """Parse a comma-separated step list."""
    steps = {part.strip() for part in raw.split(",") if part.strip()}
    if not steps:
        raise argparse.ArgumentTypeError("--step needs at least one step number")
    return steps


def parse_notes(raw: str) -> dict[str, str]:
    """Parse a `STEP:TEXT` note assignment."""
    step, _, text = raw.partition(":")
    step = step.strip()
    if not step or not text.strip():
        raise argparse.ArgumentTypeError("--note needs the form STEP:TEXT")
    return {step: text.strip()}


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("doc", type=Path, help="implementation procedure document")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="mark every data row")
    group.add_argument("--step", type=parse_steps, help="comma-separated step numbers")
    parser.add_argument(
        "--date",
        default=datetime.date.today().isoformat(),
        help="value written to the Started and Completed columns",
    )
    parser.add_argument(
        "--note",
        action="append",
        type=parse_notes,
        default=[],
        help="STEP:TEXT note assignment, repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: update one procedure document's Execution Status table."""
    args = build_parser().parse_args(argv)
    notes: dict[str, str] = {}
    for note in args.note:
        notes.update(note)
    steps = None if args.all else args.step
    try:
        reports = update_document(args.doc, steps, notes, args.date)
    except (ExecutionStatusError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"{args.doc}: {len(reports)} row(s) updated")
    for report in reports:
        print(f"  {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
