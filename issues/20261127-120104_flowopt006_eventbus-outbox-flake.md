# Stabilize the DLQ outbox restart test under parallel load

## Priority
Medium

## Summary
Find and remove the timing dependence of `test_restart_with_pending_rows`, which failed once under parallel load and passes alone.

## Background
Evidence (`Explicit in code`, by test run): in one of four full parallel runs on 2026-11-27 (`-n logical`), `tests/eventbus/test_eventbus_dlq_outbox.py::test_restart_with_pending_rows` failed at its assertion `report["generated"] == 1` with `0 == 1`. It passed in the other three full runs and three times alone.

## Problem
A result that depends on scheduling can fail a correct change and hides real failures in the same run.

## Reason for Change
Each unexplained failure costs an investigation (this one was rerun alone three times).

## Implementation Intent
Identify what the test waits for, replace the wait with a deterministic condition, and keep the product behavior unchanged.

## Target Files or Areas
- `tests/eventbus/test_eventbus_dlq_outbox.py`
- `scripts/eventbus/dlq.py`

## Required Changes
- Read the test and the DLQ outbox generation path it exercises; list every time-based or ordering assumption.
- Reproduce under load (for example repeated runs with `-n logical` and a CPU-bound neighbor) to confirm the cause.
- Make the test deterministic (an explicit event or synchronization instead of a fixed wait); change `scripts/eventbus/dlq.py` only if the race is in production code.

## Constraints
- Do not add retries (`pytest-rerunfailures`) or skips as the fix.
- Keep the test's intent: pending rows survive a restart.

## Acceptance Criteria
- [ ] The cause is stated.
- [ ] The test passes in 50 consecutive runs under parallel load.
- [ ] No other eventbus test changes behavior.

## Testing Expectations
Repeated runs of the test under load; the eventbus test directory; ruff and mypy for changed files.

## Documentation Impact
N/A: test change; if production code changes, the eventbus persistence document named by `docs/00_index.md` applies.

## Out of Scope
- Other flaky tests; unrelated eventbus changes.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether the race is in the test or in the outbox generation path.

## AI Implementation Instruction
Reproduce first. If the race is in production code, report it before changing `scripts/`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120104
- **Related target files**: `tests/eventbus/test_eventbus_dlq_outbox.py`, `scripts/eventbus/dlq.py`
