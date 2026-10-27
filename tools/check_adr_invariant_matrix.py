#!/usr/bin/env python3
"""check_adr_invariant_matrix.py — Verify test paths cited in the ADR Invariant Verification Matrix exist.

`docs/10_adr/adr_01_index.md`'s "## ADR Invariant Verification Matrix" table's
`Verification Status` column sometimes cites a specific pytest node id in
backticks (e.g. `` `tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition` ``)
as evidence that an invariant is covered by an automated test. Nothing
previously verified that the cited path still exists — it could go stale
after a file move/rename/deletion with no signal to a reader.

This check extracts every backtick-quoted `path/to/file.py::test_name`-shaped
substring from that column and fails if the file component does not exist.
Rows whose Verification Status cites no such pattern (a code reference like
`` `config_loader.py` `restrict_to()` ``, or "no test yet" / "Not verified" /
"Not implemented") are correctly out of scope — they already document a known
gap, not a claim this check can verify.

This check does not run the cited tests to confirm they pass — only that the
path exists. Running cited tests is a separate, not-yet-implemented sub-step
(see docs/00_governance/governance_04_documentation-checks.md GV-012 Follow-up Work).

Two further rules read the ADR bodies (the ADR body Verification section is the
canonical evidence record; the index mirrors it):

1. An ADR body `### Automated Tests` row whose `Implementation` cell is empty (or
   `-`) is reported. A non-empty cell, including one that starts with "Not verified",
   counts as an explicit status.
2. For an invariant that appears in both an ADR body and the index matrix, the cited
   test files (the union over the body rows, compared with the index cell) must
   agree; a difference is reported when both sides cite at least one test file.

Both rules report `WARNING` (see `_BODY_RULE_SEVERITY`), so they do not change the exit
code. Promote them to `ERROR` once a corpus survey reports no finding and the
repository owner approves (`rules/coding.md` "Explicit sign-off gates").

Usage:
    python tools/check_adr_invariant_matrix.py
    python tools/check_adr_invariant_matrix.py --format json
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping
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

# A cited pytest node id: backtick-quoted, contains a `.py::` separator so a
# bare code reference like `` `config_loader.py` `` (no `::`) is not matched.
_TEST_PATH_RE = re.compile(r"`([^`]+\.py)::([^`]+)`")


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _matrix_rows(lines: list[str]) -> list[tuple[int, str]]:
    """Return (1-indexed line_no, line) pairs for each table data row under
    the ADR Invariant Verification Matrix heading, skipping the header row
    and its `---` separator row."""
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


def check_invariant_matrix_test_paths(lines: list[str]) -> list[Issue]:
    """Fail for every cited pytest node id whose file component does not exist."""
    issues: list[Issue] = []
    for line_no, row in _matrix_rows(lines):
        for match in _TEST_PATH_RE.finditer(row):
            file_part = match.group(1)
            if not (REPO_ROOT / file_part).exists():
                issues.append(
                    Issue(
                        file="adr_01_index.md",
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"cited test path '{file_part}::{match.group(2)}' "
                            f"does not exist (file not found: {file_part})"
                        ),
                    )
                )
    return issues


# The body-evidence rules start as warnings: the corpus still has empty cells and
# body/index disagreements. Promotion condition: see the module docstring.
_BODY_RULE_SEVERITY = "WARNING"

_ADR_LIST_HEADING = "## ADR List"
_AUTOMATED_TESTS_HEADING = "### Automated Tests"
_HEADING_RE = re.compile(r"^#{1,6} ")
_ADR_NUMBER_RE = re.compile(r"ADR-(\d+)")
_INV_NUMBER_RE = re.compile(r"INV-(\d+)")
_ADR_PART_SPLIT_RE = re.compile(r"\s+and\s+(?=ADR-)")
# A cited test file, with or without a `::node` suffix; source-file references
# (for example `scripts/...`) are not test evidence and are ignored.
_CITED_TEST_FILE_RE = re.compile(r"`(tests/[^`:]+\.py)(?:::[^`]*)?`")
_EMPTY_CELLS = frozenset({"", "-", "\u2014"})
_INDEX_NAME = "adr_01_index.md"


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table_lines(lines: list[str], heading: str) -> list[tuple[int, str]]:
    """Return the (1-indexed line, text) pairs of the first table under `heading`;
    the table ends at the next heading or the first non-table line after it."""
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        return []
    table: list[tuple[int, str]] = []
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if _HEADING_RE.match(line):
            break
        if _TABLE_ROW_RE.match(line):
            table.append((i + 1, line))
        elif table:
            break
    return table


def _first_table_after(
    lines: list[str], heading: str
) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header cells and the (line, cells) data rows of that table."""
    table = [
        (line_no, _split_row(line))
        for line_no, line in _table_lines(lines, heading)
        if not _TABLE_SEPARATOR_RE.match(line)
    ]
    if not table:
        return [], []
    return table[0][1], table[1:]


def _adr_file_map(index_lines: list[str]) -> dict[str, str]:
    """Map an ADR number (`"001"`) to its file path, from the index `ADR List`."""
    header, rows = _first_table_after(index_lines, _ADR_LIST_HEADING)
    if "ID" not in header or "File" not in header:
        return {}
    id_col, file_col = header.index("ID"), header.index("File")
    mapping: dict[str, str] = {}
    for _, cells in rows:
        match = (
            _ADR_NUMBER_RE.fullmatch(cells[id_col])
            if len(cells) == len(header)
            else None
        )
        if match:
            mapping[match.group(1)] = "docs/" + cells[file_col].strip("`")
    return mapping


