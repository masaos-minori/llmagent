# Implementation Procedure: scripts/shared/tool_executor_helpers.py

Source plan: `plans/20260715-133548_plan.md`

## Goal

Extend `_SIDE_EFFECT_TOOLS` (the set backing `is_side_effect()`) to also cover
CI/CD (`trigger_workflow`), RAG (`rag_delete_document`), and MDQ
(`index_paths`, `refresh_index`, `fts_rebuild`) write/admin tools, so that
`is_side_effect()` becomes the single source of truth `tool_runner.py` can
delegate to for write classification, per the requirement's Implementation
Notes.

## Scope

**In scope:**
- Import the new frozensets from `scripts/shared/tool_constants.py`
  (`CICD_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `MDQ_WRITE_TOOLS`,
  `MDQ_SERIAL_TOOLS`) — depends on
  `implementations/20260715-150757_tool_constants.py.md` being applied first.
- Extend the `_SIDE_EFFECT_TOOLS` frozenset union with these four new sets.
- Update the comment above `_SIDE_EFFECT_TOOLS` to mention the newly covered
  families.

**Out of scope:**
- No change to `is_side_effect()`'s function body (it stays
  `return tool_name in _SIDE_EFFECT_TOOLS`).
- No change to `format_transport_error()` or `tool_hash_key()`.
- No change to the single consumer, `_execute_standard()` in
  `tool_runner.py` (that consumer's behavior is a documented side effect of
  this change, not something this file's edit needs to touch).

## Assumptions

- `_SIDE_EFFECT_TOOLS`'s only consumer is `is_side_effect()`, and
  `is_side_effect()`'s only call site outside tests is `tool_runner.py:360`
  inside `_execute_standard()`, where it is used purely to decide whether a
  non-DAG round should fall back to serial execution. Expanding the set only
  makes that fallback path more conservative (never less safe). Confirmed by
  reading the full file and grepping `is_side_effect(` across `scripts/`.
- This file's `_SIDE_EFFECT_TOOLS` will also become the classification source
  `tool_runner.py`'s `_build_tool_meta()` reads from (via `is_side_effect()`)
  once `implementations/20260715-150757_tool_runner.py.md` is applied — so
  `MDQ_SERIAL_TOOLS` (`fts_rebuild`) must be included here too, even though
  `_build_tool_meta()` will *also* independently check `MDQ_SERIAL_TOOLS` for
  `requires_serial` — the two checks are for different fields (`is_write` vs
  `requires_serial`), so `fts_rebuild` needs to appear in both.

## Implementation

### Target file

`scripts/shared/tool_executor_helpers.py`

### Procedure

1. Update the `from shared.tool_constants import (...)` block (currently lines
   7-13) to add the four new names, keeping the import list alphabetically
   sorted per `ruff` `I` rules.
2. Update the `_SIDE_EFFECT_TOOLS` frozenset expression (currently lines
   18-25) to union in the four new sets.
3. Update the one-line comment directly above `_SIDE_EFFECT_TOOLS` to mention
   CI/CD, RAG, and MDQ write/admin tools.
4. Do not touch `is_side_effect()`, `format_transport_error()`, or
   `tool_hash_key()` function bodies.

### Method

Additive edit to one import block and one frozenset literal; run `ruff
format`/`ruff check --fix` afterward to normalize import ordering rather than
hand-sorting.

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
    MDQ_SERIAL_TOOLS,
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
# CI/CD workflow triggers, RAG document deletion, or MDQ index write/admin ops.
# Used to auto-downgrade parallel execution to serial in execute_all_tool_calls(),
# and (via is_side_effect()) as the write-classification source for
# tool_runner.py's _build_tool_meta().
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS
    | RAG_WRITE_TOOLS
    | MDQ_WRITE_TOOLS
    | MDQ_SERIAL_TOOLS
)
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-150757_tool_constants.py.md` applied first | New names importable |
| Format/lint | `uv run ruff format scripts/shared/tool_executor_helpers.py && uv run ruff check scripts/shared/tool_executor_helpers.py` | 0 errors, import order correct |
| Type check | `uv run mypy scripts/shared/tool_executor_helpers.py` | 0 new errors |
| Unit tests | `uv run pytest tests/test_tool_executor_helpers.py -v` | All existing tests pass unchanged |
| New coverage | New tests added per `implementations/20260715-150757_test_tool_executor_helpers.py.md` | `is_side_effect("trigger_workflow")`, `is_side_effect("rag_delete_document")`, `is_side_effect("index_paths")`, `is_side_effect("refresh_index")`, `is_side_effect("fts_rebuild")` all `True` |
| Regression | `uv run pytest tests/test_tool_constants.py -v` | No disjointness assertions broken (sets are additive, `GIT_TOOLS`/`GITHUB_TOOLS` untouched) |
