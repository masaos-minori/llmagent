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


def check_malformed_tables(content: str, filename: str) -> list[str]:
    """Check for markdown tables with mismatched column counts."""
    issues = []
    lines = content.split("\n")
    in_table = False
    table_lines: list[str] = []
    expected_cols = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("|") and not stripped.startswith("----"):
            if not in_table:
                in_table = True
                table_lines = [stripped]
                expected_cols = len(stripped.split("|")) - 2
                continue
            table_lines.append(stripped)
            cols = len(stripped.split("|")) - 2
            if cols != expected_cols:
                issues.append(
                    f"{filename}:{i}: malformed table — expected {expected_cols} columns, got {cols}"
                )
        elif in_table and stripped == "":
            # Empty line may end a table; check if it looks like a paragraph break
            in_table = False
            table_lines = []
            expected_cols = 0
        elif (
            in_table and not stripped.startswith("|") and not stripped.startswith("---")
        ):
            in_table = False
            table_lines = []
            expected_cols = 0

    return issues


def check_unclosed_inline_code(content: str, filename: str) -> list[str]:
    """Check for unclosed inline code blocks (odd number of backticks)."""
    issues = []
    # Remove fenced code blocks first
    cleaned = re.sub(r"```[^`]*```", "", content)
    # Count inline backticks
    backtick_count = cleaned.count("`")
    if backtick_count % 2 != 0:
        # Find the unclosed one
        matches = list(re.finditer(r"`([^`]*)", cleaned))
        for m in matches:
            if not re.search(r"`" + re.escape(m.group(1)), cleaned[m.end() :]):
                issues.append(f"{filename}: unclosed inline code — '{m.group(0)}'")
    return issues


def check_json_not_wrapped(content: str, filename: str) -> list[str]:
    """Check for JSON examples not wrapped in fenced code blocks."""
    issues = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Look for JSON-like patterns that should be in fenced code blocks
        if stripped.startswith("{") or stripped.startswith("["):
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
