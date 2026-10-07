#!/usr/bin/env python3
"""check_known_deviation_sync.py — Verify ADR Known Deviations stay in sync with docs/.

Every ADR's `## Known Deviations` section cites Known Issue IDs (e.g. `EVENTBUS-008`)
that are tracked in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1.
Two failure modes are reported:

  1. A `- **Resolved**:` bullet appears in an ADR's Known Deviations. The
     Current-Specification-Only Policy keeps no resolved items in active
     documents: a resolved deviation is removed, with any still-applicable
     requirement stated in the ADR's current sections instead (ERROR).
  2. An ADR references an ID that has no matching entry heading in the
     canonical document -- a dangling reference (e.g. a typo or a removed
     entry) (WARNING).

Usage:
    python tools/check_known_deviation_sync.py
    python tools/check_known_deviation_sync.py --format json
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

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    discover_md_files,
    report_and_exit,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ADR_DIR = DOCS_DIR / "10_adr"

# Canonical documents are discovered by suffix, not a hardcoded three-document
# list -- EVENTBUS-008 is cited by ADR-006/ADR-008 but only resolves against
# docs/06_eventbus_90_inconsistencies_and_known_issues.md, which is not one of
# the three areas (mcp/agent/shared) the originating issue named explicitly.
#
# The five area-specific `*_90_inconsistencies_and_known_issues.md` files this
# suffix originally matched were consolidated into
# `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 and
# deleted on 2026-09-03 (see that document's own Part 1 Consolidation Note) --
# the suffix match below now finds nothing on its own and is kept only as a
# harmless no-op in case a future per-area file reappears; the governance
# document is the current, real canonical source and is always included
# explicitly, independent of the suffix.
_CANONICAL_SUFFIX = "_90_inconsistencies_and_known_issues.md"
_GOVERNANCE_KNOWN_ISSUES_DOC = "governance_03_issue-and-uncertainty-management.md"
_GOVERNANCE_KNOWN_ISSUES_PATH = (
    DOCS_DIR / "00_governance" / _GOVERNANCE_KNOWN_ISSUES_DOC
)

# Matches both the legacy per-area heading ("### MCP-004: Some title") and the
# consolidated governance document's heading ("#### RAG-003", no title on the
# same line) -- see docs/00_governance/governance_03_issue-and-uncertainty-management.md
# Part 1's Entry Template.
_CANONICAL_ID_HEADER_RE = re.compile(r"^#{3,4} ([A-Z]+-\d+)(?::|\s*$)")
# The governance document's Part 2 ("Needs Confirmation Inventory") also uses
# `#### NC-<N>` headings that match the ID shape above (letters-dash-digits)
# but are a different inventory entirely -- entries at or after this heading
# must not be parsed as Known Issues.
_PART_BOUNDARY_RE = re.compile(r"^## Part 2\b")
# Bullet-list form, e.g. "- **Status**: resolved" (04_mcp_90, 05_agent_90, and
# the consolidated governance document, which also uses this form).
_CANONICAL_BULLET_STATUS_RE = re.compile(r"^-\s+\*\*Status\*\*:\s*(\S+)")
# Inline-prose fallback, e.g. "... Status: partially resolved / Severity: High
# / Type: design-gap. ..." (90_shared_90).
_CANONICAL_INLINE_STATUS_RE = re.compile(
    r"Status:\s*([A-Za-z][A-Za-z ]*?)\s*/\s*Severity", re.IGNORECASE
)

# A candidate ID token must be immediately followed by whitespace, an em-dash,
# or end-of-line -- otherwise "ADR-004-D1-profile-config-model-still-present"
# would be misread as the ID "ADR-004".
_ID_LOOKAHEAD_RE = re.compile(r"([A-Z]+-\d+)(?=\s|—|$)")
# "- **Known Issue**: <ID> ..." bullets inside `## Known Deviations` cite an
# active Known Issue.
_LABELED_BULLET_RE = re.compile(r"^\s*-\s+\*\*Known Issue\*\*:\s*(.*)$")
# Any "- **Resolved ...**:" bullet, or a "- **Status**: Resolved" continuation
# bullet, inside `## Known Deviations` records a resolved item, which the
# Current-Specification-Only Policy does not allow in active documents.
_RESOLVED_BULLET_RE = re.compile(
    r"^\s*-\s+(?:\*\*Resolved[^*]*\*\*:|\*\*Status\*\*:\s*Resolved\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CanonicalStatus:
    """A canonical Known Issue entry's Status, as recorded in one doc."""

    doc: str  # canonical doc's rel_path, relative to docs/
    raw_status: str


