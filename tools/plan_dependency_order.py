"""tools/plan_dependency_order.py
Reads the Plan-to-Plan dependencies of the open Plans (`plans/*.md`, never
`plans/done/`), builds the dependency graph, detects cycles, prints a recommended
order, and reports each open Plan as `ready` or `gated` with the blocking item.

A dependency is one bullet (top-level or nested under `Dependencies`) in the Plan's
`## Scope` section:

    - **Depends on**: {path} | phase {N or all} | {reason}

`{path}` is a Plan (`plans/...`) or an Issue (`issues/...`). A Plan without such a
bullet is read through a fallback: every `plans/` or `issues/` path found in its
free-text `- **Dependencies**:` bullet becomes a dependency with phase `all`, and a
`prose-dependency` warning is emitted for it.

Readiness of one dependency:
- closed: the Issue is in `issues/done/`, the Plan is in `plans/done/`, or the named
  phase row of the depended-on open Plan's `### Execution Status` is `Completed`.
- open: the Issue is still in `issues/`, or the depended-on Plan is still in `plans/`
  and the phase is `all` or its row is not `Completed`.
- unresolvable: the path cannot be found, escapes the repository, or the phase row
  cannot be matched; reported as `Needs confirmation` and it does not gate by itself.

A Plan with any open dependency is `gated`; otherwise it is `ready`.

Shared target files (the data of `tools/check_plan_target_overlaps.py`) are shown as
`overlap` notes only. They are never ordering edges: this tool may not infer an order
the owner has not stated. The result is a recommendation; the owner decides the order.

Never writes, renames, moves, or deletes anything and makes no network access.

`--plan` also accepts a Plan already archived in `plans/done/`: only that Plan's own
readiness is reported (it is not part of the order).

Usage:
    python tools/plan_dependency_order.py
    python tools/plan_dependency_order.py --plan plans/20260101-000000_x_plan.md
    python tools/plan_dependency_order.py --format json
    python tools/plan_dependency_order.py --root <dir>

Exit code: 0 on a completed run, including gated Plans, warnings, and cycles
(report-only). 1 only for a missing `--plan` path or an unreadable `plans/` directory.
"""

from __future__ import annotations

import argparse
import heapq
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.check_plan_target_overlaps import (
    PlanDocument,
    extract_freeze_status,
    extract_target_file_rows,
    find_cross_plan_target_overlaps,
)
from tools.manage_workitem_stage import parse_execution_status_rows

ROOT_DIR = Path(__file__).resolve().parent.parent

HEADER = (
    "Recommended order only. The owner decides the order; this tool never "
    "reorders or edits a document."
)

_SCOPE_HEADING_RE = re.compile(r"(?m)^## Scope\s*$")
_NEXT_HEADING_RE = re.compile(r"(?m)^## ")
_STRUCTURED_RE = re.compile(
    r"(?m)^[ \t]*- \*\*Depends on\*\*:\s*`?(\S+?)`?\s*\|\s*phase\s+`?(\S+?)`?\s*\|\s*(.+?)\s*$"
)
_DEPENDENCIES_BULLET_RE = re.compile(r"(?m)^- \*\*Dependencies\*\*:")
_TOP_BULLET_RE = re.compile(r"(?m)^- ")
_PROSE_PATH_RE = re.compile(r"\b((?:plans|issues)/[\w./-]+\.md)")
_ALLOWED_TOP_DIRS = frozenset({"plans", "issues"})

CLOSED = "closed"
OPEN = "open"
UNRESOLVABLE = "unresolvable"


@dataclass(frozen=True)
class Dependency:
    path: str
    phase: int | str
    reason: str
    declared: bool


@dataclass(frozen=True)
class PlanNode:
    path: str
    dependencies: tuple[Dependency, ...]
    targets: tuple[str, ...]
    steps: dict[str, str]
    is_frozen: bool


@dataclass
class Readiness:
    plan: str
    status: str  # "ready" | "gated"
    label: str  # "ready" | "gated" | "gated (prose)"
    blocking: list[str] = field(default_factory=list)
    confirmations: list[str] = field(default_factory=list)


