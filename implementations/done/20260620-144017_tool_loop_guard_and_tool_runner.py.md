# Implementation: tool_loop_guard.py + tool_runner.py (update — import rename)

## Goal

Update `scripts/agent/tool_loop_guard.py` and `scripts/agent/tool_runner.py` to import
and call `tool_hash_key` instead of the renamed `tool_call_key`, following the rename
in `tool_executor.py`.

## Scope

**In:**
- `tool_loop_guard.py` line 18: update import
- `tool_loop_guard.py` line 157: update function call
- `tool_runner.py` line 22: update import
- `tool_runner.py` line 141: update function call

**Out:**
- Logic changes in either file
- Other imports or function calls

## Assumptions

- `tool_executor.py` rename has been applied first (see `20260620-144016_tool_executor.py.md`)
- Both files import from `shared.tool_executor`; no intermediate re-export module exists

## Implementation

### Target files

- `scripts/agent/tool_loop_guard.py`
- `scripts/agent/tool_runner.py`

### Procedure

#### tool_loop_guard.py

1. Line 18 — update import:
   ```
   - from shared.tool_executor import tool_call_key
   + from shared.tool_executor import tool_hash_key
   ```
2. Line 157 — update call:
   ```
   - if tool_call_key(func.get("name", ""), tc_args) in failed_calls:
   + if tool_hash_key(func.get("name", ""), tc_args) in failed_calls:
   ```

#### tool_runner.py

1. Line 22 — update import:
   ```
   - from shared.tool_executor import is_side_effect, tool_call_key
   + from shared.tool_executor import is_side_effect, tool_hash_key
   ```
2. Line 141 — update call:
   ```
   - out_failed_keys.add(tool_call_key(name, args))
   + out_failed_keys.add(tool_hash_key(name, args))
   ```

### Details

- No other lines in either file reference `tool_call_key`
- Alphabetical order of imports in `tool_runner.py` is preserved
  (`is_side_effect` < `tool_hash_key` alphabetically — confirm order after edit)

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old name absent (loop_guard) | `grep -n "tool_call_key" scripts/agent/tool_loop_guard.py` | 0 matches |
| Old name absent (runner) | `grep -n "tool_call_key" scripts/agent/tool_runner.py` | 0 matches |
| New name present (loop_guard) | `grep -n "tool_hash_key" scripts/agent/tool_loop_guard.py` | 2 matches (import + call) |
| New name present (runner) | `grep -n "tool_hash_key" scripts/agent/tool_runner.py` | 2 matches (import + call) |
| Lint | `uv run ruff check scripts/agent/tool_loop_guard.py scripts/agent/tool_runner.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/tool_loop_guard.py scripts/agent/tool_runner.py` | 0 errors |
| Loop guard tests | `uv run pytest tests/test_tool_loop_guard.py -x -v` | all pass |
| Tool runner tests | `uv run pytest tests/test_tool_runner.py -x -v` | all pass |
