## Goal

Expand the `_reset_for_testing()` function docstring in `scripts/shared/plugin_registry.py` to explicitly forbid production use and verify the module-level lifecycle docstring already covers all four required documentation points.

## Scope

- In-Scope:
  - Replace the single-line `_reset_for_testing()` docstring (line 429) with a multi-line docstring that covers: what the function does, that it is for test use only, that production code must not call it, and when to call it in tests.
  - Verify (read-only check) that the module-level docstring (lines 35-51) already contains all four required points; add any missing point under the `Test isolation:` block if absent.
- Out-of-Scope:
  - Behavior changes to any function.
  - Inline comments on `_commands`, `_tools`, `_pipeline_post` declarations (already reference `_reset_for_testing()` as clearing mechanism per lines 89-94).
  - Any other file.

## Assumptions

1. The module-level docstring already contains the four required points (lines 35-51): `load_plugins()` startup-only, repeated calls accumulate, `_reset_for_testing()` is the only supported clearing mechanism, non-test code must not call it. Verification is needed before deciding whether to edit.
2. The current `_reset_for_testing()` docstring at line 429 is `"""Clear all registries. For test use only. Do not call from production code."""` — a single short line that lacks detail about when to call it in tests.
3. Replacing the docstring with a multi-line version has zero behavior impact (docstrings are not executed).
4. `uv run pytest` is the correct invocation per MEMORY.md.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/shared/plugin_registry.py`

### Procedure

1. Read lines 35-51 of `/home/masaos/llmagent/scripts/shared/plugin_registry.py` to confirm all four lifecycle documentation points are present in the module docstring. If any are missing, add them inside the `Test isolation:` block before the `Reload:` block.
2. Locate line 429: `def _reset_for_testing() -> None:` and its current single-line docstring.
3. Replace the single-line docstring with the following multi-line docstring (exact text from plan Step 1):
   ```python
   def _reset_for_testing() -> None:
       """Clear all registries and reset module-level state.

       For test use only. Do not call from production code.
       Call at the start (and optionally end) of each test that loads plugins
       or registers commands/tools directly. This is the only supported way
       to clear global registry state between tests.
       """
   ```
4. Verify no other lines changed by running a targeted diff.
5. Run `uv run pytest tests/test_plugin_registry.py -v` to confirm all tests pass.

### Method

- Use the Edit tool with `old_string` = the current one-line docstring and `new_string` = the multi-line replacement.
- The current docstring text to match: `"""Clear all registries. For test use only. Do not call from production code."""`

### Details

- Target location: `/home/masaos/llmagent/scripts/shared/plugin_registry.py`, line 429 (the `_reset_for_testing` function body).
- Existing single-line docstring (exact text): `"""Clear all registries. For test use only. Do not call from production code."""`
- The module-level docstring `Test isolation:` block (lines 45-48) already states the required points. If a point is missing, insert it before the closing blank line of the block.
- No imports or function signatures change.

## Validation plan

```bash
# Confirm docstring is multi-line
grep -A 6 'def _reset_for_testing' /home/masaos/llmagent/scripts/shared/plugin_registry.py

# Confirm no production callers added
grep -rn '_reset_for_testing' /home/masaos/llmagent/scripts/ | grep -v 'plugin_registry.py'

# Run plugin registry tests
uv run pytest tests/test_plugin_registry.py -v
```

Expected: grep on scripts/ returns only the definition in `plugin_registry.py`; all plugin registry tests pass.
