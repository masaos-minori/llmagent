# Limit HALF_OPEN trial calls to one

## Priority
Low

## Summary
Allow only a single trial call while a server's circuit breaker is HALF_OPEN, and make other calls wait or be rejected until the result is known.

## Background
Source: local investigation notes (memo1.md, ISSUE-13), from an earlier review finding.

## Problem
- When the circuit breaker is HALF_OPEN, `_check_health()` lets all calls through, so any number of trial calls can flow concurrently (Explicit in code — `scripts/shared/tool_transport_invoker.py` logs "allowing trial dispatch" for every call in that state).

## Reason for Change
- HALF_OPEN exists to test recovery with one call; sending many at once concentrates load on a recovering server and can cause another failure.

## Implementation Intent
- Restrict HALF_OPEN to one in-flight trial.

## Target Files or Areas
- `scripts/shared/tool_transport_invoker.py`; state transitions in `scripts/shared/mcp_config.py` (to be read)

## Required Changes
- Keep a per-server in-flight trial flag (or semaphore); return "unavailable" for other calls while a trial is in flight.

## Constraints
- Must release the flag on success, failure, and cancellation.

## Acceptance Criteria
- With concurrent calls in HALF_OPEN, exactly one is sent (test).

## Testing Expectations
- Async concurrency test; ruff, mypy, targeted pytest.

## Documentation Impact
Update the circuit-breaker description only if it states trial behavior.

## Out of Scope
- Breaker thresholds and timing.

## Dependencies
N/A: none

## Unresolved Questions
- The state-transition implementation of `McpServerHealthRegistry`.

## AI Implementation Instruction
Keep the change local to the trial gating. Ensure the flag cannot leak on exceptions.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154049
- **Related target files**: `scripts/shared/tool_transport_invoker.py`
