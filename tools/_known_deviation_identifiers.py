#!/usr/bin/env python3
"""tools/_known_deviation_identifiers.py — UNK-/NC- identifier resolution
helpers for `check_known_deviation_sync.py` (rule 6, GV-022).

Split out by `tools/module_nodes.py` when the checker's rule set exceeded the
24576 B module-size gate. Imported only by `check_known_deviation_sync.py`.
"""

from __future__ import annotations

import re

from tools._docs_consistency_lib import DocFile, Issue

# Matches both the legacy per-area heading ("### MCP-004: Some title") and the
# consolidated governance document's heading ("#### RAG-003", no title on the
# same line) -- see docs/00_governance/governance_03_issue-and-uncertainty-management.md
# Part 1's Entry Template.
_CANONICAL_ID_HEADER_RE = re.compile(r"^#{3,4} ([A-Z]+-\d+)(?::|\s*$)")
# Plan-local `UNK-<N>` and inventory `NC-<N>` identifiers cited in an ADR must
# resolve to exactly one heading in the canonical document. The trailing
# lookahead follows `_ID_LOOKAHEAD_RE`: "UNK-01-D1-profile-config" is not the
# token "UNK-01".
_CITED_IDENTIFIER_RE = re.compile(r"\b(?:UNK|NC)-\d+\b(?!-?\w)")


def collect_governance_heading_counts(files: list[DocFile]) -> dict[str, int]:
    """Count every `###/#### <ID>` heading in the canonical documents.

    Unlike `parse_canonical_statuses()`, this ignores the `## Part 2` boundary:
    the Needs Confirmation Inventory headings are exactly what an `NC-`
    identifier must resolve to.
    """
    counts: dict[str, int] = {}
    for doc in files:
        for line in doc.lines:
            if match := _CANONICAL_ID_HEADER_RE.match(line):
                counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return counts


def find_unresolved_identifiers(
    files: list[DocFile], counts: dict[str, int]
) -> list[Issue]:
    """Report `UNK-`/`NC-` tokens cited in ADR documents whose heading count
    is not exactly 1 (ERROR)."""
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _CITED_IDENTIFIER_RE.finditer(line):
                identifier = match.group(0)
                count = counts.get(identifier, 0)
                if count == 1:
                    continue
                if count == 0:
                    reason = (
                        "has no entry in the canonical Known Issue document "
                        "(a plan-local identifier must not be cited in an ADR)"
                    )
                else:
                    reason = (
                        f"has {count} entries in the canonical Known Issue "
                        "document (an identifier must resolve to exactly one "
                        "heading)"
                    )
                issues.append(
                    Issue(
                        file=f"adr/{doc.rel_path}",
                        line_no=line_no,
                        severity="ERROR",
                        message=f"{identifier} {reason}",
                    )
                )
    return issues


# Matches both the legacy per-area heading ("### MCP-004: Some title") and the
# consolidated governance document's heading ("#### RAG-003", no title on the
# same line) -- see docs/00_governance/governance_03_issue-and-uncertainty-management.md
# Part 1's Entry Template.
_CANONICAL_ID_HEADER_RE = re.compile(r"^#{3,4} ([A-Z]+-\d+)(?::|\s*$)")


# Plan-local `UNK-<N>` and inventory `NC-<N>` identifiers cited in an ADR must
# resolve to exactly one heading in the canonical document. The trailing
# lookahead follows `_ID_LOOKAHEAD_RE`: "UNK-01-D1-profile-config" is not the
# token "UNK-01".
_CITED_IDENTIFIER_RE = re.compile(r"\b(?:UNK|NC)-\d+\b(?!-?\w)")
