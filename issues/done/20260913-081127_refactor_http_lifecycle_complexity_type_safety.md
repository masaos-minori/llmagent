# Refactor http_lifecycle.py: reduce complexity and improve type safety

## Priority
Medium

## Summary
Refactor `scripts/agent/http_lifecycle.py` to reduce cyclomatic complexity, fix type safety gaps between `_build_snapshot_dict()` and `ProcessInfoSnapshot`, and consolidate resource cleanup logic into shared helpers.

## Background
`http_lifecycle.py` is the HTTP subprocess MCP server lifecycle manager. It was previously extracted from `lifecycle.py` and refactored to delegate to six concern-specific modules (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ProcessSnapshotProvider, ShutdownCoordinator). However, the class itself still contains significant complexity:

- `_health_poll_until_ready()` has deeply nested try/except blocks and multiple early-exit paths
- `_terminate_with_timeout()` duplicates pgid-based termination logic in two places
- `_build_snapshot_dict()` returns a dict with `pgid` as `int | None`, but `ProcessInfoSnapshot.pgid` expects `int | None` — there's a type mismatch between the dict snapshot and the frozen dataclass
- Resource cleanup logic is scattered across `_cleanup_server_resources()`, `_terminate_with_timeout()`, and `_create_and_validate_proc()`
- `shutdown_all()` uses fragile SIGINT signal handlers that could leave orphaned processes if interrupted during handler setup

## Problem
The class violates the Single Responsibility Principle despite having injected components — it still orchestrates too much lifecycle logic internally. Additionally, type mismatches between internal dicts and `ProcessInfoSnapshot` cause LSP errors.

## Reason for Change
- Reduces maintenance burden by consolidating duplicate cleanup logic
- Fixes type safety gaps that cause LSP errors
- Improves testability by extracting complex control flow into smaller units
- Prevents potential resource leaks from fragile SIGINT handling

## Implementation Intent
Focus on responsibility boundaries: each method should do one thing well. Extract complex control flow into helper functions or small classes. Ensure type consistency between internal dicts and `ProcessInfoSnapshot`. Do not change public behavior or API contracts.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py`
- `scripts/agent/services/models.py` (for reference only — do not modify `ProcessInfoSnapshot`)

## Required Changes
- Extract `_terminate_with_timeout()`'s dual pgid-based termination logic into a shared helper
- Consolidate resource cleanup into a single `_cleanup_server_resources()` call path
- Fix type mismatch: ensure `_build_snapshot_dict()` returns values compatible with `ProcessInfoSnapshot` fields
- Simplify `_health_poll_until_ready()` by extracting early-exit paths into named methods
- Improve `shutdown_all()` SIGINT handling to prevent orphaned processes

## Constraints
- Preserve all public method signatures and behavior
- Do not change `ProcessInfoSnapshot` schema
- Keep injection pattern for the six concern-specific modules
- Maintain backward compatibility with existing callers

## Acceptance Criteria
- All existing tests pass after refactoring
- No LSP/type errors reported for `http_lifecycle.py`
- Cyclomatic complexity of `_health_poll_until_ready()` reduced below 15
- No duplicate resource cleanup code paths remain
- SIGINT handler in `shutdown_all()` properly restores original handler even if interrupted

## Testing Expectations
- Run `uv run pytest scripts/agent/test_http_lifecycle.py -v` (or equivalent test suite)
- Verify no new type errors via `uv run mypy scripts/agent/http_lifecycle.py`
- Manual verification: confirm SIGINT handling works correctly during shutdown

## Documentation Impact
Update module docstring to reflect any new private helper methods added.

## Out of Scope
- Adding new features or capabilities
- Changing public API contracts
- Modifying `ProcessInfoSnapshot` or other DTO models
- Refactoring the six delegated concern modules

## Dependencies
N/A: none

## Unresolved Questions
- Should `_build_snapshot_dict()` return `ProcessInfoSnapshot` directly instead of a dict? This would eliminate the type mismatch entirely but requires verifying all callers accept the same interface.
- Is the SIGINT handler approach in `shutdown_all()` the right strategy, or should we use a different mechanism (e.g., asyncio task cancellation)?

## AI Implementation Instruction
Constrain changes to the scope above: reduce complexity, fix types, consolidate cleanup. Do not add features, change public APIs, or modify other files. Preserve all existing behavior. After refactoring, verify no new type errors and all tests pass.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-081127
- **Related target files**: scripts/agent/http_lifecycle.py
