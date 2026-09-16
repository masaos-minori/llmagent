## Goal

Remove the `build_discovery_map` import and the `TestBuildDiscoveryMap` class from `tests/shared/test_route_resolver.py`.

## Scope

- Remove `build_discovery_map` from the import statement on line 8 (`from shared.route_resolver import ToolRouteResolver, build_discovery_map`)
- Delete the `TestBuildDiscoveryMap` class (lines 183-260), which includes:
  - `test_normal_path`
  - `test_outer_key_used_for_routing`
  - `test_empty_tool_name_skipped`
  - `test_duplicate_tool_first_wins`
  - `test_single_server_no_warning`
  - `test_duplicate_tool_different_key_logs_warning`
- No other files are modified in this row

## Assumptions

- `TestDuplicateToolRegistration` (lines 277-293, tests `ToolRegistry.register()`'s existing reject-on-duplicate behavior) is unrelated and stays untouched.
- Removing `build_discovery_map` from the import does not affect `ToolRouteResolver` usage elsewhere in the file.

## Design decisions

- Complete removal of the class and its import rather than partial cleanup: the entire class tests only `build_discovery_map()`, which is removed by REQ-001.

## Alternatives considered

- Keeping the class but modifying it to test the canonical exclude-and-FATAL policy — rejected: that would require adding new production code dependencies and is covered by the existing suite in `tests/agent/services/test_mcp_tool_discovery.py`.

## Implementation

### Target file

`tests/shared/test_route_resolver.py`

### Procedure

Remove the `build_discovery_map` import and delete the `TestBuildDiscoveryMap` class from `test_route_resolver.py`.

### Method

1. Update the import statement on line 8 to remove `build_discovery_map`:
   - Change: `from shared.route_resolver import ToolRouteResolver, build_discovery_map`
   - To: `from shared.route_resolver import ToolRouteResolver`
2. Delete the `TestBuildDiscoveryMap` class definition (lines 183-260).
3. Verify the remaining classes (`TestRoutingSourceIsolation`, `TestDuplicateToolRegistration`) still pass.

### Details

```python
# Line 8: update import to remove build_discovery_map:
# Before:
from shared.route_resolver import ToolRouteResolver, build_discovery_map

# After:
from shared.route_resolver import ToolRouteResolver

# Lines 183-260: delete entirely:
class TestBuildDiscoveryMap:
    """Tests for build_discovery_map() function."""
    ...
```

## Compatibility considerations

- Remaining tests in this file (`TestRoutingSourceIsolation`, `TestDuplicateToolRegistration`) are unaffected — they do not depend on `build_discovery_map`.
- `pytest --collect-only tests/shared/test_route_resolver.py` will collect fewer tests after this change.

## Security considerations

- No security impact. This is a test file modification.

## Rollback considerations

- Reverting this change restores the deleted tests. If needed later, the tests should be rewritten to cover the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/shared/test_route_resolver.py -v` to confirm no import error for removed symbols and that remaining `ToolRouteResolver`/`TestRoutingSourceIsolation`/`TestDuplicateToolRegistration` tests pass unchanged.
- Collection check: `uv run pytest --collect-only tests/shared/test_route_resolver.py` — confirm no tests collected from `TestBuildDiscoveryMap`.
- Static analysis: `uv run ruff check tests/shared/test_route_resolver.py`, `uv run mypy tests/shared/test_route_resolver.py`.

## Completion criteria

- `build_discovery_map` removed from the import statement on line 8.
- `TestBuildDiscoveryMap` class deleted from the file.
- All remaining tests in the file continue to pass without referencing removed symbols.
- No new lint/type errors introduced.

## Out of scope

- Modifying `TestDuplicateToolRegistration` — unrelated class testing `ToolRegistry.register()`.
- Changes to `docs/*.md` — deferred to REQ-001's Documentation Impact item.
- Adding new tests — this row is purely subtractive.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove build_discovery_map import and TestBuildDiscoveryMap class | Pending | — | — | |
| 2 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-103315_mcpagent08_duplicate-tool-ownership-routing-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-130526_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-230424
- **Related target files**: tests/shared/test_route_resolver.py
