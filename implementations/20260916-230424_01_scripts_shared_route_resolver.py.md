## Goal

Remove `build_discovery_map()` and its `ToolDescriptor` TypedDict from `scripts/shared/route_resolver.py`, updating the module docstring to remove the now-inaccurate reference to a discovery-map-building routing input.

## Scope

- Remove `build_discovery_map()` function (lines 33-62) from `route_resolver.py`
- Remove `ToolDescriptor` TypedDict class (lines 26-30) from `route_resolver.py`
- Update the module docstring to remove the reference to `build_discovery_map()` as a discovery-map-building routing input
- No other files are modified in this row

## Assumptions

- `build_discovery_map()` has zero production callers (confirmed via `rg -n "build_discovery_map" scripts/ tests/` in this cycle)
- `ToolDescriptor` is referenced nowhere else besides `build_discovery_map()`'s signature
- Removing these symbols does not affect `ToolRouteResolver` (the production routing class in the same file), which consults only `RuntimeToolRegistry`

## Design decisions

- Removal rather than modification: modifying `build_discovery_map()` to exclude duplicates would leave in place a second, redundant duplicate-detection implementation with no caller to justify its maintenance cost.
- The module docstring already states "`RuntimeToolRegistry` ... is the sole routing authority"; the removed function's description must be dropped to keep the docstring consistent.

## Alternatives considered

- Fixing `build_discovery_map()` to implement the canonical exclude-and-FATAL policy instead of removing it — rejected: leaves a dead code path that contradicts the Issue's Reason for Change ("must not disagree" — best satisfied by there being only one implementation at all).
- Deprecating `build_discovery_map()` before removal — rejected: per `rules/coding.md`'s Deprecation policy, a zero-caller re-check performed at the time of removal is the documented bar for safe removal; no diagnostic or future caller was found needing the function's current shape.

## Implementation

### Target file

`scripts/shared/route_resolver.py`

### Procedure

Remove the dead, policy-contradicting `build_discovery_map()` function and its `ToolDescriptor` TypedDict from `route_resolver.py`; update the module docstring to drop the now-removed function's description.

### Method

1. Delete `ToolDescriptor` TypedDict class definition (lines 26-30).
2. Delete `build_discovery_map()` function definition (lines 33-62).
3. Update the module docstring (lines 1-13) to remove the reference to `build_discovery_map()` as a discovery-map-building routing input.
4. Remove the `TypedDict` import if no longer needed after `ToolDescriptor` removal.

### Details

```python
# After line 13 (module docstring end), update to remove the reference to build_discovery_map():
"""scripts/shared/route_resolver.py

Tool-name to server-key resolution for ToolExecutor.

`RuntimeToolRegistry` (populated from live /v1/tools discovery via
`ToolExecutor.set_runtime_registry()`) is the sole routing authority. When a tool is not
found there, `resolve()` either raises `ValueError` immediately (strict_mode) or logs a
warning and then raises. `ToolRegistry` is no longer consulted here.

Config `tool_names` is NOT a routing input; it is drift validation metadata only.
Live /v1/tools discovery is used for startup validation only, not routing.
"""

# After line 18 (import line), remove TypedDict if no longer needed:
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

logger = logging.getLogger(__name__)

# After line 24 (logger line), delete lines 26-62 entirely:
#   class ToolDescriptor(TypedDict, total=False): ...
#   def build_discovery_map(...) -> tuple[dict[str, str], dict[str, list[str]]]: ...

# Lines 65+ (ToolRouteResolver class) remain unchanged.
```

## Compatibility considerations

- `ToolRouteResolver` (the production routing class) is unaffected — it never calls `build_discovery_map()` and does not depend on `ToolDescriptor`.
- Any external code importing `build_discovery_map` or `ToolDescriptor` will get an `ImportError` after this change — but `rg -n "build_discovery_map" scripts/ tests/` confirmed exactly 3 consuming files, all test files this Plan also updates/removes in the same change.

## Security considerations

- No security impact. This is a dead-code removal, not a security boundary change.

## Rollback considerations

- Reverting this change restores the dead code path. If `build_discovery_map()` is needed again, it should be reimplemented to match the canonical exclude-and-FATAL policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/shared/test_route_resolver.py -v` to confirm no import error for removed symbols and that remaining `ToolRouteResolver`/`TestRoutingSourceIsolation`/`TestDuplicateToolRegistration` tests pass unchanged.
- Static analysis: `uv run ruff check scripts/shared/route_resolver.py`, `uv run mypy scripts/shared/route_resolver.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `build_discovery_map()` and `ToolDescriptor` are removed from `scripts/shared/route_resolver.py`.
- Module docstring no longer references `build_discovery_map()` as a discovery-map-building routing input.
- `TypedDict` import removed if no longer needed.
- All existing tests in `tests/shared/test_route_resolver.py` continue to pass without referencing removed symbols.
- No new lint/type errors introduced.

## Out of scope

- Modifying `ToolRouteResolver` — unrelated class in the same file, not touched by this row.
- Changes to `docs/*.md` — deferred to REQ-001's Documentation Impact item.
- Adding new tests — this row is purely subtractive.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove build_discovery_map() and ToolDescriptor from route_resolver.py | Completed | 20260917-213110 | 20260917-213110 |  |
| 2 | Update module docstring to remove reference to build_discovery_map | Completed | 20260917-213110 | 20260917-213110 |  |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-213110 | 20260917-213110 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-213111 | 20260917-213111 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103315_mcpagent08_duplicate-tool-ownership-routing-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-130526_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-230424
- **Related target files**: scripts/shared/route_resolver.py