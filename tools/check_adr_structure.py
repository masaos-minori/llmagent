#!/usr/bin/env python3
"""check_adr_structure.py — Structural checks for docs/adr/*.md.

Two checks, both operating over every file under docs/adr/*.md:

(a) `## Known Deviations` heading presence (ERROR). Every ADR must carry this
    heading per docs/00_governance_04_documentation-checks.md's "ADR Section
    Header Compliance" manual check — a missing heading is a structural gap a
    future ADR author can easily forget.
(b) Implementation Notes vs Implementation References drift (WARNING). A
    backtick-quoted `scripts/...`/`tests/...` path cited under
    `## Implementation Notes` but absent from `### Implementation References`
    suggests the two lists have silently diverged. An ADR whose Notes section
    cites zero such paths is skipped for this check entirely — that is the
    expected, correct end state after Notes has been reduced to a plain
    pointer sentence, not a violation.

Usage:
    python tools/check_adr_structure.py
    python tools/check_adr_structure.py --format json
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    discover_md_files,
    report_and_exit,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = REPO_ROOT / "docs" / "10_adr"

_KNOWN_DEVIATIONS_RE = re.compile(r"^## Known Deviations\s*$")
_IMPLEMENTATION_NOTES_RE = re.compile(r"^## Implementation Notes\s*$")
_IMPLEMENTATION_REFERENCES_RE = re.compile(r"^### Implementation References\s*$")
_H2_HEADING_RE = re.compile(r"^## ")
_H1_TO_H3_HEADING_RE = re.compile(r"^#{1,3} ")

# A `scripts/...`/`tests/...` path, backtick-quoted, with a file extension.
_SOURCE_OR_TEST_PATH_RE = re.compile(r"`((?:scripts|tests)/[^`]+\.\w+)`")


def check_known_deviations_heading(docs: list[DocFile]) -> list[Issue]:
    """Flag (ERROR) every ADR file that lacks a `## Known Deviations` heading."""
    issues: list[Issue] = []
    for doc in docs:
        if not any(_KNOWN_DEVIATIONS_RE.match(line) for line in doc.lines):
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=0,
                    severity="ERROR",
                    message="missing '## Known Deviations' heading",
                )
            )
    return issues


def _section_paths(
    lines: list[str], heading_re: re.Pattern[str], boundary_re: re.Pattern[str]
) -> list[tuple[str, int]]:
    """Return (path, 1-indexed line_no) pairs for every matched path within the
    section starting at the first line matching *heading_re*, ending at the
    next line matching *boundary_re* (or end of file)."""
    start: int | None = None
    for i, line in enumerate(lines):
        if heading_re.match(line):
            start = i
            break
    if start is None:
        return []

    results: list[tuple[str, int]] = []
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if boundary_re.match(line):
            break
        for match in _SOURCE_OR_TEST_PATH_RE.finditer(line):
            results.append((match.group(1), i + 1))
    return results


def check_notes_references_drift(docs: list[DocFile]) -> list[Issue]:
    """Flag (WARNING) a scripts/tests path cited in Implementation Notes but
    absent from Implementation References. Skips an ADR entirely if its Notes
    section cites zero such paths."""
    issues: list[Issue] = []
    for doc in docs:
        notes_paths = _section_paths(
            doc.lines, _IMPLEMENTATION_NOTES_RE, _H2_HEADING_RE
        )
        if not notes_paths:
            continue

        references_paths = {
            path
            for path, _line_no in _section_paths(
                doc.lines, _IMPLEMENTATION_REFERENCES_RE, _H1_TO_H3_HEADING_RE
            )
        }

        for path, line_no in notes_paths:
            if path not in references_paths:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="WARNING",
                        message=(
                            f"'{path}' appears in Implementation Notes but not "
                            f"in Implementation References — drift risk"
                        ),
                    )
                )
    return issues


def collect_issues() -> list[Issue]:
    docs = discover_md_files(ADR_DIR, prefix="")
    return check_known_deviations_heading(docs) + check_notes_references_drift(docs)


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
            "Check docs/adr/*.md for a missing '## Known Deviations' heading "
            "(ERROR) and Implementation Notes vs Implementation References "
            "file/symbol drift (WARNING)."
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
