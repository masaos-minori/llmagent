#!/usr/bin/env python3
"""merge_part_files.py — Merge *_part*.md pairs into single files."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def find_groups(docs_dir: Path) -> dict[str, list[tuple[int, str]]]:
    """Group partN files by their common base name. Returns sorted (part_num, filename) tuples."""
    groups: dict[str, list[tuple[int, str]]] = {}
    import re as _re

    pattern = _re.compile(r"^(.+)-part(\d+)\.md$")
    for fname in sorted(docs_dir.glob("*-part*.md")):
        match = pattern.match(fname.name)
        if match:
            base = match.group(1)
            part_num = int(match.group(2))
            groups.setdefault(base, []).append((part_num, fname.name))
    # Sort each group by part number
    for base in groups:
        groups[base].sort(key=lambda x: x[0])
    return groups


def strip_frontmatter(content: str) -> tuple[str, str]:
    """Remove YAML front matter from content, return (fm, body)."""
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            return content[3:end], content[end + 4 :]
    return "", content


def merge_content(part1_path: Path, part2_path: Path) -> str:
    """Merge two part files into one document."""
    p1_content = part1_path.read_text(encoding="utf-8")
    p2_content = part2_path.read_text(encoding="utf-8")

    # Strip front matter from both parts
    p1_fm, p1_body = strip_frontmatter(p1_content)
    p2_fm, p2_body = strip_frontmatter(p2_content)

    # Use part1's front matter as the merged document's front matter
    fm = p1_fm

    # Check if part2 starts with a heading — if so, add blank line separator
    p2_stripped = p2_body.lstrip()
    needs_separator = bool(re.match(r"^#{1,6}\s+", p2_stripped))

    if needs_separator:
        body = p1_body.rstrip() + "\n\n" + p2_body.lstrip()
    else:
        body = p1_body.rstrip() + "\n" + p2_body.lstrip()

    result_parts = []
    if fm:
        result_parts.append(fm)
    result_parts.append(body)
    return "\n".join(result_parts) + "\n"


def update_internal_refs(merged_content: str, base_name: str, docs_dir: Path) -> str:
    """Update internal links that pointed to the old part files."""
    # Find all internal .md links in the merged content
    pattern = r"\]\(([^)]+)\)"

    def replace_link(m: re.Match) -> str:
        link = m.group(1)
        # Only handle internal .md links (not URLs)
        if not link.endswith(".md"):
            return m.group(0)

        # Check if this is a reference to one of our part files
        for suffix in ["-part1.md", "-part2.md"]:
            target = link.replace(suffix, ".md")
            if target == base_name + ".md":
                return f"]({target})"
        return m.group(0)

    return re.sub(pattern, replace_link, merged_content)


def merge_all_parts(parts: list[tuple[int, str]], docs_dir: Path) -> tuple[str, bool]:
    """Merge multiple part files into one document. Returns (content, has_frontmatter)."""
    contents = []
    fm = ""

    for _, fname in parts:
        path = docs_dir / fname
        content = path.read_text(encoding="utf-8")

        # Strip front matter from each part
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                if not fm:  # Use first part's front matter
                    fm = content[3:end]
                content = content[end + 4 :]

        p_stripped = content.lstrip()
        needs_separator = bool(re.match(r"^#{1,6}\s+", p_stripped))

        if needs_separator:
            contents.append(content.rstrip() + "\n\n" + content.lstrip())
        else:
            contents.append(content.rstrip() + "\n" + content.lstrip())

    result_parts = []
    if fm:
        result_parts.append(fm)
    result_parts.append("\n".join(contents))
    return "\n".join(result_parts) + "\n", bool(fm)


def update_internal_refs_for_multi(
    merged_content: str, base_name: str, docs_dir: Path, parts: list[tuple[int, str]]
) -> str:
    """Update internal links that pointed to the old part files."""
    pattern = r"\]\(([^)]+)\)"

    def replace_link(m: re.Match) -> str:
        link = m.group(1)
        if not link.endswith(".md"):
            return m.group(0)

        # Check if this is a reference to one of our part files
        for _, old_fname in parts:
            target = link.replace(old_fname, f"{base_name}.md")
            if target != link:
                return f"]({target})"
        return m.group(0)

    return re.sub(pattern, replace_link, merged_content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge *_part*.md files into single files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args(argv)

    if not DOCS.is_dir():
        print(f"ERROR: docs directory not found: {DOCS}", file=sys.stderr)
        return 1

    groups = find_groups(DOCS)
    if not groups:
        print("No *_part*.md files found.")
        return 0

    print(f"Found {len(groups)} groups to merge:")
    for base, parts in sorted(groups.items()):
        sizes = [os.path.getsize(DOCS / fn) for _, fn in parts]
        print(
            f"  {base}: {' + '.join(fn for _, fn in parts)} ({' + '.join(f'{s:,}' for s in sizes)} bytes)"
        )

    if args.dry_run:
        print("\n[Dry run mode — no changes made]")
        return 0

    # Phase 1: Merge groups with internal cross-references first
    internal_ref_bases = [
        "03_rag_03_02_query_pipeline-rag-pipeline-class",
        "03_rag_91_design_notes",
        "05_agent_10_04_operations-and-observability-validation-and-troubleshooting",
    ]

    # First pass: merge internal-ref groups and update their references
    for base in internal_ref_bases:
        if base not in groups:
            continue
        parts = groups[base]

        merged_path = DOCS / f"{base}.md"

        print(f"\nMerging {' + '.join(fn for _, fn in parts)} → {base}.md")
        merged_content, has_fm = merge_all_parts(parts, DOCS)
        merged_content = update_internal_refs_for_multi(
            merged_content, base, DOCS, parts
        )
        merged_path.write_text(merged_content, encoding="utf-8")

        # Update remaining part files to point to merged file
        for _, old_fname in parts[:-1]:  # Skip last part (will be deleted)
            part_path = DOCS / old_fname
            part_content = part_path.read_text(encoding="utf-8")
            part_content = part_content.replace(f"[{old_fname}]", f"[{base}.md]")
            part_content = part_content.replace(f"]({old_fname})", f"]({base}.md)")
            part_path.write_text(part_content, encoding="utf-8")

        # Delete all old files
        for _, old_fname in parts:
            (DOCS / old_fname).unlink()
            print(f"  Deleted: {old_fname}")

    # Second pass: merge remaining groups
    for base, parts in sorted(groups.items()):
        if base in internal_ref_bases:
            continue

        merged_path = DOCS / f"{base}.md"

        print(f"\nMerging {' + '.join(fn for _, fn in parts)} → {base}.md")
        merged_content, has_fm = merge_all_parts(parts, DOCS)
        merged_path.write_text(merged_content, encoding="utf-8")

        # Delete all old files
        for _, old_fname in parts:
            (DOCS / old_fname).unlink()
            print(f"  Deleted: {old_fname}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
