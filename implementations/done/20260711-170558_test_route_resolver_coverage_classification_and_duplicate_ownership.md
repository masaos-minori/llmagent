# Implementation Procedure: `tests/test_route_resolver.py` — coverage-classification and duplicate-ownership tests

## Goal

Add tests proving the corrected `_log_routing_coverage()` classification (registry-first, not
discovery-map-first) behaves as intended, plus a direct unit test confirming
`ToolRegistry.register()`'s existing duplicate-ownership `ValueError` guard.

## Scope

**In-Scope:**
- `tests/test_route_resolver.py`: add two tests exercising `_log_routing_coverage()`'s
  corrected classification order:
  1. A tool present only in `discovery_map` (not the registry) must be logged as UNMAPPED.
  2. A tool present in the registry but absent from `discovery_map` must still be logged as
     MAPPED.
- `tests/test_route_resolver.py` (or an appropriate existing test module for
  `ToolRegistry` if that is a better fit — verify at implementation time; the plan's Design
  section places this test alongside route-resolver tests): add a duplicate-ownership
  registration test exercising `ToolRegistry.register()`'s existing `ValueError` when a tool
  name is registered to a second, different `server_key`.

**Out-of-Scope:**
- Any change to `ToolRouteResolver` or `ToolRegistry` production code (covered by the
  companion `route_resolver.py` implementation doc).
- The set-membership completeness test for `tool_constants.py` frozensets — that belongs in
  `tests/test_tool_registry.py` (separate doc).
- The drift-guard docstring for `tests/test_tool_registry_counts.py` (separate doc).

## Assumptions

1. `_log_routing_coverage()` will be fixed (per the companion `route_resolver.py` doc) to
   classify a tool as "mapped" solely based on `self._lookup_registry(tool_name) is not
   None` — `discovery_map` membership no longer affects the classification.
2. `ToolRouteResolver.__init__()` triggers `_log_routing_coverage()` only when `known_tools`
   is truthy (confirmed at `route_resolver.py` line 85: `if known_tools:
   self._log_routing_coverage(known_tools)`).
3. Test approach: construct a `ToolRouteResolver` with a `known_tools` frozenset including a
   "ghost" tool name not present in the registry, and a `discovery_map={"ghost_tool":
   "some_server"}`; assert (via `caplog` or equivalent logging capture) that the resulting
   coverage log reports the ghost tool as unmapped, not mapped.
4. Conversely, construct with a tool that genuinely exists in the registry (e.g. a real tool
   from `tool_constants.py`, confirmed registered) but absent from `discovery_map`; assert it
   is reported as mapped.
5. `ToolRegistry.register()` (`shared/tool_registry.py`, confirmed near lines 54-63) raises
   `ValueError` with message `"Tool {name!r} already registered to server
   {existing.server_key!r}; cannot reassign to {definition.server_key!r}"` when a tool name is
   registered a second time to a different `server_key` — this plan only adds a direct test
   for this existing behavior, not new production logic.
6. Existing test file structure/imports/fixtures in `tests/test_route_resolver.py` should be
   read first to match established conventions (fixture names, registry setup helpers, caplog
   usage patterns) before adding new tests.

## Implementation

### Target file

`tests/test_route_resolver.py`

### Procedure

1. Read the existing `tests/test_route_resolver.py` in full to identify: existing fixtures
   for constructing a `ToolRegistry` and `ToolRouteResolver`, existing `caplog` usage
   conventions (if any), and existing helper functions for registering tools.
2. Add `test_coverage_counts_discovery_only_tool_as_unmapped()`:
   - Arrange a registry (via existing fixture or direct `ToolRegistry` instance) that does
     NOT contain a chosen "ghost" tool name.
   - Construct `ToolRouteResolver` with `discovery_map={"ghost_tool": "some_server"}` and
     `known_tools=frozenset({"ghost_tool"})`.
   - Capture logging output (`caplog.at_level(logging.WARNING)` or module logger equivalent).
   - Assert the log message reports `ghost_tool` under the unmapped list/count, not mapped.
3. Add `test_coverage_counts_registry_tool_as_mapped_even_without_discovery()`:
   - Arrange a registry containing a real, registered tool name.
   - Construct `ToolRouteResolver` with `discovery_map={}` (or omitted) and
     `known_tools=frozenset({<that tool name>})`.
   - Capture logging output.
   - Assert the log reports full coverage (mapped count equals total, no unmapped entries).
4. Add `test_duplicate_tool_registration_raises_value_error()` (or similarly named):
   - Register a tool name to one `server_key` via `ToolRegistry.register()`.
   - Attempt to register the same tool name again with a different `server_key`.
   - Assert `ValueError` is raised, and optionally assert the message contains both the
     original and attempted `server_key` values.

### Method

Three new test functions added to `tests/test_route_resolver.py`, following existing file
conventions for registry/resolver setup and logging assertions. No production code changes.
Use `pytest.raises(ValueError)` for the duplicate-registration test; use `caplog` (or the
project's established logging-capture convention in this file) for the coverage-classification
tests.

### Details

Reference pseudocode (illustrative signatures only, per python-design skill's
pseudocode-only rule):

```python
def test_coverage_counts_discovery_only_tool_as_unmapped() -> None:
    """A tool present only in discovery_map (not registry) must be UNMAPPED."""
    # Arrange: registry without "ghost_tool"; discovery_map={"ghost_tool": "some_server"}
    # Act: construct ToolRouteResolver(known_tools=frozenset({"ghost_tool"}), ...)
    # Assert: caplog shows "ghost_tool" under unmapped, not mapped

def test_coverage_counts_registry_tool_as_mapped_even_without_discovery() -> None:
    """A tool in the registry but absent from discovery_map must still be MAPPED."""
    # Arrange: registry containing a real tool; discovery_map={}
    # Act: construct ToolRouteResolver(known_tools=frozenset({<tool>}), ...)
    # Assert: caplog shows full mapped coverage, no unmapped entries

def test_duplicate_tool_registration_raises_value_error() -> None:
    """ToolRegistry.register() rejects reassigning a tool name to a different server_key."""
    # Arrange: register tool_name -> server_a
    # Act/Assert: pytest.raises(ValueError) on register(tool_name -> server_b)
```

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_route_resolver.py` | 0 errors |
| Tests | `uv run pytest tests/test_route_resolver.py -v` | All pass, including the 3 new tests |
| Regression | `uv run pytest tests/test_tool_executor_routing.py -q` | No new failures |
