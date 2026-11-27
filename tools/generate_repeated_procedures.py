#!/usr/bin/env python3
"""tools/generate_repeated_procedures.py
Write one implementation procedure per listed Plan row from one body template.

When several rows of a Plan's `Implementation Target Files` table need the same
small change, each row still needs its own procedure document. This tool writes
those documents from one body template that may use the placeholders `{path}`,
`{name}` (base name), `{seq}`, and `{timestamp}`. Each document keeps its own file
(`implementations/{timestamp}_{seq}_{target_file_slug}.md`, the same name
`tools/generate_workitem.py` assigns: the Plan's shared pass timestamp and the
row's 1-indexed position in the table) and its own `## Traceability` block, which
the tool fills from the Plan.

The tool refuses, and writes nothing, when:

- a listed path is not a row of the Plan, or is listed twice;
- an output path (or its `done/` counterpart) already exists;
- the template contains a `## Traceability` heading or an unknown placeholder;
- the `Change Responsibility` texts of the listed rows differ after replacing each
  row's own path and base name with `{path}` and `{name}`.

After writing, `tools/check_workitem_structure.py --file` runs on every created
document and its result is printed. `tools/stale_detector.py` is still to be run on
each document. `--dry-run` writes nothing, including the Plan's timestamp marker.

Usage:
    python tools/generate_repeated_procedures.py plans/<plan>.md \\
        --rows <path> [<path> ...] --body-template <file> [--dry-run] [--root DIR]

Exit codes: 0 success; 1 refusal or a failed structure check; 2 usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — fixed argv, no shell, standard input closed
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tools.generate_workitem as gw
from tools._atomic_write import add_dry_run_argument, atomic_write_text

ROOT_DIR = Path(__file__).resolve().parent.parent

ALLOWED_PLACEHOLDERS = frozenset({"path", "name", "seq", "timestamp"})
_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_SOURCE_ISSUE_RE = re.compile(r"^- \*\*Source issue\*\*: (.+)$", re.MULTILINE)
_TRACEABILITY_HEADING_RE = re.compile(r"^## Traceability\s*$", re.MULTILINE)
_BLANK_CELLS = {"", "—", "-", "–"}


@dataclass(frozen=True)
class PlanRow:
    path: str
    responsibility: str
    requirement: str


def _cells(line: str) -> list[str]:
    return [c.strip() for c in _CELL_SPLIT.split(line.strip().strip("|"))]


def parse_rows(plan_text: str) -> list[PlanRow]:
    """Rows of `## Implementation Target Files` with their change and requirement."""
    rows: list[PlanRow] = []
    in_section = False
    seen = 0
    for line in plan_text.splitlines():
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == "## Implementation Target Files"
            continue
        if not (in_section and line.startswith("|")):
            continue
        seen += 1
        if seen <= 2:  # header and separator
            continue
        cells = _cells(line)
        path = cells[0].strip("`").strip()
        if path in _BLANK_CELLS:
            continue
        rows.append(
            PlanRow(
                path,
                cells[1] if len(cells) > 1 else "",
                cells[3] if len(cells) > 3 else "",
            )
        )
    return rows


def normalize_change(responsibility: str, path: str) -> str:
    """Replace the row's own path and base name with placeholders, collapse spaces."""
    text = responsibility.replace(path, "{path}")
    text = text.replace(Path(path).name, "{name}")
    return " ".join(text.split())


def check_request(
    rows: list[PlanRow], listed: list[str], template: str, timestamp: str
) -> list[str]:
    """Return every reason to refuse; an empty list means the request may proceed."""
    problems: list[str] = []
    by_path = {row.path: row for row in rows}
    for path in listed:
        if path not in by_path:
            problems.append(f"{path} is not a row of the Plan's target files")
    for path in sorted({p for p in listed if listed.count(p) > 1}):
        problems.append(f"{path} is listed more than once")
    if _TRACEABILITY_HEADING_RE.search(template):
        problems.append("the template must not contain a '## Traceability' heading")
    for name in sorted(set(_PLACEHOLDER_RE.findall(template)) - ALLOWED_PLACEHOLDERS):
        problems.append(f"unknown placeholder {{{name}}} in the template")
    known = [by_path[p] for p in listed if p in by_path]
    if known:
        first = known[0]
        base = normalize_change(first.responsibility, first.path)
        for row in known[1:]:
            text = normalize_change(row.responsibility, row.path)
            if text != base:
                problems.append(
                    f"Change Responsibility of {row.path} differs from {first.path}: "
                    f"'{text}' vs '{base}'"
                )
    for index, row in enumerate(rows, start=1):
        if row.path not in listed:
            continue
        out = gw.implementation_procedure_output_path(
            timestamp, f"{index:02d}", row.path
        )
        existing = gw.check_collision(out)
        if existing is not None:
            problems.append(f"output already exists: {existing}")
    return problems


