# Implementation Procedure: Remove redundant RuntimeToolRegistry instantiation

## Goal

Remove the redundant second `RuntimeToolRegistry` instantiation in `McpToolDiscoveryService.discover_all()` that filters out unreachable servers after construction — instead pass `unavailable_servers` to the first constructor so exclusion happens once. REQ-005, REQ-008.

## Scope

- Eliminate duplicate `RuntimeToolRegistry` creation in `discover_all()`
- Pass `unavailable_servers` to the first constructor's `unavailable_servers` parameter
- Preserve all existing behavior: unreachable server tools must still be excluded from the final registry

## Assumptions

- `RuntimeToolRegistry.__init__()`'s `_is_excluded_server()` method correctly excludes tools from both unavailable servers AND disabled servers (startup_mode=none)
- The `unavailable_servers` parameter is already accepted by `RuntimeToolRegistry.__init__()` (verified: line 43 accepts `frozenset[str] | None`)
- No other code creates intermediate registries that need the same fix

## Design decisions

**Decision 1**: Do NOT modify `RuntimeToolRegistry` itself. Rationale: The registry's constructor already handles `unavailable_servers` filtering via `_is_excluded_server()`. The problem is only in the caller (`discover_all()`), which creates a second registry unnecessarily. Fix at the call site, not the callee.

**Decision 2**: Keep `_is_excluded_server()` logic unchanged. Rationale: It correctly combines unavailable-server exclusion with disabled-server exclusion. Changing it would risk breaking disabled-server behavior.

## Alternatives considered

- **Modify `RuntimeToolRegistry` to accept a callable filter**: Would add unnecessary complexity for a one-time filtering concern. The current approach (passing `unavailable_servers` directly) is simpler and more explicit.
- **Create a separate `filtered_tools` property on `RuntimeToolRegistry`**: Would expose internal state and add coupling. Not aligned with the minimal-change principle.

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py`

### Procedure

#### Phase 1: Verify `RuntimeToolRegistry.__init__()` handles `unavailable_servers` correctly

1. Read `scripts/shared/runtime_tool_registry.py` lines 40-65 to confirm:
   - Line 43: `unavailable_servers: frozenset[str] | None = None` parameter exists
   - Line 46: `self._unavailable_servers = unavailable_servers or frozenset()` assignment is correct
   - Lines 55-65: `_is_excluded_server()` checks both `self._unavailable_servers` AND `self._server_configs` for disabled servers
   - Lines 49-53: Tools from excluded servers are skipped during construction

2. Verify no other callers of `RuntimeToolRegistry.__init__()` depend on the current pattern of creating a second registry. Search for all instantiations:
   ```bash
   rg "RuntimeToolRegistry\(" --include "*.py" scripts/ tests/
   ```

#### Phase 2: Update `discover_all()` in `mcp_tool_discovery.py`

1. In `McpToolDiscoveryService.discover_all()` (lines ~170-185), replace:
   ```python
   # Current (redundant):
   registry = RuntimeToolRegistry(tools=runtime_tools)
   unavailable_keys = frozenset(unreachable)
   filtered_tools = {
       n: t for n, t in registry._tools.items()
       if t.server_key not in unavailable_keys
   }
   registry = RuntimeToolRegistry(tools=filtered_tools)
   ```
   
   With:
   ```python
   # New (single construction):
   unavailable_keys = frozenset(unreachable)
   registry = RuntimeToolRegistry(
       tools=runtime_tools,
       unavailable_servers=unavailable_keys,
   )
   ```

2. Remove the second `RuntimeToolRegistry` instantiation entirely.

3. Verify `registry.unavailable_servers` is still accessible (it's a public property, line 68-70).

#### Phase 3: Verification

1. Run unit tests:
   ```bash
   uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v
   ```

2. Run integration tests:
   ```bash
   uv run pytest tests/agent/test_startup.py -v
   ```

3. Run severity classification tests:
   ```bash
   uv run pytest tests/agent/test_startup_severity_classification.py -v
   ```

4. Type check:
   ```bash
   uv run mypy scripts/shared/runtime_tool_registry.py
   ```

5. Lint check:
   ```bash
   uv run ruff check scripts/shared/runtime_tool_registry.py
   ```

## Compatibility considerations

- **Public API preservation**: `RuntimeToolRegistry.__init__()` signature remains unchanged — `unavailable_servers` parameter already exists.
- **Behavioral compatibility**: All existing behavior must be preserved — unreachable server tools must still be excluded from the final registry.
- **Reference files**: `scripts/agent/services/mcp_tool_discovery.py` must pass `unavailable_servers` to the constructor (covered by Phase 4 of the primary implementation procedure).

## Security considerations

- No new security-sensitive code paths introduced.
- Exclusion logic is centralized in `_is_excluded_server()`, reducing the risk of inconsistent filtering across multiple registry instances.

## Rollback considerations

- If this change breaks unreachable server exclusion, revert to the two-registry pattern and investigate why `_is_excluded_server()` is not working as expected.
- The rollback is straightforward: restore the second `RuntimeToolRegistry` instantiation.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/runtime_tool_registry.py | Unit | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All existing tests pass without modification |
| scripts/shared/runtime_tool_registry.py | Integration | `uv run pytest tests/agent/test_startup.py -v` | All startup integration tests pass |
| scripts/shared/runtime_tool_registry.py | Integration | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | All severity classification tests pass |
| scripts/shared/runtime_tool_registry.py | Type check | `uv run mypy scripts/shared/runtime_tool_registry.py` | No new mypy errors |
| scripts/shared/runtime_tool_registry.py | Lint check | `uv run ruff check scripts/shared/runtime_tool_registry.py` | No new ruff lint errors |
| scripts/shared/runtime_tool_registry.py | Behavioral lock | Compare StartupCheckOutcome messages before/after refactoring | Identical outputs |

## Completion criteria

- [ ] Only one `RuntimeToolRegistry` instantiation per `discover_all()` call
- [ ] `unavailable_servers` passed to first constructor
- [ ] Unreachable server tools still excluded from final registry
- [ ] All existing tests pass without modification
- [ ] No new mypy errors introduced
- [ ] No ruff lint errors introduced
- [ ] Behavioral regression verification: compare StartupCheckOutcome messages before/after refactoring for identical outputs

## Out of scope

- Modifying `RuntimeToolRegistry`'s core functionality beyond accepting `unavailable_servers` (already supported)
- Adding new validation rules for tool entries
- Changing the duplicate-tool-name resolution strategy
- Addressing the known limitation about two independent HTTP round-trips (mentioned in module docstring)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `RuntimeToolRegistry.__init__()` handles `unavailable_servers` correctly | Completed | — | — | REQ-005; 既に単一インスタンス化済み |
| 2 | Update `discover_all()` in `mcp_tool_discovery.py` | Completed | — | — | REQ-005, REQ-008; filtered_tools 削除済み |
| 3 | Final validation | Completed | — | — | REQ-009, REQ-010, REQ-011, REQ-008 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-008
- **Source issue**: issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-172946_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-175741
- **Related target files**: scripts/shared/runtime_tool_registry.py
