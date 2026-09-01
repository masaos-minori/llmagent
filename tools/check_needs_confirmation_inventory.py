#!/usr/bin/env python3
"""check_needs_confirmation_inventory.py — Verify the NC inventory stays in sync with docs/.

docs/00_governance_03_issue-and-uncertainty-management.md Part 2 is meant to be the
single, centralized place where every "Needs confirmation" item across
docs/ is tracked to resolution. Two failure modes were found by manual
review (docs_review_governance.md):

  1. An NC entry is marked "resolved" in the inventory, but its cited
     Source File still contains an inline "Needs confirmation" marker --
     the source doc was never updated to remove the now-stale caveat.
  2. A doc contains an inline "Needs confirmation" marker for a file that
     has no corresponding entry in the inventory at all -- an untracked
     item that the inventory's stated purpose ("centralized inventory ...
     preventing them from being silently accepted as facts") fails to
     cover.

A third, self-contained check catches the inventory document contradicting
itself: 00_governance_03 states its entries "must contain the following
eleven fields" while actually enumerating a different number.

Usage:
    python tools/check_needs_confirmation_inventory.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

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
INVENTORY_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"

# Meta/governance docs that discuss the "Needs confirmation" label itself
# (defining it, cross-referencing it) rather than flagging an actual
# unverified statement in domain content.
_GOVERNANCE_META_DOCS = frozenset(
    {
        "00_governance_01_documentation-governance.md",
        "00_governance_02_canonical-source-rule.md",
        "00_governance_03_evidence-labels.md",
        "00_governance_04_known-issues-template.md",
        "00_governance_05_deprecated-items.md",
        "00_governance_06_ai-reading-metadata.md",
        "00_governance_03_issue-and-uncertainty-management.md",
        "00_governance_08_known-issues-migration-plan.md",
    }
)

_INLINE_MARKER_RE = re.compile(r"needs confirmation", re.IGNORECASE)
_NC_ENTRY_RE = re.compile(r"^#### (NC-\d+)\s*$")
_PART2_HEADER_RE = re.compile(r"^## Part 2:")
_SECTION_HEADER_RE = re.compile(r"^## ")
_SOURCE_FILE_RE = re.compile(r"\*\*Source File\*\*:\s*`([^`]+)`")
_STATUS_RE = re.compile(r"\*\*Status\*\*:\s*(\S+)")

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}
_DECLARED_COUNT_RE = re.compile(
    r"following (" + "|".join(_NUMBER_WORDS) + r") (?:required )?fields", re.IGNORECASE
)
_NUMBERED_ITEM_RE = re.compile(r"^\d+\.\s+\*\*")


class NcEntry:
    def __init__(self, nc_id: str, source_file: str | None, status: str | None):
        self.nc_id = nc_id
        self.source_file = source_file
        self.status = status


def _parse_inventory_entries(inventory: DocFile) -> list[NcEntry]:
    """Split the inventory's '## Inventory Items' section into per-NC entries."""
    entries: list[NcEntry] = []
    current_id: str | None = None
    current_source: str | None = None
    current_status: str | None = None
    in_part2 = False

    def flush() -> None:
        if current_id is not None:
            entries.append(NcEntry(current_id, current_source, current_status))

    for line in inventory.lines:
        if not in_part2:
            if _PART2_HEADER_RE.match(line):
                in_part2 = True
                continue
            continue
        if _SECTION_HEADER_RE.match(line):
            break
        match = _NC_ENTRY_RE.match(line)
        if match:
            flush()
            current_id = match.group(1)
            current_source = None
            current_status = None
            continue
        if current_id is None:
            continue
        src_match = _SOURCE_FILE_RE.search(line)
        if src_match:
            current_source = src_match.group(1)
        status_match = _STATUS_RE.search(line)
        if status_match:
            current_status = status_match.group(1)
    flush()
    return entries


def check_stale_resolved_markers(
    docs_dir: Path, files: list[DocFile], entries: list[NcEntry]
) -> list[Issue]:
    """Flag a 'resolved' NC entry whose Source File still carries the marker."""
    by_name = {f.name: f for f in docs_dir.glob("*.md")}
    issues: list[Issue] = []
    for entry in entries:
        if entry.status not in ("resolved", "fixed") or not entry.source_file:
            continue
        target = by_name.get(entry.source_file)
        if target is None:
            continue
        content = target.read_text(encoding="utf-8")
        if _INLINE_MARKER_RE.search(content):
            issues.append(
                Issue(
                    file=entry.source_file,
                    line_no=0,
                    severity="ERROR",
                    message=(
                        f"{entry.nc_id} is marked resolved in "
                        f"{INVENTORY_DOC_NAME}, but this source file still "
                        f"contains a 'Needs confirmation' marker "
                        f"(source doc was not updated after resolution)"
                    ),
                )
            )
    return issues


def check_untracked_inline_markers(
    docs_dir: Path, files: list[DocFile], entries: list[NcEntry]
) -> list[Issue]:
    """Flag an inline 'Needs confirmation' marker whose file has no inventory entry."""
    tracked_files = {e.source_file for e in entries if e.source_file}
    issues: list[Issue] = []
    for doc in files:
        if doc.rel_path in _GOVERNANCE_META_DOCS:
            continue
        for line_no, line in enumerate(doc.lines, start=1):
            if _INLINE_MARKER_RE.search(line) and doc.rel_path not in tracked_files:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="WARNING",
                        message=(
                            f"inline 'Needs confirmation' marker has no matching "
                            f"entry in {INVENTORY_DOC_NAME} (untracked item)"
                        ),
                    )
                )
    return issues


def check_declared_field_count(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag 'the following N fields' claims contradicted by the actual list length."""
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            match = _DECLARED_COUNT_RE.search(line)
            if not match:
                continue
            declared = _NUMBER_WORDS[match.group(1).lower()]
            actual = 0
            for later_line in doc.lines[line_no:]:
                if _NUMBERED_ITEM_RE.match(later_line.strip()):
                    actual += 1
                elif actual and not later_line.strip():
                    break
            if actual and actual != declared:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"declares '{match.group(1)} fields' ({declared}) but "
                            f"the following numbered list has {actual} item(s)"
                        ),
                    )
                )
    return issues


def main() -> int:
    files = discover_md_files(DOCS_DIR, prefix="")
    inventory = next((f for f in files if f.rel_path == INVENTORY_DOC_NAME), None)
    if inventory is None:
        print(f"ERROR: {INVENTORY_DOC_NAME} not found under docs/.", file=sys.stderr)
        return 1

    entries = _parse_inventory_entries(inventory)

    all_issues: list[Issue] = []
    all_issues += check_stale_resolved_markers(DOCS_DIR, files, entries)
    all_issues += check_untracked_inline_markers(DOCS_DIR, files, entries)
    all_issues += check_declared_field_count(DOCS_DIR, files)

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
