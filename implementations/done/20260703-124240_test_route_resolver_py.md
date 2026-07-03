# Step 3 — Replace tests asserting discovery wins over registry

## Goal

Replace `TestLiveDiscoveryRouting.test_discovery_wins_over_registry` with a test proving the registry wins when `discovery_map` and registry disagree, and rename the test class to reflect its new validation-only purpose.

## Scope

- **In-Scope:**
  - Delete `test_discovery_wins_over_registry` (lines 259-264 in `TestLiveDiscoveryRouting`).
  - Rename `TestLiveDiscoveryRouting` to `TestDiscoveryMapValidationOnly`.
  - Update the renamed class's docstring.
  - Add new test `test_discovery_map_does_not_override_registry` inside the renamed class.
  - Retain the four surviving tests: `test_registry_fallback_when_tool_not_in_discovery_map`, `test_empty_discovery_map_falls_through_to_registry`, `test_unknown_tool_raises_regardless_of_discovery_map`, `test_discovery_map_none_falls_through_to_registry`.

- **Out-of-Scope:**
  - Do not modify `TestRegistryRouting`, `TestConfigDrivenRouting`, `TestRegistryWithoutConfig`, or `TestBuildDiscoveryMap`.
  - Do not change `_log_routing_coverage()` tests; the method is tested indirectly via `known_tools` parameter.

## Assumptions

1. After Step 1 (removal of Priority 1 block from `resolve()`), passing `discovery_map={"read_text_file": "custom_server"}` will no longer affect routing — `resolve("read_text_file")` will return `"file_read"` from the registry.
2. The four surviving tests in `TestLiveDiscoveryRouting` remain semantically correct after Step 1 (they already test registry-fallback behavior or raise behavior, not discovery override).
3. `read_text_file` is in `READ_TOOLS` and is registered to `"file_read"` in the default registry — confirmed in `TestRegistryRouting.test_read_tools` (line 34).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_route_resolver.py`

### Procedure

1. **Rename the class** at line 250: Change:
   ```python
   class TestLiveDiscoveryRouting:
       """Tests for live-discovery-wins-over-registry routing priority."""
   ```
   to:
   ```python
   class TestDiscoveryMapValidationOnly:
       """Tests proving discovery_map does NOT override registry routing.

       The discovery_map parameter is retained for backward compatibility with
       integration tests that route synthetic tool names, but it has no effect
       on routing results — ToolRegistry is the sole routing authority.
       """
   ```

2. **Delete `test_discovery_wins_over_registry`** (lines 259-264):
   Remove the entire method:
   ```python
   def test_discovery_wins_over_registry(self) -> None:
       """Discovery map overrides registry routing for the same tool."""
       configs = self._make_configs()
       discovery_map = {"read_text_file": "custom_server"}
       resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
       assert resolver.resolve("read_text_file") == "custom_server"
   ```

3. **Add `test_discovery_map_does_not_override_registry`** in its place (at the beginning of the class body, after the `_make_configs` helper):
   ```python
   def test_discovery_map_does_not_override_registry(self) -> None:
       """Registry routing wins even when discovery_map maps the tool to a different server."""
       configs = self._make_configs()
       discovery_map = {"read_text_file": "custom_server"}
       resolver = ToolRouteResolver(configs, discovery_map=discovery_map)
       # Registry maps read_text_file → file_read; discovery_map must not override it.
       assert resolver.resolve("read_text_file") == "file_read"
   ```

4. **Verify the four surviving tests** are unchanged:
   - `test_registry_fallback_when_tool_not_in_discovery_map` (line 266): Already tests registry fallback — correct post-Step 1.
   - `test_empty_discovery_map_falls_through_to_registry` (line 273): Correct.
   - `test_unknown_tool_raises_regardless_of_discovery_map` (line 279): Correct.
   - `test_discovery_map_none_falls_through_to_registry` (line 287): Correct.

### Method

- Use the Edit tool for targeted replacements: class name + docstring as one Edit, method deletion as one Edit, method addition as one Edit.
- The new test follows the exact pattern of the deleted test but asserts the opposite result.
- No new imports needed; `ToolRouteResolver` is already imported at line 9.

### Details

- Class rename: line 250 (`class TestLiveDiscoveryRouting:`).
- Method to delete: lines 259-264 (inclusive; includes the def line through the assert line).
- New test position: immediately after `_make_configs()` helper (lines 253-257), before the surviving tests.
- The `_make_configs()` helper (lines 253-257) includes `"file_read"` and `"web_search"` server configs — `read_text_file` resolves to `"file_read"` via the registry.

## Validation plan

```bash
# All route resolver tests must pass; test_discovery_wins_over_registry must not exist
uv run pytest tests/test_route_resolver.py -v

# Specifically verify the new test exists and passes
uv run pytest tests/test_route_resolver.py::TestDiscoveryMapValidationOnly -v

# Confirm the deleted test name is gone
grep -n "test_discovery_wins_over_registry\|TestLiveDiscoveryRouting" tests/test_route_resolver.py
# Expected: no output
```

Expected: all tests in `tests/test_route_resolver.py` pass; `TestDiscoveryMapValidationOnly::test_discovery_map_does_not_override_registry` is green; no occurrences of `test_discovery_wins_over_registry` or `TestLiveDiscoveryRouting` remain.
