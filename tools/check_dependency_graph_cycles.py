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
