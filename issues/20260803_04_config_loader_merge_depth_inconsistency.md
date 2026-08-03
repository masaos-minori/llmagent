# ConfigLoader.load() merge depth does not match TestMergeOrder's nested-merge expectations

## Priority
Medium

## Summary
Four tests in `tests/shared/test_config_loader.py` (`TestMergeOrder` class) call
`ConfigLoader.load(...)` and expect nested dict values (e.g. `result["section"]["bar"]`,
`result["mcp_servers"]["server_a"]["url"]`) to be preserved across a merge of two files. They
fail because `load()` only performs a shallow, top-level `dict.update()` merge — it silently
drops sibling keys inside nested tables when a later file redefines the same top-level key.

## Reason for Change
`scripts/shared/config_loader.py` has two merge code paths with different semantics:
- `load()` (line 58): `merged.update(filtered)` — flat, top-level overwrite only.
- `load_all()` (~line 76): explicitly merges dict-valued keys one level deep, per its own
  docstring ("Dict-valued keys are merged one level deep so that multiple MCP server ...").

`TestMergeOrder`'s tests call `load()` but assert the one-level-deep merge behavior that only
`load_all()` actually provides. This is either (a) a test written against the wrong method, or
(b) evidence that `load()` should also do a shallow nested merge for consistency with
`load_all()` and currently silently loses data when TOML files define overlapping sections
(e.g. two MCP server config files both touching `[mcp_servers]`). Confirmed via direct
reproduction: running the exact `TestMergeOrder` assertions against `load()` fails with
`KeyError` on sibling keys that should have survived the merge.

## Implementation Intent
Determine which behavior is correct by checking real call sites of `load()` vs `load_all()`
across `scripts/` — if any caller relies on `load()` to merge multiple TOML files that both
define a nested table (e.g. `[mcp_servers]`), the shallow-merge behavior is a real bug with
production impact, not just a test issue. If no caller does this, the tests are simply
targeting the wrong method and should either call `load_all()` or have their expectations
corrected to match `load()`'s documented flat-merge behavior.

## Target Files or Areas
- `scripts/shared/config_loader.py` (`load()` line ~58, `load_all()` line ~76)
- `tests/shared/test_config_loader.py` (`TestMergeOrder` class)
- Unknown: call sites of `ConfigLoader.load()` across `scripts/` that pass multiple filenames

## Required Changes
- Audit all `ConfigLoader.load(...)` call sites that pass more than one filename.
- If any rely on nested merge semantics: align `load()`'s merge logic with `load_all()`'s
  one-level-deep dict merge, add a regression test pinning the corrected behavior.
- If none do: fix `TestMergeOrder` to call `load_all()` instead of `load()`, or adjust its
  assertions to the documented flat-overwrite behavior of `load()`.

## Acceptance Criteria
- `pytest tests/shared/test_config_loader.py::TestMergeOrder` passes.
- The chosen resolution (align `load()` with `load_all()`, or fix the test) is stated explicitly
  in the fix's commit/PR description, with the call-site audit result as justification.
- No other `ConfigLoader` test regresses.

## Testing Expectations
Unit tests. Run `PYTHONPATH=scripts pytest tests/shared/test_config_loader.py -v` after the fix.
If `load()`'s merge logic changes, add a regression test using two TOML files with overlapping
nested sections (mirroring the existing `test_nested_dict_merge` case) to lock the corrected
behavior in permanently.

## Documentation Impact
If `load()`'s merge behavior changes, update its docstring to state the new one-level-deep
merge semantics explicitly (currently it has no merge-depth note at all, unlike `load_all()`).

## Out of Scope
- Do not change `load_all()`'s existing behavior — only `load()` is in question.
- Do not touch unrelated `ConfigLoader` tests (`TestRestrictToIsolation`,
  `TestExtensionResolution`, `TestGlobalStateCleanup`, `TestTOMLLoading`, `TestJSONLoading`,
  `TestErrors`, `TestCustomExceptionTypes`, `TestLoadAllStrictMode`) unless the merge fix
  requires it.

## AI Implementation Instruction
Grep all of `scripts/` for `\.load(` call sites first and read each one's context before
deciding whether to change production merge logic — a production behavior change here affects
every caller that merges multiple config files. If in doubt about whether the shallow-merge
behavior is load-bearing, stop and report the call sites found rather than guessing.
