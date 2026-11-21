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

For a Plan, it also validates the optional release-unit declaration: a
`### Release units` block inside `## Implementation steps` whose entries read
`**Unit**: {name} | **Phases**: {N, N} | **Reason**: {text}` with every field
non-empty and every phase number a top-level numbered step of that section. A Plan
without the block is unaffected. A block that is an `N/A: ...` line is accepted unless its
text says phases land together or in the same commit: phases that cannot be validated alone
are a release unit and must be declared as one.

For an issue, plan, or procedure, it additionally reports document lines kept
verbatim from the canonical templates' scaffolds as `template-leftover`
findings — unfilled scaffold text that survived into a real document. Issues
keep `templates/issue.md` lines (the title line, placeholder bullets, and
instruction lines); plans report whole-value `{...}` Traceability fields,
all-empty table rows, and verbatim bracket-wrapped lines of
`templates/plan.md`; procedures report the first two. The rules live in
`tools/_workitem_leftover_rules.py` and read the templates at run time;
braces in the document's own content are not reported.

Never writes, renames, moves, or deletes anything under `issues/`, `plans/`,
or `implementations/`.

Usage:
    python tools/check_workitem_structure.py
    python tools/check_workitem_structure.py --kind plan
    python tools/check_workitem_structure.py --include-done
    python tools/check_workitem_structure.py --format json
    python tools/check_workitem_structure.py --file plans/20260908-073509_plan.md
    python tools/check_workitem_structure.py --file issues/a.md issues/b.md

`--file` checks one or more documents (each kind is inferred from which
top-level directory the path lives under) and ignores `--kind`/`--include-done`
— use it from a workflow step that just produced or is about to consume
specific documents, so a repository-wide scan's legacy-template findings
(documents predating the current template revision, which this tool has no
way to distinguish from a genuinely incomplete document) never block a
`--file` check.

`--archived-status [--baseline PATH]` checks a different property: no procedure under
`implementations/done/` keeps an unfinished (`Pending`, `In Progress`, `Blocked`)
Execution Status row, and no archived procedure or plan holds a Status value outside
the vocabulary. A procedure that was not implemented is archived with
`close-implementation --superseded --reason`, which marks its rows `Superseded`. The
archives predate these rules, so the paths that already violated them are listed in
`tools/check_archived_status_baseline.txt` (unfinished rows) and
`tools/check_status_value_baseline.txt` (vocabulary values) and are not reported.

Exit code: 0 when no finding is reported; 1 otherwise. A `procedure-length` finding (a
documentation-only procedure over the line limit of `tools/_workitem_length_check.py`) is
advisory: it is printed but does not make the exit code 1.
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

if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT_DIR))

from tools._workitem_leftover_rules import (
    find_issue_leftover_findings,
    find_plan_leftover_findings,
    find_procedure_leftover_findings,
    issue_template_leftover_lines,
    plan_bracket_lines,
)
from tools._workitem_length_check import find_docs_procedure_length_findings
from tools._workitem_status_check import find_status_value_findings
from tools._workitem_status_table import parse_execution_status_rows

ARCHIVED_STATUS_BASELINE = ROOT_DIR / "tools" / "check_archived_status_baseline.txt"
STATUS_VALUE_BASELINE = ROOT_DIR / "tools" / "check_status_value_baseline.txt"
ADVISORY_CATEGORIES = frozenset({"procedure-length"})
_UNFINISHED_PREFIXES = ("pending", "in progress", "in_progress", "blocked")

_FENCE_RE = re.compile(r"```markdown\n(.*?)\n```", re.DOTALL)
_HEADING_RE = re.compile(r"(?mi)^## (.+?)\s*$")
_STEPS_HEADING_RE = re.compile(r"(?mi)^## Implementation steps\s*$")
_RELEASE_UNITS_HEADING_RE = re.compile(r"(?mi)^### Release units\s*$")
_ANY_HEADING_RE = re.compile(r"(?m)^#{1,6} ")
_STEP_NUMBER_RE = re.compile(r"(?m)^(\d+)\. ")
_UNIT_ENTRY_RE = re.compile(
    r"^\*\*Unit\*\*:\s*(?P<name>.*?)\s*\|\s*\*\*Phases\*\*:\s*(?P<phases>.*?)"
    r"\s*\|\s*\*\*Reason\*\*:\s*(?P<reason>.*?)\s*$"
)

