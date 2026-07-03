## Goal

Consolidate the four inline `_reset_for_testing()` calls in `TestToolExecutorExecute` into a single class-level autouse fixture, removing ad-hoc reset calls from test method bodies.

## Scope

- In-Scope:
  - Add a `@pytest.fixture(autouse=True)` method `_reset_plugin_registry` to `TestToolExecutorExecute` that calls `plugin_registry._reset_for_testing()` before `yield` and after `yield`.
  - Remove the four inline `plugin_registry._reset_for_testing()` calls from `test_plugin_tool_success_returns_empty_x_request_id` (lines 288, 300) and `test_plugin_tool_error_returns_empty_x_request_id` (lines 303, 316).
- Out-of-Scope:
  - Any other test class in this file.
  - Any test logic or assertion changes.
  - Import additions (plugin_registry is already imported at line 14).

## Assumptions

1. `plugin_registry` is already imported at the top of the file as `import shared.plugin_registry as plugin_registry` (confirmed at line 14).
2. The two affected test methods (`test_plugin_tool_success_returns_empty_x_request_id`, `test_plugin_tool_error_returns_empty_x_request_id`) each call `_reset_for_testing()` at both start and end, totaling 4 calls. The fixture replaces exactly these calls without changing test behavior.
3. No test in `TestToolExecutorExecute` relies on registry state left by a preceding test method; all tests start clean.
4. A class-scoped `pytest.fixture(autouse=True)` defined as a method in the class is equivalent in isolation guarantees to the current manual pattern.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_executor_routing.py`

### Procedure

1. In `TestToolExecutorExecute` (starts at line 285), add the following fixture method immediately before `test_plugin_tool_success_returns_empty_x_request_id`:
   ```python
   @pytest.fixture(autouse=True)
   def _reset_plugin_registry(self):
       plugin_registry._reset_for_testing()
       yield
       plugin_registry._reset_for_testing()
   ```
2. In `test_plugin_tool_success_returns_empty_x_request_id` (lines 287-300):
   - Remove the `plugin_registry._reset_for_testing()` call on line 288 (before the decorator).
   - Remove the `plugin_registry._reset_for_testing()` call on line 300 (after assertions).
3. In `test_plugin_tool_error_returns_empty_x_request_id` (lines 302-316):
   - Remove the `plugin_registry._reset_for_testing()` call on line 303 (before the decorator).
   - Remove the `plugin_registry._reset_for_testing()` call on line 316 (after assertions).
4. Run the tests to verify no regressions.

### Method

- Use Edit tool for each removal (4 separate edits, or combine per method).
- The fixture must be a method (not a module-level function) to be auto-applied only to the class.
- `yield`-based fixture ensures teardown runs even if a test raises.

### Details

- Current line 285: `class TestToolExecutorExecute:`
- Current line 287: `    @pytest.mark.asyncio`
- Current line 288: `    async def test_plugin_tool_success_returns_empty_x_request_id(self) -> None:`
- Current line 289: `        plugin_registry._reset_for_testing()`  ← remove this
- Current line 300: `        plugin_registry._reset_for_testing()`  ← remove this (last line of first test)
- Current line 303: `    async def test_plugin_tool_error_returns_empty_x_request_id(self) -> None:`
- Current line 304: `        plugin_registry._reset_for_testing()`  ← remove this
- Current line 316: `        plugin_registry._reset_for_testing()`  ← remove this (last line of second test)
- After edits, `_reset_for_testing()` must not appear in any test method body in this file.

## Validation plan

```bash
# Confirm no inline resets remain in test method bodies
grep -n '_reset_for_testing' /home/masaos/llmagent/tests/test_tool_executor_routing.py

# Run targeted tests
uv run pytest tests/test_tool_executor_routing.py::TestToolExecutorExecute -v

# Run full file to check no regressions
uv run pytest tests/test_tool_executor_routing.py -v
```

Expected: `grep` shows `_reset_for_testing` only in the fixture definition (not in test method bodies); all tests in the file pass.
