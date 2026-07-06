#!/usr/bin/env python3
"""scripts/checks/check_mcp_docs_consistency.py

Lightweight CI check for MCP documentation quality:
- Active stdio references in HTTP-only context
- Stale 4-layer routing language
- tool_names described as a routing input (not drift validation metadata)
- References to deleted docs (04_mcp_07_mdq_rag_boundary.md)
- Absence of 04_mcp_07_tool_schema_export_policy.md from the document guide

Usage:
    python -m scripts.checks.check_mcp_docs_consistency [--fix]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = ROOT_DIR / "docs"

# Files where stdio references are legitimate active documentation
STDIO_ALLOWLIST = {
    "04_mcp_02_protocol_and_transport.md",
    "04_mcp_06_configuration_and_operations.md",
    "04_mcp_05_security_and_safety_model.md",
    "04_mcp_00_document-guide.md",
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

# Deleted doc patterns — should not appear as active references
DELETED_DOC_PATTERNS = {
    "04_mcp_07_mdq_rag_boundary.md": r"(?:^|[^`])04_mcp_07_mdq_rag_boundary\.md(?:[^`]|$)",
}

# Patterns that indicate stale 4-layer routing language (outside known-issues docs)
STALE_ROUTING_PATTERNS = {
    "Priority 3.*routing": r"Priority\s+3.*routing",
    "Priority 4.*routing": r"Priority\s+4.*routing",
}

# tool_names as routing input — must not flag "tool_names is NOT a routing input"
# Only flag when tool_names is described as a routing input (not just mentioned alongside routing)
TOOL_NAMES_ROUTING_PATTERN = r"(?:tool_names.*(routing\s+input|routing\s+drives?|routing\s+determines?)|(?:(?:routing\s+drives?|routing\s+determines?).*tool_names))"

# 04_mcp_07_tool_schema_export_policy.md should appear in the document guide
DOCUMENT_GUIDE_FILE = "04_mcp_00_document-guide.md"


def _is_historical_section(content: str, line_idx: int) -> bool:
    """Return True if the given line is inside a historical/resolved section."""
    # Look backwards up to 10 lines for a section marker
    start = max(0, line_idx - 10)
    for i in range(start, line_idx):
        stripped = content.split("\n")[i].strip().lower()
        if any(marker in stripped for marker in HISTORICAL_MARKERS):
            return True
    return False


def check_active_stdio_refs(content: str, filename: str) -> list[str]:
    """Flag stdio references in files outside the allowlist."""
    issues: list[str] = []
    if filename in STDIO_ALLOWLIST:
        return issues

    patterns = [
        ("stdio", r"(?:^|[^a-zA-Z])stdio(?:[^a-zA-Z]|$)"),
        ("StdioTransport", r"StdioTransport"),
        ("--stdio", r"--stdio"),
        ("ping_tool", r"ping_tool"),
        ("ondemand", r"ondemand"),
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip fenced code blocks and comments
        if stripped.startswith("```") or stripped.startswith("~~~"):
            continue
        if stripped.startswith("#"):
            continue

        for pattern_name, pattern in patterns:
            if re.search(pattern, stripped):
                issues.append(
                    f"{filename}:{i}: active stdio reference — '{pattern_name}': '{stripped}'"
                )
    return issues


def check_stale_4layer_routing(content: str, filename: str) -> list[str]:
    """Flag Priority 3/4 routing language outside known-issues docs."""
    issues: list[str] = []
    # Allowlist known-issues doc and document guide
    if "04_mcp_90_" in filename or "04_mcp_00_" in filename:
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            continue
        for pattern_name, pattern in STALE_ROUTING_PATTERNS.items():
            if re.search(pattern, stripped):
                issues.append(
                    f"{filename}:{i}: stale 4-layer routing — '{pattern_name}': '{stripped}'"
                )
    return issues


def check_tool_names_as_routing_input(content: str, filename: str) -> list[str]:
    """Flag tool_names described as a routing input (not drift validation)."""
    issues: list[str] = []
    # Allowlist known-issues doc and document guide — they describe the change
    if "04_mcp_90_" in filename or "04_mcp_00_" in filename:
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            continue
        # Skip lines that say "routing does not require it" or "not routing input(s)" — these are correct
        if (
            "routing does not require" in stripped.lower()
            or "not a routing input" in stripped.lower()
            or "not routing inputs" in stripped.lower()
        ):
            continue
        if re.search(TOOL_NAMES_ROUTING_PATTERN, stripped):
            issues.append(
                f"{filename}:{i}: tool_names as routing input (should be drift validation): '{stripped}'"
            )
    return issues


def check_deleted_doc_refs(content: str, filename: str) -> list[str]:
    """Flag active-section references to deleted docs."""
    issues: list[str] = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip historical sections and fenced code blocks
        if _is_historical_section(content, i - 1):
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            continue
        # Skip strikethrough rows (historical)
        if "~~" in stripped:
            continue

        for pattern_name, pattern in DELETED_DOC_PATTERNS.items():
            if re.search(pattern, stripped):
                issues.append(
                    f"{filename}:{i}: reference to deleted doc — '{pattern_name}': '{stripped}'"
                )
    return issues


def check_guide_lists_07(content: str, filename: str) -> list[str]:
    """Check that 04_mcp_07_tool_schema_export_policy.md is listed in the document guide."""
    issues: list[str] = []
    if filename != DOCUMENT_GUIDE_FILE:
        return issues

    lines = content.split("\n")
    found = False
    for line in lines:
        stripped = line.strip()
        # Skip strikethrough rows (historical)
        if stripped.startswith("~~"):
            continue
        if "04_mcp_07_tool_schema_export_policy.md" in stripped:
            found = True
            break

    if not found:
        issues.append(
            f"{filename}: 04_mcp_07_tool_schema_export_policy.md not listed in document guide"
        )
    return issues


def check_all(content: str, filename: str) -> list[str]:
    """Run all checks and return combined issues."""
    issues = []
    issues.extend(check_active_stdio_refs(content, filename))
    issues.extend(check_stale_4layer_routing(content, filename))
    issues.extend(check_tool_names_as_routing_input(content, filename))
    issues.extend(check_deleted_doc_refs(content, filename))
    issues.extend(check_guide_lists_07(content, filename))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MCP documentation consistency")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues (where possible)"
    )
    parser.add_argument(
        "files", nargs="*", help="Files to check (default: all docs/04_mcp_*.md)"
    )
    args = parser.parse_args()

    if not args.files:
        files = sorted(DOCS_DIR.glob("04_mcp_*.md"))
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
