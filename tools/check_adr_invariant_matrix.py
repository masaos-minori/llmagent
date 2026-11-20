#!/usr/bin/env python3
"""check_adr_invariant_matrix.py — Verify test paths and nodes cited in the ADR Invariant Verification Matrix exist.

`docs/10_adr/adr_01_index.md`'s "## ADR Invariant Verification Matrix" table's
`Verification Status` column sometimes cites a specific pytest node id in
backticks (e.g. `` `tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition` ``)
as evidence that an invariant is covered by an automated test. Nothing
previously verified that the cited path still exists — it could go stale
after a file move/rename/deletion with no signal to a reader.

This check extracts every backtick-quoted `path/to/file.py::node`-shaped
substring from that column and fails if the file component does not exist, or if
the file exists but a `::` segment of the node is not a class or function defined
in it (checked by parsing the file with `ast`; a trailing `()` and a `[...]`
parameter id are stripped from each segment, and no cited code is imported or run).
Rows whose Verification Status cites no such pattern (a code reference like
`` `config_loader.py` `restrict_to()` ``, or "no test yet" / "Not verified" /
"Not implemented") are correctly out of scope — they already document a known
gap, not a claim this check can verify.

This check does not run the cited tests to confirm they pass — only that the
path and node exist. Running the cited index tests is done by
`.github/run_cited_adr_tests.py`.

Five further rules read the ADR bodies and the index (the ADR body Verification
section is the canonical evidence record; the index mirrors it):

1. An ADR body `### Automated Tests` table whose header lacks the `Verifies` or
   `Implementation` column is reported at its header line: the checker cannot
   read the evidence such a table is meant to record. A body with no such table
   stays silent.
2. An ADR body `### Automated Tests` row whose `Implementation` cell is empty (or
   `-`) is reported. A non-empty cell, including one that starts with "Not verified",
   counts as an explicit status.
3. For an invariant that appears in both an ADR body and the index matrix, the test
   files cited by the body (the union over the body rows) must be contained in the
   union of the citations in the matrix rows naming that invariant; body-cited files
   not covered by any index citation are reported when both sides cite at least one
   test file. Extra index citations — additional evidence on rows shared by several
   invariants — are not errors (containment rule; repository owner decision, 2026-10-28).
4. Reverse direction: an invariant whose index row cites test files while the ADR
   body records no test evidence for it (no `### Automated Tests` row names it, or
   every row naming it cites no test file) is reported at the index row.
5. A `Not verified` row must be Non-Blocking: an index row whose Verification
   Status starts with "Not verified" and whose Gate is not "Non-Blocking" (unless
   the cell carries an approved `Exception: <id>` reference), and a body row whose
   Implementation starts with "Not verified" and whose Blocking cell is "Yes", are
   reported.

Every backtick-quoted `path/to/file.py::node` citation anywhere in an ADR body
(not only the Automated Tests table) must name an existing file by its full
repository path and an existing node; a path-less citation such as
`test_x.py::TestY` fails the file check.

All rules and the node validation report `ERROR` (see `_BODY_RULE_SEVERITY`),
so any finding makes the exit code non-zero.

Usage:
    python tools/check_adr_invariant_matrix.py
    python tools/check_adr_invariant_matrix.py --format json
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Mapping
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Matrix/body table parsers and the ADR body rules (split fallout 2026-11-20):
# the names re-exported here stay importable from this module for
# tools/generate_reference_table.py and .github/run_cited_adr_tests.py.
from tools._adr_matrix_core import (
    _ADR_LIST_HEADING,
    _ADR_NUMBER_RE,
    _AUTOMATED_TESTS_HEADING,
    _BODY_RULE_SEVERITY,
    _INDEX_NAME,
    _INV_NUMBER_RE,
    _first_table_after,
    _index_evidence,
    _matrix_rows,
    _read_lines,
    _split_row,
    check_adr_body_evidence_cells,
    check_adr_body_table_columns,
    check_body_index_agreement,
    check_index_only_evidence,
)
from tools._docs_consistency_lib import Issue, report_and_exit
from tools._report import PROFILE_ISSUE, add_format_argument, from_issue, render_json

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ADR_INDEX = DOCS_DIR / "10_adr" / "adr_01_index.md"

# A cited pytest node id: backtick-quoted, contains a `.py::` separator so a
# bare code reference like `` `config_loader.py` `` (no `::`) is not matched.
_TEST_PATH_RE = re.compile(r"`([^`]+\.py)::([^`]+)`")

# Skip-family markers nullify a cited node's execution evidence (REQ-002).
_SKIP_MARKER_RE = re.compile(r"\bmark\.(?:skip|skipif|xfail)$")

# Approved-exception reference grammar, shared with .github/run_cited_adr_tests.py
# (row 03 imports this module by path); documented in adr_01_index.md vocabulary.
_EXCEPTION_RE = re.compile(r"Exception: [A-Za-z0-9._-]+")


_NODE_SEGMENT_SUFFIX_RE = re.compile(r"(?:\[.*\])?(?:\(\))?$")
_DEFINED_NAMES_CACHE: dict[tuple[Path, int, int], frozenset[str] | None] = {}


def _defined_names(path: Path) -> frozenset[str] | None:
    """Return the class and function names defined anywhere in `path`, or None when
    it cannot be read or parsed. Cached per (path, mtime, size)."""
    try:
        stat = path.stat()
        key = (path, stat.st_mtime_ns, stat.st_size)
        if key in _DEFINED_NAMES_CACHE:
            return _DEFINED_NAMES_CACHE[key]
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    names = frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    _DEFINED_NAMES_CACHE[key] = names
    return names


def _node_problem(file_part: str, node: str) -> str | None:
    """Return a message when a `::` segment of `node` is not a class or function
    defined in `file_part`; None when every segment resolves."""
    names = _defined_names(REPO_ROOT / file_part)
    if names is None:
        return f"cannot parse {file_part} to verify the cited node '{node}'"
    for segment in node.split("::"):
        name = _NODE_SEGMENT_SUFFIX_RE.sub("", segment)
        if name not in names:
            return (
                f"cited node '{node}' not found in {file_part} "
                f"('{name}' is not a class or function defined there)"
            )
    return None


def _citation_problem(file_part: str, node: str) -> str | None:
    """Return the problem with one cited `file::node`, or None when it resolves."""
    if not (REPO_ROOT / file_part).is_file():
        return (
            f"cited test path '{file_part}::{node}' "
            f"does not exist (file not found: {file_part})"
        )
    return _node_problem(file_part, node)


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base is not None else None
    if isinstance(node, ast.Call):
        return _dotted_name(node.func)
    return None


_MARKER_CACHE: dict[
    tuple[Path, int, int], tuple[dict[str, frozenset[str]], bool] | None
] = {}


def _node_markers(path: Path) -> tuple[dict[str, frozenset[str]], bool] | None:
    """Return (name -> skip-family decorator names, module-level pytestmark skip)
    for class and function definitions in `path`, or None when it cannot be read
    or parsed. Cached per (path, mtime, size)."""
    try:
        stat = path.stat()
        key = (path, stat.st_mtime_ns, stat.st_size)
        if key in _MARKER_CACHE:
            return _MARKER_CACHE[key]
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    markers: dict[str, frozenset[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        found = {
            dotted
            for decorator in node.decorator_list
            if (dotted := _dotted_name(decorator)) is not None
            and _SKIP_MARKER_RE.search(dotted)
        }
        if found:
            markers[node.name] = frozenset(found)
    module_skipped = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets
        ):
            values = (
                node.value.elts
                if isinstance(node.value, (ast.List, ast.Tuple))
                else [node.value]
            )
            if any(
                (dotted := _dotted_name(value)) is not None
                and _SKIP_MARKER_RE.search(dotted)
                for value in values
            ):
                module_skipped = True
                break
    _MARKER_CACHE[key] = (markers, module_skipped)
    return _MARKER_CACHE[key]


def _marker_problem(file_part: str, node: str) -> str | None:
    """Return the skip-family marker name when a cited node is statically marked
    skip/skipif/xfail (on itself, its class, or module-level `pytestmark`); None
    otherwise. Non-skip markers (e.g. `usefixtures`) are not skip-family."""
    result = _node_markers(REPO_ROOT / file_part)
    if result is None:
        return None
    markers, module_skipped = result
    if module_skipped:
        return "pytestmark"
    for segment in node.split("::"):
        name = _NODE_SEGMENT_SUFFIX_RE.sub("", segment)
        found = markers.get(name)
        if found:
            return sorted(found)[0]
    return None


def check_invariant_matrix_test_paths(lines: list[str]) -> list[Issue]:
    """Fail for every cited pytest node id whose file or node does not exist,
    and for every cited node carrying a static skip-family marker when the row
    records no `Exception: <id>` reference (REQ-002)."""
    issues: list[Issue] = []
    for line_no, row in _matrix_rows(lines):
        status_cell = _split_row(row)[-1] if row.strip().endswith("|") else ""
        exception_approved = bool(_EXCEPTION_RE.search(status_cell))
        for match in _TEST_PATH_RE.finditer(row):
            file_part, node = match.group(1), match.group(2)
            problem = _citation_problem(file_part, node)
            if problem:
                issues.append(
                    Issue(
                        file="adr_01_index.md",
                        line_no=line_no,
                        severity="ERROR",
                        message=problem,
                    )
                )
                continue
            marker = _marker_problem(file_part, node)
            if marker and not exception_approved:
                issues.append(
                    Issue(
                        file="adr_01_index.md",
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"cited node '{file_part}::{node}' carries a static "
                            f"'{marker}' marker; the row records no approved "
                            "'Exception: <id>' reference"
                        ),
                    )
                )
    return issues


def check_adr_body_citations(adr_file: str, lines: list[str]) -> list[Issue]:
    """Report an unresolved `file.py::node` citation anywhere in an ADR body."""
    issues: list[Issue] = []
    for line_no, line in enumerate(lines, start=1):
        for match in _TEST_PATH_RE.finditer(line):
            problem = _citation_problem(match.group(1), match.group(2))
            if problem:
                issues.append(
                    Issue(
                        file=adr_file,
                        line_no=line_no,
                        severity=_BODY_RULE_SEVERITY,
                        message=problem,
                    )
                )
    return issues


_MANUAL_STATUSES = ("Manual", "Partial")
_CADENCE_FIELDS = ("Cadence:", "Expected evidence:")


def check_manual_partial_fields(lines: list[str]) -> list[Issue]:
    """REQ-004: a Manual or Partial matrix row must carry `Cadence:` and
    `Expected evidence:` inside its Verification Status cell; missing fields
    report as `ERROR`."""
    issues: list[Issue] = []
    for line_no, row in _matrix_rows(lines):
        cells = _split_row(row)
        if not cells:
            continue
        status_cell = cells[-1]
        if not status_cell.startswith(_MANUAL_STATUSES):
            continue
        for field in _CADENCE_FIELDS:
            if field not in status_cell:
                issues.append(
                    Issue(
                        file=_INDEX_NAME,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"Verification Status cell is missing the required "
                            f"'{field}' field for a Manual/Partial row"
                        ),
                    )
                )
    return issues


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


def check_not_verified_blocking(
    index_lines: list[str],
    bodies: Mapping[str, list[str]],
    adr_files: Mapping[str, str],
) -> list[Issue]:
    """Rule 5: a `Not verified` row must be Non-Blocking. An index row whose
    Verification Status starts with "Not verified" and whose Gate is not
    "Non-Blocking" is reported unless the cell carries an approved `Exception:
    <id>` reference; a body row whose Implementation starts with "Not verified"
    and whose Blocking cell starts with "Yes" is reported."""
    issues: list[Issue] = []
    for line_no, row in _matrix_rows(index_lines):
        cells = _split_row(row)
        if len(cells) < 6:
            continue
        status_cell = cells[-1]
        if not status_cell.startswith("Not verified"):
            continue
        if cells[4] == "Non-Blocking" or _EXCEPTION_RE.search(status_cell):
            continue
        issues.append(
            Issue(
                file=_INDEX_NAME,
                line_no=line_no,
                severity=_BODY_RULE_SEVERITY,
                message=(
                    f"{cells[0]}: a 'Not verified' row must be Non-Blocking or "
                    "carry an approved 'Exception: <id>' reference"
                ),
            )
        )
    for adr, body_lines in sorted(bodies.items()):
        header, rows = _first_table_after(body_lines, _AUTOMATED_TESTS_HEADING)
        if not all(
            column in header for column in ("Verifies", "Blocking", "Implementation")
        ):
            continue
        inv_col = header.index("Verifies")
        block_col = header.index("Blocking")
        impl_col = header.index("Implementation")
        adr_name = Path(adr_files[adr]).name if adr in adr_files else f"ADR-{adr}"
        for line_no, cells in rows:
            if len(cells) != len(header):
                continue
            if cells[impl_col].startswith("Not verified") and cells[
                block_col
            ].startswith("Yes"):
                names = (
                    ", ".join(
                        f"INV-{n}" for n in _INV_NUMBER_RE.findall(cells[inv_col])
                    )
                    or "an invariant"
                )
                issues.append(
                    Issue(
                        file=adr_name,
                        line_no=line_no,
                        severity=_BODY_RULE_SEVERITY,
                        message=(
                            f"{names}: a 'Not verified' row must not be Blocking; "
                            "record the change in the pending approval form"
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
    issues.extend(check_manual_partial_fields(index_lines))
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
        issues.extend(check_adr_body_table_columns(path.name, lines))
        issues.extend(check_adr_body_evidence_cells(path.name, lines))
        issues.extend(check_adr_body_citations(path.name, lines))
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
    issues.extend(check_index_only_evidence(index_lines, bodies))
    issues.extend(check_not_verified_blocking(index_lines, bodies, adr_files))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify every pytest node id cited in docs/10_adr/adr_01_index.md's ADR "
            "Invariant Verification Matrix and in the ADR bodies resolves to an "
            "existing file and node, and report an unreadable ADR body Automated "
            "Tests table, an empty body Implementation cell, body-cited test files "
            "not covered by the index citations, index-cited evidence with no body "
            "evidence, and a 'Not verified' row recorded as Blocking."
        )
    )
    add_format_argument(parser, choices=("json",), default=None)
    args = parser.parse_args(argv)

    issues = collect_issues()

    if args.format == "json":
        print(render_json([from_issue(i) for i in issues], PROFILE_ISSUE))
        return 1 if any(issue.severity == "ERROR" for issue in issues) else 0

    return report_and_exit(issues)


if __name__ == "__main__":
    raise SystemExit(main())
