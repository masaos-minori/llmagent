# Step 4 — Add strict-mode startup validation tests

## Goal

Add a `TestStartupValidationStrictMode` test class to `tests/test_tool_registry.py` covering the four live-vs-registry drift conditions that `check_routing_drift_vs_live()` (added in Step 2) must detect.

## Scope

- **In-Scope:**
  - Add class `TestStartupValidationStrictMode` at the end of `tests/test_tool_registry.py`.
  - Add four test methods covering the conditions listed in the plan.
  - Import `build_discovery_map` from `shared.route_resolver` (needed for test 4).

- **Out-of-Scope:**
  - Do not modify existing test classes (`TestValidateRoutingDriftRegistry`, `TestDuplicateOwnershipRejection`, `TestValidateRoutingAgainstLive`, `TestValidateAllRouting`).
  - Do not add integration-level tests that call `check_routing_drift_vs_live()` directly (that requires `AgentContext`).

## Assumptions

1. `validate_routing_against_live(registry, live_tool_lists)` already detects conditions 1-3; these tests confirm the return values.
2. `build_discovery_map()` already logs a warning for duplicate live tool ownership (condition 4); the test uses `caplog` to verify the warning.
3. `reset_registry()` / isolated `ToolRegistry()` instances are used to avoid cross-test state contamination.
4. The existing test at line 88 (`test_owner_mismatch_detected`) already covers a variant of condition 3; the new test uses a more explicit cross-server assignment scenario.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_tool_registry.py`

### Procedure

1. **Add import** for `build_discovery_map` at the top of the file. Modify the existing import block:
   ```python
   from shared.route_resolver import build_discovery_map
   ```
   Add this line after the existing imports from `shared.tool_registry`.

2. **Append the new test class** at the end of the file:

   ```python
   class TestStartupValidationStrictMode:
       """Tests for the four strict-mode drift conditions checked at startup.

       These tests verify the behavior of validate_routing_against_live() and
       build_discovery_map() for each condition that check_routing_drift_vs_live()
       must detect.
       """

       def test_live_returns_tool_not_in_registry(self) -> None:
           """Condition 1: live response includes a tool not in the registry.

           validate_routing_against_live() must return a non-empty drift dict.
           """
           registry = ToolRegistry()
           registry.register(ToolDefinition(name="tool_a", server_key="server_x"))
           # live response includes extra_tool not registered anywhere
           drift = validate_routing_against_live(registry, {"server_x": ["tool_a", "extra_tool"]})
           assert "server_x" in drift
           assert any("extra_tool" in msg for msg in drift["server_x"])

       def test_live_omits_registry_tool_for_server(self) -> None:
           """Condition 2: registry owns a tool for a server, but live response omits it.

           validate_routing_against_live() must detect the missing tool.
           """
           registry = ToolRegistry()
           registry.register(ToolDefinition(name="tool_a", server_key="server_x"))
           registry.register(ToolDefinition(name="tool_b", server_key="server_x"))
           # live response for server_x is missing tool_b
           drift = validate_routing_against_live(registry, {"server_x": ["tool_a"]})
           assert "server_x" in drift
           assert any("tool_b" in msg for msg in drift["server_x"])

       def test_live_returns_tool_under_wrong_server(self) -> None:
           """Condition 3: registry maps tool_x to server_a, but live returns it under server_b.

           validate_routing_against_live() must report a mismatch for server_b
           (tool present in live but not registered to server_b) and for server_a
           (tool registered to server_a but absent from its live response).
           """
           registry = ToolRegistry()
           registry.register(ToolDefinition(name="tool_x", server_key="server_a"))
           # server_a live response is empty (omits tool_x)
           # server_b live response includes tool_x (wrong server)
           drift = validate_routing_against_live(
               registry,
               {"server_a": [], "server_b": ["tool_x"]},
           )
           # server_b: tool_x in live but not in registry for server_b
           assert "server_b" in drift
           assert any("tool_x" in msg for msg in drift["server_b"])
           # server_a: tool_x in registry but not in live
           assert "server_a" in drift
           assert any("tool_x" in msg for msg in drift["server_a"])

       def test_duplicate_live_ownership_detected(
           self, caplog: pytest.LogCaptureFixture
       ) -> None:
           """Condition 4: same tool returned by two different servers.

           build_discovery_map() must log a WARNING about the duplicate.
           """
           import logging

           with caplog.at_level(logging.WARNING):
               result = build_discovery_map(
                   {
                       "server_a": [{"name": "shared_tool", "server_key": "server_a"}],
                       "server_b": [{"name": "shared_tool", "server_key": "server_b"}],
                   }
               )
           # First occurrence wins
           assert result == {"shared_tool": "server_a"}
           # Warning must have been logged
           assert any(
               "shared_tool" in r.message
               for r in caplog.records
               if r.levelno >= logging.WARNING
           )
   ```

### Method

- Tests 1-3 use isolated `ToolRegistry()` instances (not the global singleton) to avoid state contamination.
- Test 4 uses `build_discovery_map()` from `shared.route_resolver` directly; it does not depend on registry state.
- Use `caplog` fixture (already used in `TestBuildDiscoveryMap` at line 219) for log assertion.
- Follow the existing naming convention: `test_<condition_description>` as seen in `TestValidateRoutingAgainstLive`.

### Details

- Import to add: `from shared.route_resolver import build_discovery_map` — add after line 19 (after the last `shared.tool_registry` import).
- New class appended after `TestValidateAllRouting` (after line 138, end of file).
- `validate_routing_against_live` is already imported at line 19; no additional import needed for tests 1-3.
- `ToolDefinition` and `ToolRegistry` are already imported at lines 12-13; no new imports needed for registry construction.
- The `logging` import inside `test_duplicate_live_ownership_detected` is local to avoid polluting module scope; alternatively, add `import logging` at module top (preferred if the file doesn't already have it).

## Validation plan

```bash
# Run only the new test class
uv run pytest tests/test_tool_registry.py::TestStartupValidationStrictMode -v

# Confirm all four tests are green
uv run pytest tests/test_tool_registry.py -v -k "StrictMode"

# Run the full tool registry test suite to confirm no regressions
uv run pytest tests/test_tool_registry.py -v
```

Expected: all four new tests pass; no existing tests regress; total test count in `test_tool_registry.py` increases by 4.
