#!/usr/bin/env python3
"""tools/clear_gated_markers.py — Apply an owner decision to clear stale `Gated:`
markers from the Notes column of an implementation procedure's Execution Status table.

`templates/execution-status.md`: only the owner clears a `Gated:` marker; this tool is
the mechanical application of an already-made owner decision once the blocking plan has
been executed and archived. It replaces the marker prefix with an operator-supplied
record (`--record`, never invented here), keeps the remaining Notes text, and normalizes
rows whose companion note was written as a seventh cell past the template's six
columns — a generator artifact that `set_execution_status.py` and
`manage_workitem_stage.py close-implementation` refuse to parse. Only `Pending` rows
whose Notes start with `Gated:` are touched; Status, Started, and Completed are never
changed. `--rewrite OLD:NEW` fixes stale claim phrases inside the Notes text, and
`--dry-run` prints the unified diff without writing.

Usage:
    python -m tools.clear_gated_markers.py <procedure.md>... --record TEXT [--rewrite OLD:NEW] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run

HEADING = "### Execution Status"
MARKER_PREFIX = "Gated:"
COLUMNS = ("step", "description", "status", "started", "completed", "notes")
EMPTY_CELL = "\u2014"
GATED_STATUS = "Pending"


class MarkerError(Exception):
    """Raised when the procedure document does not carry a parseable Execution Status table."""


def split_row(line: str) -> list[str]:
    """Split one Markdown table row into its trimmed cells."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    """True for the `|---|---|` line that follows a table header row."""
    body = line.strip().strip("|")
    return bool(body) and all(set(cell.strip()) <= {"-"} for cell in body.split("|"))


def find_table(lines: list[str]) -> tuple[int, int]:
    """Return the half-open line range of the table's data rows.

    Raises `MarkerError` when the heading, the header row, or the separator is missing.
    """
    try:
        heading_at = next(i for i, line in enumerate(lines) if line.strip() == HEADING)
    except StopIteration as exc:
        raise MarkerError(f"no {HEADING!r} heading found") from exc

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
        raise MarkerError(f"{HEADING} heading is not followed by a table")

    start = header_at + 2
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    if end == start:
        raise MarkerError("the Execution Status table has no data rows")
    return start, end


def parse_rows(lines: list[str], start: int, end: int) -> list[dict[str, str]]:
    """Parse data rows into column-keyed dicts.

    A row written with a seventh cell past the template's six columns keeps that extra
    text in a `companion` key rather than folding it into `notes`, so the marker reason
    and the companion note stay distinguishable.
    """
    rows: list[dict[str, str]] = []
    for index in range(start, end):
        cells = split_row(lines[index])
        if len(cells) == len(COLUMNS):
            rows.append(dict(zip(COLUMNS, cells), companion=""))
        elif len(cells) > len(COLUMNS):
            row = dict(zip(COLUMNS, cells[: len(COLUMNS)]))
            row["companion"] = " - ".join(cells[len(COLUMNS) :])
            rows.append(row)
        else:
            raise MarkerError(
                f"line {index + 1} has {len(cells)} cells, expected {len(COLUMNS)}"
            )
    return rows


def clear_markers(
    rows: list[dict[str, str]],
    record: str,
    rewrites: dict[str, str],
) -> list[str]:
    """Replace each `Gated:` marker with the record; return the report lines.

    The marker's original reason is dropped: it explains a block that the owner decision
    resolves. Only the operator-supplied record and the row's companion note remain.
    """
    reports: list[str] = []
    for row in rows:
        if not row["notes"].startswith(MARKER_PREFIX):
            continue
        if row["status"] != GATED_STATUS:
            raise MarkerError(
                f"step {row['step']}: marker on a {row['status']!r} row, expected Pending"
            )
        new_notes = record
        if row["companion"]:
            new_notes += f" - {row['companion']}"
        for old, new in rewrites.items():
            new_notes = new_notes.replace(old, new)
        if "|" in new_notes:
            raise MarkerError(f"step {row['step']}: record or rewrite contains a pipe")
        reports.append(f"step {row['step']}: marker cleared")
        row["notes"] = new_notes
    return reports


def render_rows(rows: list[dict[str, str]]) -> list[str]:
    """Render parsed rows back into six-column Markdown data rows."""
    return [
        "| " + " | ".join(row[col] or EMPTY_CELL for col in COLUMNS) + " |"
        for row in rows
    ]


def update_document(
    path: Path,
    record: str,
    rewrites: dict[str, str],
    dry_run: bool = False,
) -> list[str]:
    """Rewrite one procedure document's Execution Status table and return the report lines."""
    original = path.read_text()
    lines = original.splitlines()
    start, end = find_table(lines)
    rows = parse_rows(lines, start, end)
    reports = clear_markers(rows, record, rewrites)
    if not reports:
        return [f"{path}: no Gated marker found"]
    rebuilt = lines[:start] + render_rows(rows) + lines[end:]
    new_text = "\n".join(rebuilt) + "\n"
    if dry_run:
        print_dry_run(path, original, new_text)
    else:
        atomic_write_text(path, new_text)
    return reports


def parse_rewrite(raw: str) -> dict[str, str]:
    """Parse an `OLD:NEW` rewrite assignment."""
    old, _, new = raw.partition(":")
    if not old.strip() or not new.strip():
        raise argparse.ArgumentTypeError("--rewrite needs the form OLD:NEW")
    return {old.strip(): new.strip()}


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("docs", type=Path, nargs="+", help="procedure documents")
    parser.add_argument("--record", required=True, help="cleared-marker record text")
    parser.add_argument(
        "--rewrite",
        action="append",
        type=parse_rewrite,
        default=[],
        help="OLD:NEW phrase fix inside Notes, repeatable",
    )
    add_dry_run_argument(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the tool; exit 1 on any parse or validation error, 0 otherwise."""
    args = build_parser().parse_args(argv)
    rewrites: dict[str, str] = {}
    for rewrite in args.rewrite:
        rewrites.update(rewrite)

    failed = False
    for doc in args.docs:
        try:
            for report in update_document(doc, args.record, rewrites, args.dry_run):
                print(report)
        except MarkerError as exc:
            print(f"error: {doc}: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
