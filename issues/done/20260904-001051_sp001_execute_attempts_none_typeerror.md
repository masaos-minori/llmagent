# Fix SessionPersister.execute_attempts TypeError propagation

## Summary

SessionPersister.persist_session_diagnostics retrieves execute_attempts via store.get_execute_attempt_count(sid), then computes retry_count = max(0, execute_attempts - task_count). If get_execute_attempt_count returns None, the subtraction raises TypeError, which is NOT caught by the outer except (RuntimeError, sqlite3.Error) clause and propagates unhandled.

## Background

persist_session_diagnostics saves session diagnostics summary and memories. It catches RuntimeError and sqlite3.Error but not TypeError.

## Problem

A None return from get_execute_attempt_count causes an unhandled TypeError during session persistence at shutdown time, losing the session summary.

## Reason for Change

Data integrity risk: unhandled TypeError during shutdown causes silent session data loss. The error is not caught by the existing exception handler.

## Implementation Intent

Either: (1) add None-check before arithmetic: `execute_attempts = store.get_execute_attempt_count(sid); if execute_attempts is None: execute_attempts = 0`, or (2) add TypeError to the except clause. Option 1 is preferred as it makes the intent explicit rather than relying on exception handling for control flow.

## Target Files or Areas

- scripts/agent/session_persister.py

## Required Changes

- Add None-check after get_execute_attempt_count call at line 82
- Default execute_attempts to 0 if None is returned
- OR add TypeError to the except clause (document why)

## Constraints

- Must not change the semantics of retry_count calculation for valid inputs
- Must preserve existing error handling for RuntimeError and sqlite3.Error

## Out of Scope

- Changing the store interface contract
- Adding new exception types

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] persist_session_diagnostics handles None return from get_execute_attempt_count gracefully
- [ ] retry_count defaults to 0 when execute_attempts is None
- [ ] No TypeError propagation during shutdown

## Testing Expectations

- Unit test: mock get_execute_attempt_count returning None, verify no TypeError
- Integration test: verify session persistence completes during shutdown with degraded store

## Documentation Impact

Document the expected return type contract for get_execute_attempt_count in the store interface.

## Priority

High

## AI Implementation Instruction

Fix only the execute_attempts None-handling issue. Do not rewrite the persistence layer. Preserve existing retry_count semantics. Stop and report if the store interface contract is unclear.
