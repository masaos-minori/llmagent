# `agent.context` has no `TurnContext` — test_approval_task_persistence.py fails to collect

## Priority
High

## Summary
`tests/agent/test_approval_task_persistence.py` imports `TurnContext` from `agent.context`, but
that symbol does not exist. Every test in the file fails at collection time, so the approval
task persistence behavior it is meant to protect currently has zero test coverage.

## Reason for Change
`scripts/agent/context.py` defines `AgentContext` (a class with a `.turn` attribute holding a
`TurnState` instance), not `TurnContext`. The test file was written against an older or intended
API shape (`ctx = TurnContext(); ctx.turn.pending_approval_id = ...`) that no longer matches the
current class name. Because the import fails, pytest cannot even collect the file — this is a
silent, total loss of coverage for pending-approval-id clearing behavior across
resolution/rejection paths, not a partial failure.

## Implementation Intent
Confirm whether `TurnContext` was renamed to `AgentContext` (most likely, given the `.turn`
attribute match) or was a distinct class that was removed. Update the test to use the current
`AgentContext` API. Do not change `scripts/agent/context.py` unless investigation shows the test
was correct and the rename was the actual bug — evidence collected so far (see below) points to
the test being stale, not the implementation.

## Target Files or Areas
- `tests/agent/test_approval_task_persistence.py`
- `scripts/agent/context.py` (reference only, not expected to change)

## Required Changes
- Replace `from agent.context import TurnContext` with the correct current symbol
  (`AgentContext`, pending confirmation).
- Update all `ctx = TurnContext()` call sites in the file to construct the class correctly
  (`AgentContext` may require constructor arguments that `TurnContext()` did not — check
  `AgentContext.__init__` before mechanically renaming).
- Re-run the file after the fix and confirm `ctx.turn.pending_approval_id` still behaves as the
  tests expect.

## Acceptance Criteria
- `pytest tests/agent/test_approval_task_persistence.py` collects without error.
- All tests in the file pass.
- No other test file's collection is affected.

## Testing Expectations
Unit tests only (the file itself). Run
`PYTHONPATH=scripts pytest tests/agent/test_approval_task_persistence.py -v` after the fix.

## Documentation Impact
None expected — this is a test/implementation naming mismatch, not a behavior or public API
change.

## Out of Scope
- Do not modify `scripts/agent/context.py` structure or `AgentContext`/`TurnState` fields.
- Do not touch other collection errors (`apply_config_changes`, `_ACTIVE_ISSUE_ALLOWLIST`) —
  those are filed as separate issues.

## AI Implementation Instruction
Read `scripts/agent/context.py` fully before editing the test. Confirm `AgentContext`'s
constructor signature and how `.turn` is initialized. Fix only the import and construction
call sites in the test file; do not rewrite assertions or add new test cases. Stop and report
if `AgentContext()` requires arguments that make a 1:1 replacement non-trivial.
