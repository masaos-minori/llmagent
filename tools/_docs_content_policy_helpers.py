"""Shared helpers for the `check_docs_*` policy checkers.

Leaf nodes extracted from `tools/check_docs_content_policy.py` by
`tools/module_nodes.py extract`: the auto-generated guard-comment predicates
and the docs-tree file discovery types. Kept import-cycle free — this module
depends only on the standard library, and the checkers import from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _is_guard_start(line: str) -> bool:
    """Return True if *line* opens an auto-generated guarded block.

    Recognizes any line starting with `<!-- AUTO-GENERATED` — not only the
    exact bare `<!-- AUTO-GENERATED -->` string — so the real guard-comment
    format `tools/generate_reference_table.py` emits (e.g. `<!--
    AUTO-GENERATED: generate_reference_table.py port-tool-reference -->`) is
    recognized.
    """
    return line.strip().startswith("<!-- AUTO-GENERATED")


def _is_guard_end(line: str) -> bool:
    """Return True if *line* closes an auto-generated guarded block."""
    return line.strip().startswith("<!-- END AUTO-GENERATED")


@dataclass(frozen=True)
class DocFile:
    """A single documentation file with its contents."""

    path: Path
    rel_path: str  # relative to docs/
    lines: list[str] = field(default_factory=list)


def discover_all_md_files(docs_dir: Path) -> list[DocFile]:
    """Return every `.md` file under *docs_dir*, recursively, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob("*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result