# An `N/A` release-unit line that describes phases landing together contradicts itself.
_NA_CONTRADICTION_RE = re.compile(
    r"(?i)land(?:s|ed)?\s+together|same\s+commit|validated\s+together"
    r"|until\s+(?:another|a\s+later)\s+phase"
)

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
    # Compare case-insensitively. `_HEADING_RE` matches headings regardless of
    # case, but the captured groups retain their original casing, so a plain
    # set-membership test would falsely report a section as missing whenever a
    # document (or a sibling template) uses different casing than the canonical
    # one. Lowercasing both sides keeps detection robust to such casing
    # differences instead of erroring on them.
    doc_headings = {h.lower() for h in _HEADING_RE.findall(text)}
    rel_path = doc_path.relative_to(ROOT_DIR).as_posix()
    return [
        {
            "category": "missing-section",
            "file": rel_path,
            "detail": f"missing required section: ## {required}",
        }
        for required in spec.required_headings
        if required.lower() not in doc_headings
    ]


def _section_after(text: str, heading_end: int, boundary_re: re.Pattern[str]) -> str:
    """Return the text from `heading_end` up to the next boundary heading."""
    boundary = boundary_re.search(text, heading_end)
    return text[heading_end : boundary.start() if boundary else len(text)]


def _release_unit_entry_problem(line: str, known_phases: set[int]) -> str | None:
    """Return why one declaration line is malformed, or None when it is valid."""
    match = _UNIT_ENTRY_RE.match(line)
    if match is None:
        return (
            "expected `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {reason}`"
            f", got: {line}"
        )
    if not match["name"]:
        return "missing unit name"
    if not match["reason"]:
        return "missing reason"
    phase_tokens = [token.strip() for token in match["phases"].split(",")]
    if not match["phases"] or not all(token.isdigit() for token in phase_tokens):
        return "missing or non-numeric member phases"
    unknown = sorted({int(t) for t in phase_tokens} - known_phases)
    if unknown:
        return f"phase(s) {unknown} are not top-level steps of Implementation steps"
    return None


def find_release_unit_findings(doc_path: Path) -> list[dict[str, str]]:
    """Validate a Plan's optional `### Release units` declaration (REQ-004)."""
    text = doc_path.read_text(encoding="utf-8")
    rel_path = doc_path.relative_to(ROOT_DIR).as_posix()

    def finding(detail: str) -> dict[str, str]:
        return {
            "category": "release-unit",
            "file": rel_path,
            "detail": f"release unit declaration: {detail}",
        }

    unit_headings = list(_RELEASE_UNITS_HEADING_RE.finditer(text))
    if not unit_headings:
        return []
    steps_heading = _STEPS_HEADING_RE.search(text)
    steps_start = steps_heading.end() if steps_heading else -1
    steps_text = _section_after(text, steps_start, _HEADING_RE) if steps_heading else ""
    steps_end = steps_start + len(steps_text)
    findings: list[dict[str, str]] = []
    inside = [h for h in unit_headings if steps_start <= h.start() < steps_end]
    if len(inside) < len(unit_headings):
        findings.append(
            finding("`### Release units` is outside `## Implementation steps`")
        )
    if not inside:
        return findings
    block = _section_after(text, inside[0].end(), _ANY_HEADING_RE)
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return [*findings, finding("block is empty (use `N/A: no release unit`)")]
    if all(line.startswith("N/A") for line in lines):
        if _NA_CONTRADICTION_RE.search(" ".join(lines)):
            findings.append(
                finding(
                    "`N/A` says phases land together or in the same commit; phases "
                    "that cannot be validated alone are a release unit, declare one"
                )
            )
        return findings
    known_phases = {int(n) for n in _STEP_NUMBER_RE.findall(steps_text)}
    for line in lines:
        problem = _release_unit_entry_problem(line, known_phases)
        if problem is not None:
            findings.append(finding(problem))
    return findings


