"""tools/check_plan_target_overlaps.py
Detects two or more active (`plans/*.md`, not `plans/done/`) `Frozen` Plans
that list the same file in their `## Implementation Target Files` table.

Motivating incident: an SSE-heartbeat Plan and a delivery-state-transition
Plan were both `Frozen` at the same time and both targeted the DLQ requeue
model in contradictory ways. Neither Plan's own review caught this --
each was self-consistent in isolation -- and it only surfaced later as a
test-suite collision once both were implemented. No existing tool compares
target-file lists ACROSS Plans; `check_workitem_traceability.py` and
`check_workitem_structure.py` both validate one document at a time.

This checker does not (and cannot, via static analysis) judge whether two
Plans' designs actually contradict each other -- it only surfaces the
much cheaper, purely mechanical precondition for that risk: the same file
path appearing in more than one currently-Frozen Plan's target-file table.
A human (or the `issue-to-plan` workflow's own review step) still has to
read both Plans and judge whether the overlap is a genuine conflict, a
sequencing dependency, or entirely compatible incidental overlap -- same
"candidate, not verdict" posture as `check_workitem_traceability.py`'s
`stale-target-heuristic` category.

Draft Plans are excluded: `## Implementation Target Files` is explicitly
not yet a validated, canonical file list until `Freeze status: Frozen` (see
`templates/plan.md`), so a Draft's in-progress scope would only add noise.

Never writes, renames, moves, or deletes anything.

Usage:
    python tools/check_plan_target_overlaps.py
    python tools/check_plan_target_overlaps.py --format json
    python tools/check_plan_target_overlaps.py --format csv
    python tools/check_plan_target_overlaps.py --plan plans/<plan>.md [--plan ...]

Exit code: always 0 (report-only heuristic; see the candidate-not-verdict
note above).
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
PLANS_DIR = ROOT_DIR / "plans"

_FREEZE_STATUS_RE = re.compile(r"(?m)^\*\*Freeze status\*\*:\s*(\S+)")
_TARGET_FILES_HEADING_RE = re.compile(r"(?m)^## Implementation Target Files\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^## ")
# A `templates/plan.md` target-file table row: 7 `|`-delimited cells, the
# first non-empty and not the literal header/separator text.
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")


@dataclass
class PlanDocument:
    path: Path
    rel_path: str
    is_frozen: bool
    target_files: list[str]


def _section_text(text: str, heading_re: re.Pattern[str]) -> str | None:
    heading_match = heading_re.search(text)
    if heading_match is None:
        return None
    section_start = heading_match.end()
    next_heading = _NEXT_HEADING_RE.search(text, section_start)
    section_end = next_heading.start() if next_heading else len(text)
    return text[section_start:section_end]


def extract_freeze_status(text: str) -> str | None:
    match = _FREEZE_STATUS_RE.search(text)
    return match.group(1) if match else None


def extract_target_file_rows(text: str) -> list[str]:
    """Return the `File Path` column of every real row in the
    `Implementation Target Files` table (header and `|---|...` separator
    rows, and rows with an empty/placeholder first cell, are skipped).
    """
    section_text = _section_text(text, _TARGET_FILES_HEADING_RE)
    if section_text is None:
        return []

    paths: list[str] = []
    for line in section_text.splitlines():
        row_match = _TABLE_ROW_RE.match(line.strip())
        if row_match is None:
            continue
        cells = [cell.strip() for cell in row_match.group(1).split("|")]
        if not cells:
            continue
        first_cell = cells[0]
        if not first_cell:
            continue
        # Normalize citation style: some Plans wrap the path cell in backticks.
        # Without this, a backticked row and a bare row for the same file are
        # treated as two different targets and real overlaps go undetected.
        first_cell = first_cell.strip("`").strip()
        if not first_cell:
            continue
        if first_cell == "File Path":
            continue
        if set(first_cell) <= {"-"}:
            continue
        paths.append(first_cell)
    return paths


def discover_plan_documents(plans_dir: Path = PLANS_DIR) -> list[PlanDocument]:
    documents: list[PlanDocument] = []
    if not plans_dir.is_dir():
        return documents
    for md_path in sorted(plans_dir.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        freeze_status = extract_freeze_status(text)
        documents.append(
            PlanDocument(
                path=md_path,
                rel_path=md_path.relative_to(ROOT_DIR).as_posix(),
                is_frozen=(freeze_status == "Frozen"),
                target_files=extract_target_file_rows(text),
            )
        )
    return documents


def make_finding(category: str, file_path: str, detail: str) -> dict[str, str]:
    return {"category": category, "file": file_path, "detail": detail}


def find_cross_plan_target_overlaps(
    documents: list[PlanDocument],
) -> list[dict[str, str]]:
    frozen_docs = [doc for doc in documents if doc.is_frozen]

    target_to_plans: dict[str, set[str]] = {}
    for doc in frozen_docs:
        for target_file in doc.target_files:
            target_to_plans.setdefault(target_file, set()).add(doc.rel_path)

    findings: list[dict[str, str]] = []
    for target_file, plan_paths in sorted(target_to_plans.items()):
        if len(plan_paths) < 2:
            continue
        others = sorted(plan_paths)
        findings.append(
            make_finding(
                "cross-plan-target-overlap",
                target_file,
                f"targeted by {len(others)} Frozen Plans at once: "
                f"{', '.join(others)} -- verify their designs do not "
                f"contradict each other before/while implementing",
            )
        )
    return findings


def normalize_plan_path(value: str) -> str:
    """Repository-relative POSIX form of a Plan path, as `PlanDocument.rel_path`."""
    path = Path(value)
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return path.as_posix()


def _finding_plans(detail: str) -> list[str]:
    """The Plan paths a finding's detail lists, between `: ` and ` -- `."""
    listed = detail.split(": ", 1)[-1].split(" -- ", 1)[0]
    return [item.strip() for item in listed.split(", ")]


def filter_findings_by_plans(
    findings: list[dict[str, str]], plans: list[str]
) -> list[dict[str, str]]:
    """Keep findings that name any of *plans* (exact path match); no plans keeps all."""
    if not plans:
        return findings
    wanted = {normalize_plan_path(plan) for plan in plans}
    return [f for f in findings if wanted & set(_finding_plans(f["detail"]))]


def render_text(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "No findings.\n"
    lines = [f"[{f['category']}] {f['file']}: {f['detail']}" for f in findings]
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
            "Report-only scan of plans/*.md (active Plans, not plans/done/) "
            "for a file path listed in more than one Frozen Plan's "
            "Implementation Target Files table at the same time."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    parser.add_argument(
        "--plan",
        action="append",
        default=None,
        metavar="PATH",
        help="Keep only findings that name this Plan (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    for plan in args.plan or []:
        if not Path(plan).is_file():
            print(f"error: not a file: {plan}", file=sys.stderr)
            return 2

    documents = discover_plan_documents()
    findings = filter_findings_by_plans(
        find_cross_plan_target_overlaps(documents), args.plan or []
    )

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
