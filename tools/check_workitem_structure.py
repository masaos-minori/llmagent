#!/usr/bin/env python3
"""tools/check_workitem_structure.py — Verify work-item documents contain every
required `## ` section from their canonical template.

Read-only checker over `issues/`, `plans/`, and `implementations/` (optionally
including each directory's `done/` subdirectory). For each document, extracts
the `## ` heading set from the matching canonical template's fenced
` ```markdown ` block (`templates/issue.md`, `templates/plan.md`,
`templates/implementation-procedure.md`) and reports any required heading
missing from the document itself.

This complements `check_workitem_traceability.py` (which validates the
content of an existing `## Traceability` section) by validating that a
document has every required section in the first place — a document missing
`## Implementation Target Files` or `## Traceability` entirely was previously
only caught by manually reading it end-to-end, as happened once in a live
`plan-to-implementation-procedure` run against a non-conforming Plan.

Never writes, renames, moves, or deletes anything under `issues/`, `plans/`,
or `implementations/`.

Usage:
    python tools/check_workitem_structure.py
    python tools/check_workitem_structure.py --kind plan
    python tools/check_workitem_structure.py --include-done
    python tools/check_workitem_structure.py --format json
    python tools/check_workitem_structure.py --file plans/20260908-073509_plan.md

`--file` checks exactly one document (its kind is inferred from which
top-level directory it lives under) and ignores `--kind`/`--include-done` —
use it from a workflow step that just produced or is about to consume one
specific document, so a repository-wide scan's legacy-template findings
(documents predating the current template revision, which this tool has no
way to distinguish from a genuinely incomplete document) never block a
single-file check.

Exit code: 0 when no document is missing a required section; 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent

_FENCE_RE = re.compile(r"```markdown\n(.*?)\n```", re.DOTALL)
_HEADING_RE = re.compile(r"(?m)^## (.+?)\s*$")

# (kind, template path relative to ROOT_DIR, work-item directory relative to ROOT_DIR)
_WORK_ITEM_KINDS: tuple[tuple[str, str, str], ...] = (
    ("issue", "templates/issue.md", "issues"),
    ("plan", "templates/plan.md", "plans"),
    ("implementation", "templates/implementation-procedure.md", "implementations"),
)

_DIR_TO_KIND: dict[str, str] = {
    dir_rel_path: kind for kind, _template_rel_path, dir_rel_path in _WORK_ITEM_KINDS
}


@dataclass
class TemplateSpec:
    """Required `## ` headings for one work-item kind, from its canonical template."""

    kind: str
    required_headings: tuple[str, ...]


def _extract_template_headings(template_path: Path) -> tuple[str, ...]:
    """Return the ordered `## ` heading set from a template's fenced example block.

    Each of the three templates this tool checks defines its canonical output
    structure inside a single ` ```markdown ` fenced block — headings outside
    that fence belong to the template document's own explanatory prose, not
    to the contract this tool enforces.
    """
    text = template_path.read_text(encoding="utf-8")
    fence_match = _FENCE_RE.search(text)
    if fence_match is None:
        return ()
    fenced_body = fence_match.group(1)
    return tuple(dict.fromkeys(_HEADING_RE.findall(fenced_body)))


def load_template_specs() -> dict[str, TemplateSpec]:
    specs: dict[str, TemplateSpec] = {}
    for kind, template_rel_path, _dir_rel_path in _WORK_ITEM_KINDS:
        headings = _extract_template_headings(ROOT_DIR / template_rel_path)
        specs[kind] = TemplateSpec(kind=kind, required_headings=headings)
    return specs


def discover_documents(kinds: set[str], include_done: bool) -> list[tuple[str, Path]]:
    """Return (kind, path) pairs for every target document to check."""
    documents: list[tuple[str, Path]] = []
    for kind, _template_rel_path, dir_rel_path in _WORK_ITEM_KINDS:
        if kind not in kinds:
            continue
        dir_candidates = [ROOT_DIR / dir_rel_path]
        if include_done:
            dir_candidates.append(ROOT_DIR / dir_rel_path / "done")
        for dir_path in dir_candidates:
            if not dir_path.is_dir():
                continue
            for md_path in sorted(dir_path.glob("*.md")):
                documents.append((kind, md_path))
    return documents


def find_missing_sections(doc_path: Path, spec: TemplateSpec) -> list[dict[str, str]]:
    text = doc_path.read_text(encoding="utf-8")
    doc_headings = set(_HEADING_RE.findall(text))
    rel_path = doc_path.relative_to(ROOT_DIR).as_posix()
    return [
        {
            "category": "missing-section",
            "file": rel_path,
            "detail": f"missing required section: ## {required}",
        }
        for required in spec.required_headings
        if required not in doc_headings
    ]


def infer_kind(doc_path: Path) -> str | None:
    """Infer a document's work-item kind from its top-level directory.

    Accepts both `<dir>/<file>.md` and `<dir>/done/<file>.md` layouts. Returns
    `None` when the path is not under `issues/`, `plans/`, or
    `implementations/` — the caller reports this as an argument error rather
    than guessing.
    """
    rel_path = doc_path.resolve().relative_to(ROOT_DIR)
    parts = rel_path.parts
    if not parts:
        return None
    return _DIR_TO_KIND.get(parts[0])


def collect_single_file_findings(doc_path: Path) -> list[dict[str, str]]:
    doc_path = doc_path.resolve()
    kind = infer_kind(doc_path)
    if kind is None:
        rel_path = doc_path.relative_to(ROOT_DIR).as_posix()
        return [
            {
                "category": "unknown-kind",
                "file": rel_path,
                "detail": (
                    "path is not under issues/, plans/, or implementations/ "
                    "— cannot infer which template to check against"
                ),
            }
        ]
    spec = load_template_specs()[kind]
    if not spec.required_headings:
        return []
    return find_missing_sections(doc_path, spec)


def collect_findings(kinds: set[str], include_done: bool) -> list[dict[str, str]]:
    specs = load_template_specs()
    findings: list[dict[str, str]] = []
    for kind, doc_path in discover_documents(kinds, include_done):
        spec = specs[kind]
        if not spec.required_headings:
            continue
        findings.extend(find_missing_sections(doc_path, spec))
    return findings


def render_text(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "No findings.\n"
    lines: list[str] = []
    by_file: dict[str, list[dict[str, str]]] = {}
    for finding in findings:
        by_file.setdefault(finding["file"], []).append(finding)
    for file_path, file_findings in by_file.items():
        lines.append(f"{file_path} ({len(file_findings)} missing)")
        for finding in file_findings:
            lines.append(f"  {finding['detail']}")
    lines.append(f"\n{len(findings)} finding(s) total.")
    return "\n".join(lines) + "\n"


def render_json(findings: list[dict[str, str]]) -> str:
    return orjson.dumps(
        findings, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
    ).decode()


def render_csv(findings: list[dict[str, str]]) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["category", "file", "detail"])
    writer.writeheader()
    writer.writerows(findings)
    return buffer.getvalue()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only check that issues/, plans/, and implementations/ "
            "documents contain every '## ' section required by their "
            "canonical template (templates/issue.md, templates/plan.md, "
            "templates/implementation-procedure.md)."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help=(
            "Check exactly this one document instead of scanning a "
            "directory; its kind is inferred from its path. Ignores "
            "--kind/--include-done."
        ),
    )
    parser.add_argument(
        "--kind",
        choices=["issue", "plan", "implementation"],
        action="append",
        dest="kinds",
        help="Restrict the check to one kind (repeatable; default: all three)",
    )
    parser.add_argument(
        "--include-done",
        action="store_true",
        help="Also check each kind's done/ subdirectory (default: skipped, since "
        "documents already archived predate later template revisions)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.file is not None:
        findings = collect_single_file_findings(args.file)
    else:
        kinds = set(args.kinds) if args.kinds else {"issue", "plan", "implementation"}
        findings = collect_findings(kinds, args.include_done)

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
