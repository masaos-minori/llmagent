## Goal

Modify `_validate_command_conflicts()` to reject (delete) shadowed plugin commands from `_commands`, rename `PluginLoadResult.command_shadows` to `command_shadows_rejected`, change the function's return type to `tuple[int, list[str]]`, and wire the rejected names into the strict-mode `PluginLoadError` message.

## Scope

- In-Scope:
  - Add `del _commands[name]` inside `_validate_command_conflicts()` after counting the shadow (mirrors `_validate_tool_conflicts()` pattern)
  - Add `strict_rejected: list[str]` accumulator inside `_validate_command_conflicts()`
  - Change return type from `int` to `tuple[int, list[str]]`
  - Update `load_plugins()` call site to unpack the new tuple
  - Add `"Command builtin conflicts rejected: ..."` part to the strict-mode `PluginLoadError` message in `load_plugins()`
  - Rename `PluginLoadResult.command_shadows` field to `command_shadows_rejected`
  - Update the one assignment in `load_plugins()`: `command_shadows=cmd_shadows` → `command_shadows_rejected=cmd_shadows`
  - Update module-level docstring line referencing `command_shadows`
  - Update `_validate_command_conflicts()` docstring to say "reject" not "warn"
- Out-of-Scope:
  - `_validate_tool_conflicts()` logic (no changes)
  - Any caller outside this file (handled in separate docs)
  - Adding new public API functions
  - Changing `_reset_for_testing()` or other accessors

## Assumptions

1. `_validate_command_conflicts()` is only called from one site: `load_plugins()` at line 389. Confirmed by grep — no other caller.
2. The `PluginLoadResult` dataclass is `frozen=True`; renaming `command_shadows` to `command_shadows_rejected` is a backward-incompatible change. All callers (`cmd_plugins.py`, `test_cmd_plugins.py`) must be updated in their own steps.
3. The `strict_rejected` list should only be populated when `strict_mode=True`, matching the tool conflict pattern in `_validate_tool_conflicts()` (line 291: `if strict_mode: strict_rejected.append(tool_name)`).
4. The strict-mode aggregation in `load_plugins()` currently checks `if strict_mode and (failures or strict_rejected)` (line 391). After this change, the condition must also include the command shadow strict_rejected list; the simplest correct approach is to pass both lists and join.
5. Returning `(count, [])` in the non-strict path is safe — the empty list is ignored by the caller.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/shared/plugin_registry.py`

### Procedure

1. Rename `PluginLoadResult.command_shadows` field to `command_shadows_rejected` (line 253 of the current file). Change `command_shadows: int = 0` to `command_shadows_rejected: int = 0`.
2. Update the module-level docstring (line 147 of the current file): replace `command_shadows` with `command_shadows_rejected` in the `PluginLoadResult` fields reference.
3. Update `_validate_command_conflicts()` signature and body:
   a. Change return type annotation from `-> int` to `-> tuple[int, list[str]]`.
   b. Update docstring: change "Warn when" to "Reject" and note that commands are removed from `_commands` and counted.
   c. Add `strict_rejected: list[str] = []` before the `for name in list(_commands.keys()):` loop.
   d. Inside the `if name in _builtin_command_names:` block, add `del _commands[name]` immediately after incrementing `shadowed_count`. Place it before the `logger.info(...)` call.
   e. Inside the same block, add `if strict_mode: strict_rejected.append(name)` after the deletion.
   f. Update the log message from `"[plugin] command shadow: '%s' in '%s' shadows built-in"` to `"[plugin] command shadow rejected: '%s' in '%s' shadows built-in"` (new canonical log format per doc plan).
   g. Remove the existing strict-mode `logger.error(...)` block (lines 329–332 in current file) — it is replaced by the aggregation in `load_plugins()`.
   h. Change the final `return shadowed_count` to `return (shadowed_count, strict_rejected)`.
4. Update `load_plugins()` at the call site (line 389):
   a. Change `cmd_shadows = _validate_command_conflicts(strict_mode)` to `cmd_shadows, cmd_strict_rejected = _validate_command_conflicts(strict_mode)`.
5. Update `load_plugins()` strict-mode aggregation block (lines 391–398):
   a. Change the condition from `if strict_mode and (failures or strict_rejected):` to `if strict_mode and (failures or strict_rejected or cmd_strict_rejected):`.
   b. Add a third `if cmd_strict_rejected:` branch appending `f"Command builtin conflicts rejected: {', '.join(cmd_strict_rejected)}"`.
6. Update `load_plugins()` `PluginLoadResult` construction (line 400–406): change `command_shadows=cmd_shadows` to `command_shadows_rejected=cmd_shadows`.

### Method

- Follow the exact pattern of `_validate_tool_conflicts()` for the deletion + strict accumulation:
  ```python
  # Existing pattern in _validate_tool_conflicts (lines 288-293):
  del _tools[tool_name]
  shadowed_count += 1
  if strict_mode:
      strict_rejected.append(tool_name)
  ```
- New return signature:
  ```python
  def _validate_command_conflicts(strict_mode: bool = False) -> tuple[int, list[str]]:
  ```
- Strict-mode message part to append in `load_plugins()`:
  ```python
  if cmd_strict_rejected:
      parts.append(f"Command builtin conflicts rejected: {', '.join(cmd_strict_rejected)}")
  ```
- `PluginLoadResult` field after rename:
  ```python
  @dataclass(frozen=True)
  class PluginLoadResult:
      loaded_count: int
      failed: tuple[PluginFailure, ...]
      tool_conflicts_shadowed: int = 0
      tool_conflicts_allowed: int = 0
      command_shadows_rejected: int = 0
  ```

### Details

- **File line references (current):**
  - `PluginLoadResult.command_shadows` field: line 253
  - `_validate_command_conflicts()` signature: line 307
  - `_validate_command_conflicts()` loop: lines 317–333
  - `load_plugins()` call to `_validate_command_conflicts()`: line 389
  - `load_plugins()` strict-mode block: lines 391–398
  - `load_plugins()` `PluginLoadResult` construction: lines 400–406
- **Log message change:** `"[plugin] command shadow:"` → `"[plugin] command shadow rejected:"` (also update the `logger.info` summary message from `"[plugin] command shadows: %d"` to `"[plugin] command shadows rejected: %d"`).
- **No change needed** to `register_builtin_commands()`, `get_command()`, `iter_commands()`, `_reset_for_testing()`.
- The `_validate_command_conflicts()` early-return `return 0` (line 314) must be updated to `return (0, [])` to match the new return type.

## Validation plan

```bash
# Type check
uv run mypy scripts/shared/plugin_registry.py

# Lint
uv run ruff check scripts/shared/plugin_registry.py

# Regression: existing tests pass
uv run pytest tests/test_plugin_registry.py -x -q

# Verify field rename — should find no remaining references to old name
grep -r 'command_shadows[^_]' scripts/ tests/ || echo 'CLEAN'
```

Expected outcomes:
- `mypy` reports no new type errors
- `ruff` reports no errors
- Existing tests that reference `result.command_shadows` will **fail** until `test_plugin_registry.py` and `test_cmd_plugins.py` are updated (addressed in separate docs)
- `grep` for old field name finds nothing in production code
