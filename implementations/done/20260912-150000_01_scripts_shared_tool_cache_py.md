## Goal

Remove stale references to nonexistent `_execute_with_cache()` and `_store_and_evict()` methods from `scripts/shared/tool_cache.py`'s module docstring.

## Scope

- **In-Scope**: Modifying `scripts/shared/tool_cache.py`'s module docstring only
- **Out-of-Scope**: Any changes to `config/agent.toml`, `test_runtime_tool_routing_integration.py`, or reinstating caching in `ToolExecutor`

## Assumptions

- The decision to remove tool-result caching from `ToolExecutor` was intentional and not reverted since the issue was filed
- No other code depends on the stale docstring's description of `ToolExecutor`'s caching behavior

## Design decisions

- Update the module docstring to remove references to the nonexistent `_execute_with_cache()` and `_store_and_evict()` methods
- Clarify that `ToolExecutor` has no internal cache mechanism
- Keep `ToolResultCache` as a standalone utility description

## Alternatives considered

- Keeping the stale docstring: would leave developers confused about the relationship between `ToolResultCache` and `ToolExecutor`
- Adding a note about historical removal: would add unnecessary complexity and still reference nonexistent methods

## Implementation

### Target file

`scripts/shared/tool_cache.py`

### Procedure

1. Verify `scripts/shared/tool_executor.py`'s current signature confirms no cache-related parameters
2. Edit `scripts/shared/tool_cache.py`'s module docstring to remove references to `_execute_with_cache()` and `_store_and_evict()` methods
3. Run existing tests to confirm no regressions

### Method

For the docstring update:
- Remove lines 6-9 that describe `_execute_with_cache()` and `_store_and_evict()` as part of `ToolExecutor`'s internal cache mechanism
- Rewrite the remaining text to clarify that `ToolExecutor` has no internal cache mechanism and that `ToolResultCache` exists solely as a standalone utility

### Details

#### Step 1: Update module docstring

```python
# Before:
"""scripts/shared/tool_cache.py

Cache entry dataclass and ToolResultCache for a standalone tool-result cache.

Status: ToolResultCache is NOT currently used by ToolExecutor -- ToolExecutor
maintains its own internal OrderedDict-based cache (see _execute_with_cache(),
_store_and_evict() in shared/tool_executor.py), tightly integrated with its
stampede-protection (_inflight future sharing) mechanism, which this class has
no equivalent of. ToolResultCache remains available as a standalone, simpler
utility for a future caller that needs LRU+TTL caching without stampede
protection -- it is not deprecated, but it is also not the canonical cache.
"""

# After:
"""scripts/shared/tool_cache.py

Cache entry dataclass and ToolResultCache for a standalone tool-result cache.

ToolResultCache is a standalone, simpler utility for callers that need LRU+TTL
caching without stampede protection. It is NOT currently used by ToolExecutor,
which has no internal cache mechanism. ToolResultCache is not deprecated, but
it is also not the canonical cache.
"""
```

## Compatibility considerations

- The docstring change does not affect any runtime behavior
- Existing tests (`tests/shared/test_tool_cache.py`, `tests/shared/test_tool_result_cache.py`) should continue passing unchanged

## Security considerations

- No security implications — this is a documentation-only change

## Rollback considerations

- If the docstring change causes issues in production, roll back to the previous state
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/tool_cache.py` | Unit test execution | `uv run pytest tests/shared/test_tool_cache.py tests/shared/test_tool_result_cache.py -q` | Zero failures |
| `scripts/shared/tool_executor.py` | Signature verification | Direct read of `__init__()` definition | No cache-related parameters present |

## Completion criteria

- [ ] `scripts/shared/tool_cache.py`'s module docstring no longer mentions `_execute_with_cache()` or `_store_and_evict()`
- [ ] Docstring accurately reflects that `ToolExecutor` has no internal cache mechanism
- [ ] `ToolResultCache` is described as a standalone utility with no implied integration with `ToolExecutor`
- [ ] No behavioral changes to `ToolResultCache` or any other component

## Out of scope

- Changes to `config/agent.toml`
- Changes to `test_runtime_tool_routing_integration.py`
- Reinstating caching in `ToolExecutor`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify tool_executor.py signature | Pending | — | — | |
| 2 | Update module docstring | Pending | — | — | |
| 3 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260909-183426_toolcache01_removed-tool-result-caching-leaves-orphaned-config-keys-and-stale-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-143431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: scripts/shared/tool_cache.py
