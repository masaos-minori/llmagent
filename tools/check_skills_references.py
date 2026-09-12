#!/usr/bin/env python3
"""check_skills_references.py — Verify file-path references among skills/rules/prompts resolve.

`prompts/05_skills.md`'s Context Loader Pattern workflow relies on
skills/*.md, rules/*.md, and prompts/*.md files pointing at a shared
canonical source instead of restating it inline (e.g. `` `rules/ai-execution.md`
Global Safety Restrictions (Base) `` or the formal `` See `rules/coding.md`,
section "Suppression governance". `` form). Nothing currently re-checks that
these references still resolve after a file is renamed, split, or removed —
each `prompts/05_skills.md` run has done this by hand (fork-agent inventory)
instead. This script automates the mechanical, exact half of that check: does
the referenced file still exist.

A companion heuristic — matching the free-text phrase after a file reference
against the target file's actual headings — was prototyped and dropped: on
this repository's current prose style it flagged ~290 references, essentially
all false positives (most references name a Step/Rule number or a file
itself, not a heading a human would quote verbatim), which would make the
tool noise rather than signal. Heading-level drift is still the
`prompts/05_skills.md` workflow's own job to catch by reading the target
section (see that file's "Circular reference check").

Check:
- `dangling-reference` (ERROR): a backtick-quoted `.md` path under `rules/`,
  `skills/`, or `templates/` (or the bare `AGENTS.md`/`routing.md` files) that
  does not exist in the repository.

Scope mirrors `prompts/05_skills.md`'s "Scope" section: `AGENTS.md`,
`routing.md`, `skills/DESIGN.md`, `rules/*.md`, `skills/**/*.md`,
`prompts/*.md`. `templates/*.md` files are valid reference *targets* (per that
Scope note) but are not themselves scanned as source files, since they define
structural format only.

Usage:
    python tools/check_skills_references.py
    python tools/check_skills_references.py --format json
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent

# Source files scanned for outgoing references — mirrors prompts/05_skills.md Scope.
_SOURCE_GLOBS = [
    "AGENTS.md",
    "routing.md",
    "skills/DESIGN.md",
    "rules/*.md",
    "skills/**/*.md",
    "prompts/*.md",
]

# A backtick-quoted reference target: rules/skills/templates paths, or the
# two bare root files. Deliberately excludes docs/*.md and config/*.toml —
# this tool checks the skills/rules/prompts reference graph, not doc-domain
# consistency (already covered by check_docs_consistency.py).
_REF_PATH_RE = re.compile(
    r"`((?:rules|skills|templates)/[A-Za-z0-9_./-]+\.md|AGENTS\.md|routing\.md)`"
)


def _repo_glob(patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(REPO_ROOT.glob(pattern))
    return sorted(p for p in paths if p.is_file())


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def find_referenced_paths(lines: list[str]) -> list[tuple[int, str]]:
    """Return (1-indexed line_no, target_path) for every backtick-quoted
    reference-scope path found in *lines*."""
    refs: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        for match in _REF_PATH_RE.finditer(line):
            refs.append((i + 1, match.group(1)))
    return refs


def check_references(source_files: list[tuple[str, list[str]]]) -> list[Issue]:
    issues: list[Issue] = []
    for source_file, lines in source_files:
        for line_no, target_path in find_referenced_paths(lines):
            if not (REPO_ROOT / target_path).exists():
                issues.append(
                    Issue(
                        file=source_file,
                        line_no=line_no,
                        severity="ERROR",
                        message=(f"dangling-reference: '{target_path}' does not exist"),
                    )
                )
    return issues


def collect_issues() -> list[Issue]:
    source_files: list[tuple[str, list[str]]] = []
    for path in _repo_glob(_SOURCE_GLOBS):
        rel = _rel(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        source_files.append((rel, lines))
    return check_references(source_files)


def render_json(issues: list[Issue]) -> str:
    payload = [
        {
            "file": issue.file,
            "line_no": issue.line_no,
            "severity": issue.severity,
            "message": issue.message,
        }
        for issue in sorted(issues, key=lambda i: (i.file, i.line_no))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify every skills/rules/prompts backtick-quoted file reference "
            "resolves to a file that actually exists."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    args = parser.parse_args(argv)

    issues = collect_issues()

    if args.format == "json":
        print(render_json(issues))
        return 1 if any(issue.severity == "ERROR" for issue in issues) else 0

    return report_and_exit(issues)


if __name__ == "__main__":
    raise SystemExit(main())
