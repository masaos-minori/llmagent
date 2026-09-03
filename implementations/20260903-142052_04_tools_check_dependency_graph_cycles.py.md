## Goal
Add a new tool, `tools/check_dependency_graph_cycles.py`, that parses the Software
Runtime Dependency Graph's edge list from
`docs/00_governance_01_documentation-policy.md` (as that section is defined by seq
01 of this Plan) and exits non-zero if a cycle exists among its 5 in-scope nodes
(Agent, MCP, RAG, EventBus, Shared/DB), automating the invariant the previous
`## Area Dependency Graph` stated but silently violated.

## Scope
- **In-Scope**: `tools/check_dependency_graph_cycles.py` only (new file).
- **Out-of-Scope**: `tests/tools/test_check_dependency_graph_cycles.py` (seq 05 —
  the test file for this tool), wiring this tool into
  `.github/workflows/governance-docs-consistency.yml` (seq 06),
  `docs/00_governance_01_documentation-policy.md` (seq 01, already applied by the
  time this row runs, per Implementation Target Files ordering),
  `docs/00_governance_04_documentation-checks.md` (seq 02, which describes this tool
  in section 12's rewritten text). Cycle detection for the Deployment Management
  Graph, Documentation Reference Graph, or Governance Applicability Matrix — REQ-007
  scopes this tool to the Software Runtime Dependency Graph only; the other three
  relation types are explicitly "not cycle-checked" per their own sections in
  `docs/00_governance_01_documentation-policy.md` (seq 01).

## Assumptions
- Seq 01's edit to `docs/00_governance_01_documentation-policy.md` has already been
  applied to the repository before this tool is run against it — this row's
  `Confirmed edges`/`Needs Confirmation` bullet format below is exactly seq 01's
  Details output, not the pre-seq-01 `A → B, C` grouped format.
- No existing `tools/*.py` contains cycle- or graph-traversal logic (re-confirmed by
  `grep -rln "cycle\|topological\|DFS\|has_cycle" tools/*.py` finding no match,
  consistent with the Plan's own 2026-09-02 confirmation) — this is a genuinely new
  capability, not a duplicate of an existing checker (`tools/check_docs_quality.py`,
  `tools/check_docs_consistency.py` / `_docs_consistency_lib.py`, and
  `tools/check_docs_structure.py` were each individually re-confirmed to contain no
  such logic, matching the Plan's Reference Files rows for this file).

## Design decisions
- **Edge-list format parsed is one-edge-per-line (`- A → B`), not the original
  `A → B, C` comma-grouped format.** The Plan's own Assumption
  ("Runtime Dependency Graph's own edge list stays in the current plain-text
  `A → B, C` bullet format ... so the new cycle-detection tool can regex-parse it
  the same way") anticipated the comma-grouped shape, but seq 01's actual section
  text (required by REQ-002 to mark exactly 3 of Agent's/MCP's/RAG's edges as `Needs
  Confirmation` while leaving other edges from the same source node confirmed)
  cannot cleanly express a per-edge confirmation split within a single
  comma-grouped source line. One-edge-per-line is still plain Markdown-bullet text
  (no YAML/JSON, no new structured data format) and satisfies the Assumption's
  actual purpose; this is recorded here as a deliberate, evidence-driven refinement
  of the stated format, not a silent deviation — see seq 01's own Design decisions
  for the same note from the documentation side.
- **Both `Confirmed edges` and `Needs Confirmation` edges are included in cycle
  detection.** REQ-002/AC-2 state the no-cycle invariant applies to "its 5 in-scope
  nodes" without carving out an exception for edges whose real-world existence is
  itself unconfirmed — a cycle formed partly of Needs-Confirmation edges would still
  violate the stated invariant once/if those edges are confirmed, so excluding them
  from the check would let a real problem go undetected until confirmation happens.
  Verified this choice does not change the current pass/fail outcome: manually
  tracing all 6 edges in seq 01's corrected graph (`Agent → MCP`, `Agent →
  Shared/DB`, `EventBus → Shared/DB`, `RAG → EventBus`, `MCP → EventBus`,
  `Agent → EventBus`) finds no cycle regardless of which subset is included.
- **A parse failure (missing section, zero edges found, or an edge naming a node
  outside the 5-node in-scope set) is a hard error (exit 1 with a clear message),
  not a silent pass.** Directly implements this Plan's own Risks mitigation ("a
  parse failure should raise a clear error rather than silently passing") for the
  identified risk of a future editor reformatting the bullet list.
- **Reuses `tools/_docs_consistency_lib.discover_md_files` for file loading**,
  matching the Reference Files' stated intent ("establish this repo's
  markdown-parsing tool conventions for the new tool to follow"), but does not use
  that module's `Issue`/`report_and_exit` machinery — those are designed for
  reporting an arbitrary-length list of independent issues across many files, while
  this tool has exactly one boolean outcome (cycle found in one specific section, or
  not) against one specific file; a direct print-and-return-exit-code pattern is a
  better fit and avoids forcing a single result into a list-of-Issue abstraction
  built for a different shape of problem.
- **Cycle detection algorithm**: iterative-recursion DFS with a 3-color
  (white/gray/black) node-state scheme — a standard, well-understood approach for a
  5-node graph, returning the actual cyclic path (not just a boolean) so a failing
  CI run's error message names the offending nodes directly.

## Alternatives considered
- **Keep the `A → B, C` comma-grouped parsing format and represent Needs-Confirmation
  status as a suffix annotation on individual comma-list items (e.g. `Agent → MCP,
  Shared/DB, EventBus (needs confirmation)`)** — rejected: this packs two different
  kinds of information (edge target, confirmation status) into one comma-separated
  token stream, which is harder to regex-parse reliably than one edge per line, and
  contradicts seq 01's own chosen documentation format (see Design decisions above,
  and seq 01's own Alternatives considered).
- **Use `tools/_docs_consistency_lib`'s `Issue`/`report_and_exit` for this tool
  too, for maximum convention consistency** — considered, rejected in favor of a
  direct print+return pattern (see Design decisions) since a single-outcome check
  gains no benefit from a multi-issue list abstraction, and forcing it in would
  need an artificial "issue" wrapping a cycle path that isn't really a per-line,
  per-file issue in the same sense as broken links or stale references.
- **Recursive backtracking without explicit color-marking (plain visited set,
  re-raising on any revisit)** — rejected: cannot distinguish "already fully
  explored, no cycle through here" (black) from "currently on the DFS stack, so
  revisiting it IS a cycle" (gray) — the 3-color scheme is the standard fix for
  exactly this ambiguity and is not meaningfully more complex to implement.

## Implementation
### Target file
`tools/check_dependency_graph_cycles.py` (new file)

### Procedure
1. Create `tools/check_dependency_graph_cycles.py` with the exact content in
   Details below.
2. Confirm the module runs standalone: `uv run python
   tools/check_dependency_graph_cycles.py` (see Validation plan).

### Method
Create the file directly (new file — no before/after diff applies).

### Details

Full file content:

```python
#!/usr/bin/env python3
"""check_dependency_graph_cycles.py — Detect cycles in the Software Runtime Dependency Graph.

docs/00_governance_01_documentation-policy.md's `## Software Runtime Dependency
Graph` section declares "Cycles prohibited" for its 5 in-scope nodes (Agent, MCP,
RAG, EventBus, Shared/DB). No automated check previously verified this invariant —
the graph's predecessor (`## Area Dependency Graph`) stated the same invariant
while itself containing a direct Overview <-> Governance cycle, undetected until
manual review (see issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md).

This tool parses the edge list directly from that section's Markdown bullets (no
new data format -- the same plain-text `A -> B` bullet convention already used in
the document) and exits non-zero if a cycle exists among the 5 in-scope nodes. Both
"Confirmed edges" and "Needs Confirmation" edges are included in cycle detection:
the no-cycle invariant applies to every edge asserted in the section, regardless of
whether the edge's real-world existence is itself still Needs Confirmation.

Usage:
    python tools/check_dependency_graph_cycles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import discover_md_files

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"
TARGET_SECTION = "Software Runtime Dependency Graph"
IN_SCOPE_NODES = frozenset({"Agent", "MCP", "RAG", "EventBus", "Shared/DB"})

_SECTION_HEADING_RE = re.compile(r"^## (.+)$")
_EDGE_RE = re.compile(r"^-\s+([A-Za-z][\w/]*)\s+→\s+([A-Za-z][\w/]*)\s*$")


def extract_section(lines: list[str], heading: str) -> list[str]:
    """Return the lines within a top-level `## {heading}` section (exclusive of
    the heading itself), stopping before the next `## ` heading."""
    section: list[str] = []
    in_section = False
    for line in lines:
        if _SECTION_HEADING_RE.match(line):
            if in_section:
                break
            in_section = line.strip() == f"## {heading}"
            continue
        if in_section:
            section.append(line)
    return section


def parse_edges(section_lines: list[str]) -> list[tuple[str, str]]:
    """Parse `- A -> B` bullet lines into (source, target) edge tuples."""
    edges: list[tuple[str, str]] = []
    for line in section_lines:
        match = _EDGE_RE.match(line.strip())
        if match:
            edges.append((match.group(1), match.group(2)))
    return edges


def find_cycle(nodes: frozenset[str], edges: list[tuple[str, str]]) -> list[str] | None:
    """Return a cycle (as a node-name path) if one exists among `nodes`, else None."""
    graph: dict[str, list[str]] = {node: [] for node in nodes}
    for source, target in edges:
        if source in nodes and target in nodes:
            graph[source].append(target)

    white, gray, black = 0, 1, 2
    color = {node: white for node in nodes}
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = gray
        path.append(node)
        for neighbor in graph[node]:
            if color[neighbor] == gray:
                cycle_start = path.index(neighbor)
                return [*path[cycle_start:], neighbor]
            if color[neighbor] == white:
                found = visit(neighbor)
                if found:
                    return found
        path.pop()
        color[node] = black
        return None

    for node in sorted(nodes):
        if color[node] == white:
            found = visit(node)
            if found:
                return found
    return None


def main() -> int:
    files = discover_md_files(DOCS_DIR, prefix="")
    graph_doc = next((f for f in files if f.rel_path == GRAPH_DOC_NAME), None)
    if graph_doc is None:
        print(f"ERROR: {GRAPH_DOC_NAME} not found under docs/.", file=sys.stderr)
        return 1

    section_lines = extract_section(graph_doc.lines, TARGET_SECTION)
    if not section_lines:
        print(
            f"ERROR: '## {TARGET_SECTION}' section not found in {GRAPH_DOC_NAME}.",
            file=sys.stderr,
        )
        return 1

    edges = parse_edges(section_lines)
    if not edges:
        print(
            f"ERROR: no edges parsed from '## {TARGET_SECTION}' in {GRAPH_DOC_NAME} "
            f"-- the edge-list bullet format may have changed.",
            file=sys.stderr,
        )
        return 1

    unknown_nodes = sorted(
        {node for edge in edges for node in edge if node not in IN_SCOPE_NODES}
    )
    if unknown_nodes:
        print(
            f"ERROR: edge(s) reference node(s) outside the in-scope set "
            f"{sorted(IN_SCOPE_NODES)}: {unknown_nodes}",
            file=sys.stderr,
        )
        return 1

    cycle = find_cycle(IN_SCOPE_NODES, edges)
    if cycle:
        print(
            f"ERROR: cycle detected in the Software Runtime Dependency Graph: "
            f"{' -> '.join(cycle)}",
            file=sys.stderr,
        )
        return 1

    print(f"No cycle found among {len(IN_SCOPE_NODES)} node(s), {len(edges)} edge(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Note: the literal arrow character used in the actual source file is `→` (U+2192);
it is written as `→` in the regex literal above and as `->` in printed
messages/docstring prose only to keep this Details block's own Markdown rendering
unambiguous — the created file must use the real `→` character everywhere the
target document itself uses it (matching `_EDGE_RE`'s pattern and the doc's own
edge-list text), and the plain `->` only where shown above (printed messages,
docstring prose).

## Compatibility considerations
New, standalone file — no existing caller. Not wired into CI or `pre-commit` by
this row (seq 06 wires it into `.github/workflows/governance-docs-consistency.yml`).
Depends on seq 01 having already been applied to
`docs/00_governance_01_documentation-policy.md` (see Assumptions) — if run before
seq 01, this tool will correctly exit 1 with the "no edges parsed" error (the
pre-seq-01 `A → B, C` format does not match `_EDGE_RE`), not silently pass.

## Security considerations
None — reads one local Markdown file and performs in-memory graph analysis; no
network access, no subprocess execution, no user-controlled input.

## Rollback considerations
New, standalone file with no callers outside its own test (seq 05) and the CI step
(seq 06, not yet added). Revert by deleting the file; no other file requires
follow-up changes if reverted, as long as seq 06 has not yet added the CI step (if
it has, revert that step in the same rollback).

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_dependency_graph_cycles.py | Integration: run against the real, seq-01-corrected graph | `uv run python tools/check_dependency_graph_cycles.py` | Exit 0, prints "No cycle found among 5 node(s), 6 edge(s)." |
| tools/check_dependency_graph_cycles.py | Unit (seq 05 owns the actual test file) | `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` | Cycle-free and synthetic-cyclic cases both pass as expected |
| tools/check_dependency_graph_cycles.py | Standard tool validation sequence | `rules/toolchain.md` sequence (ruff, mypy, bandit) | No new errors |

## Completion criteria
- `tools/check_dependency_graph_cycles.py` exists and exits 0 when run against the
  current (seq-01-corrected) `docs/00_governance_01_documentation-policy.md`
  (AC-8, first half).
- The tool exits non-zero and prints the cyclic path when run against a graph text
  containing a cycle among the 5 in-scope nodes (verified by seq 05's test fixture).
- `ruff`, `mypy`, and `bandit` report no new errors for this file.

## Out of scope
`tests/tools/test_check_dependency_graph_cycles.py` (seq 05),
`.github/workflows/governance-docs-consistency.yml` (seq 06),
`docs/00_governance_01_documentation-policy.md` (seq 01),
`docs/00_governance_04_documentation-checks.md` (seq 02) — each has its own
implementation-procedure document per this Plan's Implementation Target Files
table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Apply after seq 01 (see Compatibility considerations) |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test file itself is seq 05's row; this row only confirms the tool runs standalone |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's own file is not documentation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142052
- **Related target files**: tools/check_dependency_graph_cycles.py
