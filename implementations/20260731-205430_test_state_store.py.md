# Implementation Procedure: Add tests for optimistic locking in StateStore

## Goal
Add test coverage to verify the correctness of the new optimistic locking mechanism in `StateStore`.

## Scope
- **In scope**: `tests/test_state_store.py`
- **Out of scope**: other test suites.

## Assumptions
- Testing environment has necessary dependencies installed.
- SQLite supports the required operations for integration tests.

## Design decisions
- Implement both unit tests (logic) and integration tests (concurrency).
- Use integration tests with actual SQLite to properly simulate race conditions.

## Alternatives considered**:
- Pure mocking (insufficient for verifying real concurrency/locking behavior).

## Implementation
- **Target file**: `tests/test_state_store.py`
- **Procedure**:
  - Add a test case simulating concurrent calls to `recover_stale_attempts()`.
  - Assert that only one caller receives a positive `rowcount` / return value for a single attempt.
  - Verify that the attempt status is updated to `recovered` exactly once.
  - Add regression tests for existing stale recovery scenarios.
- **Method**: Concurrent execution simulation using `threading` or `multiprocessing`.
- **Details**: Use a shared SQLite connection or file to allow true concurrent access during the test.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations**:
Remove the new test cases if they introduce non-deterministic flakiness.

## Validation plan
- Execute `uv run pytest tests/test_state_store.py`.

## Out of scope
N/A

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-070555_require.md
- Source plan: plans/20260731-085748_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-205430
- Related target files: tests/test_state_store.py
