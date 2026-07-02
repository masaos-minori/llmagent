#!/usr/bin/env python3
"""scripts/checks/check_docs_consistency.py

Lightweight CI check for RAG documentation quality:
- Broken headings (malformed heading markers)
- Malformed markdown tables
- Unclosed inline code blocks
- JSON examples not wrapped in fenced code blocks
- Stale artifact path references (.txt → .json)
- Non-canonical command names (/db fts-rebuild → /db rebuild-fts)
- Resolved issues under active issues section
- Stale issue ID routing in document guide
- References to deleted RAG source files (03_spec_rag.md, 03_rag-ref-*, etc.)
- Duplicate heading numbers at the same level
- Migration Notes sections in active docs

Usage:
    python -m scripts.checks.check_docs_consistency [--fix]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = ROOT_DIR / "docs"

# Stale patterns that should not appear as active references in docs
STALE_PATTERNS = {
    "rag-src/*.txt": r"(?:^|[^`])rag-src/[^`]*\.txt(?:[^`]|$)",
    "rag-src/chunk/*.txt": r"(?:^|[^`])rag-src/chunk/[^`]*\.txt(?:[^`]|$)",
    "rag-src/registered/*.txt": r"(?:^|[^`])rag-src/registered/[^`]*\.txt(?:[^`]|$)",
    "stem-0000.txt": r"(?:^|[^`])\{?stem\}?.*0000\.txt(?:[^`]|$)",
    "/db fts-rebuild": r"/db\s+fts-rebuild",
    # Deleted RAG source files — should not be referenced as active guidance
    "03_spec_rag.md": r"(?:^|[^a-zA-Z])03_spec_rag\.md(?:[^a-zA-Z]|$)",
    "03_rag-ref-*": r"03_rag-ref-[^`]*\.md",
    "03_rag-ingestion-*": r"03_rag-ingestion-[^`]*\.md",
    "05_ref-rag.md": r"(?:^|[^a-zA-Z])05_ref-rag\.md(?:[^a-zA-Z]|$)",
}

# Patterns that are allowed in resolved/historical sections
HISTORICAL_MARKERS = {
    "legacy",
    "historical",
    "archive only",
    "resolved",
    "was:",
    "removed",
}


def check_broken_headings(content: str, filename: str) -> list[str]:
    """Check for malformed heading markers (e.g. # without space)."""
    issues = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            # Level-1 heading should be at start of line or after whitespace
            if re.match(r"^#+[^# ]", stripped):
                issues.append(
                    f"{filename}:{i}: broken heading — '# without space': '{stripped}'"
                )
        elif stripped.startswith("##") and not stripped.startswith("###"):
            # Level-2 heading: should have space after '##'
            if re.match(r"^##[^# ]", stripped):
                issues.append(
                    f"{filename}:{i}: broken heading — '## without space': '{stripped}'"
                )
        elif stripped.startswith("###") and not stripped.startswith("####"):
            # Level-3 heading: should have space after '###'
            if re.match(r"^###[^# ]", stripped):
                issues.append(
                    f"{filename}:{i}: broken heading — '### without space': '{stripped}'"
                )
    return issues


def _count_table_cols(row: str) -> int:
    """Count columns in a markdown table row, ignoring escaped pipes (\\|)."""
    # Replace escaped pipes with a placeholder before splitting
    normalized = row.replace(r"\|", "\x00")
    return len(normalized.split("|")) - 2


def _is_separator_row(row: str) -> bool:
    """Return True if row is a markdown table separator (|---|---|)."""
    return bool(re.match(r"^\|[-| :]+\|$", row))


def check_malformed_tables(content: str, filename: str) -> list[str]:
    """Check for markdown tables with mismatched column counts.

    Only checks rows that follow a proper markdown separator row (|---|---|) to
    avoid false positives from ASCII box-art diagrams.
    """
    issues = []
    lines = content.split("\n")
    in_fenced_block = False
    in_table = False
    header_pending = False  # True after a header row, waiting for separator
    expected_cols = 0
    pending_header_line: str = ""

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Track fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fenced_block = not in_fenced_block
            in_table = False
            header_pending = False
            continue
        if in_fenced_block:
            continue

        if stripped.startswith("|"):
            if _is_separator_row(stripped):
                if header_pending:
                    # Separator confirms this is a real markdown table
                    sep_cols = _count_table_cols(stripped)
                    header_cols = _count_table_cols(pending_header_line)
                    if sep_cols != header_cols:
                        issues.append(
                            f"{filename}:{i}: malformed table — expected {header_cols} columns, got {sep_cols}"
                        )
                    in_table = True
                    expected_cols = header_cols
                header_pending = False
                continue
            # Non-separator pipe row
            if in_table:
                cols = _count_table_cols(stripped)
                if cols != expected_cols:
                    issues.append(
                        f"{filename}:{i}: malformed table — expected {expected_cols} columns, got {cols}"
                    )
            else:
                # Could be a table header — wait for separator to confirm
                header_pending = True
                pending_header_line = stripped
        else:
            # Non-pipe line ends any table tracking
            in_table = False
            header_pending = False
            expected_cols = 0

    return issues


def check_unclosed_inline_code(content: str, filename: str) -> list[str]:
    """Check for unclosed inline code blocks (odd number of backticks per line)."""
    issues = []
    lines = content.split("\n")
    in_fenced_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Strip blockquote markers (> prefix) for analysis
        inner = re.sub(r"^(>\s*)+", "", stripped)
        # Track fenced code block boundaries (``` or ~~~ markers, with or without blockquote)
        if inner.startswith("```") or inner.startswith("~~~"):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue
        # Skip table separator rows (|---|---|)
        if re.match(r"^\|[-| ]+\|$", stripped):
            continue
        # Skip lines that contain triple-backtick mentions (e.g. documentation of syntax)
        if "```" in stripped:
            continue
        # Count backticks on this line; odd count means an unclosed inline code span
        backtick_count = inner.count("`")
        if backtick_count % 2 != 0:
            issues.append(f"{filename}:{i}: unclosed inline code — '{stripped[:80]}'")
    return issues


def check_json_not_wrapped(content: str, filename: str) -> list[str]:
    """Check for JSON examples not wrapped in fenced code blocks."""
    issues = []
    lines = content.split("\n")
    in_fenced_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Track fenced code block boundaries
        if stripped.startswith("```"):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue
        # Look for JSON object examples ({...}) that should be in fenced code blocks.
        # Only flag lines starting with '{' — lines starting with '[' are ambiguous
        # (could be markdown links, numbered lists like "[1] Stage", or diagram labels).
        if stripped.startswith("{"):
            if "```" not in stripped:
                issues.append(
                    f"{filename}:{i}: JSON example not wrapped in fenced code block — '{stripped[:80]}'"
                )
    return issues


def check_stale_patterns(content: str, filename: str) -> list[str]:
    """Check for stale artifact paths and non-canonical command names."""
    issues = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Check if this line is in a resolved/historical section
        is_historical = any(
            marker.lower() in stripped.lower() for marker in HISTORICAL_MARKERS
        )

        for pattern_name, pattern in STALE_PATTERNS.items():
            if re.search(pattern, stripped):
                if not is_historical:
                    issues.append(f"{filename}:{i}: stale reference — '{pattern_name}'")

    return issues


def check_deleted_rag_refs(content: str, filename: str) -> list[str]:
    """Check for references to deleted RAG source files in active sections."""
    issues: list[str] = []
    lines = content.split("\n")
    in_active = False

    # Only check RAG docs (03_rag_*.md files)
    if not filename.startswith("03_rag_"):
        return issues

    # Track which sections are historical/archival (not active)
    HISTORICAL_SECTIONS = {
        "legacy",
        "archive",
        "historical",
        "deleted",
        "removed",
        "migration",
    }

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Track section boundaries
        if stripped.startswith("##"):
            section_name = stripped.replace("#", "").strip().lower()
            is_historical_section = any(h in section_name for h in HISTORICAL_SECTIONS)
            in_active = not is_historical_section
            continue

        if not in_active:
            continue

        # Check for deleted RAG source file references
        if re.search(r"03_spec_rag\.md", stripped):
            issues.append(
                f"{filename}:{i}: reference to deleted RAG source — '03_spec_rag.md'"
            )
        elif re.search(r"03_rag-ref-", stripped):
            issues.append(
                f"{filename}:{i}: reference to deleted RAG source — '03_rag-ref-*'"
            )
        elif re.search(r"03_rag-ingestion-", stripped):
            issues.append(
                f"{filename}:{i}: reference to deleted RAG source — '03_rag-ingestion-*'"
            )
        elif re.search(r"05_ref-rag\.md", stripped):
            issues.append(
                f"{filename}:{i}: reference to deleted RAG source — '05_ref-rag.md'"
            )

    return issues


def check_migration_notes_in_active(content: str, filename: str) -> list[str]:
    """Check for Migration Notes sections in active RAG docs."""
    issues: list[str] = []
    lines = content.split("\n")
    in_active = False

    # Only check RAG docs (03_rag_*.md files)
    if not filename.startswith("03_rag_"):
        return issues

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Only check section headers (## or ###) for "Migration Notes"
        if stripped.startswith("##"):
            section_name = stripped.replace("#", "").strip().lower()
            # Check if this is a historical section (not active)
            is_historical_section = any(
                h in section_name for h in ["legacy", "archive", "historical"]
            )
            in_active = not is_historical_section
            # Check if this section is named "Migration Notes"
            if "migration notes" in section_name:
                if not is_historical_section:
                    issues.append(
                        f"{filename}:{i}: Migration Notes in active section — '{stripped}'"
                    )
            continue

        if not in_active:
            continue

    return issues


def check_resolved_in_active(content: str, filename: str) -> list[str]:
    """Check that no resolved issue remains under active issues section."""
    issues = []
    lines = content.split("\n")

    in_active = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("## Active Issues"):
            in_active = True
            continue
        if stripped.startswith("## ") and not stripped.startswith("## Active Issues"):
            in_active = False
            continue
        if in_active and ("[Resolved]" in stripped or "resolved" in stripped.lower()):
            issues.append(
                f"{filename}:{i}: resolved issue under active issues — '{stripped[:80]}'"
            )

    return issues


def check_stale_issue_routing(content: str, filename: str) -> list[str]:
    """Check for stale issue ID routing in document guide."""
    issues = []
    lines = content.split("\n")

    # Check AI Query Routing Table for resolved issue references
    in_routing_table = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "AI Query Routing" in stripped:
            in_routing_table = True
            continue
        if in_routing_table and stripped.startswith("---"):
            in_routing_table = False
            continue
        if in_routing_table and ("SPEC-1" in stripped or "BUG-3" in stripped):
            issues.append(f"{filename}:{i}: stale issue ID routing — '{stripped[:80]}'")

    return issues


def check_duplicate_heading_numbers(content: str, filename: str) -> list[str]:
    """Check for duplicate heading numbers at the same heading level.

    Detects headings like '## 3. Foo' and '## 3. Bar' in the same file.
    Only headings with a numeric prefix (e.g. '## 3.', '### 2.1') are checked.
    Headings inside fenced code blocks are skipped.
    """
    issues: list[str] = []
    lines = content.split("\n")
    in_fenced_block = False
    # seen: maps (heading_level, number_prefix) -> first line number seen
    seen: dict[tuple[int, str], int] = {}

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue
        # Match headings: one or more '#' followed by space and optional number prefix
        m = re.match(r"^(#{1,6})\s+(\d[\d.]*\.)\s+", stripped)
        if m:
            level = len(m.group(1))
            number = m.group(2)
            key = (level, number)
            if key in seen:
                issues.append(
                    f"{filename}:{i}: duplicate heading number — "
                    f"'{'#' * level} {number}' also at line {seen[key]}: '{stripped}'"
                )
            else:
                seen[key] = i
    return issues


def check_all(content: str, filename: str) -> list[str]:
    """Run all checks and return combined issues."""
    issues = []
    issues.extend(check_broken_headings(content, filename))
    issues.extend(check_malformed_tables(content, filename))
    issues.extend(check_unclosed_inline_code(content, filename))
    issues.extend(check_json_not_wrapped(content, filename))
    issues.extend(check_stale_patterns(content, filename))
    issues.extend(check_resolved_in_active(content, filename))
    issues.extend(check_stale_issue_routing(content, filename))
    issues.extend(check_duplicate_heading_numbers(content, filename))
    issues.extend(check_deleted_rag_refs(content, filename))
    issues.extend(check_migration_notes_in_active(content, filename))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check RAG documentation consistency")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues (where possible)"
    )
    parser.add_argument(
        "files", nargs="*", help="Files to check (default: all docs/*.md)"
    )
    args = parser.parse_args()

    if not args.files:
        files = sorted(DOCS_DIR.glob("*.md"))
    else:
        files = [Path(f) for f in args.files]

    total_issues = 0
    for filepath in files:
        content = filepath.read_text(encoding="utf-8")
        issues = check_all(content, filepath.name)
        if issues:
            total_issues += len(issues)
            print(f"\n--- {filepath.name} ---", file=sys.stderr)
            for issue in issues:
                print(issue, file=sys.stderr)

    if total_issues > 0:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
