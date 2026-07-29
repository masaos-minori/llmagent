#!/usr/bin/env python3
"""Add missing YAML Front Matter to docs/*.md files.

Checks each Markdown file under docs/ for a valid YAML Front Matter block
(starting with --- and ending with ---).  If missing, adds a minimal template
based on the filename prefix and existing category mappings.

Usage:
    python tools/add_missing_frontmatter.py [--dry-run] [--fix]

Options:
    --dry-run   Print what would be changed without modifying files
    --fix       Actually modify files (default: dry-run mode)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

# Category mapping from filename prefix to category value
CATEGORY_PREFIX_MAP: dict[str, str] = {
    "00_index": "overview",
    "00_governance": "governance",
    "01_spec": "overview",
    "02_ref": "overview",
    "03_rag": "rag",
    "04_mcp": "mcp",
    "05_agent": "agent",
    "06_config": "operations",
    "07_ref": "overview",
    "08_spec": "overview",
    "09_spec": "overview",
    "10_spec": "overview",
    "90_shared": "shared",
    "91_eventbus": "eventbus",
}

# Default tags derived from category
DEFAULT_TAGS: dict[str, list[str]] = {
    "agent": ["agent"],
    "deployment": ["deployment"],
    "eventbus": ["eventbus"],
    "governance": ["governance"],
    "mcp": ["mcp"],
    "operations": ["operations"],
    "overview": ["overview"],
    "rag": ["rag"],
    "shared": ["shared"],
}


# Custom titles for governance files where auto-generation is insufficient
GOVERNANCE_TITLES: dict[str, str] = {
    "00_governance_01_documentation-governance.md": "Documentation Governance",
    "00_governance_02_canonical-source-rule.md": "Canonical Source Rule",
    "00_governance_03_evidence-labels.md": "Evidence Labels",
    "00_governance_04_known-issues-template.md": "Known Issues Template",
    "00_governance_05_deprecated-items.md": "Deprecated Items",
    "00_governance_06_ai-reading-metadata.md": "AI Reading Metadata",
    "00_governance_07_needs-confirmation-inventory.md": "Needs Confirmation Inventory",
    "00_governance_08_known-issues-migration-plan.md": "Known Issues Migration Plan",
}


def extract_category_from_filename(filename: str) -> str | None:
    """Determine category from the filename prefix."""
    # Check custom governance titles first
    if filename in GOVERNANCE_TITLES:
        return "governance"

    # Remove .md extension and split on underscore
    base = filename.rsplit(".", 1)[0]
    parts = base.split("_")

    # Try longest prefix match first
    for i in range(len(parts), 0, -1):
        prefix = "_".join(parts[:i])
        if prefix in CATEGORY_PREFIX_MAP:
            return CATEGORY_PREFIX_MAP[prefix]

    # Fallback: try single number prefix
    if parts[0].isdigit():
        num = parts[0]
        if num == "00":
            return "overview"
        elif num.startswith("03"):
            return "rag"
        elif num.startswith("04"):
            return "mcp"
        elif num.startswith("05"):
            return "agent"
        elif num.startswith("90"):
            return "shared"
        elif num.startswith("91"):
            return "eventbus"

    return None


def extract_tags_from_filename(filename: str) -> list[str]:
    """Derive tags from the filename."""
    base = filename.rsplit(".", 1)[0]
    # Use the last meaningful part as primary tag
    parts = base.split("_")
    if len(parts) >= 2:
        # Take the descriptive part after the numbering prefix
        desc_parts = [p for p in parts if not p.isdigit()]
        if desc_parts:
            primary_tag = desc_parts[-1]
            return [primary_tag] + sorted(
                set(p for p in desc_parts if p != primary_tag and not p.isdigit())
            )
    return []


def build_frontmatter(
    filename: str,
    title: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Build a YAML Front Matter block."""
    if category is None:
        category = extract_category_from_filename(filename) or "overview"
    if tags is None:
        tags = DEFAULT_TAGS.get(category, [])
        # Add filename-derived tags if none from category
        if not tags:
            tags = extract_tags_from_filename(filename)
    if not tags:
        tags = [category]

    # Generate title from filename if not provided
    if not title:
        if filename in GOVERNANCE_TITLES:
            title = GOVERNANCE_TITLES[filename]
        else:
            base = filename.rsplit(".", 1)[0]
            # Convert underscores/hyphens to spaces and title-case
            title = " ".join(p.replace("-", " ") for p in base.split("_")).title()

    fm_lines = [
        "---",
        f'title: "{title}"',
        f"category: {category}",
        "tags:",
    ]
    for tag in tags:
        fm_lines.append(f"  - {tag}")

    # Add related documents based on category
    if category == "governance":
        fm_lines.append("related:")
        fm_lines.append("  - 00_index.md")
        fm_lines.append("  - 01_overview.md")
    elif category == "overview":
        fm_lines.append("related:")
        fm_lines.append("  - 00_index.md")
    else:
        fm_lines.append("related:")

    fm_lines.append("---")

    return "\n".join(fm_lines) + "\n"


