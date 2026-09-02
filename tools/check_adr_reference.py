#!/usr/bin/env python3
"""check_adr_reference.py — Verify scripts/*.py files named by the ADR Invariant Matrix carry an ADR-XXX comment.

`docs/adr-index.md`'s "## ADR Invariant Verification Matrix" table sometimes
cites a `scripts/<path>.py` source file directly in a row's `Verification
Status` cell (e.g. `` `scripts/agent/startup.py` `` for INV-011/ADR-004) as
the implementation evidence for that invariant. This check requires that any
such named source file contain an inline reference to the row's ADR ID
(e.g. `ADR-004`) somewhere in its text — so a reader opening the file can
find which ADR it implements, and this check can later be extended to a
smaller, well-scoped "ADR-vs-code" audit rather than a repository-wide
mandate (per docs/00_governance_04_documentation-checks.md GV-014
Implementation intent §3: scoped to matrix-named files only).

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
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ADR_INDEX = DOCS_DIR / "adr-index.md"

_MATRIX_HEADING = "## ADR Invariant Verification Matrix"
_SECTION_HEADING_RE = re.compile(r"^#{1,2} ")
_TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

# A `scripts/...py` source-file reference, with no `::` (a test-node
# reference is a different check's concern — see module docstring).
_SOURCE_FILE_RE = re.compile(r"`(scripts/[^`]+\.py)`")
_ADR_ID_RE = re.compile(r"^ADR-\d+$")


@dataclass(frozen=True)
class MatrixSourceRef:
    """One `scripts/*.py` file named by a matrix row, with that row's ADR id."""

    file_path: str
    adr_id: str
    line_no: int


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _matrix_rows(lines: list[str]) -> list[tuple[int, str]]:
    """Return (1-indexed line_no, line) pairs for each table data row under
    the ADR Invariant Verification Matrix heading, skipping the header row
    and its `---` separator row. Mirrors check_adr_invariant_matrix.py's
    row-location logic (kept local rather than imported to avoid a
    cross-tool private-function dependency for this small amount of logic)."""
    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == _MATRIX_HEADING:
            start = i
            break
    if start is None:
        return []

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
            continue  # header row itself
        rows.append((i + 1, line))
    return rows


def parse_matrix_source_refs(lines: list[str]) -> list[MatrixSourceRef]:
    """Extract every `scripts/*.py` file the matrix names, with its row's ADR id."""
    refs: list[MatrixSourceRef] = []
    for line_no, row in _matrix_rows(lines):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        adr_id = cells[1]
        verification_status = cells[6]
        if not _ADR_ID_RE.match(adr_id):
            continue
        for match in _SOURCE_FILE_RE.finditer(verification_status):
            refs.append(
                MatrixSourceRef(
                    file_path=match.group(1), adr_id=adr_id, line_no=line_no
                )
            )
    return refs


def check_adr_reference(refs: list[MatrixSourceRef]) -> list[Issue]:
    """Fail for every named source file that does not contain its ADR id."""
    issues: list[Issue] = []
    for ref in refs:
        target = REPO_ROOT / ref.file_path
        if not target.exists():
            issues.append(
                Issue(
                    file="adr-index.md",
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
        if ref.adr_id not in content:
            issues.append(
                Issue(
                    file=ref.file_path,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"file is cited by docs/adr-index.md's Invariant Matrix "
                        f"for {ref.adr_id}, but contains no inline reference to "
                        f"'{ref.adr_id}'"
                    ),
                )
            )
    return issues


def collect_issues() -> list[Issue]:
    if not ADR_INDEX.exists():
        return [
            Issue(
                file="adr-index.md",
                line_no=0,
                severity="ERROR",
                message="docs/adr-index.md not found",
            )
        ]
    refs = parse_matrix_source_refs(_read_lines(ADR_INDEX))
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
            "Verify every scripts/*.py file cited by docs/adr-index.md's ADR "
            "Invariant Verification Matrix contains an inline reference to "
            "that row's ADR id."
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
