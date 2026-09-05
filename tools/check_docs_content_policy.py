#!/usr/bin/env python3
"""check_docs_content_policy.py — Scan docs/*.md for implementation-detail content.

`skills/DESIGN.md`'s "Docs content policy — remove" names five categories of
implementation-detail content a `docs/*.md` document should not contain: full
file trees, per-file descriptions embedded in a tree or table, class/function/
method index tables, implementation-location mappings, and literal port
numbers. This is a report-only (Warning) check — it never blocks CI; see
`docs/00_governance_04_documentation-checks.md`'s Governance Verification
Matrix for its registered entry.

Scans the full `docs/` tree recursively (including `docs/adr/`,
`docs/databases/`, etc.) — deliberately does not reuse
`tools/_docs_consistency_lib.py`'s `discover_md_files()`, which globs
non-recursively and requires a domain `prefix`.

Usage:
    python tools/check_docs_content_policy.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

_TREE_CHARS_RE = re.compile(r"[├│└]")
_INLINE_COMMENT_DESCRIPTION_RE = re.compile(r"[├│└].*#\s*\S")
_TABLE_DESCRIPTION_RE = re.compile(r"^\s*\|.*\|.*\|.*\|\s*$")
_INDEX_TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*(?:Function|Method|Class)\s*\|.*\|\s*(?:Signature|Description)\s*\|",
    re.IGNORECASE,
)
_LOCATION_MAPPING_RE = re.compile(
    r"\b(?:moved|implemented|handled)\s+by\s+`?[\w./-]+\.py`?", re.IGNORECASE
)
_PORT_NUMBER_RE = re.compile(r"\bPort\s+\d{2,5}\b", re.IGNORECASE)
_ILLUSTRATIVE_MARKERS = frozenset(
    {"illustrative", "worked example", "for example", "e.g."}
)


@dataclass(frozen=True)
class DocFile:
    """A single documentation file with its contents."""

    path: Path
    rel_path: str  # relative to docs/
    lines: list[str] = field(default_factory=list)


def discover_all_md_files(docs_dir: Path) -> list[DocFile]:
    """Return every `.md` file under *docs_dir*, recursively, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob("*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


def check_full_file_tree(files: list[DocFile]) -> list[Issue]:
    """Flag lines containing ASCII tree-drawing characters (a full file tree)."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _TREE_CHARS_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "full file tree: line contains ASCII tree-drawing "
                            "characters (├/│/└) — see skills/DESIGN.md Docs "
                            "content policy — remove"
                        ),
                    )
                )
    return issues


def check_per_file_description(files: list[DocFile]) -> list[Issue]:
    """Flag a tree line carrying an inline `#`-style per-file description."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _INLINE_COMMENT_DESCRIPTION_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "per-file one-line description embedded in a tree — "
                            "see skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_index_table(files: list[DocFile]) -> list[Issue]:
    """Flag a Markdown table header naming a Function/Method/Class + Signature/Description."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _INDEX_TABLE_HEADER_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "class/function/method index table header — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_location_mapping(files: list[DocFile]) -> list[Issue]:
    """Flag an inline statement naming which `.py` file implements a behavior."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if _LOCATION_MAPPING_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="WARNING",
                        message=(
                            "implementation-location mapping — see "
                            "skills/DESIGN.md Docs content policy — remove"
                        ),
                    )
                )
    return issues


def check_literal_port_number(files: list[DocFile]) -> list[Issue]:
    """Flag a literal port number, unless the line is explicitly labeled illustrative."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, 1):
            if not _PORT_NUMBER_RE.search(line):
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in _ILLUSTRATIVE_MARKERS):
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "literal port number — see skills/DESIGN.md Docs "
                        "content policy — remove"
                    ),
                )
            )
    return issues


def main() -> int:
    files = discover_all_md_files(DOCS_DIR)

    all_issues: list[Issue] = []
    all_issues += check_full_file_tree(files)
    all_issues += check_per_file_description(files)
    all_issues += check_index_table(files)
    all_issues += check_location_mapping(files)
    all_issues += check_literal_port_number(files)

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
