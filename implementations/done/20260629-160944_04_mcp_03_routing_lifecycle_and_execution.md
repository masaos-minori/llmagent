# Implementation: MCP Routing Authority Clarification

## Goal

Establish a single, unambiguous documented and code-enforced routing authority for MCP tools: ToolRegistry (populated from tool_constants.py frozensets) is the primary routing source; config tool_names and live /v1/tools are validation-only unless discovery map is explicitly built.

## Scope

- **In-Scope**:
  - Fix docstrings in `shared/route_resolver.py` (module-level and class-level)
  - Fix docstring in `shared/tool_registry.py` (module-level routing priority table)
  - Fix `_raise_strict_error` message in `route_resolver.py` (stop directing users to config)
  - Update `docs/04_mcp_03_routing_lifecycle_and_execution.md`: remove "config-driven routing" framing; clarify static fallback = frozensets = same source as registry
  - Update `docs/04_mcp_06_configuration_and_operations.md`: minor wording fix for tool_names field description
  - Add tests in `tests/test_route_resolver.py`: prove routing works without config tool_names when registry has the tool
- **Out-of-Scope**:
  - Adding dynamic runtime routing from live discovery
  - Changing tool naming convention
  - Changing runtime behavior (no logic changes in resolve())
  - DB schema changes

## Assumptions

- The 4-layer priority order in route_resolver.py resolve() is correct as-is; only docs and error messages need fixing.
- `_fallback_route()` (priority 4) and `ToolRegistry` (priority 2) use the same frozensets but serve different lookup paths; this distinction should be documented clearly.
- The discovery map (priority 1) is conditionally built at startup and is not always present; it is not the default runtime path for most tools.

## Implementation

### Target file: `scripts/shared/route_resolver.py`

#### Procedure

1. Fix module docstring — rename from "Config-driven" to clarify registry as primary
2. Fix class docstring — remove "Config-driven" framing
3. Fix `_raise_strict_error` message — direct users to tool_constants.py instead of config
4. Fix `_warn_on_fallback` log message — remove instruction to add tool_names to config

#### Method

Direct file edit — update docstrings and error messages in place.

#### Details

**1. Module docstring (lines 2-10):**
```python
"""shared/route_resolver.py
Tool-name to server-key resolution for ToolExecutor.

Routing priority:
  1. Live-discovered tool metadata from /v1/tools (server_key field) — optional, only when discovery map is built at startup
  2. Tool registry (canonical source of truth from tool_registry.py; populated from tool_constants.py frozensets)
  3. Config-driven tool_names from mcp_servers config — validation hint only, not a routing input for priority 2 tools
  4. Static fallback constants (compatibility/emergency use only; same frozensets as registry but accessed differently)
"""
```

**2. Class docstring — remove "Config-driven" framing:**
Change the class docstring to state that discovery map is optional and registry is primary.

**3. `_raise_strict_error` message (line 168-171):**
```python
# Change from:
f"ToolRouteResolver: tool {tool_name!r} not in config map "
f"and strict_mode=True; add it to tool_names in mcp_servers config"

# To:
f"ToolRouteResolver: tool {tool_name!r} not in config map "
f"and strict_mode=True; add it to the appropriate frozenset in shared/tool_constants.py"
```

**4. `_warn_on_fallback` log message (lines 153-157):**
```python
# Change from:
"ToolRouteResolver: tool %r not in config map; using static fallback. "
"Add tool_names to mcp_servers config to suppress this warning.",

# To:
"ToolRouteResolver: tool %r not in config map; using static fallback. "
"Add the tool to the appropriate frozenset in shared/tool_constants.py to suppress this warning.",
```

### Target file: `scripts/shared/tool_registry.py`

#### Procedure

Fix module docstring routing priority table — clarify that config tool_names is "validation-only, not a routing fallback for priority 2 tools".

#### Method

Direct file edit — update routing priority table in module docstring.

#### Details

**In the module docstring routing priority table:**
```python
# Change:
3. Config-driven tool_names — fallback for stdio servers without /v1/tools

# To:
3. Config tool_names — validation hint only; not a routing input for tools already in ToolRegistry
4. Static fallback (same frozensets as registry, accessed differently)
```

### Target file: `docs/04_mcp_03_routing_lifecycle_and_execution.md`

#### Procedure

Remove "config-driven routing" framing; clarify static fallback = frozensets = same source as registry.

#### Method

Direct file edit — update multiple sections.

#### Details

**Section "ToolRouteResolver":**
- Remove "Config-driven tool-name" from the opening description
- Rewrite priority 1 description: clarify that discovery map is only populated when servers respond to /v1/tools at startup; not always active
- Rewrite priority 3 description: state explicitly that config tool_names is NOT a routing input; it is only consulted when both discovery map and registry have no match
- Remove or retract "Config-driven routing" section heading if present

**Section "Routing Source of Truth":**
- Update table role for config tool_names from "Priority 3 — fallback validation" to "Priority 3 — last-resort fallback; not needed if tool is in ToolRegistry"
- Add note: "For all tools defined in tool_constants.py frozensets, routing succeeds via priority 2 (registry) without config tool_names"

**Section "Adding a new tool":**
- Step 3 (config tool_names): rephrase from "Optional" to clearly say "validation hint only; routing does not require it"
- Remove step 5 about /v1/tools discovery override unless discovery is actually wired

**Section "New Server/Tool Registration Checklist":**
- Change config tool_names row from "Optional" to "Optional — validation hint only; routing works without it if tool is in tool_constants.py"

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure

Verify tool_names field description is accurate and consistent with new framing. Based on plan, already says "Validation hint (optional); registry routes regardless" — verify this is correct.

### Target file: `tests/test_route_resolver.py`

#### Procedure

1. Rename `TestStaticFallbackRouting` to `TestRegistryRouting` with comment explaining tests verify registry-based routing (priority 2)
2. Add new test class `TestRegistryWithoutConfig`:
   - `test_registry_routes_without_config_tool_names`: create resolver with server configs that have empty tool_names; verify known tools resolve correctly via registry
   - `test_registry_routes_all_tool_constants_tools`: iterate all tools from get_all_mcp_tool_names() and assert each resolves without config tool_names
   - `test_strict_mode_error_message_points_to_tool_constants`: trigger strict_mode ValueError for unknown tool; assert error message mentions tool_constants.py, not mcp_servers config

#### Method

Direct file edit — rename class and add new test class.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `shared/route_resolver.py` | Unit tests: registry routing without config | `uv run pytest tests/test_route_resolver.py -v` | All tests pass; new registry-without-config tests pass |
| `shared/tool_registry.py` | Docstring only; no logic change | `uv run pytest tests/ -v` | No regressions |
| `docs/04_mcp_03_routing_lifecycle_and_execution.md` | Manual review for contradictions | `grep -n "config-driven\|discovery.*highest\|static fallback" docs/04_mcp_03_routing_lifecycle_and_execution.md` | No contradictory terms remain |
| `tests/test_route_resolver.py` | New tests prove registry authority | `uv run pytest tests/test_route_resolver.py::TestRegistryWithoutConfig -v` | All 3 new tests pass |
| Full test suite | Regression check | `uv run pytest tests/ -x -q` | No failures introduced |
