#!/usr/bin/env python3
"""tools/generate_workitem.py — Scaffold issue/plan/implementation-procedure/
unknowns/risks files.

Generates a correctly-named, correctly-structured skeleton file for one of the
five work-item document kinds (`issues/*.md`, `plans/*.md`,
`implementations/*.md`, `issues/{timestamp}_unknowns.md`,
`issues/{timestamp}_risks.md`) by extracting the canonical fenced skeleton from
the corresponding template file (`templates/issue.md`, `templates/plan.md`,
`templates/implementation-procedure.md`, `templates/unknowns-issue.md`,
`templates/risks-issue.md`) verbatim and writing it to a computed output path.
Placeholder text only — this tool never invents substantive field content, and
never modifies the template files it reads from.

Refuses to overwrite an existing file: if the computed output path already
exists in the target directory or its `done/` counterpart, the tool exits
non-zero without writing (no auto-increment, no overwrite) — per
`skills/issue-to-plan/workflow.md` Step 6, a collision on `unknowns`/`risks`
output is the caller's signal to retry with the next zero-padded sequence
(`{timestamp}_01_unknowns.md`, ...), not a tool failure.

Timestamp sharing (`--kind implementation-procedure` only): per
`skills/plan-to-implementation-procedure/workflow.md` Step 3, every document
generated for one Plan's `Implementation Target Files` table must share a
single timestamp across the whole pass, so filenames sort into the Plan's row
order. This tool has no `--timestamp` flag; instead, the first invocation for
a given `--source-plan` records an HTML-comment marker
(`<!-- tools/generate_workitem.py implementation-procedure-pass timestamp:
{timestamp} -->`) appended to that Plan file, and every subsequent invocation
against the same Plan reads that marker back and reuses its timestamp instead
of generating a new one. This is the one write this tool makes to a file it
does not itself create — the Plan's own content above the marker is never
touched — and it makes the shared timestamp durable across separate tool
invocations, including a resumed session.

Usage:
    python tools/generate_workitem.py --kind issue --id nc020 --title "Fix the thing"
    python tools/generate_workitem.py --kind plan
    python tools/generate_workitem.py --kind implementation-procedure \\
        --source-plan plans/20260901-105731_plan.md \\
        --target-file-path tools/generate_workitem.py --seq 01
    python tools/generate_workitem.py --kind implementation-procedure \\
        --source-plan plans/20260901-105731_plan.md \\
        --target-file-path tools/manage_workitem_stage.py --seq 02
    python tools/generate_workitem.py --kind unknowns
    python tools/generate_workitem.py --kind risks --seq 01
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TEMPLATE_ISSUE = REPO_ROOT / "templates" / "issue.md"
TEMPLATE_PLAN = REPO_ROOT / "templates" / "plan.md"
TEMPLATE_IMPLEMENTATION_PROCEDURE = (
    REPO_ROOT / "templates" / "implementation-procedure.md"
)
TEMPLATE_UNKNOWNS_ISSUE = REPO_ROOT / "templates" / "unknowns-issue.md"
TEMPLATE_RISKS_ISSUE = REPO_ROOT / "templates" / "risks-issue.md"

ISSUES_DIR = REPO_ROOT / "issues"
PLANS_DIR = REPO_ROOT / "plans"
IMPLEMENTATIONS_DIR = REPO_ROOT / "implementations"

_FENCE_OPEN_RE = re.compile(r"^```markdown\s*$")
_FENCE_CLOSE_RE = re.compile(r"^```\s*$")
_NON_PATH_SLUG_RE = re.compile(r"[^A-Za-z0-9_.-]")
_PASS_TIMESTAMP_MARKER_RE = re.compile(
    r"^<!-- tools/generate_workitem\.py implementation-procedure-pass "
    r"timestamp: (\d{8}-\d{6}) -->$"
)
_PASS_TIMESTAMP_MARKER_TEMPLATE = (  # nosec B105 -- HTML comment marker text, not a password/token
    "<!-- tools/generate_workitem.py implementation-procedure-pass "
    "timestamp: {timestamp} -->\n"
)


class GenerationError(Exception):
    """Raised when a validation check fails before any file would be written."""


def _require(condition: bool, message: str) -> None:
    """Raise GenerationError(message) unless *condition* is true."""
    if not condition:
        raise GenerationError(message)


def extract_fenced_skeleton(template_path: Path) -> str:
    """Return the text strictly between the first ` ```markdown ` fence and its
    matching closing ` ``` ` marker in *template_path* (fence markers excluded).
    """
    try:
        lines = template_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GenerationError(
            f"cannot read template file {template_path}: {exc}"
        ) from exc

    start_index: int | None = None
    for index, line in enumerate(lines):
        if _FENCE_OPEN_RE.match(line):
            start_index = index
            break
    if start_index is None:
        raise GenerationError(f"no ```markdown fence found in {template_path}")

    for index in range(start_index + 1, len(lines)):
        if _FENCE_CLOSE_RE.match(lines[index]):
            return "\n".join(lines[start_index + 1 : index]) + "\n"

    raise GenerationError(f"no closing ``` fence found in {template_path}")


def slugify_title(title: str) -> str:
    """Lowercase *title* and replace spaces with dashes (issue filename slug)."""
    return title.strip().lower().replace(" ", "-")


def slugify_target_file_path(target_file_path: str) -> str:
    """Replace `/` and any non-alphanumeric/`_`/`-`/`.` character with `_`."""
    return _NON_PATH_SLUG_RE.sub("_", target_file_path.replace("/", "_"))


def issue_output_path(timestamp: str, issue_id: str, title: str) -> Path:
    """`issues/{timestamp}_{id}_{slug}.md` per `skills/issue-creator/SKILL.md`."""
    return ISSUES_DIR / f"{timestamp}_{issue_id}_{slugify_title(title)}.md"


def plan_output_path(timestamp: str) -> Path:
    """`plans/{timestamp}_plan.md` per `templates/plan.md` Step 5."""
    return PLANS_DIR / f"{timestamp}_plan.md"


def implementation_procedure_output_path(
    timestamp: str, seq: str, target_file_path: str
) -> Path:
    """`implementations/{timestamp}_{seq}_{target_file_slug}.md` per
    `skills/plan-to-implementation-procedure/workflow.md` Workflow position.
    """
    target_file_slug = slugify_target_file_path(target_file_path)
    return IMPLEMENTATIONS_DIR / f"{timestamp}_{seq}_{target_file_slug}.md"


def unknowns_output_path(timestamp: str, seq: str | None) -> Path:
    """`issues/{timestamp}_unknowns.md`, or `issues/{timestamp}_{seq}_unknowns.md`
    when a zero-padded sequence is supplied, per
    `skills/issue-to-plan/workflow.md` Step 6.
    """
    if seq:
        return ISSUES_DIR / f"{timestamp}_{seq}_unknowns.md"
    return ISSUES_DIR / f"{timestamp}_unknowns.md"


def risks_output_path(timestamp: str, seq: str | None) -> Path:
    """`issues/{timestamp}_risks.md`, or `issues/{timestamp}_{seq}_risks.md`
    when a zero-padded sequence is supplied, per
    `skills/issue-to-plan/workflow.md` Step 6.
    """
    if seq:
        return ISSUES_DIR / f"{timestamp}_{seq}_risks.md"
    return ISSUES_DIR / f"{timestamp}_risks.md"


def check_collision(output_path: Path) -> Path | None:
    """Return the colliding path (*output_path* or its `done/` counterpart) if
    one already exists, else None.
    """
    if output_path.exists():
        return output_path
    done_path = output_path.parent / "done" / output_path.name
    if done_path.exists():
        return done_path
    return None


def _resolve_repo_path(path_str: str) -> Path:
    """Resolve *path_str* against REPO_ROOT unless it is already absolute."""
    path = Path(path_str)
    return path if path.is_absolute() else REPO_ROOT / path


def find_or_record_pass_timestamp(plan_path: Path, generated_timestamp: str) -> str:
    """Return the timestamp this Plan's implementation-procedure generation
    pass shares across every `Implementation Target Files` row.

    If *plan_path* already carries a `_PASS_TIMESTAMP_MARKER_RE` marker
    (written by an earlier invocation against the same Plan), return that
    recorded timestamp unchanged — *generated_timestamp* is discarded. This
    keeps every row's filename timestamp identical across separate tool
    invocations, including ones in a resumed session, without requiring the
    caller to track or pass the timestamp itself.

    If no marker exists yet, append one recording *generated_timestamp* to
    the end of *plan_path* and return *generated_timestamp*. This is the only
    write this function makes: the Plan's existing content is never rewritten
    or reordered, only appended to.
    """
    content = plan_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        match = _PASS_TIMESTAMP_MARKER_RE.match(line.strip())
        if match:
            return match.group(1)
    marker = _PASS_TIMESTAMP_MARKER_TEMPLATE.format(timestamp=generated_timestamp)
    plan_path.write_text(content.rstrip("\n") + "\n\n" + marker, encoding="utf-8")
    return generated_timestamp


def render_issue(args: argparse.Namespace, timestamp: str) -> tuple[str, Path]:
    _require(bool(args.id and args.title), "--kind issue requires --id and --title")
    skeleton = extract_fenced_skeleton(TEMPLATE_ISSUE)
    output_path = issue_output_path(timestamp, args.id, args.title)
    return skeleton, output_path


def render_plan(_args: argparse.Namespace, timestamp: str) -> tuple[str, Path]:
    skeleton = extract_fenced_skeleton(TEMPLATE_PLAN)
    return skeleton, plan_output_path(timestamp)


def render_implementation_procedure(
    args: argparse.Namespace, timestamp: str
) -> tuple[str, Path]:
    _require(
        bool(args.source_plan and args.target_file_path and args.seq),
        "--kind implementation-procedure requires --source-plan, "
        "--target-file-path, and --seq",
    )
    source_plan_path = _resolve_repo_path(args.source_plan)
    _require(
        source_plan_path.exists(),
        f"--source-plan path does not exist: {args.source_plan}",
    )
    pass_timestamp = find_or_record_pass_timestamp(source_plan_path, timestamp)
    skeleton = extract_fenced_skeleton(TEMPLATE_IMPLEMENTATION_PROCEDURE)
    output_path = implementation_procedure_output_path(
        pass_timestamp, args.seq, args.target_file_path
    )
    return skeleton, output_path


def render_unknowns(args: argparse.Namespace, timestamp: str) -> tuple[str, Path]:
    skeleton = extract_fenced_skeleton(TEMPLATE_UNKNOWNS_ISSUE)
    return skeleton, unknowns_output_path(timestamp, args.seq)


def render_risks(args: argparse.Namespace, timestamp: str) -> tuple[str, Path]:
    skeleton = extract_fenced_skeleton(TEMPLATE_RISKS_ISSUE)
    return skeleton, risks_output_path(timestamp, args.seq)


_RENDERERS: dict[str, Callable[[argparse.Namespace, str], tuple[str, Path]]] = {
    "issue": render_issue,
    "plan": render_plan,
    "implementation-procedure": render_implementation_procedure,
    "unknowns": render_unknowns,
    "risks": render_risks,
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a correctly-named, correctly-structured skeleton file for "
            "an issue, plan, implementation-procedure, unknowns-follow-up, or "
            "risks-follow-up work item. Placeholder text only — never invents "
            "substantive field content. Refuses to overwrite an existing file "
            "(reject-only; no auto-increment)."
        )
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=["issue", "plan", "implementation-procedure", "unknowns", "risks"],
        help="Work-item kind to generate.",
    )
    parser.add_argument("--id", help="Issue mode: short identifier, e.g. 'nc020'.")
    parser.add_argument("--title", help="Issue mode: issue title.")
    parser.add_argument(
        "--source-plan",
        help=(
            "Implementation-procedure mode: path to the source plan file. "
            "The tool appends a timestamp marker comment to this file (or "
            "reads one back from a prior invocation) so repeated calls "
            "against the same plan share one timestamp; see this module's "
            "docstring, Timestamp sharing."
        ),
    )
    parser.add_argument(
        "--target-file-path",
        help="Implementation-procedure mode: repository-relative target file path.",
    )
    parser.add_argument(
        "--seq",
        help=(
            "Implementation-procedure mode: the row's 1-indexed, zero-padded "
            "position within the plan's Implementation Target Files table "
            "(e.g. '01'). Not derived by this tool — supply it directly. "
            "Unknowns/risks mode: optional zero-padded sequence (e.g. '01') to "
            "retry after a collision, per skills/issue-to-plan/workflow.md "
            "Step 6 — omit for the first attempt."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    try:
        skeleton, output_path = _RENDERERS[args.kind](args, timestamp)
        _require(
            output_path.parent.exists(),
            f"target directory does not exist: {output_path.parent}",
        )
        collision = check_collision(output_path)
        _require(collision is None, f"output path already exists: {collision}")
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_path.write_text(skeleton, encoding="utf-8")
    print(f"Created {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
