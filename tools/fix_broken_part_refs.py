#!/usr/bin/env python3
"""Fix broken cross-references to deleted *-part*.md files."""

import argparse
import re
from pathlib import Path

DOCS = Path(__file__).parent.parent / "docs"


def fix_file(filepath: Path) -> int:
    """Fix one file. Returns number of replacements made."""
    content = filepath.read_text(encoding="utf-8")

    # Pattern 1: Markdown links [text](old-part-file.md)
    def replace_link(m: re.Match) -> str:
        text = m.group(1)
        old_file = m.group(2)
        new_file = old_file.rsplit("-part", 1)[0] + ".md"
        return f"[{text}]({new_file})"

    content = re.sub(r"\[([^\]]+)\]\(([^)]+?)-part\d+\.md\)", replace_link, content)

    # Pattern 1b: Markdown links [text](old-part-file.md#anchor)
    def replace_link_anchor_url(m: re.Match) -> str:
        text = m.group(1)
        old_file = m.group(2)
        anchor = m.group(3)
        new_file = old_file.rsplit("-part", 1)[0] + ".md"
        return f"[{text}]({new_file}{anchor})"

    content = re.sub(
        r"\[([^\]]+)\]\(([^)]+?)-part\d+\.md(#.*?)\)", replace_link_anchor_url, content
    )

    # Pattern 2: Backtick references `old-part-file.md`
    def replace_backtick(m: re.Match) -> str:
        old_file = m.group(1)
        new_file = old_file.rsplit("-part", 1)[0] + ".md"
        return f"`{new_file}`"

    content = re.sub(r"`([^`]+?)-part\d+\.md`", replace_backtick, content)

    # Pattern 3: Plain text references without backticks but with .md extension
    # e.g., "see docs/03_rag_01_system_overview-part1.md"
    def replace_plain(m: re.Match) -> str:
        prefix = m.group(1) or ""
        old_file = m.group(2)
        new_file = old_file.rsplit("-part", 1)[0] + ".md"
        return f"{prefix}{new_file}"

    content = re.sub(r"(^|\s)([^`[]\S*?)-part(\d+)\.md\b", replace_plain, content)

    # Pattern 4: Markdown link text contains -partN.md (URL may be correct already)
    # e.g., "[05_agent_02_runtime-architecture-part1.md](05_agent_02_runtime-architecture.md)"
    def replace_link_text(m: re.Match) -> str:
        text = m.group(1)
        url = m.group(2)
        new_text = text.rsplit("-part", 1)[0] + ".md"
        return f"[{new_text}]({url})"

    content = re.sub(
        r"\[([^\]]+?)-part\d+\.md\]\(([^)]+)\)", replace_link_text, content
    )

    # Pattern 5: Markdown link text contains -partN.md followed by section name (e.g., "§AgentREPL")
    # e.g., "[05_agent_02_runtime-architecture-part1.md §AgentREPL](05_agent_02_runtime-architecture.md)"
    def replace_link_section(m: re.Match) -> str:
        filename = m.group(1)
        section = m.group(2)
        url = m.group(3)
        new_filename = filename.rsplit("-part", 1)[0] + ".md"
        return f"[{new_filename}{section}]({url})"

    content = re.sub(
        r"\[([^\]]+?)-part\d+\.md\s+(§[^\]]*)\]\(([^)]+)\)",
        replace_link_section,
        content,
    )

    # Pattern 6: Markdown link text contains -partN.md#anchor
    # e.g., "[05_agent_03_03_turn-processing-flow-workflow-engine-part1.md#anchor](target.md#anchor)"
    def replace_link_anchor(m: re.Match) -> str:
        filename = m.group(1)
        anchor = m.group(2)
        url = m.group(3)
        new_filename = filename.rsplit("-part", 1)[0] + ".md"
        return f"[{new_filename}{anchor}]({url})"

    content = re.sub(
        r"\[([^\]]+?)-part\d+\.md(#.*?)\]\(([^)]+)\)", replace_link_anchor, content
    )

    # Pattern 7: Plain text with -partN.md#anchor (no markdown link)
    # e.g., "05_agent_03_03_turn-processing-flow-workflow-engine-part1.md#anchor"
    def replace_plain_anchor(m: re.Match) -> str:
        prefix = m.group(1) or ""
        filename = m.group(2)
        anchor = m.group(3)
        new_filename = filename.rsplit("-part", 1)[0] + ".md"
        return f"{prefix}{new_filename}{anchor}"

    content = re.sub(
        r"(^|\s)([^`[]\S*?)-part(\d+)\.md(#.*?)$", replace_plain_anchor, content
    )

    changed = content != filepath.read_text(encoding="utf-8")
    if changed:
        filepath.write_text(content, encoding="utf-8")
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fix broken *-part*.md references")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )
    args = parser.parse_args(argv)

    if not DOCS.is_dir():
        print(f"ERROR: docs directory not found: {DOCS}", file=__import__("sys").stderr)
        return 1

    total_files = 0
    total_changes = 0

    for md_file in sorted(DOCS.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        has_part_ref = bool(re.search(r"-part\d+\.md", content))
        if not has_part_ref:
            continue

        total_files += 1
        if args.dry_run:
            matches = re.findall(r".*-part\d+\.md", content)
            unique = set(matches)
            print(f"\n{md_file.name} ({len(unique)} unique references):")
            for ref in sorted(unique)[:10]:
                print(f"  {ref}")
            if len(unique) > 10:
                print(f"  ... and {len(unique) - 10} more")
        else:
            changes = fix_file(md_file)
            if changes:
                total_changes += 1
                print(f"Fixed {md_file.name}")

    print(f"\nTotal: {total_files} files scanned, {total_changes} modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
