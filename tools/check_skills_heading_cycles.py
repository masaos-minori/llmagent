#!/usr/bin/env python3
"""check_skills_heading_cycles.py — Detect heading-level circular references among skills/rules/prompts.

`prompts/05_skills.md` "Circular reference check" requires that the reference
graph among `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`,
`skills/**/*.md`, and `prompts/*.md` contains no cycle: file A MUST NOT point to
a section of file B for content whose own section points back to A.
`check_skills_references.py` only checks that the referenced *file* exists; this
tool checks the *section-level* graph.

Nodes are `(file, heading)` pairs (headings inside fenced code blocks are
ignored; text before the first heading is the node `(preamble)`). A backtick-quoted
`.md` path creates an edge from the section containing it to a target section,
resolved from the text right after the path in one of three forms:

- a quoted heading, e.g. `` `rules/coding.md`, section "Suppression governance" ``;
- `Step N` / `Phase N` (with an optional letter suffix);
- an unquoted heading name, e.g. `` `skills/DESIGN.md` Output language ``.

A reference that resolves to no heading (a bare file reference such as a load
list, a routing table row, or "see `workflow.md`") creates no edge; such
references are navigational and are not checked. References inside fenced code
blocks and references to the same file are ignored, so a cycle that runs through
two sections of one file is not detected (cross-file cycles only). Every strongly
connected component with more than one node is reported as an ERROR.

Usage:
    python tools/check_skills_heading_cycles.py
    python tools/check_skills_heading_cycles.py --format json
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import Issue, report_and_exit

REPO_ROOT = Path(__file__).resolve().parent.parent

# Source files scanned — mirrors prompts/05_skills.md Scope.
_SOURCE_GLOBS = [
    "AGENTS.md",
    "routing.md",
    "skills/DESIGN.md",
    "rules/*.md",
    "skills/**/*.md",
    "prompts/*.md",
]

_PREAMBLE = "(preamble)"
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^(#{1,6}) +(.*)$")
_REF_RE = re.compile(r"`([A-Za-z0-9_./-]+\.md)`")
_QUOTED_RE = re.compile(r'"([^"]{3,80})"|“([^”]{3,80})”')
_STEP_RE = re.compile(r"[\s,.:;\-—(]*(?:Step|Phase)\s+(\d+[a-z]?)")
_LEAD_RE = re.compile(r"^[\s,.:;\-—(§]*(?:section|heading)?\s*")
_STEP_PREFIX_RE = re.compile(r"^(?:Step|Phase)\s+\d+[a-z]?:?\s*")

Node = tuple[str, str]  # (relative file path, heading text)


@dataclass(frozen=True)
class Section:
    heading: str
    line_no: int
    body: str


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def split_sections(text: str) -> list[Section]:
    """Split Markdown *text* into sections.

    Lines inside fenced code blocks (``` or ~~~, closed by a fence of the same
    character and at least the same length) are neither headings nor part of a
    section body. A heading repeated within one file is suffixed ` (2)`, ` (3)`,
    ... so every node of a file is distinct.
    """
    sections: list[tuple[str, int, list[str]]] = [(_PREAMBLE, 1, [])]
    seen: dict[str, int] = {}
    fence: str | None = None
    for line_no, line in enumerate(text.split("\n"), start=1):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        match = _HEADING_RE.match(line)
        if match:
            heading = match.group(2).strip()
            seen[heading] = seen.get(heading, 0) + 1
            if seen[heading] > 1:
                heading = f"{heading} ({seen[heading]})"
            sections.append((heading, line_no, []))
        else:
            sections[-1][2].append(line)
    return [Section(h, n, "\n".join(body)) for h, n, body in sections]


def resolve_heading(headings: list[str], tail: str) -> str | None:
    """Resolve the target heading named by *tail* (text after a file reference).

    Forms are tried in this order: `Step N`/`Phase N` directly after the
    reference, a quoted heading, then an unquoted heading name at the start.
    """
    step = _STEP_RE.match(tail[:60])
    if step:
        key = step.group(1)
        for heading in headings:
            if re.match(r"(?:Step|Phase)\s+" + re.escape(key) + r"\b", heading):
                return heading
        return None
    for groups in _QUOTED_RE.findall(tail[:140]):
        quoted = _norm(groups[0] or groups[1])
        for heading in headings:
            name = _norm(heading)
            if name == quoted or (
                len(quoted) > 6 and quoted in name and len(quoted) * 10 >= len(name) * 6
            ):
                return heading
    lead = _norm(_LEAD_RE.sub("", tail[:110]))
    best: str | None = None
    for heading in headings:
        name = _norm(_STEP_PREFIX_RE.sub("", heading))
        if len(name) >= 6 and (lead == name or lead.startswith(name + " ")):
            if best is None or len(name) > len(_norm(best)):
                best = heading
    return best


def build_edges(files: dict[str, str]) -> dict[Node, set[Node]]:
    """Return heading-level edges for *files* (POSIX relative path -> text).

    The text naming a target heading is read only up to the next file
    reference in the same section, so a list of references does not lend one
    reference's heading to its neighbour.
    """
    sections = {path: split_sections(text) for path, text in files.items()}
    edges: dict[Node, set[Node]] = {}
    for path, secs in sections.items():
        base = posixpath.dirname(path)
        for sec in secs:
            matches = list(_REF_RE.finditer(sec.body))
            for i, match in enumerate(matches):
                target = _locate(match.group(1), base, files)
                if target is None or target == path:
                    continue
                end = matches[i + 1].start() if i + 1 < len(matches) else len(sec.body)
                headings = [s.heading for s in sections[target]]
                heading = resolve_heading(headings, sec.body[match.end() : end])
                if heading is not None:
                    edges.setdefault((path, sec.heading), set()).add((target, heading))
    return edges


def _locate(ref: str, base: str, files: dict[str, str]) -> str | None:
    """Resolve *ref* against the repository root first, then the source directory."""
    for candidate in (ref, posixpath.join(base, ref)):
        normalized = posixpath.normpath(candidate)
        if normalized in files:
            return normalized
    return None


def find_cycles(edges: dict[Node, set[Node]]) -> list[list[Node]]:
    """Return strongly connected components with more than one node (Tarjan)."""
    nodes = set(edges) | {t for targets in edges.values() for t in targets}
    index: dict[Node, int] = {}
    low: dict[Node, int] = {}
    stack: list[Node] = []
    on_stack: set[Node] = set()
    cycles: list[list[Node]] = []
    counter = 0

    for root in sorted(nodes):
        if root in index:
            continue
        work: list[tuple[Node, Iterable[Node]]] = [
            (root, iter(sorted(edges.get(root, ()))))
        ]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(edges.get(child, ())))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component: list[Node] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    cycles.append(sorted(component))
    return sorted(cycles)


def _repo_glob(patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(REPO_ROOT.glob(pattern))
    return sorted(p for p in paths if p.is_file())


def collect_issues() -> list[Issue]:
    files = {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in _repo_glob(_SOURCE_GLOBS)
    }
    line_of = {
        (path, sec.heading): sec.line_no
        for path, text in files.items()
        for sec in split_sections(text)
    }
    issues: list[Issue] = []
    for cycle in find_cycles(build_edges(files)):
        first = cycle[0]
        members = "; ".join(f"{path} :: {heading}" for path, heading in cycle)
        issues.append(
            Issue(
                file=first[0],
                line_no=line_of.get(first, 1),
                severity="ERROR",
                message=f"circular-reference: {members}",
            )
        )
    return issues


def render_json(issues: list[Issue]) -> str:
    payload = [
        {
            "file": issue.file,
            "line_no": issue.line_no,
            "severity": issue.severity,
            "message": issue.message,
        }
        for issue in sorted(issues, key=lambda i: (i.file, i.line_no))
    ]
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect heading-level circular references among skills/rules/prompts "
            "(prompts/05_skills.md Circular reference check)."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    args = parser.parse_args(argv)

    issues = collect_issues()

    if args.format == "json":
        print(render_json(issues))
        return 1 if any(issue.severity == "ERROR" for issue in issues) else 0

    return report_and_exit(issues)


if __name__ == "__main__":
    raise SystemExit(main())
