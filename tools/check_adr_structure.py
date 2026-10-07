#!/usr/bin/env python3
"""check_adr_structure.py — Structural checks for docs/10_adr/*.md.

Four checks, all operating over docs/10_adr/*.md:

(a) `## Known Deviations` heading presence (ERROR). Every ADR must carry this
    heading per docs/00_governance/governance_04_documentation-checks.md's "ADR Section
    Header Compliance" manual check — a missing heading is a structural gap a
    future ADR author can easily forget.
(b) Implementation Notes vs Implementation References drift (WARNING). A
    backtick-quoted `scripts/...`/`tests/...` path cited under
    `## Implementation Notes` but absent from `## Implementation References`
    suggests the two lists have silently diverged. An ADR whose Notes section
    cites zero such paths is skipped for this check entirely — that is the
    expected, correct end state after Notes has been reduced to a plain
    pointer sentence, not a violation.

(c) Section headings of each `ADR-NNN-*.md` (ERROR): only the headings of the
    "ADR Section Header Standardization" list in
    docs/00_governance/governance_01_documentation-policy.md are allowed, in that
    order; every non-conditional heading is required.
(d) Template instruction text and global invariant IDs (ERROR): an ADR body must
    not contain template instructions (for example "Briefly describe") or a
    global `INV-NNN` invariant ID (invariant IDs are ADR-local, `INV-NN`).

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
_IMPLEMENTATION_REFERENCES_RE = re.compile(r"^## Implementation References\s*$")
_H2_HEADING_RE = re.compile(r"^## ")

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
                doc.lines, _IMPLEMENTATION_REFERENCES_RE, _H2_HEADING_RE
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


# "ADR Section Header Standardization" (governance_01): required headings in order,
# then the conditional ones (allowed only between Invariants and Verification).
_REQUIRED_HEADINGS = (
    "Keywords",
    "Status",
    "Summary",
    "Context",
    "Assumptions",
    "Decision",
    "Rationale",
    "Alternatives Considered",
    "Consequences",
    "Invariants",
    "Verification",
    "Implementation Notes",
    "Known Deviations",
    "Review Triggers",
    "Approval",
    "Related ADRs",
    "Implementation References",
    "Completion Checklist",
)
_CONDITIONAL_HEADINGS = (
    "Exceptions",
    "Failure Policy",
    "Data Ownership and Persistence",
)
_HEADING_ORDER = (
    *_REQUIRED_HEADINGS[: _REQUIRED_HEADINGS.index("Verification")],
    *_CONDITIONAL_HEADINGS,
    *_REQUIRED_HEADINGS[_REQUIRED_HEADINGS.index("Verification") :],
)
_TEMPLATE_RESIDUE_RE = re.compile(
    r"Briefly describe|If not applicable, write|Add review conditions|"
    r"Record any discrepancy between this ADR|Register any Invariant without",
)
_GLOBAL_INV_RE = re.compile(r"\bINV-\d{3}\b")
_ADR_FILE_RE = re.compile(r"^ADR-\d{3}-.*\.md$")


def _top_level_headings(lines: list[str]) -> list[tuple[int, str]]:
    """`## ` headings outside fenced code blocks, as (line number, title)."""
    headings: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            headings.append((i, line[3:].strip()))
    return headings


def check_section_headings(docs: list[DocFile]) -> list[Issue]:
    """Flag (ERROR) ADR headings that are unknown, out of order, or missing."""
    issues: list[Issue] = []
    for doc in docs:
        if not _ADR_FILE_RE.match(Path(doc.rel_path).name):
            continue
        headings = _top_level_headings(doc.lines)
        last_pos = -1
        for line_no, title in headings:
            if title not in _HEADING_ORDER:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=f"'## {title}' is not an allowed ADR heading",
                    )
                )
                continue
            pos = _HEADING_ORDER.index(title)
            if pos < last_pos:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=f"'## {title}' is out of order",
                    )
                )
            last_pos = max(last_pos, pos)
        present = {title for _line, title in headings}
        for required in _REQUIRED_HEADINGS:
            if required not in present:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=1,
                        severity="ERROR",
                        message=f"missing required heading '## {required}'",
                    )
                )
    return issues


def check_template_residue(docs: list[DocFile]) -> list[Issue]:
    """Flag (ERROR) template instruction text and global INV-NNN IDs in ADR bodies."""
    issues: list[Issue] = []
    for doc in docs:
        if not _ADR_FILE_RE.match(Path(doc.rel_path).name):
            continue
        for i, line in enumerate(doc.lines, start=1):
            if _TEMPLATE_RESIDUE_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message="template instruction text left in the ADR body",
                    )
                )
            if _GLOBAL_INV_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message="global INV-NNN id; use the ADR-local INV-NN",
                    )
                )
    return issues


def collect_issues() -> list[Issue]:
    docs = discover_md_files(ADR_DIR, prefix="")
    return (
        check_known_deviations_heading(docs)
        + check_notes_references_drift(docs)
        + check_section_headings(docs)
        + check_template_residue(docs)
    )


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
            "Check docs/10_adr/*.md for a missing '## Known Deviations' heading "
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
