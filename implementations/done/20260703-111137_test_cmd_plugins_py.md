## Goal

Update `test_cmd_plugins.py` to use the renamed `command_shadows_rejected` field on `PluginLoadResult` and the updated row label `"Command shadows (rejected)"`.

## Scope

- In-Scope:
  - `test_result_writes_table`: update `PluginLoadResult` construction to not rely on old field (currently no `command_shadows` arg — uses default; verify it stays valid after rename)
  - Add assertion for the `"Command shadows (rejected)"` row label if not already tested
- Out-of-Scope:
  - Other test methods in `TestCmdPlugin`
  - Any change to `_make_mixin()` or fixture setup

## Assumptions

1. `PluginLoadResult.command_shadows` has been renamed to `command_shadows_rejected` in `plugin_registry.py` before this step.
2. In the current `test_result_writes_table` (lines 26–43), the `PluginLoadResult` is constructed **without** passing `command_shadows` (only `loaded_count`, `failed`, `tool_conflicts_shadowed`, `tool_conflicts_allowed`). After renaming, default value `command_shadows_rejected=0` applies — the construction itself requires no change.
3. No current assertion in `test_result_writes_table` checks for a `"Command shadows"` row by label. If such an assertion is absent, the only required change is to add a row-label assertion for `"Command shadows (rejected)"` to protect against future regressions, following the plan requirement.
4. If a row-label assertion for `"Command shadows"` does exist (it does not in the current file), it must be updated to `"Command shadows (rejected)"`.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_cmd_plugins.py`

### Procedure

1. Inspect `test_result_writes_table` (lines 26–43) for any reference to `command_shadows`:
   - Current code constructs `PluginLoadResult(loaded_count=3, failed=(), tool_conflicts_shadowed=1, tool_conflicts_allowed=0)` — no `command_shadows` kwarg. This is already valid after rename (default field is used).
   - No assertion currently checks the `"Command shadows"` row label.

2. Add an assertion for the renamed row label inside `test_result_writes_table`, after the existing `loaded_row` assertion:
   ```python
   shadow_row = next(r for r in rows if r[0] == "Command shadows (rejected)")
   assert shadow_row[1] == "0"  # default value
   ```

3. If any other test method constructs `PluginLoadResult(command_shadows=N)`, update to `command_shadows_rejected=N`. Based on current inspection, no other method does this.

### Method

- Pattern for row lookup: same as existing `loaded_row = next(r for r in rows if r[0] == "Loaded")` at line 41.
- The `shadow_row` assertion value is `"0"` because the test `PluginLoadResult` uses the default (`command_shadows_rejected=0`).

### Details

- **Current `test_result_writes_table` full picture (lines 26–43):** constructs result with `loaded_count=3`, no `command_shadows` kwarg. After rename, the dataclass default `command_shadows_rejected=0` is used automatically — no constructor change needed.
- **Row assertion to add:** validates that `cmd_plugins.py` outputs the correct label `"Command shadows (rejected)"`. This closes the test gap identified in the plan.
- **`PluginLoadResult` import:** already present at line 28 (`from shared.plugin_registry import PluginLoadResult`).

## Validation plan

```bash
# Run the specific test file
uv run pytest tests/test_cmd_plugins.py -v

# Check no reference to old field name remains
grep 'command_shadows' tests/test_cmd_plugins.py
# Expected: zero lines OR only lines containing 'command_shadows_rejected'

# Lint
uv run ruff check tests/test_cmd_plugins.py
```

Expected outcomes:
- All 4 tests in `TestCmdPlugin` pass
- `grep` finds no reference to old field name `command_shadows` without `_rejected` suffix
