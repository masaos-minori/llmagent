# Step 1 — Remove discovery routing from `ToolRouteResolver.resolve()`

## Goal

Remove the Priority 1 discovery-map lookup from `ToolRouteResolver.resolve()` so that `ToolRegistry` becomes the sole routing authority, while retaining `self._discovery_map` as a non-routing attribute for backward-compatible constructor calls.

## Scope

- **In-Scope:**
  - Delete the `Priority 1: discovery map` block (lines 102-104) from `resolve()`.
  - Update the module-level docstring to reflect single-authority routing.
  - Update the `ToolRouteResolver` class docstring similarly.
  - Update the inline comment on `self._discovery_map` in `__init__`.
  - Update `_raise_strict_error()` error message to remove "not in discovery map or".
  - Update the `_warn_on_missing` log message in `resolve()` to remove "not in discovery map or".
  - Update the numbering comment in `resolve()` from "Priority 2" to "Priority 1".

- **Out-of-Scope:**
  - Do not remove `self._discovery_map` attribute or the `discovery_map` constructor parameter.
  - Do not modify `_log_routing_coverage()` logic or its `if tool_name in self._discovery_map` branch (that branch is for coverage reporting, not routing).
  - Do not modify `build_discovery_map()` function (it becomes a validation helper).
  - Do not touch `shared/tool_executor.py`.

## Assumptions

1. `_log_routing_coverage()` at line 132 checks `self._discovery_map` for coverage reporting — this is separate from routing and must remain unchanged.
2. The `ToolExecutor` in `tool_executor.py` still accepts `discovery_map` in its constructor; retaining `self._discovery_map` ensures no constructor-call-site changes are required.
3. After this change, `resolve()` will raise `ValueError` for any tool not in the registry, even if `discovery_map` maps it — this is the intended behavior.
4. Tests in `TestLiveDiscoveryRouting.test_discovery_wins_over_registry` (line 259) will fail after this change and must be replaced in Step 3.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/shared/route_resolver.py`

### Procedure

1. **Update module-level docstring** (lines 4-9): Replace the two-line routing priority list with:
   ```
   Routing priority:
     1. Tool registry (canonical source of truth from tool_registry.py; populated from tool_constants.py frozensets)

   Config `tool_names` is NOT a routing input; it is drift validation metadata only.
   Live /v1/tools discovery is used for startup validation only, not routing.
   ```

2. **Update `ToolRouteResolver` class docstring** (lines 62-69): Replace:
   ```
   Routing priority:
     1. Discovery map (live /v1/tools metadata with server_key) — only when built at startup
     2. Tool registry (canonical source of truth from tool_registry.py)
   Raises ValueError when none of the above match.
   ```
   with:
   ```
   Maps tool_name → server_key using ToolRegistry as the sole routing authority.
   Raises ValueError when the tool is not in the registry.

   Live /v1/tools discovery (discovery_map parameter) is retained for backward
   compatibility with integration tests but does NOT affect routing results.
   Config `tool_names` is NOT a routing input; it is validation metadata only.
   ```

3. **Update `self._discovery_map` inline comment** (line 81): Change:
   ```python
   # Discovery map from live /v1/tools metadata (highest priority).
   self._discovery_map: dict[str, str] = discovery_map or {}
   ```
   to:
   ```python
   # Validation data from live /v1/tools (not used for routing).
   self._discovery_map: dict[str, str] = discovery_map or {}
   ```

4. **Delete the Priority 1 discovery map block from `resolve()`** (lines 102-104). Remove:
   ```python
   # Priority 1: discovery map (live server metadata).
   if (key := self._discovery_map.get(tool_name)) is not None:
       return key
   ```

5. **Update the registry lookup comment** in `resolve()`: Change:
   ```python
   # Priority 2: tool registry (canonical source of truth).
   ```
   to:
   ```python
   # Priority 1: tool registry (canonical source of truth).
   ```

6. **Update `_raise_strict_error()` message** (lines 127-130): Change:
   ```python
   f"ToolRouteResolver: tool {tool_name!r} not in discovery map or ToolRegistry "
   f"and strict_mode=True; add it to the appropriate frozenset in shared/tool_constants.py"
   ```
   to:
   ```python
   f"ToolRouteResolver: tool {tool_name!r} not in ToolRegistry "
   f"and strict_mode=True; add it to the appropriate frozenset in shared/tool_constants.py"
   ```

7. **Update `_warn_on_missing` log message** in `resolve()` (lines 113-116): Change:
   ```python
   "ToolRouteResolver: tool %r not in discovery map or ToolRegistry; "
   "add it to the appropriate frozenset in shared/tool_constants.py or register it in ToolRegistry.",
   ```
   to:
   ```python
   "ToolRouteResolver: tool %r not in ToolRegistry; "
   "add it to the appropriate frozenset in shared/tool_constants.py.",
   ```

### Method

- Use the Edit tool with exact string matching to apply each change independently.
- After removing the Priority 1 block, `resolve()` becomes a 2-branch function: registry lookup → raise ValueError.

### Details

- **Lines to delete:** 102-104 (`# Priority 1: discovery map` + the `if` block).
- **Lines to update:** 81 (comment on `_discovery_map`), 105 (Priority 2 comment), 113-116 (warn message), 127-130 (`_raise_strict_error` message).
- **Do not touch:** `_log_routing_coverage()` (lines 132-155); it reads `self._discovery_map` for coverage reporting, not routing, and remains correct.
- Pattern in the file: all docstring updates use triple-quoted strings; use the Edit tool targeting the exact current text.

## Validation plan

```bash
# After edit, verify no "Priority 1: discovery map" text remains in resolve()
grep -n "Priority 1.*discovery\|discovery map.*priority" /home/masaos/llmagent/scripts/shared/route_resolver.py

# Run the resolver test suite — TestLiveDiscoveryRouting.test_discovery_wins_over_registry
# is expected to FAIL here; it will be replaced in Step 3
uv run pytest tests/test_route_resolver.py -v -k "not test_discovery_wins_over_registry"

# Verify registry routing tests still pass
uv run pytest tests/test_route_resolver.py::TestRegistryRouting tests/test_route_resolver.py::TestRegistryWithoutConfig -v
```

Expected: `TestRegistryRouting`, `TestRegistryWithoutConfig`, `TestConfigDrivenRouting`, `TestBuildDiscoveryMap` all pass. `test_discovery_wins_over_registry` is skipped (will be replaced in Step 3).
