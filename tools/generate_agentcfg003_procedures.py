#!/usr/bin/env python3
"""tools/generate_agentcfg003_procedures.py — Write the agentcfg003 procedure documents.

One implementation-procedure document per `Implementation Target Files` row of the Plan,
in the naming form `skills/plan-to-implementation-procedure/workflow.md` defines and under
the Plan's recorded implementation-procedure pass timestamp. Names and the shared pass timestamp
come from `tools/generate_workitem.py` so the naming rule is applied exactly as the workflow
defines it; this module only assembles the template order.

Field content is authored in the sibling private modules `tools/_agentcfg003_content_*`
(base defaults, shared, agent, producers, tests, docs), so a row's content stays readable as
prose rather than being mixed with the assembly logic here.

A test row is not given its own document when it is a companion of the single row that names
it in `Related Tests`; a test row named by more than one row, or one that names only itself,
keeps its own document (`tools/_agentcfg003_content_tests.py` `OWN_DOC`). Every row of this
Plan is covered by a document, so nothing is skipped as already existing.

Usage:
    python -m tools.generate_agentcfg003_procedures <plan.md> [--dry-run]

Output: one line per written document, then a count. Exit 0 when every row is written or
nothing needed to be written, 1 when a row has no authored content, 2 on a usage error. A dry
run prints the diff for each document and writes nothing.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict

# The agent and shared modules register their rows at import time, so they are imported for
# that side effect and their content is read through the base module's table.
import tools._agentcfg003_content_agent  # noqa: F401
import tools._agentcfg003_content_shared  # noqa: F401
from tools._agentcfg003_content_base import CONTENT as BASE_CONTENT
from tools._agentcfg003_content_docs import CONTENT as DOC_CONTENT
from tools._agentcfg003_content_producers import CONTENT as PRODUCER_CONTENT
from tools._agentcfg003_content_tests import COMPANIONS, OWN_DOC, TEST_CONTENT
from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run
from tools._tool_common import EXIT_ERROR, EXIT_FINDINGS, EXIT_OK
from tools.generate_workitem import (
    find_or_record_pass_timestamp,
    implementation_procedure_output_path,
)

REPO = Path(__file__).resolve().parent.parent

SOURCE_ISSUE = "issues/20261120-114211_agentcfg003_runtime-tool-metadata.md"

UNITS = {
    2: "contract-and-producers",
    3: "contract-and-producers",
    4: "contract-and-producers",
    5: "config-removal-and-tests",
    6: "config-removal-and-tests",
}
NO_UNIT = "N/A: not part of a release unit"

GATE = (
    "Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the "
    "reconciliation field values and the replay boundary are defined by that issue"
)

DEFAULT_STEPS: list[list[str]] = [
    [
        "1",
        "Implement the change described in Implementation > Procedure/Method/Details",
        "Pending",
        "—",
        "—",
        "release unit",
    ],
    ["2", "Add or update tests per Validation plan", "Pending", "—", "—", ""],
    [
        "3",
        "Run the validation sequence (`rules/toolchain.md`)",
        "Pending",
        "—",
        "—",
        "",
    ],
    [
        "4",
        "Update documentation, if in scope per Compatibility/Out of scope",
        "Pending",
        "—",
        "—",
        "",
    ],
]


class Row(TypedDict):
    seq: int
    path: str
    action: str
    req_ids: str
    tests: str


def parse_rows(plan: Path) -> list[Row]:
    """The `Implementation Target Files` rows, in table order."""
    rows: list[Row] = []
    for line in plan.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `") or "Related Requirement" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        rows.append(
            {
                "seq": len(rows) + 1,
                "path": cells[0].strip("`"),
                "action": cells[1],
                "req_ids": cells[3].split(" / ")[0].strip(),
                "tests": cells[5],
            }
        )
    return rows


def parse_phases(plan: Path) -> dict[str, int]:
    """First phase recorded for each target file in `### Requirement Traceability`."""
    phases: dict[str, int] = {}
    for line in plan.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| REQ-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 7:
            continue
        path = cells[2].strip("`")
        marker = cells[3]
        if marker.startswith("Phase ") and path not in phases:
            phases[path] = int(marker[6:].split(",")[0])
    return phases


def named_by(rows: list[Row], test_rows: set[str]) -> dict[str, list[int]]:
    """Test files named by other rows, with the rows that name them."""
    named: dict[str, list[int]] = {}
    for row in rows:
        for item in row["tests"].split(","):
            item = item.strip().strip("`").strip()
            if item and item != "this file" and item in test_rows:
                named.setdefault(item, []).append(row["seq"])
    return named


def companions_for(
    tests_cell: str, test_rows: set[str], named: dict[str, list[int]]
) -> list[str]:
    """Test files that are companions of this row rather than their own document."""
    out: list[str] = []
    for item in tests_cell.split(","):
        item = item.strip().strip("`").strip()
        if (
            item
            and item != "this file"
            and item in test_rows
            and len(named.get(item, [])) == 1
            and item not in OWN_DOC
        ):
            out.append(item)
    return out


def keeps_own_document(path: str, namers: list[int], test_rows: set[str]) -> bool:
    """Whether a test row needs a document of its own rather than being a companion.

    A companion is a `tests/` row named by exactly one other row. A row named by more than
    one row, or one that names only itself, is named by no other row, so it keeps its own
    document. `OWN_DOC` records the rows judged to need a design decision of their own,
    which is the third companion condition.
    """
    if path in OWN_DOC:
        return True
    return len(namers) != 1 and path in test_rows


def content_for(path: str) -> dict[str, object] | None:
    for table in (PRODUCER_CONTENT, BASE_CONTENT, TEST_CONTENT, DOC_CONTENT):
        if path in table:
            return table[path]
    return None


def text_of(value: object) -> str:
    return str(value)


def items_of(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def matrix_of(value: object) -> list[list[str]]:
    """A table's rows; a plain list of strings becomes one cell per row."""
    if not isinstance(value, list):
        return []
    rows: list[list[str]] = []
    for item in value:
        rows.append(
            [str(cell) for cell in item] if isinstance(item, list) else [str(item)]
        )
    return rows