def render_document(
    template: str,
    row: PlanRow,
    seq: str,
    timestamp: str,
    source_issue: str,
    plan_rel: str,
) -> str:
    """Fill the template placeholders and append the row's Traceability block."""
    body = template
    for key, value in (
        ("path", row.path),
        ("name", Path(row.path).name),
        ("seq", seq),
        ("timestamp", timestamp),
    ):
        body = body.replace("{" + key + "}", value)
    trace = (
        "\n## Traceability\n"
        "- **Workflow phase**: plan-to-implementation-procedure\n"
        f"- **Requirement ID**: {row.requirement}\n"
        f"- **Source issue**: {source_issue}\n"
        "- **Source requirement**: N/A: no standalone requirement document is "
        "generated\n"
        f"- **Source plan**: {plan_rel}\n"
        "- **Source implementation procedure**: N/A: this document is the generated "
        "implementation procedure\n"
        f"- **Generated at**: {timestamp}\n"
        f"- **Related target files**: `{row.path}`\n"
    )
    return body.rstrip("\n") + "\n" + trace


def _structure_check(root: Path, doc: Path) -> int:
    completed = subprocess.run(  # nosec B603 — fixed argv, no shell
        [
            sys.executable,
            str(root / "tools" / "check_workitem_structure.py"),
            "--file",
            str(doc),
        ],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
        cwd=root,
    )
    print(f"{doc.name}: {(completed.stdout + completed.stderr).strip()}")
    return completed.returncode


def run(
    plan: Path, rows_arg: list[str], template_file: Path, root: Path, dry_run: bool
) -> int:
    plan_text = plan.read_text(encoding="utf-8")
    template = template_file.read_text(encoding="utf-8")
    rows = parse_rows(plan_text)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    # A dry-run lookup reads an existing marker and never writes one.
    timestamp = gw.find_or_record_pass_timestamp(plan, stamp, True)
    problems = check_request(rows, rows_arg, template, timestamp)
    if problems:
        for problem in problems:
            print(f"refused: {problem}", file=sys.stderr)
        return 1
    timestamp = gw.find_or_record_pass_timestamp(plan, stamp, dry_run)
    issue_match = _SOURCE_ISSUE_RE.search(plan_text)
    source_issue = issue_match.group(1).strip() if issue_match else "N/A: not recorded"
    try:
        plan_rel = plan.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        plan_rel = plan.as_posix()
    created: list[Path] = []
    for index, row in enumerate(rows, start=1):
        if row.path not in rows_arg:
            continue
        seq = f"{index:02d}"
        out = gw.implementation_procedure_output_path(timestamp, seq, row.path)
        if dry_run:
            print(f"would create {out}")
            continue
        text = render_document(template, row, seq, timestamp, source_issue, plan_rel)
        atomic_write_text(out, text)
        created.append(out)
    if dry_run:
        return 0
    failed = sum(1 for doc in created if _structure_check(root, doc) != 0)
    print(
        f"created {len(created)} document(s); run tools/stale_detector.py on each "
        "document next"
    )
    return 1 if failed else 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write one procedure per listed Plan row from one body template."
    )
    parser.add_argument("plan", type=Path, help="plans/<plan>.md")
    parser.add_argument("--rows", nargs="+", required=True, help="Plan row paths")
    parser.add_argument("--body-template", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="Repository root")
    add_dry_run_argument(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    for label, path in (("plan", args.plan), ("template", args.body_template)):
        if not path.is_file():
            print(f"error: {label} is not a file: {path}", file=sys.stderr)
            return 2
    return run(args.plan, args.rows, args.body_template, args.root, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
