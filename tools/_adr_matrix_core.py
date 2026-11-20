#!/usr/bin/env python3
"""tools/_adr_matrix_core.py — Shared matrix/body table parsers and ADR body rules.

Split fallout (2026-11-20, adrchk013): `tools/check_adr_invariant_matrix.py` with its
new body rules exceeded the 24576 B `tools/` module size gate, so the ADR body rules
and the table/matrix parsers they share with the checker moved here, following the
`tools/_adr_authority_core.py` precedent.

Owns:
- the `## ADR Invariant Verification Matrix` row reader (`_matrix_rows`) and the
  generic table readers (`_table_lines`, `_first_table_after`) shared by the checker;
- the body-evidence rules: `check_adr_body_table_columns` (unreadable Automated
  Tests table), `check_adr_body_evidence_cells` (empty Implementation cell),
  `check_body_index_agreement` (containment) and `check_index_only_evidence`
  (reverse direction);
- the shared constants they parse with (`_INDEX_NAME`, `_BODY_RULE_SEVERITY`,
  `_CITED_TEST_FILE_RE`, ...).

`tools/check_adr_invariant_matrix.py` imports these and keeps the names its
in-process importers (`tools/generate_reference_table.py`,
`.github/run_cited_adr_tests.py`) read from it. This module cannot run standalone.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from tools._docs_consistency_lib import Issue

_MATRIX_HEADING = "## ADR Invariant Verification Matrix"
_SECTION_HEADING_RE = re.compile(r"^#{1,2} ")
_TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

# Body-evidence findings (empty cells, body citations not covered by the index)
# are errors, like the index checks.
_BODY_RULE_SEVERITY = "ERROR"

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
    """Rule 2: report an ADR body row whose Implementation cell is empty."""
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


def check_adr_body_table_columns(adr_file: str, lines: list[str]) -> list[Issue]:
    """Rule 1: report an `### Automated Tests` table whose header lacks an evidence
    column (`Verifies` or `Implementation`) at its header line; a body with no such
    table stays silent."""
    header, _ = _first_table_after(lines, _AUTOMATED_TESTS_HEADING)
    if not header:
        return []
    missing = [
        column for column in ("Verifies", "Implementation") if column not in header
    ]
    if not missing:
        return []
    table = _table_lines(lines, _AUTOMATED_TESTS_HEADING)
    return [
        Issue(
            file=adr_file,
            line_no=table[0][0] if table else 0,
            severity=_BODY_RULE_SEVERITY,
            message=(
                "the Automated Tests table header is missing the "
                f"{' and '.join(missing)} column"
            ),
        )
    ]


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
    """Rule 3 (containment): report an invariant whose body-cited test files are not
    all covered by the index citations, when both sides cite at least one test file."""
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
            if not index_files or not body_files or body_files <= index_files:
                continue
            issues.append(
                Issue(
                    file=_INDEX_NAME,
                    line_no=index_line[(adr, inv)],
                    severity=_BODY_RULE_SEVERITY,
                    message=(
                        f"ADR-{adr} INV-{inv}: body-cited test files not covered by "
                        f"the index citations {sorted(body_files - index_files)} "
                        f"(the index covers {sorted(index_files)})"
                    ),
                )
            )
    return issues


def _body_evidence_by_invariant(body_lines: list[str]) -> dict[str, set[str]]:
    """Union of body-cited test files per invariant number, over the Automated
    Tests rows."""
    cited: dict[str, set[str]] = {}
    for _, invariants, cell in _body_automated_tests_rows(body_lines):
        files = set(_CITED_TEST_FILE_RE.findall(cell))
        for inv in invariants:
            cited.setdefault(inv, set()).update(files)
    return cited


def check_index_only_evidence(
    index_lines: list[str], bodies: Mapping[str, list[str]]
) -> list[Issue]:
    """Rule 4 (reverse direction): report an invariant whose index row cites test
    files while its ADR body records no test evidence for it. An ADR number without
    a readable body is skipped (already reported by collect_issues)."""
    index_cited, index_line, _ = _index_evidence(index_lines)
    body_cited = {
        adr: _body_evidence_by_invariant(lines) for adr, lines in bodies.items()
    }
    issues: list[Issue] = []
    for (adr, inv), index_files in sorted(index_cited.items()):
        if not index_files or adr not in body_cited or body_cited[adr].get(inv):
            continue
        issues.append(
            Issue(
                file=_INDEX_NAME,
                line_no=index_line[(adr, inv)],
                severity=_BODY_RULE_SEVERITY,
                message=(
                    f"ADR-{adr} INV-{inv}: the index cites test files "
                    f"{sorted(index_files)} but the ADR body records no test "
                    "evidence for it"
                ),
            )
        )
    return issues