def bullets(items: object) -> str:
    values = items_of(items)
    if not values:
        return "- N/A: not applicable to this row."
    return "\n".join(f"- {item}" for item in values)


def table(header: list[str], rows: list[list[str]]) -> str:
    out = "| " + " | ".join(header) + " |"
    out += "\n|" + "|".join("---" for _ in header) + "|"
    for row in rows:
        out += "\n| " + " | ".join(row) + " |"
    return out


def render(
    rec: Row,
    content: dict[str, object],
    comps: list[str],
    phase: int,
    plan_name: str,
    timestamp: str,
) -> str:
    path = rec["path"]
    unit = UNITS.get(phase, NO_UNIT)

    lines: list[str] = []
    lines.append("## Goal\n\n" + text_of(content.get("goal", "")))
    lines.append("\n## Scope\n**Release unit**: " + unit)
    lines.append("\n## Assumptions\n" + bullets(content.get("assumptions")))
    lines.append("\n## Design decisions\n" + bullets(content.get("design")))
    lines.append(
        "\n## Alternatives considered\n" + bullets(content.get("alternatives"))
    )
    lines.append(
        "\n## Implementation\n### Target file\n`"
        + path
        + ("` (new)" if "(new)" in rec["action"] else "`")
    )
    lines.append("### Procedure\n" + bullets(content.get("procedure")))
    lines.append("### Method\n" + bullets(content.get("method")))
    lines.append("### Details\n" + bullets(content.get("details")))
    if comps:
        block = ["### Companion test files"]
        for comp in comps:
            entry = COMPANIONS[comp]
            block.append(
                f"- `{comp}`" + (" (new)" if "(new)" in entry["action"] else "")
            )
            block.append(f"  - Procedure: {entry['procedure']}")
            block.append(f"  - Validation: {entry['validation']}")
        lines.append("\n".join(block))
    for section, key in (
        ("Compatibility considerations", "compat"),
        ("Security considerations", "security"),
        ("Rollback considerations", "rollback"),
        ("Validation plan", "validation"),
        ("Completion criteria", "completion"),
        ("Out of Scope", "out_of_scope"),
    ):
        lines.append(f"\n## {section}\n" + bullets(content.get(key)))

    # A copy, so the gate text is not written back into the shared default rows.
    steps = matrix_of(content.get("exec_steps")) or [list(row) for row in DEFAULT_STEPS]
    for step in steps:
        notes = (
            f"Phase {phase}; release unit: {unit}"
            if step[5] == "release unit"
            else step[5]
        )
        if step[2] == "Pending":
            notes = f"{GATE}{'; ' + notes if notes else ''}"
        step[5] = notes
    lines.append(
        "\n## Execution Status\n\n### Execution Status\n"
        + table(
            ["Step", "Description", "Status", "Started", "Completed", "Notes"], steps
        )
    )
    lines.append(
        "\n### Blocker Log\n"
        + table(
            ["Step", "Blocker Description", "Resolved", "Resolution Date"],
            matrix_of(content.get("blockers")) or [["—"] * 4],
        )
    )
    lines.append(
        "\n### Work Items Created\n"
        + table(
            ["Item ID", "Related Step", "Type", "Status", "Owner", "Due Date"],
            matrix_of(content.get("work_items")) or [["—"] * 6],
        )
    )

    related = [f"`{path}`"] + [f"`{comp}`" for comp in comps]
    lines.append(
        "\n## Traceability\n"
        + "\n".join(
            [
                "- **Workflow phase**: plan-to-implementation-procedure",
                f"- **Requirement ID**: {rec['req_ids']}",
                f"- **Source issue**: {SOURCE_ISSUE}",
                "- **Source requirement**: N/A: no standalone requirement document is generated",
                f"- **Source plan**: plans/{plan_name}",
                "- **Source implementation procedure**: N/A: this document is the generated implementation procedure",
                f"- **Generated at**: {timestamp}",
                "- **Related target files**: " + ", ".join(related),
            ]
        )
    )
    return "\n".join(lines) + "\n"


