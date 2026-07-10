#!/usr/bin/env python3
"""Validate docs/*.md structural conventions: size, H1 count, Front Matter,
Related Documents/Keywords sections, and internal .md link reachability.

Usage:
    uv run python tools/validate_docs_structure.py [glob ...]
    uv run python tools/validate_docs_structure.py docs/05_agent_*.md --category agent
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
MAX_SIZE = 8192

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]*)?\)")


def strip_fenced_code(content: str) -> str:
    lines = content.split("\n")
    kept = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return "\n".join(kept)


def check_size(path: Path, size: int) -> list[str]:
    if size > MAX_SIZE:
        return [f"{path.name}: size {size} bytes exceeds {MAX_SIZE} byte limit"]
    return []


def check_h1_count(path: Path, body: str) -> list[str]:
    count = len(re.findall(r"^# ", body, re.MULTILINE))
    if count != 1:
        return [f"{path.name}: found {count} H1 heading(s), expected exactly 1"]
    return []


def check_front_matter(path: Path, content: str, expected_category: str | None) -> list[str]:
    issues = []
    if not content.startswith("---"):
        return [f"{path.name}: missing Front Matter (does not start with '---')"]
    end = content.find("\n---", 3)
    if end == -1:
        return [f"{path.name}: Front Matter opening '---' has no closing '---'"]
    raw = content[3:end]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return [f"{path.name}: Front Matter is not valid YAML — {exc}"]
    for field in ("title", "category", "tags", "related"):
        if field not in data:
            issues.append(f"{path.name}: Front Matter missing '{field}' field")
    if expected_category and data.get("category") != expected_category:
        issues.append(
            f"{path.name}: Front Matter category is '{data.get('category')}', expected '{expected_category}'"
        )
    return issues


def check_tail_sections(path: Path, content: str) -> list[str]:
    issues = []
    if not re.search(r"^## Related Documents", content, re.MULTILINE):
        issues.append(f"{path.name}: missing '## Related Documents' section")
    if not re.search(r"^## Keywords", content, re.MULTILINE):
        issues.append(f"{path.name}: missing '## Keywords' section")
    return issues


def check_links(path: Path, content: str) -> list[str]:
    issues = []
    body = strip_fenced_code(content)
    for _text, target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.is_file():
            issues.append(f"{path.name}: broken link -> '{target}'")
    return issues


def validate_file(path: Path, expected_category: str | None) -> list[str]:
    content = path.read_text(encoding="utf-8")
    size = len(content.encode("utf-8"))
    body = strip_fenced_code(content)
    issues = []
    issues.extend(check_size(path, size))
    issues.extend(check_h1_count(path, body))
    issues.extend(check_front_matter(path, content, expected_category))
    issues.extend(check_tail_sections(path, content))
    issues.extend(check_links(path, content))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate docs/ structural conventions")
    parser.add_argument("globs", nargs="*", help="Glob patterns relative to repo root (default: docs/*.md)")
    parser.add_argument("--category", default=None, help="Expected Front Matter category value")
    args = parser.parse_args()

    patterns = args.globs or ["docs/*.md"]
    files: set[Path] = set()
    for pattern in patterns:
        files.update(ROOT_DIR.glob(pattern))

    total_issues = 0
    for path in sorted(files):
        issues = validate_file(path, args.category)
        if issues:
            total_issues += len(issues)
            for issue in issues:
                print(issue)

    if total_issues:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
