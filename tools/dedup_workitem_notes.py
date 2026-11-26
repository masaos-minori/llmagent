#!/usr/bin/env python3
"""tools/dedup_workitem_notes.py - Removes a duplicated Notes cell in a work item table.

`manage_workitem_stage.py set-step-status --notes` appends to the Notes column, so applying
the same record twice writes the same text twice in one cell. This tool collapses a Notes
cell that is exactly `X X` into `X`, leaving every other cell untouched. It verifies nothing
else: the row must parse as a Markdown table row with a Notes column, and the cell must be a
two-fold repetition of one segment before it changes.

Usage:
    python tools/dedup_workitem_notes.py FILE.md [--dry-run]

Exit codes: 0 when every cell is already single or was collapsed, 1 when a file is missing or
unreadable, 2 on a usage error.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text

NOTES_HEADER = "Notes"


def _split_row(line: str) -> list[str] | None:
    """A Markdown table row as cells, or None when the line is not a row."""
    if not line.startswith("|"):
        return None
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    """Whether a row is the header separator (every cell a run of dashes)."""
    return all(set(cell) <= {"-", ":"} for cell in cells)


def _dedupe_file(path: Path, dry_run: bool) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: {path}: {exc}", file=sys.stderr)
        return 1

    changed = 0
    lines = text.splitlines(keepends=True)
    notes_index: int | None = None
    for number, line in enumerate(lines):
        cells = _split_row(line)
        if cells is None or _is_separator(cells):
            continue
        if NOTES_HEADER in cells:
            notes_index = cells.index(NOTES_HEADER)
            continue
        if notes_index is None or len(cells) <= notes_index:
            continue
        notes = cells[notes_index]
        half = len(notes) // 2
        if len(notes) % 2 == 1 and notes[:half] == notes[half + 1 :]:
            single = notes[:half]
            if dry_run:
                print(f"DRY RUN: {path} line {number + 1}: Notes collapsed")
            else:
                lines[number] = line.replace(notes, single, 1)
            changed += 1

    if not dry_run and changed:
        atomic_write_text(path, "".join(lines))
    print(f"{changed} Notes cell(s) collapsed in {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(
            "Usage: python tools/dedup_workitem_notes.py FILE.md [--dry-run]",
            file=sys.stderr,
        )
        return 2

    dry_run = "--dry-run" in argv
    paths = [a for a in argv if a != "--dry-run"]
    if not paths:
        print("ERROR: no file named", file=sys.stderr)
        return 2

    status = 0
    for arg in paths:
        path = Path(arg)
        if not path.is_file():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            status = 1
            continue
        status = max(status, _dedupe_file(path, dry_run))
    return status


if __name__ == "__main__":
    sys.exit(main())
