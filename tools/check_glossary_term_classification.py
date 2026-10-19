#!/usr/bin/env python3
"""check_glossary_term_classification.py — Flag general/common words in a glossary.

Scans the "Compatibility and Lifecycle Terminology" glossary table in
`docs/00_governance/governance_02_documentation-metadata.md` and flags entries
whose term is a general/common English word rather than a project-specific
identifier. This closes the documented `Partial` gap for GV-015.

Findings are Warnings: the default run is report-only (exit 0); `--strict`
exits 1 on any warning. See
`docs/00_governance/governance_04_documentation-checks.md`'s Governance
Verification Matrix (GV-015) for its registered entry.

Classification is conservative and fails safe toward not flagging ambiguous
terms: a term that carries a project-specific marker (any uppercase letter, i.e.
PascalCase/camelCase/acronym, or a project domain prefix) is treated as
project-specific. Only a fully-lowercase term that matches a small common-English
word heuristic is flagged, so the current canonical term set (all title-case)
yields zero findings.

Usage:
    python tools/check_glossary_term_classification.py            # report-only
    python tools/check_glossary_term_classification.py --strict   # exit 1 on any warning
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent

GOVERNANCE_02_REL = "docs/00_governance/governance_02_documentation-metadata.md"
GOVERNANCE_02_SECTION = "Compatibility and Lifecycle Terminology"

# A term carrying any uppercase letter is PascalCase/camelCase/acronym-shaped
# and is treated as project-specific (the fail-safe direction).
_PROJECT_PREFIX_RE = re.compile(r"^(?:gv|rag|edc|mq|nc|dlq|ack|dto)-", re.IGNORECASE)

# Curated list of generic, non-project-specific words. Kept intentionally small
# and conservative: only words that are plainly not project identifiers.
_COMMON_ENGLISH_WORDS: frozenset[str] = frozenset(
    {
        "example",
        "behavior",
        "behaviour",
        "sample",
        "demo",
        "placeholder",
        "thing",
        "stuff",
        "misc",
        "other",
        "extra",
        "foo",
        "bar",
        "baz",
        "temp",
        "dummy",
    }
)

_SEPARATOR_ROW_RE = re.compile(r"^\s*\|[\s:|-]*\|\s*$")


def resolve_governance_02(root: Path) -> Path:
    """Return the path to `governance_02_documentation-metadata.md` under *root*."""
    return root / "docs" / "00_governance" / "governance_02_documentation-metadata.md"


def _find_section_index(lines: list[str], section: str) -> int | None:
    """Return the 0-based index of the first line containing *section* (case-insensitive)."""
    lowered = section.lower()
    for i, line in enumerate(lines):
        if lowered in line.lower():
            return i
    return None


def _is_separator_row(line: str) -> bool:
    """Return True if *line* is a Markdown table separator row (`|---|---|`)."""
    return bool(_SEPARATOR_ROW_RE.match(line))


def _first_cell(line: str) -> str:
    """Return the first pipe-delimited cell of a Markdown table *line*."""
    parts = line.split("|")
    return parts[1] if len(parts) >= 2 else ""


def parse_glossary_terms(governance_02_path: Path) -> list[tuple[str, int]]:
    """Return ``(term, line_no)`` pairs from the glossary table.

    *line_no* is 1-based within ``governance_02_documentation-metadata.md``.
    Locates the "Compatibility and Lifecycle Terminology" section header and
    reads the following Markdown table rows, taking the first cell of each data
    row. Returns ``[]`` if the section or table is missing (fail safe).
    """
    if not governance_02_path.is_file():
        return []
    lines = governance_02_path.read_text(encoding="utf-8").splitlines()
    header_idx = _find_section_index(lines, GOVERNANCE_02_SECTION)
    if header_idx is None:
        return []

    table_row_idx = None
    for i in range(header_idx + 1, len(lines)):
        if lines[i].lstrip().startswith("|"):
            table_row_idx = i
            break
    if table_row_idx is None:
        return []

    terms: list[tuple[str, int]] = []
    i = table_row_idx + 1
    if i < len(lines) and _is_separator_row(lines[i]):
        i += 1
    while i < len(lines):
        line = lines[i]
        if not line.lstrip().startswith("|"):
            break
        if _is_separator_row(line):
            i += 1
            continue
        cell = _first_cell(line).strip()
        if cell:
            terms.append((cell, i + 1))
        i += 1
    return terms


def classify(term: str) -> bool:
    """Return True if *term* is a general/common English word (should be flagged).

    Conservative and fail-safe: a term with any uppercase letter (PascalCase/
    camelCase/acronym) or a project domain prefix is treated as project-specific
    and never flagged. Only a fully-lowercase term matching the common-English
    heuristic is flagged.
    """
    if not term:
        return False
    if term != term.lower():
        return False
    if _PROJECT_PREFIX_RE.match(term):
        return False
    return term in _COMMON_ENGLISH_WORDS


def audit(terms: list[tuple[str, int]]) -> list[Issue]:
    """Return a `Warning` finding for each general/common-term ``(term, line_no)``."""
    issues: list[Issue] = []
    for term, line_no in terms:
        if classify(term):
            issues.append(
                Issue(
                    file=GOVERNANCE_02_REL,
                    line_no=line_no,
                    severity="WARNING",
                    message=(
                        f"glossary term {term!r} is a general/common English "
                        "word rather than a project-specific identifier — see "
                        "GV-015"
                    ),
                )
            )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag general/common English words in the glossary term table.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root containing docs/ (default: current repo root)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any warning is found (default: report-only)",
    )
    args = parser.parse_args(argv)

    governance_02_path = resolve_governance_02(args.root)
    terms = parse_glossary_terms(governance_02_path)
    issues = audit(terms)

    exit_code = report_and_exit(issues)
    if args.strict and issues:
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
