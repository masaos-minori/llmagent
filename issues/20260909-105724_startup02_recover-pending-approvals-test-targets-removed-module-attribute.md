# `TestStartupOrchestratorRecoverPendingApprovals` patches `agent.startup` attributes removed by an architectural relocation

## Priority
Medium

## Summary
`tests/agent/test_startup.py::TestStartupOrchestratorRecoverPendingApprovals` (9 test
methods) fails with `AttributeError: <module 'agent.startup' ...> does not have the
attribute 'find_all_pending_approvals'` (8 methods) or `... does not have the attribute
'StateStore'` (1 method). Both symbols were relocated out of `agent.startup` by a prior
refactor; the class was never updated to match, and its coverage is now duplicated by a
separate, passing test file. This is a stale-test cleanup, not a `startup.py` defect.

## Background
Commit `729ff8beb` ("refactor: extract ApprovalRecovery and delegate
`_recover_pending_approvals`") moved pending-approval recovery logic out of
`StartupOrchestrator` in `scripts/agent/startup.py` into a new
`ApprovalRecovery.recover()` in `scripts/agent/startup_approval_recovery.py`.
`StartupOrchestrator._recover_pending_approvals()` now only delegates to
`self._approval_recovery.recover()`. That commit added
`tests/agent/test_startup_approval_recovery.py` (16 tests, all passing, confirmed by
isolated run) to cover the new location, but never touched
`tests/agent/test_startup.py`, leaving `TestStartupOrchestratorRecoverPendingApprovals`
behind as orphaned, now-broken duplicate coverage.

## Problem
`ApprovalRecovery.recover()` does local imports inside its own method body —
`from agent.workflow.approval_ops import find_all_pending_approvals` and
`from agent.workflow.state_store import StateStore` — so neither symbol was ever an
attribute of `agent.startup` to begin with, even before the relocation made it more
obviously wrong. `TestStartupOrchestratorRecoverPendingApprovals` patches
`agent.startup.find_all_pending_approvals` / `agent.startup.StateStore`, which fail
immediately at `mock.patch(...)` setup.

## Reason for Change
The class contributes 9 guaranteed failures to every `tests/agent/test_startup.py` run
and to the full suite, and its assertions duplicate coverage that already exists and
passes in `tests/agent/test_startup_approval_recovery.py`. Removing it eliminates dead,
misleading test debt without any loss of coverage.

## Implementation Intent
Remove `TestStartupOrchestratorRecoverPendingApprovals` from
`tests/agent/test_startup.py` rather than patching it to chase the new module path —
its scenarios (newest-pending-approval selection, task-ID-overwrite warning, store
closed on exception, no-pending-approval case) are already exercised against the
correct current module (`ApprovalRecovery.recover()`) in
`tests/agent/test_startup_approval_recovery.py`. Confirm each scenario in the old class
has an equivalent in the new file before deleting; if a scenario has no equivalent,
port it to `tests/agent/test_startup_approval_recovery.py` instead of deleting it
outright.

## Target Files or Areas
- `tests/agent/test_startup.py` (remove `TestStartupOrchestratorRecoverPendingApprovals`)
- `tests/agent/test_startup_approval_recovery.py` (reference/verification only — confirm
  scenario coverage; port any gap found)
- `scripts/agent/startup.py` (reference only — confirms `_recover_pending_approvals()`
  is a pure delegation to `ApprovalRecovery.recover()`, not itself a target for change)
- `scripts/agent/startup_approval_recovery.py` (reference only — confirms
  `find_all_pending_approvals`/`StateStore` are imported here, not in `agent.startup`)

## Required Changes
- Delete `TestStartupOrchestratorRecoverPendingApprovals` and its 9 test methods from
  `tests/agent/test_startup.py`.
- Before deleting, diff its scenarios against `tests/agent/test_startup_approval_recovery.py`'s
  existing test names/docstrings; port any scenario with no equivalent rather than
  silently dropping coverage.
- No change to `scripts/agent/startup.py` or `scripts/agent/startup_approval_recovery.py`
  — production code is confirmed correct.

## Constraints
Do not modify `scripts/agent/startup.py` or `scripts/agent/startup_approval_recovery.py`
— this is a test-only cleanup; the production relocation is intentional and correct.

## Acceptance Criteria
- [ ] `TestStartupOrchestratorRecoverPendingApprovals` no longer exists in
  `tests/agent/test_startup.py`
- [ ] Every scenario it previously covered (newest-pending-approval selection,
  task-ID-overwrite warning, store-closed-on-exception, no-pending-approval case) has a
  confirmed equivalent in `tests/agent/test_startup_approval_recovery.py`
- [ ] `uv run pytest tests/agent/test_startup.py -q` no longer reports the
  `find_all_pending_approvals`/`StateStore` `AttributeError`s

## Testing Expectations
- `uv run pytest tests/agent/test_startup.py -q` — the 9 failures from
  `TestStartupOrchestratorRecoverPendingApprovals` must be gone; other pre-existing,
  unrelated failures in this file (see Out of Scope) are not this issue's concern
- `uv run pytest tests/agent/test_startup_approval_recovery.py -q` — must remain fully
  passing (16/16, confirmed baseline) after any scenario porting

## Documentation Impact
N/A: test-only cleanup; no documented behavior changes.

## Out of Scope
- The remaining ~36 failures in `tests/agent/test_startup.py` beyond
  `TestStartupOrchestratorRecoverPendingApprovals` (observed causes include a workflow
  schema/definition check mismatch, an `McpServerConfig: auth_token must not be empty`
  validation error, and a `log_file must be a non-empty str` error against a
  `MagicMock`) — these are distinct, uninvestigated root causes and are not addressed
  here; each needs its own separate triage.
- Any change to `scripts/agent/startup.py` or `scripts/agent/startup_approval_recovery.py`.
- Any other file in the pre-existing full-suite failure list.

## Dependencies
N/A: none. Related to (but does not duplicate) the now-deleted triage record
`issues/20260908-203803_regr001_full-suite-491-pre-existing-failures.md`, which first
sampled this failure.

## Unresolved Questions
N/A: none — root cause is confirmed by direct commit inspection (`729ff8beb`) and by
`tests/agent/test_startup_approval_recovery.py`'s passing, equivalent coverage.

## AI Implementation Instruction
Do not attempt to make `TestStartupOrchestratorRecoverPendingApprovals` pass by patching
`agent.workflow.approval_ops`/`agent.workflow.state_store` instead of `agent.startup` —
the correct action is removal (with scenario-porting verification), not relocation of
the patch target, since the coverage already exists in
`tests/agent/test_startup_approval_recovery.py`. Do not touch the other, unrelated
failures in `tests/agent/test_startup.py` listed under Out of Scope.
