# Implementation Procedure: scripts/shared/tool_executor_helpers.py

Source plan: `plans/20260715-140914_plan.md`

## Prior-doc divergence note

`implementations/20260715-150757_tool_executor_helpers.py.md` targets the same
file but was written for `plans/done/20260715-133548_plan.md` (a different
requirement, `requires/20260715_18_require.md`). That doc extends
`_SIDE_EFFECT_TOOLS` with `CICD_WRITE_TOOLS | RAG_WRITE_TOOLS |
MDQ_WRITE_TOOLS | MDQ_SERIAL_TOOLS`, where — per the divergence noted in
`implementations/20260715-152212_tool_constants.py.md` — that plan's
`MDQ_WRITE_TOOLS` means `{"index_paths", "refresh_index"}` and
`MDQ_SERIAL_TOOLS` means `{"fts_rebuild"}`. This plan's requirement instead
needs `_SIDE_EFFECT_TOOLS` extended with `RAG_WRITE_TOOLS | CICD_WRITE_TOOLS |
MDQ_WRITE_TOOLS` where **this plan's** `MDQ_WRITE_TOOLS` means only
`{"fts_rebuild"}`. There is no `MDQ_SERIAL_TOOLS` in this plan's design.
Applying the other doc verbatim would leave `fts_rebuild` uncovered under this
plan's constant names (since `MDQ_WRITE_TOOLS` here does not include
`index_paths`/`refresh_index`, and no `MDQ_SERIAL_TOOLS` union member exists
in this plan). Confirmed against current source
(`scripts/shared/tool_executor_helpers.py`, read in full): `_SIDE_EFFECT_TOOLS`
today is exactly `WRITE_TOOLS | DELETE_TOOLS | {"shell_run"} | GIT_WRITE_TOOLS
| GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS` (lines 18-25) — neither design
has been applied yet. This document is written fresh for this plan.

## Goal

Widen `_SIDE_EFFECT_TOOLS` (backing `is_side_effect()`) to also cover
`rag_delete_document`, `trigger_workflow`, and `fts_rebuild`/`index_paths`/
`refresh_index` (MDQ), using the three new frozensets from
`scripts/shared/tool_constants.py`
(`implementations/20260715-152212_tool_constants.py.md`), so `ToolExecutor.execute()`
can call `is_side_effect()` as the single shared classification source for
cache-bypass routing. `index_paths`/`refresh_index` are included per the
resolution of `issues/20260715-141104_risks.md` — no additional code change
is needed here beyond what `MDQ_WRITE_TOOLS` already provides, since this
file only unions the constant, it does not enumerate tool names itself.

## Scope

**In scope**
- Import `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `MDQ_WRITE_TOOLS` from
  `shared.tool_constants`.
- Union them into `_SIDE_EFFECT_TOOLS`.
- Update the one-line comment above `_SIDE_EFFECT_TOOLS` to mention the newly
  covered tool families.

**Out of scope**
- No change to `is_side_effect()`'s function body (stays
  `return tool_name in _SIDE_EFFECT_TOOLS`).
- No change to `format_transport_error()` or `tool_hash_key()`.
- No change to `agent/tool_runner.py` in this document — widening
  `_SIDE_EFFECT_TOOLS` also changes that module's serial-vs-parallel
  scheduling decision as an accepted, documented side effect of this plan
  (see plan's Assumption 4 and Design §5), but no code change is required
  there.

## Assumptions

- Current file (confirmed by direct read, 24-line body): import block at
  lines 7-13, `_SIDE_EFFECT_TOOLS` at lines 18-25, `is_side_effect()` at lines
  28-32.
- `is_side_effect()`'s only production call sites are
  `agent/tool_runner.py:_execute_standard()` (serial-downgrade decision) and,
  after this plan lands, `scripts/shared/tool_executor.py:execute()`
  (cache-bypass routing) — both are made strictly safer (more conservative),
  never less safe, by this widening.

## Implementation

### Target file

`scripts/shared/tool_executor_helpers.py`

### Procedure

1. Update the `from shared.tool_constants import (...)` block to add
   `CICD_WRITE_TOOLS`, `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, keeping
   alphabetical order (ruff `I` rule).
2. Update the `_SIDE_EFFECT_TOOLS` frozenset expression to union in the three
   new sets.
3. Update the comment directly above `_SIDE_EFFECT_TOOLS`.
4. Do not touch `is_side_effect()`, `format_transport_error()`, or
   `tool_hash_key()` bodies.

### Method

Additive edit to one import block and one frozenset literal. Run
`ruff format` / `ruff check --fix` afterward to normalize import ordering
rather than hand-sorting.

### Details

Replace:

```python
from shared.tool_constants import (
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    WRITE_TOOLS,
)
```

with:

```python
from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    WRITE_TOOLS,
)
```

Replace:

```python
# Tools with side effects: writes, deletes, shell, or git/GitHub mutations.
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls().
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
)
```

with:

```python
# Tools with side effects: writes, deletes, shell, git/GitHub mutations,
# RAG document deletion, CI/CD workflow triggers, or MDQ index writes
# (fts_rebuild, index_paths, refresh_index).
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls(),
# and (via is_side_effect()) to route side-effecting tools past ToolExecutor's
# result cache in execute().
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
    | RAG_WRITE_TOOLS
    | CICD_WRITE_TOOLS
    | MDQ_WRITE_TOOLS
)
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-152212_tool_constants.py.md` applied first | New names importable |
| Format/lint | `uv run ruff format scripts/shared/tool_executor_helpers.py && uv run ruff check scripts/shared/tool_executor_helpers.py` | 0 errors, import order correct |
| Type check | `uv run mypy scripts/shared/tool_executor_helpers.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_constants.py -v` (this module has no dedicated `test_tool_executor_helpers.py` target in this plan; classification is verified via `test_tool_constants.py` per Design §1 of the plan) | `is_side_effect("rag_delete_document")`, `is_side_effect("trigger_workflow")`, `is_side_effect("fts_rebuild")`, `is_side_effect("index_paths")`, `is_side_effect("refresh_index")` all `True`; read-only siblings remain `False` |
| Regression | `uv run pytest tests/test_tool_runner.py -v` | No new failures from the widened set feeding `_execute_standard()`'s serial-downgrade path |