@dataclass(frozen=True)
class AdrReference:
    """One Known Issue ID reference found inside an ADR document."""

    id: str
    adr_file: str  # "adr/<name>.md", relative to docs/
    line_no: int
    section: str


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_canonical_docs() -> list[DocFile]:
    """All docs/*_90_inconsistencies_and_known_issues.md files, plus the
    consolidated `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
    (the current real canonical source — see the module-level comment above
    `_CANONICAL_SUFFIX`)."""
    result: list[DocFile] = []
    # Search subfolders for per-area inconsistency docs (post-reorg).
    for subdir in DOCS_DIR.iterdir():
        if subdir.is_dir():
            result.extend(discover_md_files(subdir, prefix=""))
    # Also check root level for legacy files during transition.
    for p in sorted(DOCS_DIR.glob("*.md")):
        if p.name.endswith(_CANONICAL_SUFFIX):
            content = p.read_text(encoding="utf-8")
            result.append(DocFile(path=p, rel_path=p.name, lines=content.splitlines()))
    # Add the governance document explicitly, unless the subfolder scan above
    # already found it (it lives under docs/00_governance/).
    if any(doc.path == _GOVERNANCE_KNOWN_ISSUES_PATH for doc in result):
        return result
    try:
        content = _GOVERNANCE_KNOWN_ISSUES_PATH.read_text(encoding="utf-8")
        result.append(
            DocFile(
                path=_GOVERNANCE_KNOWN_ISSUES_PATH,
                rel_path=_GOVERNANCE_KNOWN_ISSUES_DOC,
                lines=content.splitlines(),
            )
        )
    except OSError:
        pass
    return result


def discover_adr_docs() -> list[DocFile]:
    """All docs/10_adr/*.md files."""
    return discover_md_files(ADR_DIR, prefix="")


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------


def _heading_level(line: str) -> int | None:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return None
    return len(stripped) - len(stripped.lstrip("#"))


def _section_body(lines: list[str], heading: str, level: int) -> list[tuple[int, str]]:
    """Return (1-indexed line_no, line) pairs for the body of the first
    section whose heading line equals *heading* exactly, stopping before the
    next heading of level <= *level* (or end of file)."""
    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i
            break
    if start is None:
        return []
    body: list[tuple[int, str]] = []
    for i in range(start + 1, len(lines)):
        line_level = _heading_level(lines[i])
        if line_level is not None and line_level <= level:
            break
        body.append((i + 1, lines[i]))
    return body


# ---------------------------------------------------------------------------
# Canonical-doc parsing
# ---------------------------------------------------------------------------


def parse_canonical_statuses(
    files: list[DocFile],
) -> tuple[dict[str, CanonicalStatus], list[Issue]]:
    """Parse every `### <ID>: <title>` entry's Status field across *files*.

    Returns the {ID: CanonicalStatus} map plus a WARNING Issue for any entry
    whose Status could not be parsed in either recognized format -- flagged
    explicitly rather than silently skipped.
    """
    statuses: dict[str, CanonicalStatus] = {}
    issues: list[Issue] = []
    for doc in files:
        # Stop scanning at a "## Part 2" boundary (the governance document's
        # Needs Confirmation Inventory) -- its `#### NC-<N>` headings are
        # ID-shaped but belong to a different inventory, not Known Issues.
        boundary = next(
            (i for i, line in enumerate(doc.lines) if _PART_BOUNDARY_RE.match(line)),
            len(doc.lines),
        )
        scan_lines = doc.lines[:boundary]
        headers = [
            (m.group(1), i)
            for i, line in enumerate(scan_lines)
            if (m := _CANONICAL_ID_HEADER_RE.match(line))
        ]
        for idx, (entry_id, header_idx) in enumerate(headers):
            end_idx = headers[idx + 1][1] if idx + 1 < len(headers) else boundary
            body = doc.lines[header_idx + 1 : end_idx]

            raw_status: str | None = None
            for line in body:
                bullet_match = _CANONICAL_BULLET_STATUS_RE.match(line)
                if bullet_match:
                    raw_status = bullet_match.group(1)
                    break
            if raw_status is None:
                inline_match = _CANONICAL_INLINE_STATUS_RE.search(" ".join(body))
                if inline_match:
                    raw_status = inline_match.group(1).strip()

            if raw_status is None:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=header_idx + 1,
                        severity="WARNING",
                        message=(
                            f"{entry_id}'s Status field could not be parsed in "
                            f"either the bullet-list or inline-prose format "
                            f"(skipped from cross-check)"
                        ),
                    )
                )
                continue

            statuses[entry_id] = CanonicalStatus(
                doc=doc.rel_path, raw_status=raw_status
            )
    return statuses, issues


