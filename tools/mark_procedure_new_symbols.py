#!/usr/bin/env python3
"""tools/mark_procedure_new_symbols.py — Add (new) markers to procedure docs.

`templates/implementation-procedure.md` requires that a name a procedure will
create (it does not exist yet) is written in backticks followed by the marker
`(new)`. `tools/stale_detector.py` skips exactly those marked names; an unmarked
name is checked against the current source and reported as `symbol_missing` when
it is absent, which makes a procedure whose own new symbols are unmarked
unexecutable under the code-implementation workflow's pre-execution gate.

This tool closes that gap for a named procedure document:

- `list` reports the symbol names `stale_detector` currently reports as missing,
  with the line numbers of their unmarked backticked occurrences, so the operator
  can confirm each one is a name the procedure (or a sibling procedure row)
  creates rather than a citation of existing source that has drifted.
- `mark` inserts ` (new)` after the unmarked backticked occurrences of the names
  the operator supplies. A name that `stale_detector` does not report as missing
  is refused: an existing symbol must never be declared new, because that would
  silence the check that protects it.

The tool never infers which names are new. Reviewing the `list` output and
choosing the names stays with the operator.

Usage:
    python -m tools.mark_procedure_new_symbols list <procedure.md>
    python -m tools.mark_procedure_new_symbols mark <procedure.md> --symbols a,b,c
    python -m tools.mark_procedure_new_symbols mark <procedure.md> --all [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
STALE_DETECTOR = ROOT_DIR / "tools" / "stale_detector.py"

# Marker stale_detector recognizes, written after a backticked name.
NEW_MARKER = " (new)"

# One stale_detector mismatch line: "  - symbol_missing: Symbol 'name' not found in source"
_MISSING_SYMBOL_RE = re.compile(
    r"Symbol '([A-Za-z_][A-Za-z0-9_]*)' not found in source"
)


def reported_missing_symbols(proc: Path) -> list[str]:
    """Return symbol names stale_detector reports as missing, in first-seen order."""
    completed = subprocess.run(
        [sys.executable, str(STALE_DETECTOR), str(proc)],
        capture_output=True,
        text=True,
        check=False,
    )
    names: list[str] = []
    for line in completed.stdout.splitlines():
        match = _MISSING_SYMBOL_RE.search(line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    return names


def _name_pattern(name: str) -> re.Pattern[str]:
    """Backticked *name* with any marker already present captured as group 1."""
    return re.compile(rf"`{re.escape(name)}`( ?\(new\))?")


def unmarked_lines(text: str, name: str) -> list[int]:
    """1-based line numbers holding an unmarked backticked occurrence of *name*."""
    lines: list[int] = []
    for match in _name_pattern(name).finditer(text):
        if match.group(1):
            continue
        line_no = text.count("\n", 0, match.start()) + 1
        if line_no not in lines:
            lines.append(line_no)
    return lines


def mark_names(text: str, names: Iterable[str]) -> tuple[str, dict[str, int]]:
    """Insert the marker after every unmarked backticked occurrence of *names*.

    Returns the rewritten text and a per-name count of markers inserted. Already
    marked occurrences are left untouched, so the operation is idempotent.
    """
    counts: dict[str, int] = {}
    for name in names:
        inserted = 0

        def _replace(match: re.Match[str], _name: str = name) -> str:
            nonlocal inserted
            if match.group(1):
                return match.group(0)
            inserted += 1
            return f"{match.group(0)}{NEW_MARKER}"

        text = _name_pattern(name).sub(_replace, text)
        counts[name] = inserted
    return text, counts


def _print_list(proc: Path) -> int:
    names = reported_missing_symbols(proc)
    if not names:
        print(f"No missing-symbol findings in {proc}")
        return 0
    text = proc.read_text(encoding="utf-8")
    print(f"{proc}: {len(names)} missing symbol name(s)")
    for name in names:
        lines = unmarked_lines(text, name)
        print(f"  {name}  unmarked occurrences on lines: {', '.join(map(str, lines))}")
    return len(names)


def _print_mark(proc: Path, names: Iterable[str], dry_run: bool) -> int:
    allowed = set(reported_missing_symbols(proc))
    text = proc.read_text(encoding="utf-8")
    requested: list[str] = []
    for name in names:
        if name not in allowed:
            print(f"REFUSED: '{name}' is not reported missing; it exists in source")
            continue
        requested.append(name)
    if not requested:
        print("Nothing to mark.")
        return 1
    rewritten, counts = mark_names(text, requested)
    total = sum(counts.values())
    for name in requested:
        print(f"  {name}: {counts[name]}")
    if dry_run:
        print(f"DRY RUN: {total} marker(s) would be inserted in {proc}")
        return 0
    if total == 0:
        print(f"No unmarked occurrences found; {proc} unchanged")
        return 0
    proc.write_text(rewritten, encoding="utf-8")
    print(f"OK: inserted {total} marker(s) for {len(requested)} name(s) in {proc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser(
        "list", help="report missing symbol names and their lines"
    )
    list_parser.add_argument("path", help="implementation procedure document")

    mark_parser = sub.add_parser("mark", help="insert (new) markers for supplied names")
    mark_parser.add_argument("path", help="implementation procedure document")
    mark_parser.add_argument(
        "--symbols", default="", help="comma-separated names to mark"
    )
    mark_parser.add_argument(
        "--all",
        action="store_true",
        help="mark every name stale_detector reports as missing",
    )
    mark_parser.add_argument(
        "--dry-run", action="store_true", help="report without writing"
    )

    args = parser.parse_args(argv)
    proc = Path(args.path)
    if not proc.is_file():
        print(f"ERROR: not a file: {proc}")
        return 2

    if args.command == "list":
        _print_list(proc)
        return 0

    names = [part.strip() for part in args.symbols.split(",") if part.strip()]
    if args.all:
        names = reported_missing_symbols(proc)
    if not names and not args.all:
        print("ERROR: supply --symbols or --all")
        return 2
    return _print_mark(proc, names, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
