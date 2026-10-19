#!/usr/bin/env python3
"""check_metadata_field_policy.py — GV-016 metadata/status field policy checker.

Scans `docs/*.md` front matter and workitem files (`issues/`, `plans/`,
`implementations/`) for metadata/status fields outside the sanctioned field set,
then flags them at `Warning`. This closes the documented `Partial` gap for
`governance_04_documentation-checks.md`'s GV-016 ("No unnecessary Metadata or
Status fields added").

Two scanners share one reporting path:

1. Front-matter scanner — every `docs/*.md` YAML front-matter key compared against
   the permitted set derived from `schemas/doc_front_matter.json`'s `properties`.
2. Workitem-section scanner — every workitem's top-level `## ` sections compared
   against its domain template's canonical section set (unioned with embedded
   sub-template sections).

Findings are `Warning`s: the default run is report-only
(`report_and_exit()` returns 0 for warning-only output), and `--strict` exits 1
on any warning.

Permitted sets are DERIVED from authoritative sources, never hardcoded
(REQ-001 / REQ-002):

* Front matter: `schemas/doc_front_matter.json` `properties` keys.
  `additionalProperties: true` is intentionally ignored — GV-016 treats a field
  outside the defined properties as "unnecessary".
* Workitems: each template's canonical `## ` sections, minus meta/instructional
  sections, unioned with the sections contributed by embedded sub-templates.

Section-name comparison is case-insensitive: the canonical templates spell a
section e.g. "Out of Scope" while current generated files use "Out of scope";
GV-016 targets out-of-set fields, not casing, so comparison normalizes case.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from tools._docs_consistency_lib import Issue, report_and_exit
from tools._front_matter_schema import load_front_matter_schema

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "schemas" / "doc_front_matter.json"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Directory -> main template basename for each workitem domain.
_DOMAIN_TEMPLATES: dict[str, str] = {
    "issues": "issue.md",
    "plans": "plan.md",
    "implementations": "implementation-procedure.md",
}

# Embedded sub-templates whose sections are unioned into every domain's
# permitted set. They are shared across the workitem templates (traceability /
# execution-status families) or are issue-domain follow-up shapes
# (risks-issue / unknowns-issue).
_SUB_TEMPLATE_NAMES: tuple[str, ...] = (
    "requirement-traceability.md",
    "traceability.md",
    "risks-issue.md",
    "unknowns-issue.md",
    "execution-status.md",
)

# Meta/instructional sections that appear in template prose but never in a
# generated workitem body. Matched as case-insensitive prefixes so that both
# "Notes on filling ..." and a bare "Notes" are dropped.
_META_SECTION_PREFIXES: tuple[str, ...] = (
    "field notes",
    "notes on filling",
    "column definitions",
    "notes",
)


def _is_meta_section(name: str) -> bool:
    """True when *name* is a meta/instructional template section (never emitted)."""
    lowered = name.strip().lower()
    return any(lowered.startswith(prefix) for prefix in _META_SECTION_PREFIXES)


def _extract_heading(line: str) -> str | None:
    """Return the trimmed text of a top-level `## ` heading, or None."""
    match = re.match(r"^## (.+)$", line)
    return match.group(1).strip() if match else None


def _iter_sections(content: str, mode: str) -> list[tuple[str, int]]:
    """Yield `(section, line_no)` for top-level `## ` headings.

    Fences are tracked with a stack so a closing ```` ``` ```` pops whichever
    fence is currently open instead of assuming a fixed style:

    * A ```markdown block wraps a template's canonical structure, so its headings
      are the ones we want.
    * Any other code fence (```` ```lang ````) wraps an example, whose headings
      must be skipped.

    `mode="template"` returns headings inside ```markdown blocks plus headings
    outside every fence (canonical template structure, including the meta
    sections that sit after the closing fence and are dropped later).
    `mode="document"` returns only headings outside every fence — the real
    structure of a generated workitem, with embedded code examples skipped.
    """
    results: list[tuple[str, int]] = []
    fence_stack: list[str] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            if lang == "":  # bare ``` closes the current fence
                if fence_stack:
                    fence_stack.pop()
            elif lang == "markdown":
                fence_stack.append("markdown")
            else:
                fence_stack.append("other")
            continue
        heading = _extract_heading(line)
        if heading is None:
            continue
        if not fence_stack:
            results.append((heading, line_no))
            continue
        top = fence_stack[-1]
        if mode == "template" and top == "markdown":
            results.append((heading, line_no))
    return results


def _template_canonical_sections(path: Path) -> set[str]:
    """Lowercased canonical `## ` sections for a template, minus meta sections.

    Uses the ```markdown fenced block when present; otherwise scans the whole
    file for top-level headings. Meta/instructional sections are dropped via the
    prefix exclusion list.
    """
    text = path.read_text(encoding="utf-8")
    names = [name for name, _ in _iter_sections(text, "template")]
    return {name.lower() for name in names if not _is_meta_section(name)}


def _permitted_workitem_sections(domain: str) -> set[str]:
    """Canonical `## ` sections allowed for *domain* workitems (REQ-002).

    = main template's canonical sections
      union embedded sub-template sections
      minus meta/instructional sections
    Returned lowercased; callers compare case-insensitively.
    """
    allowed: set[str] = set()
    main_template = _DOMAIN_TEMPLATES.get(domain)
    if main_template:
        allowed |= _template_canonical_sections(TEMPLATES_DIR / main_template)
    for name in _SUB_TEMPLATE_NAMES:
        allowed |= _template_canonical_sections(TEMPLATES_DIR / name)
    return allowed


def _permitted_front_matter_keys() -> tuple[str, ...]:
    """Permitted front-matter keys = schema `properties` keys (REQ-001).

    Falls back to the loader's built-in required-field default when the schema
    file is absent or unreadable. `additionalProperties: true` is NOT treated as
    permission: GV-016 treats a field outside the defined properties as
    unnecessary.
    """
    schema = load_front_matter_schema()
    try:
        data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return schema.required_fields
    properties = data.get("properties")
    if isinstance(properties, dict):
        return tuple(properties)
    return schema.required_fields


def _extract_front_matter(content: str) -> tuple[str, object]:
    """Return `(status, value)`: `"none"` (no front matter), `"ok"` (parsed
    mapping), or `"error"` (malformed / unclosed)."""
    if not content.startswith("---"):
        return "none", None
    end = content.find("\n---", 3)
    if end == -1:
        return "error", None
    try:
        parsed = yaml.safe_load(content[3:end])
    except yaml.YAMLError:
        return "error", None
    return "ok", parsed


def _rel(path: Path) -> str:
    """Repo-relative path for reporting; falls back to the raw string when the
    scanned tree is not under ROOT_DIR (e.g. a custom --root)."""
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve()))
    except ValueError:
        return str(path)


def _scan_front_matter(path: Path, permitted: Iterable[str]) -> list[Issue]:
    rel = _rel(path)
    content = path.read_text(encoding="utf-8")
    status, parsed = _extract_front_matter(content)
    if status != "ok" or not isinstance(parsed, dict):
        return []  # no front matter / malformed: validity is other checkers' job
    permitted_set = set(permitted)
    issues: list[Issue] = []
    for key in parsed:
        if key not in permitted_set:
            issues.append(
                Issue(
                    file=rel,
                    line_no=1,
                    severity="WARNING",
                    message=(
                        f"{path.name}: front-matter key '{key}' is outside the "
                        f"permitted field set (GV-016)"
                    ),
                )
            )
    return issues


def _scan_workitem(path: Path) -> list[Issue]:
    domain = next((d for d in _DOMAIN_TEMPLATES if d in path.parts), None)
    if domain is None:
        return []
    permitted = _permitted_workitem_sections(domain)
    content = path.read_text(encoding="utf-8")
    rel = _rel(path)
    issues: list[Issue] = []
    for name, line_no in _iter_sections(content, "document"):
        if name.lower() not in permitted:
            issues.append(
                Issue(
                    file=rel,
                    line_no=line_no,
                    severity="WARNING",
                    message=(
                        f"{path.name}: section '## {name}' is outside this "
                        f"document type's canonical section set (GV-016)"
                    ),
                )
            )
    return issues


def _iter_doc_files(root: Path) -> list[Path]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    return sorted(docs.glob("*.md"))


def _iter_workitem_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for domain in _DOMAIN_TEMPLATES:
        domain_dir = root / domain
        if not domain_dir.is_dir():
            continue
        for path in sorted(domain_dir.rglob("*.md")):
            if "done" in path.parts:
                continue  # skip archived workitems (non-canonical history)
            files.append(path)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GV-016: flag metadata/status fields outside the sanctioned set."
    )
    parser.add_argument(
        "--root",
        default=str(ROOT_DIR),
        help="Repository root to scan (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)

    permitted_keys = _permitted_front_matter_keys()

    all_issues: list[Issue] = []
    for path in _iter_doc_files(root):
        all_issues.extend(_scan_front_matter(path, permitted_keys))
    for path in _iter_workitem_files(root):
        all_issues.extend(_scan_workitem(path))

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
