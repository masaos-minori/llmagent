#!/usr/bin/env python3
"""check_known_deviation_sync.py — Verify ADR Known Deviations stay in sync with docs/.

Every ADR's `## Known Deviations` section (and `## Related Documents` ->
`### Known Issues` subsection) cites Known Issue IDs (e.g. `MCP-004`,
`EVENTBUS-008`) that are supposed to be tracked, with their current Status,
in one of the per-area canonical `docs/*_90_inconsistencies_and_known_issues.md`
documents. Two failure modes are possible:

  1. An ADR's Known Deviations bullet marks an ID as still open (or as
     resolved) while the canonical document's Status field for that same
     ID disagrees -- one side was updated and the other was not.
  2. An ADR references an ID that has no matching `### <ID>` entry in any
     canonical document at all -- a dangling reference (e.g. a typo, a
     removed entry, or a canonical entry recorded under the wrong heading
     level).

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
ADR_DIR = DOCS_DIR / "adr"

# Canonical documents are discovered by suffix, not a hardcoded three-document
# list -- EVENTBUS-008 is cited by ADR-006/ADR-008 but only resolves against
# docs/06_eventbus_90_inconsistencies_and_known_issues.md, which is not one of
# the three areas (mcp/agent/shared) the originating issue named explicitly.
_CANONICAL_SUFFIX = "_90_inconsistencies_and_known_issues.md"

_CANONICAL_ID_HEADER_RE = re.compile(r"^### ([A-Z]+-\d+):")
# Bullet-list form, e.g. "- **Status**: resolved" (04_mcp_90, 05_agent_90).
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
# Top-level "- **Known Issue**: ..." / "- **Resolved**: ..." bullets inside
# `## Known Deviations` -- these carry the resolved-like/open-like signal.
# Sibling continuation bullets ("- **Type**: ...", "- **Status**: ...", used
# by ADR-002's CI-001 for its own Proposed->Accepted transition, unrelated to
# canonical Known Issue sync) are intentionally not matched by this pattern.
_LABELED_BULLET_RE = re.compile(r"^\s*-\s+\*\*(Known Issue|Resolved)\*\*:\s*(.*)$")
_BULLET_LINE_RE = re.compile(r"^\s*-\s+")

# Canonical Status values recognized as "resolved-like" or "open-like" for
# automatic mismatch detection. Any other value (e.g. "deferred", the
# 90_shared_90 "partially resolved" bucket, or a 05_agent_90-style 5-tier
# label) is excluded from automatic mismatch reporting -- informational only,
# per the source Plan's Assumptions.
_RESOLVED_LIKE_STATUSES = frozenset({"resolved", "fixed", "closed"})
_OPEN_LIKE_STATUSES = frozenset({"open"})


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
    # "resolved-like" / "open-like" for a `## Known Deviations` bullet (which
    # always carries an explicit **Known Issue**/**Resolved** label); None for
    # a `## Related Documents` -> `### Known Issues` mention, which has no
    # such label and therefore contributes to the dangling-reference check
    # only, never to the Status-mismatch check.
    signal: str | None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_canonical_docs() -> list[DocFile]:
    """All docs/*_90_inconsistencies_and_known_issues.md files."""
    all_files = discover_md_files(DOCS_DIR, prefix="")
    return [f for f in all_files if f.rel_path.endswith(_CANONICAL_SUFFIX)]


def discover_adr_docs() -> list[DocFile]:
    """All docs/adr/*.md files."""
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
        headers = [
            (m.group(1), i)
            for i, line in enumerate(doc.lines)
            if (m := _CANONICAL_ID_HEADER_RE.match(line))
        ]
        for idx, (entry_id, header_idx) in enumerate(headers):
            end_idx = headers[idx + 1][1] if idx + 1 < len(headers) else len(doc.lines)
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


def _status_family(raw_status: str) -> str | None:
    lowered = raw_status.strip().lower()
    if lowered in _RESOLVED_LIKE_STATUSES:
        return "resolved-like"
    if lowered in _OPEN_LIKE_STATUSES:
        return "open-like"
    return None


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
            label, rest = labeled_match.group(1), labeled_match.group(2)
            # Anchored match, not search: the ID (if any) is always the very
            # first token after the label (e.g. "MCP-003 — ..."). A search
            # would also catch an unrelated ID-shaped token appearing later
            # in a free-form description (e.g. an "INV-03" invariant mention
            # inside a bullet that cites no real Known Issue ID at all).
            id_match = _ID_LOOKAHEAD_RE.match(rest.lstrip())
            if not id_match:
                continue
            signal = "resolved-like" if label == "Resolved" else "open-like"
            refs.append(
                AdrReference(
                    id=id_match.group(1),
                    adr_file=adr_file,
                    line_no=line_no,
                    section="Known Deviations",
                    signal=signal,
                )
            )

        known_issues = _section_body(doc.lines, "### Known Issues", 3)
        for line_no, line in known_issues:
            if not _BULLET_LINE_RE.match(line):
                continue
            for id_match in _ID_LOOKAHEAD_RE.finditer(line):
                refs.append(
                    AdrReference(
                        id=id_match.group(1),
                        adr_file=adr_file,
                        line_no=line_no,
                        section="Related Documents > Known Issues",
                        signal=None,
                    )
                )
    return refs


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

        if ref.signal is None:
            continue  # Related Documents mention: dangling check only.

        canonical_family = _status_family(canonical_entry.raw_status)
        if canonical_family is None:
            continue  # deferred / partially resolved / 5-tier value: informational only.

        if canonical_family != ref.signal:
            issues.append(
                Issue(
                    file=ref.adr_file,
                    line_no=ref.line_no,
                    severity="ERROR",
                    message=(
                        f"{ref.id} Status mismatch: canonical "
                        f"{canonical_entry.doc} marks it "
                        f"'{canonical_entry.raw_status}' ({canonical_family}), "
                        f"but this ADR's Known Deviations bullet marks it "
                        f"{ref.signal}"
                    ),
                )
            )
    return issues


def collect_issues() -> list[Issue]:
    canonical, parse_issues = parse_canonical_statuses(discover_canonical_docs())
    adr_refs = parse_adr_references(discover_adr_docs())
    issues = list(parse_issues)
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
            "Read-only cross-check of every ADR's Known Deviations (and "
            "Related Documents -> Known Issues) references against the "
            "Status field of the same Known Issue ID in its canonical "
            "docs/*_90_inconsistencies_and_known_issues.md document."
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
