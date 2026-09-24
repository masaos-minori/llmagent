#!/usr/bin/env python3
"""tools/check_issue_inventory_conformance.py

Conformance checker for docs/00_governance_03_issue-and-uncertainty-management.md.

Validates:
  (a) Vocabulary conformance — Status/Type/Severity/Area/Owner against defined value sets
   (b) Template field-count — 16 fields per Part 1 entry, 14 per Part 2 entry; exempt removal placeholders.
  (c) Orphaned bullets — - **Field:** bullets after removal placeholders
  (d) Closing-summary consistency — Part 1 closing ID list vs. actual headings
  (e) Referential integrity — Related/Related NC/Target ID resolution

Removal placeholders (prose paragraphs ending in 'do not create a #### {ID} heading')
are exempt from field-count checks and classified as Warning (not Blocking) for
referential-integrity lookups.

Modeled on tools/check_known_deviation_sync.py and tools/check_needs_confirmation_inventory.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

# Reused from _docs_consistency_lib.py
from _docs_consistency_lib import DocFile, Issue, report_and_exit

# ── Vocabulary value sets ────────────────────────────────────────────────────────

PART1_STATUS_VALUES = {"open", "investigating", "deferred"}
PART1_TYPE_VALUES = {
    "document-code-mismatch",
    "document-document-mismatch",
    "obsolete-description",
    "missing-documentation",
    "ambiguous-behavior",
    "implementation-bug",
    "design-gap",
    "operational-gap",
}
PART1_SEVERITY_VALUES = {"High", "Medium", "Low"}
PART1_AREA_VALUES = {
    "Overview",
    "Deployment",
    "RAG",
    "MCP",
    "Agent",
    "EventBus",
    "Shared/DB",
    "Governance",
}
PART1_OWNER_VALUES = {"Unassigned", "[Name]", "Team"}

PART2_STATUS_VALUES = {"open", "investigating", "deferred"}

# ── Document structure constants ─────────────────────────────────────────────────

GOVERNANCE_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"
REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
GOVERNANCE_DOC_PATH = DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME
REMOVAL_PLACEHOLDER_RE = re.compile(r"do not create a `#### ([A-Z]+-\d+)` heading")
FIELD_BULLET_RE = re.compile(r"- \*\*([^*]+)\*\*: ")
HEADING_RE = re.compile(r"^#### (.+)$")
CLOSING_SUMMARY_RE = re.compile(
    r"No other active .* beyond (\S+)(?: through (\S+))? above\."
)

# ── Entry parsing helpers ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Entry:
    """Parsed entry from the governance document."""

    id: str
    part: str  # "Part 1" or "Part 2"
    line_start: int
    line_end: int
    fields: dict[str, str]  # field_name -> value
    is_removal_placeholder: bool = False


def parse_entries(doc: DocFile) -> list[Entry]:
    """Parse all entries from the governance document."""
    entries: list[Entry] = []
    current_part: str | None = None
    current_entry: Entry | None = None

    for line_no, line in enumerate(doc.lines, start=1):
        # Track which part we're in
        if line.startswith("## Part 1"):
            current_part = "Part 1"
        elif line.startswith("## Part 2"):
            current_part = "Part 2"

        # Check for new entry heading
        heading_match = HEADING_RE.match(line.strip())
        if heading_match:
            # Save previous entry if exists
            if current_entry is not None:
                entries.append(current_entry)

            entry_id = heading_match.group(1).strip()
            current_entry = Entry(
                id=entry_id,
                part=current_part or "Unknown",
                line_start=line_no,
                line_end=line_no,
                fields={},
                is_removal_placeholder=False,
            )
        elif current_entry is not None:
            # Parse field bullet
            field_match = FIELD_BULLET_RE.match(line.strip())
            if field_match:
                field_name = field_match.group(1).strip()
                field_value = line.strip()[field_match.end() :].strip()
                current_entry.fields[field_name] = field_value
                current_entry = replace(current_entry, line_end=line_no)

            # Check for removal placeholder paragraph
            if not field_match and current_part == "Part 1":
                placeholder_match = REMOVAL_PLACEHOLDER_RE.search(line)
                if placeholder_match:
                    current_entry = replace(current_entry, is_removal_placeholder=True)
        else:
            # Check for removal placeholder paragraph even without a preceding entry
            if current_part == "Part 1":
                placeholder_match = REMOVAL_PLACEHOLDER_RE.search(line)
                if placeholder_match:
                    # Create synthetic entry for orphaned-bullet detection
                    entry_id = placeholder_match.group(1)
                    synthetic = Entry(
                        id=entry_id,
                        part="Part 1",
                        line_start=line_no,
                        line_end=line_no,
                        fields={},
                        is_removal_placeholder=True,
                    )
                    entries.append(synthetic)

    # Don't forget the last entry
    if current_entry is not None:
        entries.append(current_entry)

    return entries


# ── Check functions ──────────────────────────────────────────────────────────────


def check_vocabulary(doc: DocFile) -> list[Issue]:
    """Validate Status/Type/Severity/Area/Owner against defined value sets."""
    issues: list[Issue] = []
    entries = parse_entries(doc)

    for entry in entries:
        if entry.is_removal_placeholder:
            continue

        if entry.part == "Part 1":
            # Validate Part 1 fields
            status_val = entry.fields.get("Status", "")
            if status_val not in PART1_STATUS_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Status value '{status_val}'",
                    )
                )

            type_val = entry.fields.get("Type", "")
            if type_val not in PART1_TYPE_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Type value '{type_val}'",
                    )
                )

            severity_val = entry.fields.get("Severity", "")
            if severity_val not in PART1_SEVERITY_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Severity value '{severity_val}'",
                    )
                )

            area_val = entry.fields.get("Area", "")
            if area_val not in PART1_AREA_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Area value '{area_val}'",
                    )
                )

            owner_val = entry.fields.get("Owner", "")
            if owner_val not in PART1_OWNER_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Owner value '{owner_val}'",
                    )
                )

        elif entry.part == "Part 2":
            # Validate Part 2 Status only
            status_val = entry.fields.get("Status", "")
            if status_val not in PART2_STATUS_VALUES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=entry.line_start,
                        severity="ERROR",
                        message=f"{entry.id}: invalid Status value '{status_val}'",
                    )
                )

    return issues


def check_template_field_count(doc: DocFile) -> list[Issue]:
    """Count - **Field:** bullets per entry; require 16 (Part 1) / 14 (Part 2); exempt placeholders."""
    issues: list[Issue] = []
    entries = parse_entries(doc)

    for entry in entries:
        if entry.is_removal_placeholder:
            continue

        required_fields = 16 if entry.part == "Part 1" else 15
        actual_fields = len(entry.fields)

        if actual_fields != required_fields:
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=entry.line_start,
                    severity="ERROR",
                    message=f"{entry.id}: expected {required_fields} fields, found {actual_fields}",
                )
            )

    return issues


def check_orphaned_bullets(doc: DocFile) -> list[Issue]:
    """Detect - **Field:** bullets after a removal-placeholder with no intervening #### heading."""
    issues: list[Issue] = []
    entries = parse_entries(doc)

    for i, entry in enumerate(entries):
        if entry.is_removal_placeholder:
            # Check if next entry has any fields (orphaned bullets)
            if i + 1 < len(entries):
                next_entry = entries[i + 1]
                if next_entry.fields:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=next_entry.line_start,
                            severity="WARNING",
                            message=f"{next_entry.id}: orphaned bullets after removal placeholder",
                        )
                    )

    return issues