def _body_automated_tests_rows(lines: list[str]) -> list[tuple[int, list[str], str]]:
    """Return (line, invariant numbers, Implementation cell) per data row of the
    `### Automated Tests` table; empty when the table or a column is absent."""
    header, rows = _first_table_after(lines, _AUTOMATED_TESTS_HEADING)
    if "Verifies" not in header or "Implementation" not in header:
        return []
    verifies_col = header.index("Verifies")
    impl_col = header.index("Implementation")
    return [
        (line_no, _INV_NUMBER_RE.findall(cells[verifies_col]), cells[impl_col])
        for line_no, cells in rows
        if len(cells) == len(header)
    ]


def check_adr_body_evidence_cells(adr_file: str, lines: list[str]) -> list[Issue]:
    """Rule 1: report an ADR body row whose Implementation cell is empty."""
    issues: list[Issue] = []
    for line_no, invariants, cell in _body_automated_tests_rows(lines):
        if cell in _EMPTY_CELLS:
            names = ", ".join(f"INV-{n}" for n in invariants) or "an invariant"
            issues.append(
                Issue(
                    file=adr_file,
                    line_no=line_no,
                    severity=_BODY_RULE_SEVERITY,
                    message=(
                        f"{names}: Implementation cell is empty; cite a test or "
                        "record 'Not verified'"
                    ),
                )
            )
    return issues


def _index_evidence(
    index_lines: list[str],
) -> tuple[dict[tuple[str, str], set[str]], dict[tuple[str, str], int], set[str]]:
    """Return the test files cited per (ADR number, invariant number), the first
    index line of each, and every ADR number named in the matrix."""
    cited: dict[tuple[str, str], set[str]] = {}
    first_line: dict[tuple[str, str], int] = {}
    adr_numbers: set[str] = set()
    for line_no, row in _matrix_rows(index_lines):
        cells = _split_row(row)
        if len(cells) < 2:
            continue
        files = set(_CITED_TEST_FILE_RE.findall(cells[-1]))
        for part in _ADR_PART_SPLIT_RE.split(cells[0]):
            adr = _ADR_NUMBER_RE.search(part)
            if not adr:
                continue
            adr_numbers.add(adr.group(1))
            for inv in _INV_NUMBER_RE.findall(part):
                key = (adr.group(1), inv)
                cited.setdefault(key, set()).update(files)
                first_line.setdefault(key, line_no)
    return cited, first_line, adr_numbers


def check_body_index_agreement(
    index_lines: list[str], bodies: Mapping[str, list[str]]
) -> list[Issue]:
    """Rule 2: report an invariant whose cited test files differ between the index
    and the ADR body, when both sides cite at least one test file."""
    index_cited, index_line, _ = _index_evidence(index_lines)
    issues: list[Issue] = []
    for adr, body_lines in sorted(bodies.items()):
        body_cited: dict[str, set[str]] = {}
        for _, invariants, cell in _body_automated_tests_rows(body_lines):
            files = set(_CITED_TEST_FILE_RE.findall(cell))
            for inv in invariants:
                body_cited.setdefault(inv, set()).update(files)
        for inv, body_files in sorted(body_cited.items()):
            index_files = index_cited.get((adr, inv))
            if not index_files or not body_files or index_files == body_files:
                continue
            issues.append(
                Issue(
                    file=_INDEX_NAME,
                    line_no=index_line[(adr, inv)],
                    severity=_BODY_RULE_SEVERITY,
                    message=(
                        f"ADR-{adr} INV-{inv}: cited test files differ between the "
                        f"index {sorted(index_files)} and the ADR body "
                        f"{sorted(body_files)}"
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
    index_lines = _read_lines(ADR_INDEX)
    issues = check_invariant_matrix_test_paths(index_lines)
    adr_files = _adr_file_map(index_lines)
    bodies: dict[str, list[str]] = {}
    for adr, relative in sorted(adr_files.items()):
        path = REPO_ROOT / relative
        try:
            lines = _read_lines(path)
        except OSError as exc:
            issues.append(
                Issue(
                    file=_INDEX_NAME,
                    line_no=0,
                    severity=_BODY_RULE_SEVERITY,
                    message=f"ADR-{adr} file cannot be read ({relative}): {exc.strerror}",
                )
            )
            continue
        bodies[adr] = lines
        issues.extend(check_adr_body_evidence_cells(path.name, lines))
    for adr in sorted(_index_evidence(index_lines)[2] - adr_files.keys()):
        issues.append(
            Issue(
                file=_INDEX_NAME,
                line_no=0,
                severity=_BODY_RULE_SEVERITY,
                message=f"ADR-{adr} is named in the matrix but not in the ADR List",
            )
        )
    issues.extend(check_body_index_agreement(index_lines, bodies))
    return issues


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
            "Verify every pytest node id cited in docs/10_adr/adr_01_index.md's ADR "
            "Invariant Verification Matrix resolves to an existing file, and report "
            "(as warnings) an empty ADR body Implementation cell and a body/index "
            "disagreement of cited test files."
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
