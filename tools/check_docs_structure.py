#!/usr/bin/env python3
"""Validate docs/*.md structural conventions: size, H1 count, Front Matter,
Related Documents/Keywords sections, and internal .md link reachability.

Usage:
    uv run python tools/check_docs_structure.py [glob ...]
    uv run python tools/check_docs_structure.py docs/05_agent_*.md --area agent
    uv run python tools/check_docs_structure.py docs/*.md docs/adr/*.md --schema schemas/doc_front_matter.json
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._front_matter_schema import FrontMatterSchema, load_front_matter_schema

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
# Raised from 16384 (2026-09-03, plans/20260902-191512_plan.md): a governance
# doc consolidation was already at 16252 bytes before the dependency-graph
# redesign added ~2900 bytes of required content (four scoped relation-type
# sections), leaving no realistic headroom under the old limit. 24576 covers
# that need with margin while still catching genuinely oversized files (e.g.
# docs/00_governance_03_issue-and-uncertainty-management.md at ~46KB remains
# correctly flagged).
MAX_SIZE = 24576

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


def check_front_matter(
    path: Path, content: str, expected_area: str | None
) -> list[str]:
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
    for field in ("title", "area", "tags", "related"):
        if field not in data:
            issues.append(f"{path.name}: Front Matter missing '{field}' field")
    if expected_area and data.get("area") != expected_area:
        issues.append(
            f"{path.name}: Front Matter area is '{data.get('area')}', expected '{expected_area}'"
        )
    return issues


def check_schema_compliance(
    path: Path, content: str, schema: FrontMatterSchema
) -> list[str]:
    """Validate Front Matter against `schema` (required fields, `area`/`status`
    enums). Opt-in only — called from `validate_file()` when `--schema` was
    passed. Missing/unparsable Front Matter is already reported by
    `check_front_matter()`; this function returns early rather than
    double-reporting the same root cause.
    """
    if not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []
    issues: list[str] = []
    for field in schema.required_fields:
        if field not in data:
            issues.append(
                f"{path.name}: Front Matter missing required '{field}' field "
                f"(schema: {schema.source})"
            )
    if schema.area_enum is not None:
        area = data.get("area")
        if area is not None and area not in schema.area_enum:
            issues.append(
                f"{path.name}: Front Matter 'area' value {area!r} is not one of "
                f"the schema's allowed values {list(schema.area_enum)} "
                f"(schema: {schema.source})"
            )
    if schema.status_enum is not None:
        status = data.get("status")
        if status is not None and status not in schema.status_enum:
            issues.append(
                f"{path.name}: Front Matter 'status' value {status!r} is not one "
                f"of the schema's allowed values {list(schema.status_enum)} "
                f"(schema: {schema.source})"
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


def check_related_links(path: Path, content: str) -> list[str]:
    if not content.startswith("---"):
        return []
    end = content.find("\n---", 3)
    if end == -1:
        return []
    try:
        data = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError:
        return []  # already reported by check_front_matter(); avoid double-reporting
    issues = []
    for field in ("related", "source"):
        for entry in data.get(field) or []:
            resolved = (path.parent / entry).resolve()
            if not resolved.is_file():
                issues.append(
                    f"{path.name}: front matter references missing file '{entry}' (field: {field})"
                )
    return issues


def validate_file(
    path: Path,
    expected_area: str | None,
    schema: FrontMatterSchema | None = None,
) -> list[str]:
    content = path.read_text(encoding="utf-8")
    size = len(content.encode("utf-8"))
    body = strip_fenced_code(content)
    issues = []
    issues.extend(check_size(path, size))
    issues.extend(check_h1_count(path, body))
    issues.extend(check_front_matter(path, content, expected_area))
    if schema is not None:
        issues.extend(check_schema_compliance(path, content, schema))
    issues.extend(check_tail_sections(path, content))
    issues.extend(check_links(path, content))
    issues.extend(check_related_links(path, content))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/ structural conventions"
    )
    parser.add_argument(
        "globs",
        nargs="*",
        help="Glob patterns relative to repo root (default: docs/*.md)",
    )
    parser.add_argument("--area", default=None, help="Expected Front Matter area value")
    parser.add_argument(
        "--schema",
        nargs="?",
        const="__default__",
        default=None,
        help=(
            "Validate Front Matter against a JSON Schema file (required fields, "
            "'area'/'status' enums). Give a path, or pass the flag with no value "
            "to use the canonical schemas/doc_front_matter.json. Omit entirely to "
            "skip schema validation (default — existing behavior unchanged)."
        ),
    )
    args = parser.parse_args()

    patterns = args.globs or ["docs/*.md"]
    files: set[Path] = set()
    for pattern in patterns:
        files.update(ROOT_DIR.glob(pattern))

    schema: FrontMatterSchema | None = None
    if args.schema is not None:
        schema_path = None if args.schema == "__default__" else Path(args.schema)
        schema = load_front_matter_schema(schema_path)

    total_issues = 0
    for path in sorted(files):
        issues = validate_file(path, args.area, schema)
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
