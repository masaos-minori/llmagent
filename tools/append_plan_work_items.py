#!/usr/bin/env python3
"""tools/append_plan_work_items.py — Append Work Items rows for generated procedures.

`skills/plan-to-implementation-procedure/workflow.md` Step 4 requires one
`### Work Items Created` row in the Plan for every implementation-procedure document the
pass generated: Item ID is the document path, Related Step is the `Implementation steps`
entry that cites its target file, Type is `Procedure`, Status is `Pending`. Writing that
row by hand for a whole batch is the same operation repeated once per document, so this
tool writes it from the documents themselves:

- The batch is the set of files under `implementations/` carrying the Plan's recorded
  implementation-procedure pass timestamp; `- **Source plan**:` must name the Plan, so a
  document of another pass is never added. The pass timestamp must already be recorded in
  the Plan; nothing is written to the Plan here except the table rows.
- Each document's target file is the first path in its `- **Related target files**:` line.
  The step is the `Implementation steps` entry whose text names that path; a path named
  only by a wildcard bullet ("every row ...") falls back to the phase recorded in
  `### Requirement Traceability`, which `issue-to-plan` Step 5 numbers the same as the
  Execution Status rows.
- A document already represented by an Item ID row is skipped, so a resumed pass appends
  only what is missing. No other column or section is written.

Usage:
    python -m tools.append_plan_work_items <plan.md> [--dry-run]

Output: one line per added row, then a count. Exit 0 when nothing needed to be added or
every document is represented, 1 when a document has no row or its step cannot be resolved
or the pass timestamp is absent, 2 on a usage error. A dry run prints the diff and writes
nothing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

if __package__ in (None, ""):
    sys.path.insert(0, str(REPO))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run
from tools._tool_common import EXIT_ERROR, EXIT_FINDINGS, EXIT_OK
from tools.generate_workitem import _PASS_TIMESTAMP_MARKER_RE, IMPLEMENTATIONS_DIR

WORK_ITEMS_HEADING = "### Work Items Created"
WORK_ITEM_TYPE = "Procedure"
WORK_ITEM_STATUS = "Pending"
EMPTY_CELL = "—"
SOURCE_PLAN_FIELD = "- **Source plan**:"
TARGET_FILES_FIELD = "- **Related target files**:"
PATH_PREFIXES = ("scripts/", "tests/", "config/", "registry/", "docs/")


def recorded_timestamp(text: str) -> str:
    """The pass timestamp already recorded in the Plan, or an empty string when absent."""
    for line in text.splitlines():
        match = _PASS_TIMESTAMP_MARKER_RE.match(line.strip())
        if match:
            return match.group(1)
    return ""


def step_map(text: str) -> dict[str, int]:
    """`target file path` to `Implementation steps` entry number, read from the steps section."""
    steps: dict[str, int] = {}
    lines = text[text.index("## Implementation steps") :].splitlines()
    step = 0
    for line in lines[1:]:
        # The steps list ends at the first heading after it.
        if line.startswith("#"):
            break
        stripped = line.strip()
        match = re.match(r"^(\d+)\. \*\*", stripped)
        if match:
            step = int(match.group(1))
            continue
        for cell in stripped.split("`")[1::2]:
            if cell.startswith(PATH_PREFIXES):
                steps.setdefault(cell, step)
    return steps


def traceability_phase(text: str) -> dict[str, int]:
    """Fallback `target file path` to step number from the Requirement Traceability table."""
    phases: dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("| REQ-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        path = cells[2].strip("`")
        marker = cells[3]
        if path not in phases:
            first = re.search(r"Phase (\d+)", marker)
            if first:
                phases[path] = int(first.group(1))
    return phases


def batch_documents(plan: Path, text: str, timestamp: str) -> list[Path]:
    """The procedure documents of this pass, in row order, that name the Plan as their source."""
    kept: list[Path] = []
    for doc in sorted(IMPLEMENTATIONS_DIR.glob(f"{timestamp}_*.md")):
        body = doc.read_text(encoding="utf-8")
        for line in body.splitlines():
            if line.startswith(SOURCE_PLAN_FIELD):
                value = line[len(SOURCE_PLAN_FIELD) :].strip()
                if Path(value).name == plan.name:
                    kept.append(doc)
                break
    return kept


def target_file(doc: Path) -> str:
    """First path of the document's Related target files line, which is its own target file."""
    for line in doc.read_text(encoding="utf-8").splitlines():
        if line.startswith(TARGET_FILES_FIELD):
            return line[len(TARGET_FILES_FIELD) :].split(",")[0].strip().strip("`")
    return ""