def _section_text(text: str, heading_re: re.Pattern[str]) -> str | None:
    match = heading_re.search(text)
    if match is None:
        return None
    start = match.end()
    following = _NEXT_HEADING_RE.search(text, start)
    return text[start : following.start() if following else len(text)]


def _parse_phase(raw: str) -> int | str:
    return int(raw) if raw.isdigit() else raw


def parse_dependencies(plan_text: str) -> tuple[list[Dependency], list[str]]:
    """Return the dependencies declared in a Plan's `## Scope` and the warnings.

    A structured `**Depends on**` bullet wins. Without one, every `plans/` or
    `issues/` path in the `- **Dependencies**:` bullet (and its continuation lines)
    is a dependency with phase `all`, `declared=False`, and a warning message
    starting `prose-dependency:`. The caller prefixes the Plan name.
    """
    scope = _section_text(plan_text, _SCOPE_HEADING_RE)
    if scope is None:
        return [], []

    structured = [
        Dependency(
            path=match.group(1),
            phase=_parse_phase(match.group(2)),
            reason=match.group(3),
            declared=True,
        )
        for match in _STRUCTURED_RE.finditer(scope)
    ]
    if structured:
        return structured, []

    bullet = _DEPENDENCIES_BULLET_RE.search(scope)
    if bullet is None:
        return [], []
    following = _TOP_BULLET_RE.search(scope, bullet.end())
    bullet_text = scope[bullet.end() : following.start() if following else len(scope)]

    dependencies: list[Dependency] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for path in _PROSE_PATH_RE.findall(bullet_text):
        if path in seen:
            continue
        seen.add(path)
        dependencies.append(Dependency(path, "all", "prose", declared=False))
        warnings.append(f"prose-dependency: {path}")
    return dependencies, warnings


def _step_statuses(text: str) -> dict[str, str]:
    rows = parse_execution_status_rows(text)
    if not rows:
        return {}
    return {row.get("Step", ""): row.get("Status", "") for row in rows}


def _load_node(root: Path, md_path: Path) -> tuple[PlanNode, list[str]]:
    text = md_path.read_text(encoding="utf-8")
    rel_path = md_path.relative_to(root).as_posix()
    dependencies, dep_warnings = parse_dependencies(text)
    node = PlanNode(
        path=rel_path,
        dependencies=tuple(dep for dep in dependencies if dep.path != rel_path),
        targets=tuple(extract_target_file_rows(text)),
        steps=_step_statuses(text),
        is_frozen=extract_freeze_status(text) == "Frozen",
    )
    return node, [f"{rel_path}: {warning}" for warning in dep_warnings]


def load_plans(root: Path) -> tuple[list[PlanNode], list[str]]:
    """Parse every open Plan (`plans/*.md`, never `plans/done/`) under `root`."""
    nodes: list[PlanNode] = []
    warnings: list[str] = []
    for md_path in sorted((root / "plans").glob("*.md")):
        node, node_warnings = _load_node(root, md_path)
        nodes.append(node)
        warnings.extend(node_warnings)
    return nodes, warnings


def _safe_file(root: Path, rel: str) -> Path | None:
    """Resolve `rel` under `root`; None when it escapes or leaves plans/issues."""
    candidate = (root / rel).resolve()
    try:
        parts = candidate.relative_to(root.resolve()).parts
    except ValueError:
        return None
    if not parts or parts[0] not in _ALLOWED_TOP_DIRS:
        return None
    return candidate


