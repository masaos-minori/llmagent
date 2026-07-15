# Implementation Procedure: tests/test_tool_constants.py

Source plan: `plans/20260715-140914_plan.md`

## Prior-doc divergence note

`implementations/20260715-150757_test_tool_constants.py.md` targets the same
file but was written for `plans/done/20260715-133548_plan.md`. It adds
`TestCicdToolClassification` / `TestRagToolClassification` /
`TestMdqToolClassification` structured as read/write **union + disjointness**
tests (mirroring `TestGitToolClassification`), which requires
`CICD_READ_TOOLS`, `RAG_READ_TOOLS`, `MDQ_READ_TOOLS`,
`MDQ_SERIAL_TOOLS` to exist. This plan does not introduce any `*_READ_TOOLS`
or `MDQ_SERIAL_TOOLS` constants (see
`implementations/20260715-152212_tool_constants.py.md`), so that doc's tests
would fail with `ImportError` if applied under this plan's constants module.
This plan's own step description (Implementation Steps, Phase 1) instead
calls for direct membership assertions: `is_side_effect()` is `True` for the
three named write tools and `False` for their explicitly-named read-only
siblings — a simpler shape than the other doc's union/disjointness pattern.
This document is written fresh for this plan; do not combine it with the
other doc's classes since the required constants differ.

## Goal

Add regression tests proving `is_side_effect()` (via the frozensets added in
`implementations/20260715-152212_tool_constants.py.md`) correctly classifies
`rag_delete_document`, `trigger_workflow`, and `fts_rebuild`/`index_paths`/
`refresh_index` as side effects, while their read-only siblings remain
non-side-effects. `index_paths`/`refresh_index` are included per the
resolution of `issues/20260715-141104_risks.md` — see the updated Assumptions
note below, which supersedes this document's original deferral.

## Scope

**In scope**
- Add `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `MDQ_WRITE_TOOLS` to the
  `from shared.tool_constants import (...)` block.
- Add `TestRagWriteToolClassification`, `TestCicdWriteToolClassification`,
  `TestMdqWriteToolClassification` test classes asserting:
  - the named write tool is in the new frozenset and `is_side_effect()` is
    `True` for it
  - explicitly-named read-only siblings from the same family remain
    `is_side_effect() is False`

**Out of scope**
- No change to `TestToolConstants`, `TestGitToolClassification`,
  `TestGithubToolClassification`, or any existing assertion/expected-set
  literal.
- No `*_READ_TOOLS` union/disjointness tests (no such constants exist under
  this plan — see divergence note above).

## Assumptions

- Depends on `implementations/20260715-152212_tool_constants.py.md` (new
  frozensets must exist) being applied first.
- Follows this file's existing per-class style (`TestGitToolClassification`,
  lines 153-170) for structure, but adapted to a flat write-tool-only shape
  since no read-side split exists for these three families under this plan.
- Read-only siblings used for the negative assertions, drawn directly from
  current `RAG_TOOLS` / `CICD_TOOLS` / `MDQ_TOOLS` (confirmed by reading
  `scripts/shared/tool_constants.py`): RAG → `rag_run_pipeline`,
  `rag_debug_pipeline`, `rag_list_documents` (confirmed read-only — no
  database writes, per `issues/20260715-141104_risks.md`'s analysis of
  `scripts/rag/pipeline.py` / `scripts/mcp_servers/rag_pipeline/service.py`);
  CI/CD → `get_workflow_runs`, `get_workflow_status`, `get_workflow_logs`;
  MDQ → `search_docs`, `get_chunk`, `outline`, `stats`, `grep_docs`,
  `fts_consistency_check` (note: `index_paths`/`refresh_index` are **removed**
  from this read-only list — per the resolution of
  `issues/20260715-141104_risks.md`, they are now members of
  `MDQ_WRITE_TOOLS` and must assert `is_side_effect() is True`, not `False`;
  this supersedes this document's original deferral text).

## Implementation

### Target file

`tests/test_tool_constants.py`

### Procedure

1. Update the `from shared.tool_constants import (...)` block (lines 7-23) to
   add `CICD_WRITE_TOOLS`, `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS` in
   alphabetical position (ruff `I` rule; run `ruff check --fix` to confirm).
2. Append three new test classes at the end of the file, after
   `TestGithubToolClassification` (ends line 202).

### Method

Additive test-only edit. New classes follow the existing local-import style
used by `TestGitToolClassification` (`from shared.tool_executor_helpers import
is_side_effect` inside each test function body).

### Details

```python
class TestRagWriteToolClassification:
    def test_rag_delete_document_in_write_set(self) -> None:
        assert "rag_delete_document" in RAG_WRITE_TOOLS

    def test_rag_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in RAG_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_rag_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in ("rag_run_pipeline", "rag_debug_pipeline", "rag_list_documents"):
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"


class TestCicdWriteToolClassification:
    def test_trigger_workflow_in_write_set(self) -> None:
        assert "trigger_workflow" in CICD_WRITE_TOOLS

    def test_cicd_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in CICD_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_cicd_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in ("get_workflow_runs", "get_workflow_status", "get_workflow_logs"):
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"


class TestMdqWriteToolClassification:
    def test_fts_rebuild_in_write_set(self) -> None:
        assert "fts_rebuild" in MDQ_WRITE_TOOLS

    def test_index_paths_in_write_set(self) -> None:
        assert "index_paths" in MDQ_WRITE_TOOLS

    def test_refresh_index_in_write_set(self) -> None:
        assert "refresh_index" in MDQ_WRITE_TOOLS

    def test_mdq_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in MDQ_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_mdq_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        read_only = (
            "search_docs",
            "get_chunk",
            "outline",
            "stats",
            "grep_docs",
            "fts_consistency_check",
        )
        for tool in read_only:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-152212_tool_constants.py.md`, `implementations/20260715-152212_tool_executor_helpers.py.md` applied first | New names importable; `is_side_effect()` recognizes new tools |
| Format/lint | `uv run ruff format tests/test_tool_constants.py && uv run ruff check tests/test_tool_constants.py` | 0 errors, import order correct |
| Type check | `uv run mypy tests/test_tool_constants.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_constants.py -v` | All existing + new tests pass; `test_no_overlapping_tools` count (44) unchanged |
| Full suite | `uv run pytest -v` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