def load_archived_status_baseline(path: Path = ARCHIVED_STATUS_BASELINE) -> set[str]:
    """Repository-relative paths grandfathered by the archived-status rule."""
    if not path.is_file():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def find_archived_status_value_findings(
    value_dirs: tuple[Path, ...] | None = None,
    value_baseline: set[str] | None = None,
) -> list[dict[str, str]]:
    """Archived procedures and plans holding an out-of-vocabulary Status value."""
    directories = (
        value_dirs
        if value_dirs is not None
        else (ROOT_DIR / "implementations" / "done", ROOT_DIR / "plans" / "done")
    )
    allowed = (
        load_archived_status_baseline(STATUS_VALUE_BASELINE)
        if value_baseline is None
        else value_baseline
    )
    findings: list[dict[str, str]] = []
    for value_dir in directories:
        if not value_dir.is_dir():
            continue
        for doc in sorted(value_dir.glob("*.md")):
            rel_path = doc.relative_to(ROOT_DIR).as_posix()
            if rel_path in allowed:
                continue
            findings.extend(
                find_status_value_findings(doc.read_text(encoding="utf-8"), rel_path)
            )
    return findings


def _archived_unfinished_finding(doc: Path, rel_path: str) -> dict[str, str] | None:
    """One archived document's unfinished-row finding, or None when it has none."""
    rows = parse_execution_status_rows(doc.read_text(encoding="utf-8")) or []
    steps = [
        row.get("Step", "?")
        for row in rows
        if row.get("Status", "").strip().lower().startswith(_UNFINISHED_PREFIXES)
    ]
    if not steps:
        return None
    return {
        "category": "archived-status",
        "file": rel_path,
        "detail": (
            f"archived with unfinished Execution Status row(s) (Step "
            f"{', '.join(steps)}); archive a procedure that was not "
            "implemented with `close-implementation --superseded --reason`"
        ),
    }


def find_archived_status_findings(
    baseline: set[str] | None = None,
    done_dir: Path | None = None,
    value_dirs: tuple[Path, ...] | None = None,
    value_baseline: set[str] | None = None,
) -> list[dict[str, str]]:
    """Archived unfinished rows and archived out-of-vocabulary Status values.

    The unfinished-row scan covers `implementations/done/` with the
    `check_archived_status_baseline.txt` grandfathering; the value scan covers
    `implementations/done/` and `plans/done/` with the
    `check_status_value_baseline.txt` grandfathering (see
    `find_archived_status_value_findings`).
    """
    directory = (
        done_dir if done_dir is not None else ROOT_DIR / "implementations" / "done"
    )
    allowed = load_archived_status_baseline() if baseline is None else baseline
    findings: list[dict[str, str]] = []
    for doc in sorted(directory.glob("*.md")):
        rel_path = doc.relative_to(ROOT_DIR).as_posix()
        if rel_path in allowed:
            continue
        finding = _archived_unfinished_finding(doc, rel_path)
        if finding is not None:
            findings.append(finding)
    value_directories = value_dirs
    if value_directories is None and done_dir is not None:
        value_directories = (done_dir,)
    findings.extend(
        find_archived_status_value_findings(value_directories, value_baseline)
    )
    return findings


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


def _is_archived(doc_path: Path) -> bool:
    """True for a `<dir>/done/` document: the archived-status rules judge those."""
    parts = doc_path.resolve().relative_to(ROOT_DIR).parts
    return len(parts) >= 2 and parts[1] == "done"


def _status_value_findings(doc_path: Path) -> list[dict[str, str]]:
    """Active-document Status value rule for a plan or procedure document."""
    rel_path = doc_path.relative_to(ROOT_DIR).as_posix()
    return find_status_value_findings(doc_path.read_text(encoding="utf-8"), rel_path)


