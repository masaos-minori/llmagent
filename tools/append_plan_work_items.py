#!/usr/bin/env python3
"""Verify a procedure pass against its Plan and write the Work Items Created rows.

For a pass prefix and a Plan:

  1. Parse the Plan's `Implementation Target Files` rows and its `Implementation steps`
     phase citations.
  2. Map each generated document under `implementations/` to exactly one target row by its
     `Implementation > Target file`; check the coverage rules the workflow requires: one
     document per code or standalone row, companion rows covered by their owner's document,
     no document naming more than one target file, no companion also targeted or companioned
     elsewhere, and every document's Execution Status steps `Pending`.
  3. Print one Work Items Created row per generated document in `seq` order, where Related
     Step is the phase(s) citing that row, and write them into the Plan, replacing the
     placeholder row.

Coverage rules are checked before any write; a failure prints the findings and writes
nothing. Pass `--dry-run` to report without writing.

Usage:
    uv run python tools/append_plan_work_items.py 20261124-122732 plans/x.md
    uv run python tools/append_plan_work_items.py 20261124-122732 plans/x.md --dry-run

Exit codes:
    0  Coverage holds (rows printed, and written unless --dry-run)
    1  A coverage rule failed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPL_DIR = REPO_ROOT / "implementations"

WORK_ITEMS_HEADER = "### Work Items Created"
PLACEHOLDER_ROW = "| — | — | — | — | — | — |"
DOC_TARGET_RE = re.compile(r"^### Target file\n`(?P<path>[^`]+)`", re.MULTILINE)
DOC_RELEASE_UNIT_RE = re.compile(
    r"^\*\*Release unit\*\*: .+? \(Phase (\d+)\)", re.MULTILINE
)
PATH_RE = r"(?:scripts|tests|docs|config|registry|tools|templates)/[^\s;),\`]+"


class DocInfo(TypedDict):
    name: str
    target: str
    companions: list[str]
    statuses: list[str]
    phase: int | None


def parse_target_rows(plan_text: str) -> list[dict[str, str]]:
    """Return one dict per `Implementation Target Files` row, in table order."""
    lines = plan_text.splitlines()
    start = _section(lines, "## Implementation Target Files")
    rows: list[dict[str, str]] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 7 or cols[0] == "File Path":
            continue
        rows.append({"seq": str(len(rows) + 1), "path": cols[0]})
    return rows


def parse_phase_citations(plan_text: str) -> dict[str, list[int]]:
    """Map a target-file path to the phase numbers that cite it."""
    lines = plan_text.splitlines()
    start = _section(lines, "## Implementation steps")
    cited: dict[str, list[int]] = {}
    current = 0
    for line in lines[start + 1 :]:
        if line.startswith("#"):
            break
        match = re.match(r"^ ?(\d+)\. \*\*Phase", line)
        if match:
            current = int(match.group(1))
            continue
        if not current:
            continue
        for path in re.findall(PATH_RE, line):
            cited.setdefault(path, [])
            if current not in cited[path]:
                cited[path].append(current)
    return cited


def parse_generated_docs(prefix: str) -> dict[str, DocInfo]:
    """Return each generated document's target path, companions, and step statuses."""
    docs: dict[str, DocInfo] = {}
    for doc in sorted(IMPL_DIR.glob(f"{prefix}_*.md")):
        text = doc.read_text(encoding="utf-8")
        target = DOC_TARGET_RE.search(text)
        if not target:
            raise SystemExit(f"{doc}: no Target file section")
        companions = _companion_paths(text)
        statuses = _execution_statuses(doc, text)
        release = DOC_RELEASE_UNIT_RE.search(text)
        docs[str(int(doc.name.split("_")[1]))] = {
            "name": doc.name,
            "target": target.group("path"),
            "companions": companions,
            "statuses": statuses,
            "phase": int(release.group(1)) if release else None,
        }
    return docs


def _companion_paths(text: str) -> list[str]:
    """Return the paths named in the document's Companion test files section."""
    paths: list[str] = []
    started = False
    for line in text.splitlines():
        if line.startswith("### Companion test files"):
            started = True
            continue
        if not started:
            continue
        if line.startswith("## ") or line.startswith("### "):
            break
        match = re.match(r"- `(?P<path>[^`]+)`", line)
        if not match:
            continue
        paths.append(match.group("path"))
    return paths


def _execution_statuses(doc: Path, text: str) -> list[str]:
    """Return the Status column of the document's Execution Status table rows."""
    statuses: list[str] = []
    started = False
    for line in text.splitlines():
        if line.startswith("### Execution Status"):
            started = True
            continue
        if line.startswith("#"):
            break
        if not started or not line.startswith("| "):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 3 or not cols[0].isdigit():
            continue
        statuses.append(cols[2])
    return statuses


def _section(lines: list[str], heading: str) -> int:
    for i, line in enumerate(lines):
        if line.startswith(heading):
            return i
    raise SystemExit(f"plan has no {heading} section")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prefix")
    parser.add_argument("plan")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    plan_text = plan_path.read_text(encoding="utf-8")
    rows = parse_target_rows(plan_text)
    phases = parse_phase_citations(plan_text)
    docs = parse_generated_docs(args.prefix)

    findings: list[str] = []
    owner_of: dict[str, str] = {}
    for seq, doc in docs.items():
        if len(doc["companions"]) > 1:
            findings.append(f"{doc['name']}: more than one companion")
        for comp in doc["companions"]:
            if comp in owner_of:
                findings.append(f"{comp}: companion of rows {owner_of[comp]} and {seq}")
            owner_of[comp] = seq
        if any(s != "Pending" for s in doc["statuses"]):
            findings.append(f"{doc['name']}: Execution Status step not Pending")

    uncovered = []
    for row in rows:
        if row["seq"] in docs:
            doc = docs[row["seq"]]
            if doc["target"] != row["path"]:
                findings.append(f"row {row['seq']}: document targets {doc['target']}")
            cited = phases.get(row["path"], [])
            if doc["phase"] is None:
                findings.append(f"{doc['name']}: no phase cites this row")
            elif doc["phase"] not in cited:
                findings.append(
                    f"{doc['name']}: names Phase {doc['phase']}, the plan cites it in {cited}"
                )
            continue
        if row["path"] in owner_of:
            continue
        uncovered.append(f"{row['seq']} {row['path']}")
    if uncovered:
        findings.append("rows with no document: " + ", ".join(uncovered))
    for seq, doc in docs.items():
        if doc["target"] not in {r["path"] for r in rows}:
            findings.append(f"{doc['name']}: target is not a Plan row")

    if findings:
        print("\n".join(f"FINDING: {f}" for f in findings))
        return 1

    new_rows = []
    for seq in sorted(docs, key=int):
        doc = docs[seq]
        cited = sorted(phases.get(doc["target"], []))
        steps = ",".join(str(p) for p in cited) or "—"
        new_rows.append(
            f"| implementations/{doc['name']} | {steps} | Procedure | Pending | — | — |"
        )

    print(
        f"{len(rows)} rows, {len(docs)} documents, {len(owner_of)} companions covered: ok"
    )
    if args.dry_run:
        print("\n".join(new_rows))
        return 0

    lines = plan_text.splitlines()
    header = _section(lines, WORK_ITEMS_HEADER)
    for i in range(header, len(lines)):
        if lines[i].startswith(PLACEHOLDER_ROW):
            lines[i] = "\n".join(new_rows)
            break
    else:
        raise SystemExit("plan has no Work Items Created placeholder row")
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(new_rows)} Work Items Created rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