def process_file(filepath: Path, dry_run: bool = True) -> tuple[list[str], bool]:
    """Process a single file. Returns (issues, was_modified)."""
    issues: list[str] = []
    modified = False

    content = filepath.read_text(encoding="utf-8")

    # Check if file starts with ---
    if not content.startswith("---"):
        # Missing front matter entirely
        filename = filepath.name
        title = ""

        # Try to extract title from first H1 heading or generate from filename
        lines = content.split("\n")
        for line in lines[:10]:
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                title = stripped.lstrip("# ").strip()
                break
        if not title:
            if filename in GOVERNANCE_TITLES:
                title = GOVERNANCE_TITLES[filename]
            else:
                base = filename.rsplit(".", 1)[0]
                desc_parts = [p for p in base.split("_") if not p.isdigit()]
                if desc_parts:
                    # Replace hyphens with spaces before title-casing
                    title = " ".join(p.replace("-", " ") for p in desc_parts).title()

        fm = build_frontmatter(filename, title=title)

        if dry_run:
            print(f"[DRY-RUN] Would add front matter to {filepath.name}:")
            print(f"  Title: {title or '(generated from filename)'}")
            print(f"  Block:\n{fm}")
        else:
            new_content = fm + content
            filepath.write_text(new_content, encoding="utf-8")
            print(f"Added front matter to {filepath.name}")
            modified = True
        return issues, modified

    # Has opening --- but check for closing ---
    end = content.find("\n---", 3)
    if end == -1:
        issues.append(f"{filepath.name}: opening '---' has no closing '---'")
        return issues, modified

    # Valid front matter exists — check required fields
    fm_content = content[3:end]
    has_title = any(
        line.strip().startswith("title:") for line in fm_content.split("\n")
    )
    has_category = any(
        line.strip().startswith("category:") for line in fm_content.split("\n")
    )
    has_tags = any(line.strip().startswith("tags:") for line in fm_content.split("\n"))
    has_related = any(
        line.strip().startswith("related:") for line in fm_content.split("\n")
    )

    missing_fields = []
    if not has_title:
        missing_fields.append("title")
    if not has_category:
        missing_fields.append("category")
    if not has_tags:
        missing_fields.append("tags")
    if not has_related:
        missing_fields.append("related")

    if missing_fields:
        issues.append(f"{filepath.name}: missing fields: {', '.join(missing_fields)}")

    return issues, modified


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add missing YAML Front Matter to docs/*.md"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without modifying files"
    )
    parser.add_argument("--fix", action="store_true", help="Actually modify files")
    args = parser.parse_args(argv)

    if not DOCS_DIR.is_dir():
        print(f"ERROR: docs directory not found: {DOCS_DIR}", file=sys.stderr)
        return 1

    total_issues = 0
    total_modified = 0

    for md_file in sorted(DOCS_DIR.glob("*.md")):
        issues, modified = process_file(md_file, dry_run=args.dry_run)
        total_issues += len(issues)
        if modified:
            total_modified += 1

    if total_issues > 0:
        print(f"\nFound {total_issues} issue(s)", file=sys.stderr)
        return 1

    if total_modified > 0:
        print(f"\nModified {total_modified} file(s)")
    else:
        print("\nAll files have valid YAML Front Matter.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
