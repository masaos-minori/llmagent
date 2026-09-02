#!/usr/bin/env python3
"""check_adr_invariant_matrix.py — Verify test paths cited in the ADR Invariant Verification Matrix exist.

`docs/adr-index.md`'s "## ADR Invariant Verification Matrix" table's
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
(see docs/00_governance_04_documentation-checks.md GV-014 Follow-up Work).

Usage:
    python tools/check_adr_invariant_matrix.py
    python tools/check_adr_invariant_matrix.py --format json
"""

from __future__ import annotations

import argparse
import re
import sys
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
                        file="adr-index.md",
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"cited test path '{file_part}::{match.group(2)}' "
                            f"does not exist (file not found: {file_part})"
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
    return check_invariant_matrix_test_paths(_read_lines(ADR_INDEX))


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
            "Verify every pytest node id cited in docs/adr-index.md's ADR "
            "Invariant Verification Matrix resolves to an existing file."
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
