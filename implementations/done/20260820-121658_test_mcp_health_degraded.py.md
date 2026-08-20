# Implementation Procedure: Remove tests/shared/test_mcp_health_degraded.py

## Goal
Delete the entire test file `tests/shared/test_mcp_health_degraded.py` since it only exercises the removed `record_degraded` and `get_degraded_reason` methods.

## Scope
- Target file: `tests/shared/test_mcp_health_degraded.py`
- Complete removal of the file

## Assumptions
- All tests in this file test the removed methods (`record_degraded`, `get_degraded_reason`)
- No other test files depend on this file
- The functionality being tested is dead code being removed from production

## Design decisions
- Complete deletion since all tests are for removed functionality
- No replacement tests needed - the remaining tests cover the active health state logic

## Alternatives considered
- Keep file but mark tests as skipped: Rejected - dead tests add noise and maintenance burden
- Refactor tests to test remaining methods: Rejected - existing test files already cover the active methods

## Implementation
### Target file
`tests/shared/test_mcp_health_degraded.py`

### Procedure
1. Delete the entire file `tests/shared/test_mcp_health_degraded.py`

### Method
File deletion via `git rm` or `rm`.

### Details
The file contains 15 test functions, all of which test:
- `record_degraded()` method
- `get_degraded_reason()` method
- Interactions between these methods and `record_success()`

Since both methods are being removed from `McpServerHealthRegistry`, all these tests become invalid and should be removed.

## Compatibility considerations
- No compatibility impact - removing test file only
- Other test files (`test_tool_executor_order.py`, `test_repl_health.py`, `test_mcp_health_interpretation.py`) cover remaining health registry functionality

## Security considerations
- None - test file removal only

## Rollback considerations
- Git restore of the file if needed
- No database schema or config changes involved

## Validation plan
- Run `uv run pytest tests/shared/test_mcp_health_degraded.py` - should fail with "file not found"
- Run `uv run pytest tests/shared/` - must pass (remaining tests)
- Run full test suite `uv run pytest` - must pass

## Out of scope
- Changes to production code (separate procedures)
- Changes to other test files (separate procedure for test_cmd_mcp.py)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260817_03_issue.md
- Source requirement: requires/20260818-213740_require.md
- Source plan: plans/20260818-213740_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-121658
- Related target files: tests/shared/test_mcp_health_degraded.py