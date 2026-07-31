# Implementation Procedure: Add Exclusive Locking to Stale Attempt Recovery

## Goal
Prevent concurrent processes from recovering the same stale attempt using optimistic locking.

## Scope
- **In scope**: `scripts/agent/workflow/state_store.py`
- **Out of scope**: adding new dependencies (like Redis), refactoring other state store methods.

## Assumptions
- SQLite does not support `FOR UPDATE SKIP LOCKED`.
- Optimistic locking via status update check is sufficient for preventing race conditions.

## Design decisions
- Use a conditional `UPDATE` statement to atomically claim an attempt.
- Use `rowcount` to verify if the current process successfully transitioned the status.

## Alternatives considered
- `FOR UPDATE SKIP LOCKED`: Not supported by SQLite.
- Distributed lock (Redis): Rejected to avoid adding external dependencies.

## Implementation
- **Target file**: `scripts/agent/workflow/state_store.py`
- **Procedure**:
  - Update `recover_stale_attempts` to return the count of successfully recovered attempts.
  - Fetch stale attempts using a non-locking `SELECT`.
  - Iterate through results and attempt to claim each via `UPDATE ... WHERE id = ? AND status = 'running'`.
  - Commit only if the update affects exactly one row.
- **Method**: Optimistic locking via conditional `UPDATE`.
- **Details**: Atomic transition from `running` to `recovered` ensures only one worker succeeds per attempt ID.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
Revert `recover_stale_attempts` to the previous `SELECT`-then-`UPDATE` pattern if contention causes excessive failures.

## Validation plan
- **Unit tests**: Test concurrent execution of `recover_stale_attempts` to ensure no duplicate recoveries occur.
- **Integration tests**: Verify stale attempts are correctly marked as `recovered` under simulated load.

## Out of scope
N/A

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-070555_require.md
- Source plan: plans/20260731-085748_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-205430
- Related target files: scripts/agent/workflow/state_store.py
