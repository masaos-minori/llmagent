## Goal
Add `tests/tools/test_check_dependency_graph_cycles.py`, covering at least one
cycle-free case (passes) and one synthetic cyclic case (fails), and exercising the
parser (seq 04's `tools/check_dependency_graph_cycles.py`) against both a
constructed fixture and the real current graph text in
`docs/00_governance_01_documentation-policy.md`, per REQ-008.

## Scope
- **In-Scope**: `tests/tools/test_check_dependency_graph_cycles.py` only (new
  file).
- **Out-of-Scope**: `tools/check_dependency_graph_cycles.py` itself (seq 04, must
  already exist for this row's imports to resolve), wiring into CI (seq 06).

## Assumptions
- `tools/check_dependency_graph_cycles.py` (seq 04) has already been created with
  the exact function names `extract_section`, `parse_edges`, `find_cycle`, `main`,
  and the module-level constants `DOCS_DIR`, `GRAPH_DOC_NAME`, `TARGET_SECTION`,
  `IN_SCOPE_NODES` — this row's imports and `monkeypatch.setattr(cdgc, "DOCS_DIR",
  ...)` calls depend on these exact names.
- `docs/00_governance_01_documentation-policy.md` (seq 01) has already been applied
  — the real-graph integration test (`TestRealGraphIntegration`) asserts the
  `## Software Runtime Dependency Graph` section exists with a clear failure
  message naming this dependency, rather than silently skipping, if seq 01 has not
  yet run.
- `tests/tools/` has no shared `conftest.py` fixture this file must reuse (each
  existing test file under `tests/tools/` builds its own `tmp_path`-based fixtures
  inline, per `tests/tools/test_check_needs_confirmation_inventory.py`'s own
  docstring: "Each scenario builds its own minimal fixture set under an isolated
  `tmp_path` subdirectory").

## Design decisions
- **`monkeypatch.setattr(cdgc, "DOCS_DIR", tmp_path)` isolates `main()`-level
  tests from the real repository** rather than writing synthetic fixture files
  into the real `docs/` directory (which would pollute the repository) or calling
  `main()` unmodified against the real file (which would make `main()`-level tests
  redundant with `TestRealGraphIntegration` and unable to construct a cyclic case
  at all, since the real graph is cycle-free by design).
- **A separate `TestRealGraphIntegration` class exercises the parser against the
  actual current `docs/00_governance_01_documentation-policy.md` file**,
  satisfying REQ-008's explicit requirement to test "against both the real current
  graph text and a constructed cyclic fixture" — not merely against synthetic
  fixtures throughout.
- **Cycle detection is tested at two levels**: `find_cycle()` directly (unit level,
  fastest to diagnose a failure) and `main()` end-to-end via a synthetic doc file
  (integration level, confirms the full parse-doc → extract-section → parse-edges →
  find-cycle → report pipeline works together, not just the algorithm in
  isolation).
- **A self-loop case (`Agent → Agent`) is included** as an additional cycle
  fixture beyond the minimum REQ-008 requires, since it is the smallest possible
  cycle and a natural edge case for a DFS-based detector (an off-by-one in
  gray/black state transition could silently miss it while still catching larger
  cycles).

## Alternatives considered
- **Test only `find_cycle()` in isolation, skipping `main()`/file-parsing tests
  entirely** — rejected: REQ-008 requires exercising "the parser" (not just the
  cycle-detection algorithm) against both a real and a synthetic case: parsing
  failures (missing section, unknown node, empty edge list) are a distinct failure
  mode from a correctly-parsed-but-cyclic graph, and are exactly the failure mode
  this Plan's own Risks section calls out as needing a "clear error rather than
  silently passing."
- **Use `subprocess.run([sys.executable, "tools/check_dependency_graph_cycles.py"])`
  for `main()`-level tests instead of `monkeypatch.setattr` + direct `main()`
  calls** — rejected: subprocess tests cannot easily redirect `DOCS_DIR` to a
  `tmp_path` fixture without an environment-variable indirection this tool does not
  define, and direct-call tests already give equivalent coverage with less
  overhead, matching this repo's existing convention (`test_check_needs_confirmation_inventory.py`
  calls the tool's functions directly rather than via subprocess).

## Implementation
### Target file
`tests/tools/test_check_dependency_graph_cycles.py` (new file)

### Procedure
1. Create `tests/tools/test_check_dependency_graph_cycles.py` with the exact
   content in Details below.
2. Run `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` (see
   Validation plan) — requires seq 01 and seq 04 already applied.

### Method
Create the file directly (new file — no before/after diff applies).

### Details

Full file content:

```python
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
    actual current content. Depends on plans/20260902-191512_plan.md's seq 01
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
            f"of plans/20260902-191512_plan.md been applied yet?"
        )
        edges = parse_edges(section)
        assert edges, f"no edges parsed from '## {TARGET_SECTION}' in {doc_path}"
        cycle = find_cycle(IN_SCOPE_NODES, edges)
        assert cycle is None, f"cycle detected in real graph: {cycle}"
```

Note: as in seq 04's Details, the literal arrow character used in the actual
created file is `→` (U+2192) everywhere shown above — the plain-text rendering
here is only a Markdown-block-safety concern for this Details section, not a
substitution to make in the real file.

## Compatibility considerations
Depends on `tools/check_dependency_graph_cycles.py` (seq 04) existing with the
exact function/constant names this file imports, and on
`docs/00_governance_01_documentation-policy.md` (seq 01) already carrying the
`## Software Runtime Dependency Graph` section for `TestRealGraphIntegration` to
pass. Apply this row after both seq 01 and seq 04.

## Security considerations
None — test file exercising local file parsing and in-memory graph logic only.

## Rollback considerations
New, standalone test file; revert by deleting it. No other file depends on it.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/tools/test_check_dependency_graph_cycles.py | Full suite | `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` | All tests pass, including the cycle-free and synthetic-cyclic cases (AC-8) |
| tests/tools/test_check_dependency_graph_cycles.py | Standard tool validation sequence | `rules/toolchain.md` sequence (ruff, mypy) | No new errors |

## Completion criteria
- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` passes in
  full, covering at least one cycle-free case and one synthetic cyclic case, and
  exercising the parser against the real current graph text (AC-8, REQ-008).

## Out of scope
`tools/check_dependency_graph_cycles.py` (seq 04),
`.github/workflows/governance-docs-consistency.yml` (seq 06),
`docs/00_governance_01_documentation-policy.md` (seq 01) — each has its own
implementation-procedure document per this Plan's Implementation Target Files
table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Applied after seq 01 and seq 04 (both already in place); corrected one stale reference from "plans/20260902-191512_plan.md" to "plans/done/20260902-191512_plan.md" (the Plan has since been archived) |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | This row's own file is the test — 13 tests, all passing |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -v`: 13/13 passed, including `TestRealGraphIntegration::test_real_repo_graph_has_no_cycle`. `ruff format`/`ruff check`: clean. `mypy`: no issues. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142052
- **Related target files**: tests/tools/test_check_dependency_graph_cycles.py
