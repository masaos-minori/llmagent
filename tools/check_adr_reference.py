#!/usr/bin/env python3
"""check_adr_reference.py — Verify scripts/*.py files named by the ADR Invariant Matrix carry an ADR-XXX comment marker.

`docs/10_adr/adr_01_index.md`'s "## ADR Invariant Verification Matrix" table sometimes
cites a `scripts/<path>.py` source file directly in a row's `Verification
Status` cell (e.g. `` `scripts/agent/startup.py` `` for ADR-004 INV-07) as
the implementation evidence for that invariant. This check requires that any
such named source file carry a deliberate comment marker for every `ADR-NNN`
named in the row's `Invariant` cell: a comment that starts with `# ADR-NNN`
(e.g. `# ADR-004: startup checks`). A prose mention in a docstring or a string
does not count — so a reader opening the file finds which ADR it implements,
and the check cannot be satisfied by an incidental mention (per
docs/00_governance/governance_04_documentation-checks.md GV-012 Implementation
intent §3: scoped to matrix-named files only).

The matrix is parsed by its header row (`Invariant` and `Verification Status`
columns), not by fixed positions. When the matrix yields no source references
at all, the check fails: a changed table shape must not let it pass vacuously.
A named file that cannot be tokenized is reported as an error.

Scope is intentionally narrow: only a `scripts/<path>.py` cell with no `::`
separator (a source-file reference) is checked here. A `tests/<path>.py::test_name`
citation is a test-path reference, already covered by
tools/check_adr_invariant_matrix.py's existence check — a different
requirement (does the test exist) from this one (does the source file
self-identify its ADR).

Usage:
    python tools/check_adr_reference.py
    python tools/check_adr_reference.py --format json
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ADR_INDEX = DOCS_DIR / "10_adr" / "adr_01_index.md"

_MATRIX_HEADING = "## ADR Invariant Verification Matrix"
_SECTION_HEADING_RE = re.compile(r"^#{1,2} ")
_TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

# A `scripts/...py` source-file reference, with no `::` (a test-node
# reference is a different check's concern — see module docstring).
_SOURCE_FILE_RE = re.compile(r"`(scripts/[^`]+\.py)`")
_ADR_ID_RE = re.compile(r"ADR-\d+")


@dataclass(frozen=True)
class MatrixSourceRef:
    """One `scripts/*.py` file named by a matrix row, with that row's ADR id."""

    file_path: str
    adr_id: str
    line_no: int


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _split_row(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _matrix_table(lines: list[str]) -> tuple[list[str], list[tuple[int, str]]]:
    """Return the matrix header cells and its (1-indexed line_no, line) data rows.

    The table is the first one under the ADR Invariant Verification Matrix heading.
    An empty header is returned when the heading or the table is missing."""
    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == _MATRIX_HEADING:
            start = i
            break
    if start is None:
        return [], []

    header: list[str] = []
    rows: list[tuple[int, str]] = []
    seen_separator = False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if _SECTION_HEADING_RE.match(line):
            break
        if not _TABLE_ROW_RE.match(line):
            continue
        if not seen_separator and _TABLE_SEPARATOR_RE.match(line):
            seen_separator = True
            continue
        if not seen_separator:
            header = _split_row(line)
            continue
        rows.append((i + 1, line))
    return header, rows


def parse_matrix_source_refs(lines: list[str]) -> list[MatrixSourceRef]:
    """Extract every `scripts/*.py` file the matrix names, once per ADR id in its row.

    Columns are located by header name. Every `ADR-NNN` token of the `Invariant`
    cell is an ADR id of the row."""
    header, rows = _matrix_table(lines)
    if "Invariant" not in header or "Verification Status" not in header:
        return []
    invariant_col = header.index("Invariant")
    status_col = header.index("Verification Status")
    refs: list[MatrixSourceRef] = []
    for line_no, row in rows:
        cells = _split_row(row)
        if len(cells) != len(header):
            continue
        adr_ids = list(dict.fromkeys(_ADR_ID_RE.findall(cells[invariant_col])))
        for match in _SOURCE_FILE_RE.finditer(cells[status_col]):
            for adr_id in adr_ids:
                refs.append(
                    MatrixSourceRef(
                        file_path=match.group(1), adr_id=adr_id, line_no=line_no
                    )
                )
    return refs


def _has_adr_marker(source: str, adr_id: str) -> bool:
    """Return True when a comment token starts with `# <adr_id>`.

    Raises tokenize.TokenError or SyntaxError when the source cannot be tokenized."""
    marker = re.compile(rf"#\s*{re.escape(adr_id)}\b")
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and marker.match(token.string):
            return True
    return False


def check_adr_reference(refs: list[MatrixSourceRef]) -> list[Issue]:
    """Fail for every named source file that does not contain its ADR id."""
    issues: list[Issue] = []
    for ref in refs:
        target = REPO_ROOT / ref.file_path
        if not target.exists():
            issues.append(
                Issue(
                    file="adr_01_index.md",
                    line_no=ref.line_no,
                    severity="ERROR",
                    message=(
                        f"matrix cites source file '{ref.file_path}' for "
                        f"{ref.adr_id}, but that file does not exist"
                    ),
                )
            )
            continue
        content = target.read_text(encoding="utf-8")
        try:
            has_marker = _has_adr_marker(content, ref.adr_id)
        except (tokenize.TokenError, SyntaxError) as exc:
            issues.append(
                Issue(
                    file=ref.file_path,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"file is cited for {ref.adr_id} but cannot be tokenized: {exc}"
                    ),
                )
            )
            continue
        if not has_marker:
            issues.append(
                Issue(
                    file=ref.file_path,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"file is cited by docs/10_adr/adr_01_index.md's Invariant Matrix "
                        f"for {ref.adr_id}, but has no '# {ref.adr_id}' comment marker"
                    ),
                )
            )
    return issues


def collect_issues() -> list[Issue]:
    if not ADR_INDEX.exists():
        return [
            Issue(
                file="adr_01_index.md",
                line_no=0,
                severity="ERROR",
                message="docs/10_adr/adr_01_index.md not found",
            )
        ]
    refs = parse_matrix_source_refs(_read_lines(ADR_INDEX))
    if not refs:
        return [
            Issue(
                file="adr_01_index.md",
                line_no=0,
                severity="ERROR",
                message=(
                    "matrix yielded no source references; the matrix shape may have "
                    "changed"
                ),
            )
        ]
    return check_adr_reference(refs)


def render_json(issues: list[Issue]) -> str:
    payload = [
        {
            "file": issue.file,
            "line_no": issue.line_no,
            "severity": issue.severity,
            "message": issue.message,
        }
        for issue in sorted(issues, key=lambda i: (i.file, i.line_no))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify every scripts/*.py file cited by docs/10_adr/adr_01_index.md's ADR "
            "Invariant Verification Matrix carries a `# ADR-NNN` comment marker "
            "for that row's ADR id."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    args = parser.parse_args(argv)

    issues = collect_issues()

    if args.format == "json":
        print(render_json(issues))
        return 1 if any(issue.severity == "ERROR" for issue in issues) else 0

    return report_and_exit(issues)


if __name__ == "__main__":
    raise SystemExit(main())