# ---------------------------------------------------------------------------
# ADR-side parsing
# ---------------------------------------------------------------------------


def parse_adr_references(files: list[DocFile]) -> list[AdrReference]:
    """Extract Known Issue ID references from each ADR's two scoped sections."""
    refs: list[AdrReference] = []
    for doc in files:
        adr_file = f"adr/{doc.rel_path}"

        known_deviations = _section_body(doc.lines, "## Known Deviations", 2)
        for line_no, line in known_deviations:
            labeled_match = _LABELED_BULLET_RE.match(line)
            if not labeled_match:
                continue
            rest = labeled_match.group(1)
            # Anchored match, not search: the ID (if any) is always the very
            # first token after the label (e.g. "MCP-003 — ..."). A search
            # would also catch an unrelated ID-shaped token appearing later
            # in a free-form description (e.g. an "INV-03" invariant mention
            # inside a bullet that cites no real Known Issue ID at all).
            id_match = _ID_LOOKAHEAD_RE.match(rest.lstrip())
            if not id_match:
                continue
            refs.append(
                AdrReference(
                    id=id_match.group(1),
                    adr_file=adr_file,
                    line_no=line_no,
                    section="Known Deviations",
                )
            )
    return refs


def find_resolved_bullets(files: list[DocFile]) -> list[Issue]:
    """Report resolved-item bullets in each ADR's `## Known Deviations` (ERROR)."""
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in _section_body(doc.lines, "## Known Deviations", 2):
            if _RESOLVED_BULLET_RE.match(line):
                issues.append(
                    Issue(
                        file=f"adr/{doc.rel_path}",
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            "resolved item in Known Deviations is not allowed "
                            "(Current-Specification-Only Policy); remove it and "
                            "state any still-applicable requirement in the ADR's "
                            "current sections"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Cross-check
# ---------------------------------------------------------------------------


def cross_check(
    canonical: dict[str, CanonicalStatus], adr_refs: list[AdrReference]
) -> list[Issue]:
    issues: list[Issue] = []
    for ref in adr_refs:
        canonical_entry = canonical.get(ref.id)
        if canonical_entry is None:
            issues.append(
                Issue(
                    file=ref.adr_file,
                    line_no=ref.line_no,
                    severity="WARNING",
                    message=(
                        f"{ref.id} referenced in {ref.section} has no matching "
                        f"`### {ref.id}` entry in any docs/*{_CANONICAL_SUFFIX} "
                        f"canonical document (dangling reference)"
                    ),
                )
            )
            continue
    return issues


def collect_issues() -> list[Issue]:
    canonical, parse_issues = parse_canonical_statuses(discover_canonical_docs())
    adr_docs = discover_adr_docs()
    adr_refs = parse_adr_references(adr_docs)
    issues = list(parse_issues)
    issues.extend(find_resolved_bullets(adr_docs))
    issues.extend(cross_check(canonical, adr_refs))
    return issues


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _issue_to_dict(issue: Issue) -> dict[str, object]:
    return {
        "file": issue.file,
        "line_no": issue.line_no,
        "severity": issue.severity,
        "message": issue.message,
    }


def render_json(issues: list[Issue]) -> str:
    payload = [
        _issue_to_dict(issue)
        for issue in sorted(issues, key=lambda i: (i.file, i.line_no))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only cross-check of every ADR's Known Deviations "
            "references against the "
            "Known Issue entries in governance_03, and rejection of "
            "`- **Resolved**:` bullets in Known Deviations."
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