def _length_findings(doc_path: Path) -> list[dict[str, str]]:
    """Advisory length rule for an active procedure document."""
    rel_path = doc_path.relative_to(ROOT_DIR).as_posix()
    return find_docs_procedure_length_findings(
        doc_path.read_text(encoding="utf-8"), rel_path
    )


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
    findings = find_missing_sections(doc_path, spec)
    if kind == "plan":
        findings.extend(find_release_unit_findings(doc_path))
    if kind == "issue":
        findings.extend(find_issue_leftover_findings(doc_path, ROOT_DIR))
    if kind in ("plan", "implementation") and not _is_archived(doc_path):
        findings.extend(_status_value_findings(doc_path))
        if kind == "plan":
            findings.extend(find_plan_leftover_findings(doc_path, ROOT_DIR))
        else:
            findings.extend(find_procedure_leftover_findings(doc_path, ROOT_DIR))
            findings.extend(_length_findings(doc_path))
    return findings


def collect_findings(kinds: set[str], include_done: bool) -> list[dict[str, str]]:
    specs = load_template_specs()
    issue_rule = issue_template_leftover_lines(ROOT_DIR / "templates" / "issue.md")
    plan_brackets = plan_bracket_lines(ROOT_DIR / "templates" / "plan.md")
    findings: list[dict[str, str]] = []
    for kind, doc_path in discover_documents(kinds, include_done):
        spec = specs[kind]
        if not spec.required_headings:
            continue
        findings.extend(find_missing_sections(doc_path, spec))
        if kind == "plan":
            findings.extend(find_release_unit_findings(doc_path))
        if kind == "issue":
            findings.extend(
                find_issue_leftover_findings(doc_path, ROOT_DIR, issue_rule)
            )
        if kind in ("plan", "implementation") and not _is_archived(doc_path):
            findings.extend(_status_value_findings(doc_path))
            if kind == "plan":
                findings.extend(
                    find_plan_leftover_findings(doc_path, ROOT_DIR, plan_brackets)
                )
            else:
                findings.extend(find_procedure_leftover_findings(doc_path, ROOT_DIR))
                findings.extend(_length_findings(doc_path))
    return findings


def render_text(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "No findings.\n"
    lines: list[str] = []
    by_file: dict[str, list[dict[str, str]]] = {}
    for finding in findings:
        by_file.setdefault(finding["file"], []).append(finding)
    for file_path, file_findings in by_file.items():
        lines.append(f"{file_path} ({len(file_findings)} finding(s))")
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
            "templates/implementation-procedure.md). For a Plan it also validates "
            "the optional '### Release units' declaration; for an issue it also "
            "reports lines kept verbatim from the issue template's scaffold."
        )
    )
    parser.add_argument(
        "--file",
        type=Path,
        nargs="+",
        default=None,
        help=(
            "Check exactly these documents instead of scanning a directory; "
            "each kind is inferred from its path. Ignores --kind/--include-done."
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
        "--archived-status",
        action="store_true",
        help="Check that no procedure under implementations/done/ has an unfinished "
        "Execution Status row and no archived procedure or plan holds a Status value "
        "outside the vocabulary (paths in the two baseline files are skipped); ignores "
        "the other selection options",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Baseline file for --archived-status (default: "
        "tools/check_archived_status_baseline.txt)",
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

    if args.archived_status:
        baseline = (
            load_archived_status_baseline(args.baseline)
            if args.baseline is not None
            else None
        )
        findings = find_archived_status_findings(baseline)
    elif args.file is not None:
        findings = [
            finding
            for path in args.file
            for finding in collect_single_file_findings(path)
        ]
    else:
        kinds = set(args.kinds) if args.kinds else {"issue", "plan", "implementation"}
        findings = collect_findings(kinds, args.include_done)

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    return 1 if any(f["category"] not in ADVISORY_CATEGORIES for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
