"""tests/tools/test_check_dependency_graph_cycles.py
Tests for tools/check_dependency_graph_cycles.py.

Each scenario builds its own minimal fixture under an isolated `tmp_path`
subdirectory and calls the tool's functions directly, matching
tests/tools/test_check_needs_confirmation_inventory.py's tmp_path-fixture
pattern. TestRealGraphIntegration is the exception: it reads the actual current
docs/00_governance_01_documentation-policy.md, per REQ-008's requirement to
exercise the parser against the real current graph text, not only synthetic
fixtures.
"""

from __future__ import annotations

from pathlib import Path

import tools.check_dependency_graph_cycles as cdgc
from tools.check_dependency_graph_cycles import (
    GRAPH_DOC_NAME,
    IN_SCOPE_NODES,
    TARGET_SECTION,
    extract_section,
    find_cycle,
    parse_edges,
)


def _write(dir_path: Path, filename: str, content: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / filename).write_text(content, encoding="utf-8")


_CYCLE_FREE_DOC = """## Some Preceding Section

Some content.

## Software Runtime Dependency Graph

Node set: Agent, MCP, RAG, EventBus, Shared/DB.

Confirmed edges:
- Agent → MCP
- Agent → Shared/DB
- EventBus → Shared/DB

Needs Confirmation:
- RAG → EventBus
- MCP → EventBus
- Agent → EventBus

## Deployment Management Graph

Some other content.
"""

_CYCLIC_DOC = """## Software Runtime Dependency Graph

Node set: Agent, MCP, RAG, EventBus, Shared/DB.

Confirmed edges:
- Agent → MCP
- MCP → RAG
- RAG → Agent

## Deployment Management Graph

Some other content.
"""


# ── extract_section ──────────────────────────────────────────────────────────


class TestExtractSection:
    def test_extracts_target_section_only(self) -> None:
        lines = _CYCLE_FREE_DOC.splitlines()
        section = extract_section(lines, TARGET_SECTION)
        assert any("Agent → MCP" in line for line in section)
        assert not any("Some other content" in line for line in section)
        assert not any("Some content." in line for line in section)

    def test_missing_section_returns_empty(self) -> None:
        lines = "## A\n\nfoo\n".splitlines()
        assert extract_section(lines, TARGET_SECTION) == []


# ── parse_edges ───────────────────────────────────────────────────────────────


class TestParseEdges:
    def test_parses_valid_edges(self) -> None:
        lines = [
            "Confirmed edges:",
            "- Agent → MCP",
            "- Agent → Shared/DB",
            "",
            "prose text, not an edge",
        ]
        edges = parse_edges(lines)
        assert ("Agent", "MCP") in edges
        assert ("Agent", "Shared/DB") in edges
        assert len(edges) == 2

    def test_ignores_non_bullet_lines(self) -> None:
        lines = ["Node set: Agent, MCP, RAG, EventBus, Shared/DB."]
        assert parse_edges(lines) == []


# ── find_cycle ────────────────────────────────────────────────────────────────


class TestFindCycle:
    def test_no_cycle_returns_none(self) -> None:
        edges = [("Agent", "MCP"), ("MCP", "EventBus"), ("EventBus", "Shared/DB")]
        assert find_cycle(IN_SCOPE_NODES, edges) is None

    def test_synthetic_cycle_detected(self) -> None:
        edges = [("Agent", "MCP"), ("MCP", "RAG"), ("RAG", "Agent")]
        cycle = find_cycle(IN_SCOPE_NODES, edges)
        assert cycle is not None
        assert cycle[0] == cycle[-1]
        assert set(cycle[:-1]) == {"Agent", "MCP", "RAG"}

    def test_self_loop_detected(self) -> None:
        edges = [("Agent", "Agent")]
        assert find_cycle(IN_SCOPE_NODES, edges) == ["Agent", "Agent"]


# ── main() integration ─────────────────────────────────────────────────────────


class TestMainIntegration:
    def test_cycle_free_graph_exits_zero(self, tmp_path, monkeypatch, capsys) -> None:
        _write(tmp_path, GRAPH_DOC_NAME, _CYCLE_FREE_DOC)
        monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)
        assert cdgc.main() == 0
        assert "No cycle found" in capsys.readouterr().out

    def test_synthetic_cycle_exits_nonzero(self, tmp_path, monkeypatch, capsys) -> None:
        _write(tmp_path, GRAPH_DOC_NAME, _CYCLIC_DOC)
        monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)
        assert cdgc.main() != 0
        assert "cycle detected" in capsys.readouterr().err.lower()

    def test_missing_doc_file_exits_nonzero(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)
        assert cdgc.main() == 1

    def test_missing_section_exits_nonzero(self, tmp_path, monkeypatch) -> None:
        _write(tmp_path, GRAPH_DOC_NAME, "## Some Other Section\n\ncontent\n")
        monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)
        assert cdgc.main() == 1

    def test_unknown_node_exits_nonzero(self, tmp_path, monkeypatch) -> None:
        doc = (
            "## Software Runtime Dependency Graph\n\n"
            "- Agent → Unknown\n\n"
            "## Next Section\n"
        )
        _write(tmp_path, GRAPH_DOC_NAME, doc)
        monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)
        assert cdgc.main() == 1


# ── Real graph integration (REQ-008: exercise against real current graph text) ──


class TestRealGraphIntegration:
    """Exercises the parser against docs/00_governance_01_documentation-policy.md's
    actual current content. Depends on plans/done/20260902-191512_plan.md's seq 01
    implementation-procedure having already been applied (the '## Software
    Runtime Dependency Graph' section must exist); if run before that edit, this
    test fails with a clear assertion message rather than silently skipping.
    """

    def test_real_repo_graph_has_no_cycle(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent.parent
        doc_path = repo_root / "docs" / GRAPH_DOC_NAME
        assert doc_path.is_file(), f"{doc_path} not found"
        lines = doc_path.read_text(encoding="utf-8").splitlines()
        section = extract_section(lines, TARGET_SECTION)
        assert section, (
            f"'## {TARGET_SECTION}' section not found in {doc_path} -- has seq 01 "
            f"of plans/done/20260902-191512_plan.md been applied yet?"
        )
        edges = parse_edges(section)
        assert edges, f"no edges parsed from '## {TARGET_SECTION}' in {doc_path}"
        cycle = find_cycle(IN_SCOPE_NODES, edges)
        assert cycle is None, f"cycle detected in real graph: {cycle}"