def table_data_rows(text: str, heading: str) -> list[list[str]]:
    """Data rows of the Markdown table under `heading`, in file order; the header row is skipped."""
    rows: list[list[str]] = []
    inside = False
    header_seen = False
    for line in text.splitlines():
        if line.strip() == heading:
            inside, header_seen = True, False
            continue
        if not inside:
            continue
        if line.startswith("## "):
            break
        if not line.startswith("| "):
            continue
        if not header_seen:
            header_seen = True
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def insert_rows(text: str, rows: list[list[str]]) -> str:
    """Append the rows after the last data row of the Work Items Created table."""
    lines = text.splitlines()
    position = None
    for index, line in enumerate(lines):
        if line.strip() == WORK_ITEMS_HEADING:
            position = index
        elif (
            line.startswith("| ")
            and position is not None
            and not set(line) <= set("|- ")
        ):
            position = index
        elif line.startswith("## ") and position is not None:
            break
    if position is None:
        raise ValueError(f"{WORK_ITEMS_HEADING} not found")
    appended = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines[: position + 1] + appended + lines[position + 1 :]) + "\n"


def build_rows(
    plan: Path, text: str, timestamp: str
) -> tuple[list[list[str]], list[str]]:
    """The rows to append, and the documents that cannot be represented."""
    steps = step_map(text)
    phases = traceability_phase(text)
    known = {row[0] for row in table_data_rows(text, WORK_ITEMS_HEADING)}
    rows: list[list[str]] = []
    unresolved: list[str] = []
    for doc in batch_documents(plan, text, timestamp):
        item_id = f"implementations/{doc.name}"
        if item_id in known:
            continue
        path = target_file(doc)
        step = steps.get(path) or phases.get(path)
        if not path or not step:
            unresolved.append(item_id)
            continue
        rows.append(
            [
                item_id,
                str(step),
                WORK_ITEM_TYPE,
                WORK_ITEM_STATUS,
                EMPTY_CELL,
                EMPTY_CELL,
            ]
        )
    return rows, unresolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append Work Items rows for generated procedures."
    )
    parser.add_argument(
        "plan",
        help="Plan file under plans/ (the pass timestamp must already be recorded)",
    )
    add_dry_run_argument(parser)
    args = parser.parse_args(argv)

    plan = Path(args.plan)
    if not plan.is_file():
        print(f"plan not found: {plan}", file=sys.stderr)
        return EXIT_ERROR

    text = plan.read_text(encoding="utf-8")
    timestamp = recorded_timestamp(text)
    if not timestamp:
        print(
            "no implementation-procedure pass timestamp recorded in the plan",
            file=sys.stderr,
        )
        return EXIT_FINDINGS

    rows, unresolved = build_rows(plan, text, timestamp)
    for item in unresolved:
        print(f"unresolved step: {item}", file=sys.stderr)
    if unresolved:
        return EXIT_FINDINGS
    if not rows:
        print("no rows to add; every document of the pass is already recorded")
        return EXIT_OK

    new = insert_rows(text, rows)
    if args.dry_run:
        print_dry_run(plan, text, new)
        return EXIT_OK
    atomic_write_text(plan, new)
    for row in rows:
        print(f"added: {row[0]} -> step {row[1]}")
    print(f"{len(rows)} rows added to {plan}")
    return EXIT_FINDINGS if unresolved else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
