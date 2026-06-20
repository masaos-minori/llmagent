# Implementation: test_tool_executor_helpers.py + test_tool_loop_guard.py (update — test rename)

## Goal

Update `tests/test_tool_executor_helpers.py` and `tests/test_tool_loop_guard.py` to
use `tool_hash_key` instead of `tool_call_key`, consistent with the production code rename.

## Scope

**In:**
- `test_tool_executor_helpers.py`: rename import + all 4 test function names + all call sites
- `test_tool_loop_guard.py`: rename import + call site

**Out:**
- Test logic changes
- Adding new test cases

## Assumptions

- The production rename in `tool_executor.py`, `tool_loop_guard.py`, `tool_runner.py`
  has been applied first
- `grep "tool_call_key" tests/test_tool_executor_helpers.py` returns 10 lines;
  all must be replaced

## Implementation

### Target files

- `tests/test_tool_executor_helpers.py`
- `tests/test_tool_loop_guard.py`

### Procedure

#### test_tool_executor_helpers.py

Apply a global rename across the entire file — replace every occurrence of
`tool_call_key` with `tool_hash_key`:

```
Replace all (replace_all=true):
  old: tool_call_key
  new: tool_hash_key
```

Affected lines (current):
- Line 4 (module docstring): `- tool_call_key: ...`
- Line 8 (import): `from shared.tool_executor import is_side_effect, tool_call_key`
- Line 11 (function name): `def test_tool_call_key_consistency() -> None:`
- Line 12 (docstring): `"""Test that tool_call_key generates ...`
- Lines 14, 15, 19, 23, 27, 28 (call sites): `tool_call_key(...)`
- Line 32 (function name): `def test_tool_call_key_hash_format() -> None:`
- Line 33 (docstring): `"""Test that tool_call_key returns ...`
- Line 34 (call site): `key = tool_call_key(...)`
- Line 77 (function name): `def test_tool_call_key_with_complex_args() -> None:`
- Lines 92, 93 (call sites)
- Line 97 (function name): `def test_tool_call_key_empty_args() -> None:`
- Lines 99, 100 (call sites)

#### test_tool_loop_guard.py

Two lines to update:

1. Line 180 (import):
   ```
   - from shared.tool_executor import tool_call_key
   + from shared.tool_executor import tool_hash_key
   ```
2. Line 184 (call):
   ```
   - failed: set[str] = {tool_call_key("write_file", {})}
   + failed: set[str] = {tool_hash_key("write_file", {})}
   ```

### Details

- Module docstring update in `test_tool_executor_helpers.py` line 4 is important for
  traceability — update from `"tool_call_key: ..."` to `"tool_hash_key: ..."`
- All test function names change: `test_tool_call_key_*` → `test_tool_hash_key_*`
- No test logic changes — assertions, fixtures, and test structure are identical

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old name absent (helpers) | `grep -n "tool_call_key" tests/test_tool_executor_helpers.py` | 0 matches |
| Old name absent (loop_guard) | `grep -n "tool_call_key" tests/test_tool_loop_guard.py` | 0 matches |
| All helpers tests pass | `uv run pytest tests/test_tool_executor_helpers.py -x -v` | all pass, function names updated |
| Loop guard tests pass | `uv run pytest tests/test_tool_loop_guard.py -x -v` | all pass |
| No stale tool_call_key in codebase | `grep -rn "tool_call_key" scripts/ tests/` | 0 matches |
