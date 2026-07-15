# Implementation Procedure: tests/test_tool_constants.py

Source plan: `plans/20260715-133548_plan.md`

## Goal

Add regression tests for the new `CICD_WRITE_TOOLS`/`CICD_READ_TOOLS`,
`RAG_WRITE_TOOLS`/`RAG_READ_TOOLS`, and
`MDQ_WRITE_TOOLS`/`MDQ_SERIAL_TOOLS`/`MDQ_READ_TOOLS` frozensets, mirroring
the existing `TestGitToolClassification` / `TestGithubToolClassification`
pattern already in this file for `GIT_TOOLS` / `GITHUB_TOOLS`.

## Scope

**In scope:**
- Add the new frozenset names to the `from shared.tool_constants import (...)`
  block.
- Add `TestCicdToolClassification`: union identity, read/write disjointness,
  read tools not side-effect, write tools are side-effect.
- Add `TestRagToolClassification`: same shape for RAG.
- Add `TestMdqToolClassification`: three-way union identity (read ∪ write ∪
  serial), pairwise disjointness among all three, read tools not side-effect,
  write tools are side-effect, `fts_rebuild` (the sole `MDQ_SERIAL_TOOLS`
  member) is side-effect.

**Out of scope:**
- No change to `TestToolConstants`, `TestGitToolClassification`,
  `TestGithubToolClassification`.
- No change to any existing assertion or expected-set literal.

## Assumptions

- Depends on `implementations/20260715-150757_tool_constants.py.md` (new
  frozensets must exist) and
  `implementations/20260715-150757_tool_executor_helpers.py.md` (`is_side_effect()`
  must recognize the new write/serial tools) being applied first.
- Follow the exact structural precedent of `TestGitToolClassification` /
  `TestGithubToolClassification` (already in this file, lines 153-197):
  a `test_<family>_tools_is_union_of_...` test, a
  `test_<family>_..._are_disjoint` test, then per-subset `is_side_effect()`
  checks using a local `from shared.tool_executor_helpers import
  is_side_effect` (matching the existing in-function import style used by
  those two classes, rather than a top-of-file import).

## Implementation

### Target file

`tests/test_tool_constants.py`

### Procedure

1. Update the `from shared.tool_constants import (...)` block (currently
   lines 7-22) to add: `CICD_WRITE_TOOLS`, `CICD_READ_TOOLS`,
   `RAG_WRITE_TOOLS`, `RAG_READ_TOOLS`, `MDQ_WRITE_TOOLS`,
   `MDQ_SERIAL_TOOLS`, `MDQ_READ_TOOLS`. Keep alphabetical order per `ruff`
   `I` rules (run `ruff check --fix` after to confirm).
2. Add `class TestCicdToolClassification:` after `TestGithubToolClassification`
   (end of file, or immediately after the class it most resembles —
   `TestGitToolClassification`, since CI/CD's shape is read/write only like
   Git, not three-way like MDQ).
3. Add `class TestRagToolClassification:` next, same shape.
4. Add `class TestMdqToolClassification:` next, three-way shape.

### Method

Additive test-only edit, copying the existing `TestGitToolClassification` /
`TestGithubToolClassification` structure verbatim in shape, substituting tool
family names/constants.

### Details

```python
class TestCicdToolClassification:
    def test_cicd_tools_is_union_of_read_and_write(self) -> None:
        assert CICD_TOOLS == CICD_READ_TOOLS | CICD_WRITE_TOOLS

    def test_cicd_read_write_are_disjoint(self) -> None:
        assert CICD_READ_TOOLS.isdisjoint(CICD_WRITE_TOOLS)

    def test_cicd_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in CICD_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_cicd_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in CICD_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestRagToolClassification:
    def test_rag_tools_is_union_of_read_and_write(self) -> None:
        assert RAG_TOOLS == RAG_READ_TOOLS | RAG_WRITE_TOOLS

    def test_rag_read_write_are_disjoint(self) -> None:
        assert RAG_READ_TOOLS.isdisjoint(RAG_WRITE_TOOLS)

    def test_rag_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in RAG_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_rag_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in RAG_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"


class TestMdqToolClassification:
    def test_mdq_tools_is_union_of_read_write_and_serial(self) -> None:
        assert MDQ_TOOLS == MDQ_READ_TOOLS | MDQ_WRITE_TOOLS | MDQ_SERIAL_TOOLS

    def test_mdq_sub_sets_are_pairwise_disjoint(self) -> None:
        assert MDQ_READ_TOOLS.isdisjoint(MDQ_WRITE_TOOLS)
        assert MDQ_READ_TOOLS.isdisjoint(MDQ_SERIAL_TOOLS)
        assert MDQ_WRITE_TOOLS.isdisjoint(MDQ_SERIAL_TOOLS)

    def test_mdq_read_tools_not_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in MDQ_READ_TOOLS:
            assert not is_side_effect(tool), f"{tool!r} should not be a side-effect"

    def test_mdq_write_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in MDQ_WRITE_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"

    def test_mdq_serial_tools_are_side_effect(self) -> None:
        from shared.tool_executor_helpers import is_side_effect

        for tool in MDQ_SERIAL_TOOLS:
            assert is_side_effect(tool), f"{tool!r} should be a side-effect"
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-150757_tool_constants.py.md`, `implementations/20260715-150757_tool_executor_helpers.py.md` applied first | New names importable; `is_side_effect()` recognizes new tools |
| Format/lint | `uv run ruff format tests/test_tool_constants.py && uv run ruff check tests/test_tool_constants.py` | 0 errors, import order correct |
| Type check | `uv run mypy tests/test_tool_constants.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_constants.py -v` | All existing + new tests pass |
| Full suite | `uv run pytest -v` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