def resolve_dependency(
    dep: Dependency, root: Path, plans: dict[str, PlanNode]
) -> tuple[str, str]:
    """Return `(state, detail)`; state is closed, open, or unresolvable."""
    target = _safe_file(root, dep.path)
    if target is None:
        return UNRESOLVABLE, f"{dep.path} is outside plans/ and issues/"

    parts = Path(dep.path).parts
    if len(parts) >= 2 and parts[1] == "done":
        if target.is_file():
            return CLOSED, dep.path
        return UNRESOLVABLE, f"{dep.path} not found"

    done_path = Path(parts[0]) / "done" / Path(*parts[1:])
    if parts[0] == "issues":
        if target.is_file():
            return OPEN, dep.path
        if (root / done_path).is_file():
            return CLOSED, done_path.as_posix()
        return UNRESOLVABLE, f"{dep.path} not found"

    # parts[0] == "plans": a Plan, open while it is still in plans/.
    node = plans.get(dep.path)
    if node is None or not target.is_file():
        if (root / done_path).is_file():
            return CLOSED, done_path.as_posix()
        return UNRESOLVABLE, f"{dep.path} not found"
    if isinstance(dep.phase, int):
        status = node.steps.get(str(dep.phase))
        if status is None:
            return UNRESOLVABLE, f"{dep.path} has no Execution Status row {dep.phase}"
        return (CLOSED if status == "Completed" else OPEN), dep.path
    return OPEN, dep.path


def _edges(nodes: list[PlanNode]) -> dict[str, list[str]]:
    """Map each open Plan to the open Plans it depends on (declared and prose)."""
    known = {node.path for node in nodes}
    return {
        node.path: sorted({d.path for d in node.dependencies if d.path in known})
        for node in nodes
    }


def find_cycles(nodes: list[PlanNode]) -> list[list[str]]:
    """Return each dependency cycle among open Plans as an ordered path list."""
    edges = _edges(nodes)
    cycles: list[list[str]] = []
    seen_cycles: set[frozenset[str]] = set()
    done: set[str] = set()

    def visit(current: str, stack: list[str]) -> None:
        if current in stack:
            cycle = stack[stack.index(current) :]
            key = frozenset(cycle)
            if key not in seen_cycles:
                seen_cycles.add(key)
                cycles.append([*cycle, current])
            return
        if current in done:
            return
        for nxt in edges.get(current, []):
            visit(nxt, [*stack, current])
        done.add(current)

    for node in nodes:
        visit(node.path, [])
    return cycles


def recommended_order(nodes: list[PlanNode]) -> tuple[list[str], list[str]]:
    """Return `(order, cyclic)`: dependency-first order, ties by filename.

    Plans that are part of, or wait on, a cycle are appended last (sorted) and
    also returned in `cyclic`.
    """
    edges = _edges(nodes)
    pending = {path: set(deps) for path, deps in edges.items()}
    dependents: dict[str, list[str]] = {path: [] for path in edges}
    for path, deps in edges.items():
        for dep in deps:
            dependents[dep].append(path)

    heap = [path for path, deps in pending.items() if not deps]
    heapq.heapify(heap)
    order: list[str] = []
    while heap:
        current = heapq.heappop(heap)
        order.append(current)
        for follower in dependents[current]:
            pending[follower].discard(current)
            if not pending[follower] and follower not in order:
                heapq.heappush(heap, follower)
    cyclic = sorted(path for path in edges if path not in order)
    return [*order, *cyclic], cyclic


def readiness(node: PlanNode, root: Path, plans: dict[str, PlanNode]) -> Readiness:
    """Classify one Plan as `ready` or `gated`, naming the blocking item."""
    blocking: list[str] = []
    confirmations: list[str] = []
    open_deps: list[Dependency] = []
    for dep in node.dependencies:
        state, detail = resolve_dependency(dep, root, plans)
        if state == OPEN:
            open_deps.append(dep)
            blocking.append(f"{dep.path} phase {dep.phase}")
        elif state == UNRESOLVABLE:
            confirmations.append(
                f"Needs confirmation: {dep.path} phase {dep.phase} ({detail})"
            )
    if not open_deps:
        return Readiness(node.path, "ready", "ready", [], confirmations)
    label = "gated" if any(dep.declared for dep in open_deps) else "gated (prose)"
    return Readiness(node.path, "gated", label, blocking, confirmations)


def find_overlaps(nodes: list[PlanNode]) -> list[dict[str, str]]:
    """Shared target files among Frozen open Plans (notes only, never edges)."""
    documents = [
        PlanDocument(
            path=Path(node.path),
            rel_path=node.path,
            is_frozen=node.is_frozen,
            target_files=list(node.targets),
        )
        for node in nodes
    ]
    return find_cross_plan_target_overlaps(documents)