def build_documents(
    plan: Path, timestamp: str
) -> tuple[list[tuple[Path, str]], list[str]]:
    """The documents to write, and the rows that have no authored content."""
    rows = parse_rows(plan)
    test_rows = {row["path"] for row in rows if row["path"].startswith("tests/")}
    named = named_by(rows, test_rows)
    phases = parse_phases(plan)
    documents: list[tuple[Path, str]] = []
    missing: list[str] = []
    for row in rows:
        path = row["path"]
        # A test row gets its own document when it fails a companion condition: named by
        # more than one row, or needing a design decision of its own (`OWN_DOC`).
        if path in test_rows and not keeps_own_document(
            path, named.get(path, []), test_rows
        ):
            continue
        base_content = content_for(path)
        if base_content is None:
            missing.append(path)
            continue
        out_path = implementation_procedure_output_path(
            timestamp, f"{row['seq']:02d}", path
        )
        comps = companions_for(row["tests"], test_rows, named)
        documents.append(
            (
                out_path,
                render(
                    row, base_content, comps, phases.get(path, 0), plan.name, timestamp
                ),
            )
        )
    return documents, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write the implementation-procedure documents for one Plan."
    )
    parser.add_argument(
        "plan", help="Plan file under plans/ (its pass timestamp is reused)"
    )
    add_dry_run_argument(parser)
    args = parser.parse_args(argv)

    plan = Path(args.plan)
    if not plan.is_file():
        print(f"plan not found: {plan}", file=sys.stderr)
        return EXIT_ERROR

    # Reuse the Plan's recorded pass timestamp; a plan that has none yet gets one recorded
    # by tools/generate_workitem.py, as that module documents.
    timestamp = find_or_record_pass_timestamp(
        plan, datetime.now().strftime("%Y%m%d-%H%M%S"), dry_run=args.dry_run
    )

    documents, missing = build_documents(plan, timestamp)
    for path in missing:
        print(f"missing content: {path}", file=sys.stderr)
    if missing:
        return EXIT_FINDINGS
    if not documents:
        print("no rows to write")
        return EXIT_OK

    for out_path, text in documents:
        old = out_path.read_text(encoding="utf-8") if out_path.is_file() else ""
        if args.dry_run:
            print_dry_run(out_path, old, text)
            continue
        if old != text:
            atomic_write_text(out_path, text)
    print(f"generated {len(documents)} documents; pass timestamp {timestamp}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
