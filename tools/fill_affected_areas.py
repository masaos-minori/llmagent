#!/usr/bin/env python3
"""tools/fill_affected_areas.py
Print the mechanical columns of a Plan's `Affected areas` table.

For every row of the Plan's `Implementation Target Files` table the tool computes:

- `Change`: `Create`, `Delete`, or `Modify`, from the row's `Change Responsibility`;
- `Churn (30d)`: commits of `git log --since=30.days HEAD -- <file>`;
- `Bus Factor`: `High (N% single author)` when one lowercased author name holds more
  than 70 percent of the file's commits, otherwise `Low (N% top author)`;
- `deploy.sh Impact`: from the rsync and `cp` facts of `deploy/deploy.sh`.

`Blast Radius` is a judgment and is always the placeholder `TODO: author judgment`.
For a `scripts/**/*.py` target a module size note (bytes and headroom against the
24576 B gate) is printed after the rows.

The tool is read-only unless `--insert` is given. `--insert` rewrites only the rows
of the `## Affected areas` table (a row that already names a target keeps its
`Blast Radius`; a missing target is appended) and never touches another section;
`--dry-run` prints the diff and writes nothing. Every git call closes standard
input and names `HEAD`, so the tool does not hang when standard input is not a
terminal.

Usage:
    python tools/fill_affected_areas.py plans/<plan>.md [--insert] [--dry-run]
        [--root DIR] [--since 30.days]

Exit codes: 0 success; 1 refusal (missing section, no target rows, git failure);
2 usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — fixed git argv, no shell, standard input closed
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run
from tools.amend_plan import Refusal, _first_cell, _row, _section, _table
from tools.check_module_size import DEFAULT_LIMIT

ROOT_DIR = Path(__file__).resolve().parent.parent

CHURN_SINCE = "30.days"
HIGH_SHARE = 0.70
PLACEHOLDER = "TODO: author judgment"
NEW = "N/A (new)"
NO_HISTORY = "N/A: no history"
RSYNCED_DIRS = ("scripts/", "tests/", "docs/", "registry/")
CREATE_HINTS = ("create", "new", "generated")
DELETE_HINTS = ("delete", "remove")

_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_PLACEHOLDER_FIRST_CELLS = {"", "—", "-", "–"}


@dataclass(frozen=True)
class Target:
    path: str
    responsibility: str


@dataclass(frozen=True)
class Computed:
    path: str
    change: str
    churn: str
    bus: str
    deploy: str


def _cells(line: str) -> list[str]:
    return [c.strip() for c in _CELL_SPLIT.split(line.strip().strip("|"))]


def change_kind(responsibility: str) -> str:
    """Return `Create`, `Delete`, or `Modify`; a create hint wins over a delete hint."""
    text = responsibility.lower()
    if any(hint in text for hint in CREATE_HINTS):
        return "Create"
    if any(hint in text for hint in DELETE_HINTS):
        return "Delete"
    return "Modify"


def parse_targets(lines: list[str]) -> list[Target]:
    """Read the `Implementation Target Files` rows (path and responsibility)."""
    start, end = _section(lines, "## Implementation Target Files")
    first, last = _table(lines, start, end, "Implementation Target Files")
    targets: list[Target] = []
    for idx in range(first + 2, last + 1):
        path = _first_cell(lines[idx])
        if path in _PLACEHOLDER_FIRST_CELLS:
            continue
        cells = _cells(lines[idx])
        targets.append(Target(path, cells[1] if len(cells) > 1 else ""))
    if not targets:
        raise Refusal("no target rows in Implementation Target Files")
    return targets


def git_log(root: Path, *args: str) -> str:
    """Run `git log` with standard input closed; raise `Refusal` on a git failure."""
    result = subprocess.run(  # nosec B603 B607 — fixed git argv, no shell
        ["git", "-C", str(root), "log", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise Refusal(f"git log failed: {result.stderr.strip()}")
    return result.stdout


def churn(root: Path, path: str, since: str) -> int:
    out = git_log(root, f"--since={since}", "--format=%H", "HEAD", "--", path)
    return len(out.split())


def bus_factor(names: list[str]) -> str:
    """Return the bus factor cell for a list of author names, one per commit."""
    counts = Counter(name.strip().lower() for name in names if name.strip())
    if not counts:
        return NO_HISTORY
    total = sum(counts.values())
    share = counts.most_common(1)[0][1] / total
    pct = round(share * 100)
    if share > HIGH_SHARE:
        return f"High ({pct}% single author)"
    return f"Low ({pct}% top author)"


def deploy_impact(path: str, change: str, deploy_text: str) -> str:
    """Return the `deploy.sh Impact` cell for a path, from `deploy/deploy.sh` text."""
    if path.startswith("config/") and path.endswith(".toml"):
        if change == "Create":
            return "add cp line"
        if change == "Delete":
            return "remove cp line"
        for number, line in enumerate(deploy_text.splitlines(), start=1):
            if line.lstrip().startswith("cp ") and path in line.replace(
                "${REPO_ROOT}/", ""
            ):
                return (
                    f"existing cp line at deploy/deploy.sh:{number}; no change needed"
                )
        return "Needs review: no cp line"
    if path.startswith(RSYNCED_DIRS):
        return "not applicable (rsynced)"
    return "not applicable (not rsynced)"


def size_note(root: Path, path: str) -> str | None:
    """Return a size note for a `scripts/**/*.py` target, else None."""
    if not (path.startswith("scripts/") and path.endswith(".py")):
        return None
    file = root / path
    if not file.exists():
        return f"{path}: new file, limit {DEFAULT_LIMIT} B"
    size = file.stat().st_size
    return f"{path}: {size} B, headroom {DEFAULT_LIMIT - size} B"


def compute(root: Path, target: Target, since: str, deploy_text: str) -> Computed:
    change = change_kind(target.responsibility)
    if change == "Create":
        churn_cell, bus_cell = NEW, NEW
    else:
        names = git_log(root, "--format=%an", "HEAD", "--", target.path).splitlines()
        if names:
            churn_cell = str(churn(root, target.path, since))
            bus_cell = bus_factor(names)
        else:
            churn_cell, bus_cell = NO_HISTORY, NO_HISTORY
    return Computed(
        target.path,
        change,
        churn_cell,
        bus_cell,
        deploy_impact(target.path, change, deploy_text),
    )


def render_row(item: Computed, blast: str = PLACEHOLDER) -> str:
    return _row(f"`{item.path}`", item.change, blast, item.churn, item.bus, item.deploy)


def insert_rows(lines: list[str], items: list[Computed]) -> list[str]:
    """Return the Plan lines with the `Affected areas` rows replaced or appended."""
    start, end = _section(lines, "## Affected areas")
    first, last = _table(lines, start, end, "Affected areas")
    by_path = {item.path: item for item in items}
    body: list[str] = []
    seen: set[str] = set()
    for idx in range(first + 2, last + 1):
        key = _first_cell(lines[idx])
        if key in _PLACEHOLDER_FIRST_CELLS:
            continue
        item = by_path.get(key)
        if item is None:
            body.append(lines[idx])
            continue
        cells = _cells(lines[idx])
        blast = cells[2] if len(cells) > 2 else PLACEHOLDER
        body.append(render_row(item, blast))
        seen.add(key)
    body.extend(render_row(i) for i in items if i.path not in seen)
    return lines[: first + 2] + body + lines[last + 1 :]


def run(plan: Path, root: Path, since: str, insert: bool, dry_run: bool) -> int:
    text = plan.read_text(encoding="utf-8")
    lines = text.split("\n")
    targets = parse_targets(lines)
    deploy_file = root / "deploy" / "deploy.sh"
    if not deploy_file.is_file():
        raise Refusal(f"missing {deploy_file}")
    deploy_text = deploy_file.read_text(encoding="utf-8")
    items = [compute(root, t, since, deploy_text) for t in targets]
    for item in items:
        print(render_row(item))
    notes = [n for t in targets if (n := size_note(root, t.path))]
    if notes:
        print("\nModule size notes:")
        for note in notes:
            print(f"- {note}")
    if not insert:
        return 0
    new_text = "\n".join(insert_rows(lines, items))
    if dry_run:
        print_dry_run(plan, text, new_text)
    elif new_text != text:
        atomic_write_text(plan, new_text)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print the mechanical Affected areas columns for a Plan."
    )
    parser.add_argument("plan", type=Path, help="plans/<plan>.md")
    parser.add_argument(
        "--insert",
        action="store_true",
        help="Write the rows into the Plan's Affected areas table (default: read-only)",
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="Repository root")
    parser.add_argument("--since", default=CHURN_SINCE, help="Churn window")
    add_dry_run_argument(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if not args.plan.is_file():
        print(f"error: not a file: {args.plan}", file=sys.stderr)
        return 2
    try:
        return run(args.plan, args.root, args.since, args.insert, args.dry_run)
    except Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