@dataclass
class Report:
    order: list[str]
    cyclic: list[str]
    results: list[Readiness]
    cycles: list[list[str]]
    overlaps: list[dict[str, str]]
    warnings: list[str]


def build_report(root: Path, only_plan: str | None = None) -> Report:
    nodes, warnings = load_plans(root)
    plans = {node.path: node for node in nodes}
    order, cyclic = recommended_order(nodes)
    results = [readiness(plans[path], root, plans) for path in order]
    cycles = find_cycles(nodes)
    overlaps = find_overlaps(nodes)
    if only_plan is not None:
        results = [r for r in results if r.plan == only_plan]
        warnings = [w for w in warnings if w.startswith(f"{only_plan}:")]
        archived = root / only_plan
        if only_plan not in plans and archived.is_file():
            # An archived Plan (plans/done/) is not part of the order, but its own
            # dependencies can still be gated (code-implementation Step 1).
            node, node_warnings = _load_node(root, archived)
            results = [readiness(node, root, plans)]
            warnings = node_warnings
    return Report(order, cyclic, results, cycles, overlaps, warnings)


def render_text(report: Report) -> str:
    lines = [HEADER, "", "Recommended order:"]
    lines.extend(
        f"  {i}. {path}{' (cycle)' if path in report.cyclic else ''}"
        for i, path in enumerate(report.order, 1)
    )
    if not report.order:
        lines.append("  (no open Plans)")
    lines += ["", "Ready:"]
    ready = [r for r in report.results if r.status == "ready"]
    lines.extend(f"  {r.plan}" for r in ready)
    if not ready:
        lines.append("  (none)")
    lines += ["", "Gated:"]
    gated = [r for r in report.results if r.status == "gated"]
    lines.extend(
        f"  {r.plan}: {r.label}, blocked by {'; '.join(r.blocking)}" for r in gated
    )
    if not gated:
        lines.append("  (none)")
    confirmations = [(r.plan, c) for r in report.results for c in r.confirmations]
    if confirmations:
        lines += ["", "Needs confirmation:"]
        lines.extend(f"  {plan}: {text}" for plan, text in confirmations)
    if report.cycles:
        lines += ["", "Cycles:"]
        lines.extend(f"  cycle: {' -> '.join(cycle)}" for cycle in report.cycles)
    if report.overlaps:
        lines += ["", "Overlap notes (not ordering edges):"]
        lines.extend(f"  overlap: {o['file']}: {o['detail']}" for o in report.overlaps)
    if report.warnings:
        lines += ["", "Warnings:"]
        lines.extend(f"  {warning}" for warning in report.warnings)
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    payload = {
        "header": HEADER,
        "order": report.order,
        "cyclic": report.cyclic,
        "results": [
            {
                "plan": r.plan,
                "status": r.status,
                "label": r.label,
                "blocking": r.blocking,
                "confirmations": r.confirmations,
            }
            for r in report.results
        ],
        "cycles": report.cycles,
        "overlaps": report.overlaps,
        "warnings": report.warnings,
    }
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only: compute the dependency order and ready/gated state of "
            "the open Plans in plans/. Recommends; the owner decides the order."
        )
    )
    parser.add_argument(
        "--plan", default=None, help="Report only this Plan (path under the root)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT_DIR),
        help="Repository root holding plans/ and issues/ (default: this repository)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not (root / "plans").is_dir():
        print(f"error: {root / 'plans'} is not a readable directory", file=sys.stderr)
        return 1

    only_plan: str | None = None
    if args.plan is not None:
        plan_path = Path(args.plan)
        if not plan_path.is_absolute():
            plan_path = root / plan_path
        if not plan_path.is_file():
            print(f"error: Plan not found: {args.plan}", file=sys.stderr)
            return 1
        try:
            only_plan = plan_path.resolve().relative_to(root).as_posix()
        except ValueError:
            print(f"error: Plan is outside the root: {args.plan}", file=sys.stderr)
            return 1

    report = build_report(root, only_plan)
    if args.format == "json":
        print(render_json(report))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
