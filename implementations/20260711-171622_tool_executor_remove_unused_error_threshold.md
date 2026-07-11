# Implementation: Remove unused `repeated_tool_error_threshold` constructor parameter

## Goal

Remove the `repeated_tool_error_threshold` constructor parameter from `ToolExecutor`
in `scripts/shared/tool_executor.py`, along with its storage attribute
`self._tool_error_threshold`, since it is confirmed 100% dead code with zero callers
passing a non-default value anywhere in the codebase.

## Scope

**In-Scope:**
- `scripts/shared/tool_executor.py::ToolExecutor.__init__`: remove the
  `repeated_tool_error_threshold: int = 3` parameter (line 66) and the
  `self._tool_error_threshold = repeated_tool_error_threshold` assignment (line 77).

**Out-of-Scope:**
- `LifecycleProtocol` consolidation — handled in a separate phase/document
  (same target file, different concern).
- Any new threshold-triggered behavior — explicitly not implemented; this is a removal,
  not a reimplementation (per the plan's Assumption 4).
- Any caller in `scripts/` or `tests/` — confirmed to have zero non-default usages, so
  no caller update is needed.

## Assumptions

1. `repeated_tool_error_threshold` (`tool_executor.py:66,77`) is accepted as a
   constructor parameter and stored as `self._tool_error_threshold`, but is never read
   again anywhere in the file — confirmed via
   `grep -n "repeated_tool_error_threshold\|_tool_error_threshold" scripts/shared/tool_executor.py`
   during plan research.
2. `grep -rn "repeated_tool_error_threshold" scripts/ tests/` (excluding its own
   definition) confirms zero callers pass a non-default value anywhere in the
   codebase — removal is behavior-preserving for every existing caller.
3. No test constructs `ToolExecutor(repeated_tool_error_threshold=...)` — confirmed by
   the same grep; test suite is unaffected by the removal.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Open `ToolExecutor.__init__`'s signature.
2. Remove the `repeated_tool_error_threshold: int = 3` parameter from the parameter
   list (line 66), adjusting trailing commas/formatting as needed for the remaining
   parameters.
3. Remove the line `self._tool_error_threshold = repeated_tool_error_threshold`
   (line 77) from the constructor body.
4. Re-run a repo-wide search
   (`grep -rn "repeated_tool_error_threshold\|_tool_error_threshold" scripts/ tests/`)
   to confirm no remaining references exist after the edit.
5. Confirm no docstring on `__init__` (if present) documents this parameter; if it
   does, remove that documentation line too.

### Method

```python
# Before (illustrative signature fragment)
def __init__(
    self,
    ...,
    repeated_tool_error_threshold: int = 3,
) -> None:
    ...
    self._tool_error_threshold = repeated_tool_error_threshold

# After
def __init__(
    self,
    ...,
) -> None:
    ...
    # (assignment line removed; no replacement needed)
```

### Details

- This is a pure deletion — no replacement logic, no deprecation shim, since the
  parameter has no live callers and the requirement's resolved decision is "remove,"
  not "implement."
- This is a public constructor signature change. Per the plan's Risks section, this is
  accepted because the codebase's established convention (this session) is to remove
  confirmed-dead configuration parameters rather than preserve indefinite backward
  compatibility for zero-usage settings. Do not add a deprecated keyword-only fallback.
- Verify no other attribute or method in the class reads `self._tool_error_threshold`
  before deleting — the plan's research already confirmed this via full-file grep, but
  re-confirm at implementation time since line numbers may have shifted after the
  `LifecycleProtocol` phase's edits land first.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_executor.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Tests | `uv run pytest tests/test_tool_executor.py tests/test_tool_executor_order.py tests/test_tool_executor_routing.py -v` | All pass; no test constructs `ToolExecutor(repeated_tool_error_threshold=...)`, so removal breaks nothing |
| Regression | `grep -rn "repeated_tool_error_threshold" scripts/ tests/` | No remaining references anywhere |