def check_closing_summary(doc: DocFile) -> list[Issue]:
    """Verify Part 1 closing ID list matches actual #### headings."""
    issues: list[Issue] = []

    # Find Part 1 closing summary
    closing_line: str | None = None
    closing_line_no: int = 0

    for line_no, line in enumerate(doc.lines, start=1):
        if line.startswith("## Part 2"):
            break
        match = CLOSING_SUMMARY_RE.search(line)
        if match:
            closing_line = line
            closing_line_no = line_no

    if closing_line is None:
        return issues

    # Extract IDs from closing summary
    first_id = closing_line.split("beyond")[1].split("above")[0].strip().split()[0]
    ids_in_summary: set[str] = set()
    ids_in_summary.add(first_id)

    # Check if there's a range
    if "through" in closing_line:
        range_match = CLOSING_SUMMARY_RE.search(closing_line)
        if range_match and range_match.group(2):
            second_id = range_match.group(2)
            # Generate all IDs in the range (simplified for sequential IDs)
            prefix = re.match(r"([A-Z]+)-(\d+)", first_id)
            if prefix:
                prefix_str, start_num = prefix.groups()
                end_match = re.match(r"\d+", second_id)
                if end_match:
                    end_num = int(end_match.group())
                    for num in range(int(start_num), end_num + 1):
                        ids_in_summary.add(f"{prefix_str}-{num}")

    # Get actual headings in Part 1
    actual_ids: set[str] = set()
    in_part1 = False

    for line in doc.lines:
        if line.startswith("## Part 1"):
            in_part1 = True
        elif line.startswith("## Part 2"):
            break
        elif in_part1:
            heading_match = HEADING_RE.match(line.strip())
            if heading_match:
                actual_ids.add(heading_match.group(1).strip())

    # Compare
    missing_in_heading = ids_in_summary - actual_ids
    extra_in_heading = actual_ids - ids_in_summary

    if missing_in_heading:
        issues.append(
            Issue(
                file=doc.rel_path,
                line_no=closing_line_no,
                severity="ERROR",
                message=f"Closing summary references IDs not found as headings: {missing_in_heading}",
            )
        )

    if extra_in_heading:
        issues.append(
            Issue(
                file=doc.rel_path,
                line_no=closing_line_no,
                severity="WARNING",
                message=f"Heading IDs not referenced in closing summary: {extra_in_heading}",
            )
        )

    return issues


