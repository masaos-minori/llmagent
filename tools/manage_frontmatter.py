#!/usr/bin/env python3
"""manage_frontmatter.py — Unified YAML Front Matter manager for docs/*.md.

Consolidated from:
  - tools/add_missing_frontmatter.py
  - tools/dedupe_front_matter_lists.py

Subcommands:
  add-missing           Add missing YAML Front Matter to docs/*.md files
  dedupe-lists          Remove duplicate entries from list fields (tags/related/source)
  rename-category-to-area
                        Rename a `category:` key to `area:` in files that already
                        have valid, `---`-fenced Front Matter (value unchanged)

Usage:
    python tools/manage_frontmatter.py add-missing [--dry-run]   # report-only (safe default)
    python tools/manage_frontmatter.py add-missing --fix         # perform actual writes
    python tools/manage_frontmatter.py dedupe-lists
    python tools/manage_frontmatter.py rename-category-to-area [--dry-run]
    python tools/manage_frontmatter.py rename-category-to-area --fix

`add-missing`'s area inference never guesses when a file's Front Matter area
cannot be confidently determined from its filename — such files are reported
as ambiguous (both in `--dry-run` and `--fix` mode) and left untouched,
rather than silently defaulting to a possibly-wrong area.
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._front_matter_schema import load_front_matter_schema

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"

LIST_FIELDS = ("tags", "related", "source")

# Sentinel returned by extract_area_from_filename() when no prefix/digit rule
# confidently determines the area — callers must treat this as "ambiguous,
# do not guess" (see AmbiguousAreaError), never fall back to a default area.
AMBIGUOUS = None

AREA_PREFIX_MAP: dict[str, str] = {
    "00_index": "overview",
    "00_governance": "governance",
    "01_spec": "overview",
    "02_ref": "overview",
    "03_rag": "rag",
    "04_mcp": "mcp",
    "05_agent": "agent",
    "06_eventbus": "eventbus",
    "07_ref": "overview",
    "08_spec": "overview",
    "09_spec": "overview",
    "10_spec": "overview",
    "90_shared": "shared",
}

DEFAULT_AREAS: dict[str, list[str]] = {
    "agent": ["agent"],
    "deployment": ["deployment"],
    "eventbus": ["eventbus"],
    "governance": ["governance"],
    "mcp": ["mcp"],
    "overview": ["overview"],
    "rag": ["rag"],
    "shared": ["shared"],
}

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

# ---------------------------------------------------------------------------
# Subcommand: add-missing
# ---------------------------------------------------------------------------


def extract_area_from_filename(filename: str) -> str | None:
    """Infer the Front Matter `area` from a filename's prefix.

    Returns `None` (the `AMBIGUOUS` sentinel) when no prefix or digit rule
    confidently determines the area — callers MUST treat `None` as "cannot
    infer, do not guess" and report it, never substitute a default area.
    """
    if filename in GOVERNANCE_TITLES:
        return "governance"
    base = filename.rsplit(".", 1)[0]
    parts = base.split("_")
    for i in range(len(parts), 0, -1):
        prefix = "_".join(parts[:i])
        if prefix in AREA_PREFIX_MAP:
            return AREA_PREFIX_MAP[prefix]
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
    return AMBIGUOUS


def extract_tags_from_filename(filename: str) -> list[str]:
    base = filename.rsplit(".", 1)[0]
    parts = base.split("_")
    if len(parts) >= 2:
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
    area: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """Build a Front Matter block. `area` must already be resolved by the
    caller (e.g. via `extract_area_from_filename()`) — this function does not
    guess a default when area inference was ambiguous; callers must check
    for `AMBIGUOUS`/`None` before calling this function."""
    if area is None:
        raise ValueError(
            f"build_frontmatter({filename!r}) called with area=None — "
            "resolve or report the ambiguous area before building a block"
        )
    if tags is None:
        tags = DEFAULT_AREAS.get(area, [])
        if not tags:
            tags = extract_tags_from_filename(filename)
    if not tags:
        tags = [area]
    if not title:
        if filename in GOVERNANCE_TITLES:
            title = GOVERNANCE_TITLES[filename]
        else:
            base = filename.rsplit(".", 1)[0]
            title = " ".join(p.replace("-", " ") for p in base.split("_")).title()

    fm_lines = [
        "---",
        f'title: "{title}"',
        f"area: {area}",
        "tags:",
    ]
    for tag in tags:
        fm_lines.append(f"  - {tag}")
    if area == "governance":
        fm_lines.append("related:")
        fm_lines.append("  - 00_index.md")
        fm_lines.append("  - 01_overview.md")
    elif area == "overview":
        fm_lines.append("related:")
        fm_lines.append("  - 00_index.md")
    else:
        fm_lines.append("related:")
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n"


def cmd_add_missing(argv: list[str] | argparse.Namespace | None = None) -> int:
    if isinstance(argv, argparse.Namespace):
        args = argv
    else:
        parser = argparse.ArgumentParser(
            description="Add missing YAML Front Matter to docs/*.md"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes without modifying files",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Actually modify files (default: dry-run)",
        )
        args = parser.parse_args(argv)

    if not DOCS_DIR.is_dir():
        print(f"ERROR: docs directory not found: {DOCS_DIR}", file=sys.stderr)
        return 1

    schema = load_front_matter_schema()
    required_fields = schema.required_fields

    total_issues = 0
    total_modified = 0
    total_ambiguous = 0

    for md_file in sorted(DOCS_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        issues: list[str] = []
        modified = False

        if not content.startswith("---"):
            filename = md_file.name
            area = extract_area_from_filename(filename)
            if area is AMBIGUOUS:
                total_ambiguous += 1
                print(
                    f"[AMBIGUOUS] {filename}: cannot confidently infer 'area' from "
                    f"filename — not written, needs manual front matter (both "
                    f"--dry-run and --fix leave this file untouched)"
                )
                continue
            title = ""
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
                        title = " ".join(
                            p.replace("-", " ") for p in desc_parts
                        ).title()
            fm = build_frontmatter(filename, title=title, area=area)
            if args.fix:
                new_content = fm + content
                md_file.write_text(new_content, encoding="utf-8")
                print(f"Added front matter to {md_file.name}")
                modified = True
            else:
                print(f"[DRY-RUN] Would add front matter to {md_file.name}:")
                print(f"  Title: {title or '(generated from filename)'}")
                print(f"  Block:\n{fm}")
            continue

        end = content.find("\n---", 3)
        if end == -1:
            issues.append(f"{md_file.name}: opening '---' has no closing '---'")
            continue

        fm_content = content[3:end]
        missing_fields = [
            field
            for field in required_fields
            if not any(
                line.strip().startswith(f"{field}:") for line in fm_content.split("\n")
            )
        ]
        if missing_fields:
            issues.append(
                f"{md_file.name}: missing fields: {', '.join(missing_fields)}"
            )

        total_issues += len(issues)
        if modified:
            total_modified += 1

    if total_ambiguous > 0:
        print(
            f"\n{total_ambiguous} file(s) have an ambiguous 'area' — left "
            f"untouched, add Front Matter to them manually",
            file=sys.stderr,
        )
    if total_issues > 0:
        print(f"\nFound {total_issues} issue(s)", file=sys.stderr)
    if total_issues > 0 or total_ambiguous > 0:
        return 1
    if total_modified > 0:
        print(f"\nModified {total_modified} file(s)")
    else:
        print("\nAll files have valid YAML Front Matter.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: rename-category-to-area
# ---------------------------------------------------------------------------

_CATEGORY_LINE_RE = re.compile(r"^category:\s*")
_AREA_LINE_RE = re.compile(r"^area:\s*")


def cmd_rename_category_to_area(
    argv: list[str] | argparse.Namespace | None = None,
) -> int:
    """Rename a `category:` key to `area:` in files with valid, `---`-fenced
    Front Matter — key only, value untouched. A file with no opening `---`
    is `add-missing`'s responsibility (it needs a full block built, not a
    key rename within an existing one) and is left alone here. A file that
    already has both `category:` and `area:` is ambiguous (which one is
    authoritative?) and is reported, not auto-resolved.
    """
    if isinstance(argv, argparse.Namespace):
        args = argv
    else:
        parser = argparse.ArgumentParser(
            description="Rename 'category:' to 'area:' in docs/*.md Front Matter"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes without modifying files",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Actually modify files (default: dry-run)",
        )
        args = parser.parse_args(argv)

    if not DOCS_DIR.is_dir():
        print(f"ERROR: docs directory not found: {DOCS_DIR}", file=sys.stderr)
        return 1

    total_renamed = 0
    total_skipped = 0

    for md_file in sorted(DOCS_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue  # no valid front matter block to rename a key within
        end = content.find("\n---", 3)
        if end == -1:
            continue  # unterminated front matter — add-missing/other checks report this

        fm_lines = content[3:end].split("\n")
        has_category = any(_CATEGORY_LINE_RE.match(line) for line in fm_lines)
        has_area = any(_AREA_LINE_RE.match(line) for line in fm_lines)
        if not has_category:
            continue
        if has_area:
            total_skipped += 1
            print(
                f"[AMBIGUOUS] {md_file.name}: has both 'category:' and 'area:' — "
                f"not renamed automatically, resolve manually which is authoritative"
            )
            continue

        new_fm_lines = [
            _CATEGORY_LINE_RE.sub("area: ", line)
            if _CATEGORY_LINE_RE.match(line)
            else line
            for line in fm_lines
        ]
        new_content = content[:3] + "\n".join(new_fm_lines) + content[end:]

        if args.fix:
            md_file.write_text(new_content, encoding="utf-8")
            print(f"Renamed 'category:' to 'area:' in {md_file.name}")
        else:
            print(
                f"[DRY-RUN] Would rename 'category:' to 'area:' in {md_file.name} "
                f"(value unchanged)"
            )
        total_renamed += 1

    if total_skipped > 0:
        print(f"\n{total_skipped} file(s) skipped as ambiguous", file=sys.stderr)
        return 1
    if total_renamed > 0:
        verb = "Renamed" if args.fix else "Would rename"
        print(f"\n{verb} 'category:' to 'area:' in {total_renamed} file(s)")
    else:
        print("\nNo 'category:' keys found.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: dedupe-lists
# ---------------------------------------------------------------------------


def dedupe_front_matter(content: str) -> tuple[str, bool]:
    if not content.startswith("---"):
        return content, False
    end = content.find("\n---", 3)
    if end == -1:
        return content, False
    fm_lines = content[3:end].split("\n")
    changed = False
    out_lines: list[str] = []
    current_field = None
    seen: set[str] = set()
    for line in fm_lines:
        field_match = re.match(r"^(\w+):\s*$", line)
        item_match = re.match(r"^(\s+)-\s+(.+)$", line)
        if field_match:
            current_field = field_match.group(1)
            seen = set()
            out_lines.append(line)
            continue
        if item_match and current_field in LIST_FIELDS:
            value = item_match.group(2).strip()
            if value in seen:
                changed = True
                continue
            seen.add(value)
            out_lines.append(line)
            continue
        current_field = None
        out_lines.append(line)
    new_fm = "\n".join(out_lines)
    return content[:3] + new_fm + content[end:], changed


def cmd_dedupe_lists() -> None:
    changed_files = 0
    for fp in sorted(glob.glob(str(DOCS_DIR / "*.md"))):
        path = Path(fp)
        content = path.read_text(encoding="utf-8")
        new_content, changed = dedupe_front_matter(content)
        if changed:
            path.write_text(new_content, encoding="utf-8")
            changed_files += 1
            print(f"deduped {path.name}")
    print(f"total files changed: {changed_files}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage YAML Front Matter in docs/*.md",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # add-missing
    add_parser = subparsers.add_parser(
        "add-missing", help="Add missing YAML Front Matter"
    )
    add_parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without modifying files"
    )
    add_parser.add_argument("--fix", action="store_true", help="Actually modify files")

    # dedupe-lists
    subparsers.add_parser(
        "dedupe-lists", help="Remove duplicate entries from list fields"
    )

    # rename-category-to-area
    rename_parser = subparsers.add_parser(
        "rename-category-to-area",
        help="Rename 'category:' to 'area:' (value unchanged)",
    )
    rename_parser.add_argument(
        "--dry-run", action="store_true", help="Print changes without modifying files"
    )
    rename_parser.add_argument(
        "--fix", action="store_true", help="Actually modify files"
    )

    args = parser.parse_args(argv)

    # Pass the parsed Namespace straight through — both cmd_* functions
    # accept a Namespace directly (see TestNamespaceHandoff). Reconstructing
    # `--flag` strings from `vars(args)` here previously produced
    # `--dry_run` (argparse's underscored attribute name) instead of
    # `--dry-run`, so `add-missing --dry-run` invoked via this CLI entry
    # point raised "unrecognized arguments: --dry_run" — a confirmed,
    # pre-existing bug fixed as part of this change, not merely inherited.
    if args.subcommand == "add-missing":
        return cmd_add_missing(args)
    elif args.subcommand == "dedupe-lists":
        cmd_dedupe_lists()
        return 0
    elif args.subcommand == "rename-category-to-area":
        return cmd_rename_category_to_area(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
