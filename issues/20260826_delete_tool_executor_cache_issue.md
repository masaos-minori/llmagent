# [Refactor] Delete ToolExecutor TTL Cache

## Priority
High

## Summary
Remove the TTL-based internal cache (`_cache`, `_execute_with_cache`, `stat_cache_hits`) and the `apply_config(cache_ttl=...)` parameter from `ToolExecutor`. This eliminates complexity and inconsistencies during configuration reloads.

## Background
The current `ToolExecutor` implements a TTL-based internal cache and provides an `apply_config(cache_ttl=...)` method. Several planned refactors are blocked until this cache is removed.

## Problem
The TTL cache introduces unnecessary complexity and potential inconsistencies during configuration reloads.

## Reason for Change
This change removes the cache to simplify the codebase and eliminate configuration reload inconsistencies.

## Implementation Intent
Delete all caching-related members and the `cache_ttl` parameter from `ToolExecutor`. Update dependent components accordingly.

## Target Files or Areas
- `scripts/shared/tool_executor.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/agent/services/config_reload.py`
- `tests/shared/test_tool_executor.py`

## Required Changes
- Remove `_cache` and related logic in `scripts/shared/tool_executor.py`.
- Remove `apply_config(cache_ttl=...)` parameter and implementation.
- Remove `stat_cache_hits` tracking.
- Update `ConfigReloadService` to stop applying `cache_ttl`.
- Update `ToolConfig` dataclass.
- Update observability/stats reporting.

## Constraints
N/A: none

## Acceptance Criteria
- `ToolExecutor` has no mention of `_cache`, `_execute_with_cache`, or `stat_cache_hits`.
- `apply_config` does not accept `cache_ttl`.
- All unit tests pass.

## Testing Expectations
Unit tests for `ToolExecutor`, config reload, and `ToolConfig` validation.

## Documentation Impact
Update ADR documents referencing the TTL cache mechanism.

## Out of Scope
Adding new caching mechanisms.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Remove all caching-related members and the `cache_ttl` parameter from `ToolExecutor`. Update dependent components accordingly.