def check_referential_integrity(doc: DocFile) -> list[Issue]:
    """Resolve Related/Related NC/Target IDs against headings and placeholder-prose IDs."""
    issues: list[Issue] = []
    entries = parse_entries(doc)

    # Build set of all valid IDs (headings + placeholder IDs)
    valid_ids: set[str] = set()
    placeholder_ids: set[str] = set()

    for entry in entries:
        valid_ids.add(entry.id)
        if entry.is_removal_placeholder:
            # Extract ID from placeholder text
            placeholder_match = REMOVAL_PLACEHOLDER_RE.search(
                doc.lines[entry.line_start - 1] if entry.line_start > 0 else ""
            )
            if placeholder_match:
                placeholder_ids.add(placeholder_match.group(1))

    # Also add placeholder IDs from parsing
    for entry in entries:
        if entry.is_removal_placeholder:
            placeholder_match = REMOVAL_PLACEHOLDER_RE.search(
                doc.lines[entry.line_start - 1] if entry.line_start > 0 else ""
            )
            if placeholder_match and placeholder_match.group(1):
                placeholder_ids.add(placeholder_match.group(1))

    # Check each entry's Related/Related NC/Target fields
    for entry in entries:
        if entry.is_removal_placeholder:
            continue

        for field_name in ("Related", "Related NC", "Target"):
            related_val = entry.fields.get(field_name, "")
            if not related_val or related_val == "None":
                continue

            # Split multiple values (comma-separated)
            for ref_id in re.split(r"[,\s]+", related_val):
                ref_id = ref_id.strip().strip("`")
                if not ref_id:
                    continue

                # Skip values that don't look like IDs (e.g., dates, file paths)
                if not re.match(r"^[A-Z]+-\d+$", ref_id):
                    continue

                if ref_id in valid_ids:
                    # Resolves to existing heading — OK
                    pass
                elif ref_id in placeholder_ids:
                    # Resolves to removal placeholder — Warning
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=entry.line_start,
                            severity="WARNING",
                            message=f"{entry.id}: {field_name} → {ref_id} resolves to removal placeholder (not Blocking)",
                        )
                    )
                else:
                    # Neither heading nor placeholder — Blocking
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=entry.line_start,
                            severity="ERROR",
                            message=f"{entry.id}: {field_name} → {ref_id} unresolved (neither heading nor placeholder exists)",
                        )
                    )

    return issues


# ── Main ─────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "doc_path", nargs="?", default=None, help="Path to the governance document"
    )
    args = parser.parse_args()

    doc_path = Path(args.doc_path) if args.doc_path else GOVERNANCE_DOC_PATH

    # Parse the document
    content = doc_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    doc = DocFile(doc_path, rel_path=GOVERNANCE_DOC_NAME, lines=lines)

    issues: list[Issue] = []
    issues.extend(check_vocabulary(doc))
    issues.extend(check_template_field_count(doc))
    issues.extend(check_orphaned_bullets(doc))
    issues.extend(check_closing_summary(doc))
    issues.extend(check_referential_integrity(doc))

    if issues:
        print(f"\nFound {len(issues)} conformance violation(s):\n", file=sys.stderr)
        for issue in issues:
            print(f"  [{issue.severity}] {issue.message}", file=sys.stderr)
        report_and_exit(issues)
        sys.exit(1)
    else:
        print("All conformance checks passed.", file=sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
