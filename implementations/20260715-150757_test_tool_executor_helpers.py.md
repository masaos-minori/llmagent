# Implementation Procedure: tests/test_tool_executor_helpers.py

Source plan: `plans/20260715-133548_plan.md`

## Goal

Add regression tests proving `is_side_effect()` returns `True` for the newly
covered CI/CD, RAG, and MDQ write/admin tools, mirroring the existing
`test_is_side_effect_git_write_tools` / `test_is_side_effect_github_write_tools`
/ `test_is_side_effect_github_dangerous_tools` pattern already in this file.

## Scope

**In scope:**
- Add `test_is_side_effect_cicd_write_tools` (iterates `CICD_WRITE_TOOLS`).
- Add `test_is_side_effect_rag_write_tools` (iterates `RAG_WRITE_TOOLS`).
- Add `test_is_side_effect_mdq_write_tools` (iterates `MDQ_WRITE_TOOLS`).
- Add `test_is_side_effect_mdq_serial_tools` (iterates `MDQ_SERIAL_TOOLS`,
  i.e. `fts_rebuild`).
- Optionally extend `test_is_side_effect_non_side_effect_tools`'s read-only
  list with one MDQ/RAG/CI-CD read tool (e.g. `"search_docs"`,
  `"rag_run_pipeline"`, `"get_workflow_status"`) to directly cross-check that
  the newly-touched families' *read* tools remain non-side-effect — optional
  but recommended given this file already exercises that negative case for
  other families only indirectly (via `tests/test_tool_constants.py`'s
  `TestGitToolClassification`/`TestGithubToolClassification`, not here).

**Out of scope:**
- No change to `test_tool_hash_key_*` or `test_format_transport_error_*`
  tests.
- No change to `test_is_side_effect_write_tools`,
  `test_is_side_effect_delete_tools`, `test_is_side_effect_shell_tools`,
  `test_is_side_effect_unknown_tool`, `test_is_side_effect_git_write_tools`,
  `test_is_side_effect_github_write_tools`,
  `test_is_side_effect_github_dangerous_tools` (all pass unmodified — sets
  they check are untouched by this plan).

## Assumptions

- Depends on `implementations/20260715-150757_tool_constants.py.md` (new
  frozensets must exist) and
  `implementations/20260715-150757_tool_executor_helpers.py.md` (`_SIDE_EFFECT_TOOLS`
  must include them) being applied first.
- Follow this file's existing per-test local-import style (e.g.
  `test_is_side_effect_git_write_tools` does
  `from shared.tool_constants import GIT_WRITE_TOOLS` inside the test body,
  not at module top) — new tests should do the same for consistency, rather
  than adding these names to the top-of-file
  `from shared.tool_executor_helpers import (...)` block (that block only
  imports from `tool_executor_helpers`, not `tool_constants` — the existing
  per-family tests already establish `tool_constants` imports are local to
  each test function).

## Implementation

### Target file

`tests/test_tool_executor_helpers.py`

### Procedure

1. Add the four new test functions after `test_is_side_effect_github_dangerous_tools`
   (before `test_format_transport_error_summary_includes_all_fields`), keeping
   the existing grouping of all `is_side_effect`-related tests together.
2. Optionally update `test_is_side_effect_non_side_effect_tools`'s
   `read_only_tools` list per Scope (recommended, not required for the plan's
   acceptance criteria).

### Method

Additive test-only edit, copying the existing per-family test function shape
verbatim, substituting the tool family constant name.

### Details

```python
def test_is_side_effect_cicd_write_tools() -> None:
    """Test that CI/CD write tools are correctly identified as side effect tools."""
    from shared.tool_constants import CICD_WRITE_TOOLS

    for tool_name in CICD_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_rag_write_tools() -> None:
    """Test that RAG write tools are correctly identified as side effect tools."""
    from shared.tool_constants import RAG_WRITE_TOOLS

    for tool_name in RAG_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_mdq_write_tools() -> None:
    """Test that MDQ write/admin tools are correctly identified as side effect tools."""
    from shared.tool_constants import MDQ_WRITE_TOOLS

    for tool_name in MDQ_WRITE_TOOLS:
        assert is_side_effect(tool_name) is True


def test_is_side_effect_mdq_serial_tools() -> None:
    """Test that MDQ serial-barrier tools (fts_rebuild) are correctly identified as side effect tools."""
    from shared.tool_constants import MDQ_SERIAL_TOOLS

    for tool_name in MDQ_SERIAL_TOOLS:
        assert is_side_effect(tool_name) is True
```

Optional negative-case extension (recommended):

```python
def test_is_side_effect_non_side_effect_tools() -> None:
    """Test that non-side-effect tools are correctly identified."""
    # Test various read-only tools
    read_only_tools = [
        "read_file",
        "list_files",
        "search_files",
        "get_metadata",
        "search_docs",         # MDQ read tool
        "rag_run_pipeline",    # RAG read tool
        "get_workflow_status", # CI/CD read tool
    ]
    for tool_name in read_only_tools:
        assert is_side_effect(tool_name) is False
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-150757_tool_constants.py.md`, `implementations/20260715-150757_tool_executor_helpers.py.md` applied first | New names importable; `is_side_effect()` recognizes new tools |
| Format/lint | `uv run ruff format tests/test_tool_executor_helpers.py && uv run ruff check tests/test_tool_executor_helpers.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_executor_helpers.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_executor_helpers.py -v` | All existing + 4 new tests pass |
| Full suite | `uv run pytest -v` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
