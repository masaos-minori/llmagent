#!/usr/bin/env python3
"""check_adr_structure.py — Structural checks for docs/10_adr/*.md.

Six checks, all operating over docs/10_adr/*.md:

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

(c) Section headings of each `adr_02_GG_NNN_*.md` (ERROR): only the headings of the
    `_REQUIRED_HEADINGS` constant in this module are allowed, in that order; every
    non-conditional heading is required. This constant is the single normative
    source; governance_01's visible "ADR Section Header Standardization" block is
    a generated mirror of it (tools/generate_adr_authority.py, plan adrchk015
    REQ-013).
(d) Template instruction text and global invariant IDs (ERROR): an ADR body must
    not contain template instructions (for example "Briefly describe") or a
    global `INV-NNN` invariant ID (invariant IDs are ADR-local, `INV-NN`).
(e) `## Status` value (ERROR): the first non-empty line after the heading must be
    one of the values "ADR Status Definitions" in governance_01 defines.
(f) Pending approval bullets (ERROR): a `Current Decision Approval (pending)`
    bullet under `### Approval Record` must cite an `AAL-NNN` entry that exists
    in the ADR approval ledger (Part 5 of governance_03).

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


# Normative single source (plan adrchk015 REQ-013) for the "ADR Section Header
# Standardization" list enforced by governance_04 §18 "ADR Section Header
# Compliance": required headings in order, then the conditional ones (allowed
# only between Invariants and Verification). governance_01's visible block is a
# generated mirror imported from this constant by tools/generate_adr_authority.py.
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
_ADR_FILE_RE = re.compile(r"^adr_02_\d{2}_\d{3}_.*\.md$")

# "ADR Status Definitions" (governance_01); a test pins the two lists together.
_ALLOWED_STATUSES = ("Proposed", "Accepted", "Withdrawn")
_APPROVAL_RECORD_RE = re.compile(r"^### Approval Record\s*$")
_PENDING_BULLET_RE = re.compile(r"^- \*\*Current Decision Approval \(pending\)\*\*:")
_LEDGER_ID_RE = re.compile(r"\bAAL-\d{3}\b")
_LEDGER_HEADING_RE = re.compile(r"^#### (AAL-\d{3})\s*$")
_LEDGER_DOC = (
    REPO_ROOT
    / "docs"
    / "00_governance"
    / "governance_03_issue-and-uncertainty-management.md"
)


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


def _status_value(lines: list[str]) -> tuple[int, str] | None:
    """(line number, value) of the first non-empty line after `## Status`.

    The value is empty when the next non-empty line is another heading. None
    means the document has no `## Status` heading.
    """
    for line_no, title in _top_level_headings(lines):
        if title != "Status":
            continue
        for index in range(line_no, len(lines)):
            value = lines[index].strip()
            if value:
                return (index + 1, "" if value.startswith("#") else value)
        return (line_no, "")
    return None


def check_status_values(docs: list[DocFile]) -> list[Issue]:
    """Flag (ERROR) an ADR whose `## Status` value is not an allowed one."""
    issues: list[Issue] = []
    for doc in docs:
        if not _ADR_FILE_RE.match(Path(doc.rel_path).name):
            continue
        found = _status_value(doc.lines)
        if found is None:
            continue
        line_no, value = found
        if not value:
            message = "'## Status' has no value"
        elif value not in _ALLOWED_STATUSES:
            message = f"Status '{value}' is not one of: {', '.join(_ALLOWED_STATUSES)}"
        else:
            continue
        issues.append(
            Issue(file=doc.rel_path, line_no=line_no, severity="ERROR", message=message)
        )
    return issues


def check_pending_approval_form(
    docs: list[DocFile], ledger_ids: frozenset[str]
) -> list[Issue]:
    """Flag (ERROR) a pending approval bullet without a resolving ledger ID."""
    issues: list[Issue] = []
    for doc in docs:
        if not _ADR_FILE_RE.match(Path(doc.rel_path).name):
            continue
        in_record = False
        in_fence = False
        for line_no, line in enumerate(doc.lines, start=1):
            if line.startswith("```"):
                in_fence = not in_fence
            elif in_fence:
                continue
            elif line.startswith("#"):
                in_record = bool(_APPROVAL_RECORD_RE.match(line))
            elif in_record and _PENDING_BULLET_RE.match(line):
                cited = _LEDGER_ID_RE.findall(line)
                if not cited:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message="pending approval bullet cites no AAL-NNN ledger ID",
                        )
                    )
                issues.extend(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=f"ledger ID {ledger_id} has no entry in the ledger",
                    )
                    for ledger_id in cited
                    if ledger_id not in ledger_ids
                )
    return issues


def _ledger_ids_from_lines(lines: list[str]) -> frozenset[str]:
    """IDs of every `#### AAL-NNN` entry heading."""
    return frozenset(
        match.group(1) for line in lines if (match := _LEDGER_HEADING_RE.match(line))
    )


def _load_ledger_ids() -> frozenset[str]:
    return _ledger_ids_from_lines(_LEDGER_DOC.read_text(encoding="utf-8").splitlines())


def collect_issues() -> list[Issue]:
    docs = discover_md_files(ADR_DIR, prefix="")
    return (
        check_known_deviations_heading(docs)
        + check_notes_references_drift(docs)
        + check_section_headings(docs)
        + check_template_residue(docs)
        + check_status_values(docs)
        + check_pending_approval_form(docs, _load_ledger_ids())
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
            "(ERROR), Implementation Notes vs Implementation References "
            "file/symbol drift (WARNING), an unknown Status value (ERROR), and "
            "a pending approval bullet without a resolving ledger ID (ERROR)."
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
