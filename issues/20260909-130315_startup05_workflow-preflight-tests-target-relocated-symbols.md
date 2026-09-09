# `TestStartupWorkflowPreflight` patches `check_workflow_definition`/`_check_workflow_schema` where they no longer live

## Priority
Medium

## Summary
All 6 tests in `TestStartupWorkflowPreflight` (`tests/agent/test_startup.py`) fail:
some with `AttributeError: <module 'agent.startup'> does not have the attribute
'check_workflow_definition'`, others with `AttributeError: 'StartupOrchestrator' object
has no attribute '_check_workflow_schema'`. Both symbols were relocated out of
`agent.startup`/`StartupOrchestrator` by prior refactors; this test class was never
updated to match — the same class of defect as `startup02`, but targeting different
relocated symbols.

## Background
Two separate refactors moved these symbols out of their original locations:
- Commit `b7f2813f0` ("refactor: extract workflow schema validation into dedicated
  module") moved `check_workflow_definition` out of `agent.startup` into
  `scripts/agent/services/workflow_schema.py`.
- Commit `ea986372e` ("refactor: extract ComponentInitializer and delegate
  StartupOrchestrator concerns") moved `_check_workflow_schema` off
  `StartupOrchestrator` and onto `ComponentInitializer`
  (`scripts/agent/startup_component_init.py`).

Neither refactor updated `tests/agent/test_startup.py`'s
`TestStartupWorkflowPreflight`, which still patches the pre-relocation locations.

## Problem
All 6 tests in this class patch either `agent.startup.check_workflow_definition` or
`StartupOrchestrator._check_workflow_schema`, neither of which exists at those
locations anymore — both `mock.patch(...)` calls fail at setup, before the tests' own
assertions ever run.

## Reason for Change
6 tests providing coverage for workflow-definition/schema preflight checks during
startup currently provide none of that coverage, and their failures obscure any genuine
regression in this area.

## Implementation Intent
Update each test's patch target to the relocated symbol's current location:
`scripts/agent.services.workflow_schema.check_workflow_definition` for the
`check_workflow_definition`-patching tests, and the equivalent method on
`ComponentInitializer` (`scripts/agent/startup_component_init.py`) for the
`_check_workflow_schema`-patching tests. Confirm each test's assertion logic (what
behavior it verifies once the patch actually engages) still makes sense against the
current call chain — a relocated symbol may also have a changed call signature or
return contract worth re-checking, not just a changed import path.

## Target Files or Areas
- `tests/agent/test_startup.py` (`TestStartupWorkflowPreflight`, all 6 tests)
- `scripts/agent/services/workflow_schema.py` (reference — confirms
  `check_workflow_definition`'s current location and signature)
- `scripts/agent/startup_component_init.py` (reference — confirms
  `ComponentInitializer`'s equivalent schema-check method and signature)

## Required Changes
- Update each failing test's `mock.patch(...)` target to the symbol's current location.
- Confirm and, if needed, adjust each test's assertions to match the relocated
  function/method's current call signature and return contract.
- No change to `scripts/agent/services/workflow_schema.py` or
  `scripts/agent/startup_component_init.py` unless investigation finds those relocations
  themselves introduced a genuine behavior change worth a separate defect report.

## Constraints
Do not modify the relocated production code unless a genuine behavior regression is
found during implementation (in which case, stop and report it as a separate finding
rather than silently expanding this issue's scope).

## Acceptance Criteria
- [ ] All 6 `TestStartupWorkflowPreflight` tests patch the symbols' current locations
- [ ] `uv run pytest "tests/agent/test_startup.py::TestStartupWorkflowPreflight" -q`
  passes in full (6/6)
- [ ] No change to `scripts/agent/services/workflow_schema.py` or
  `scripts/agent/startup_component_init.py` unless a genuine regression is found and
  separately reported

## Testing Expectations
- `uv run pytest "tests/agent/test_startup.py::TestStartupWorkflowPreflight" -q` — full
  class must pass

## Documentation Impact
N/A: test-only relocation-propagation fix; no documented behavior changes expected.

## Out of Scope
- `TestStartupRollback`'s failures — tracked separately as `startup03`/`startup04`.
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging`'s 3 failures —
  tracked separately as `startup06`.
- Any change to `scripts/agent/services/workflow_schema.py` or
  `scripts/agent/startup_component_init.py`'s actual logic, absent a newly-found
  genuine regression.

## Dependencies
N/A: none. Same class of defect as `startup02`
(`issues/20260909-105724_startup02_recover-pending-approvals-test-targets-removed-module-attribute.md`),
targeting different relocated symbols in the same test file — does not duplicate it.

## Unresolved Questions
N/A: none — both relocations confirmed by direct `git log` inspection of the
responsible commits.

## AI Implementation Instruction
Apply the patch-target relocation per test; verify each test's assertions still match
the relocated symbol's current call signature before considering it fixed — do not
assume the fix is purely mechanical without checking, since two separate refactors are
involved (`workflow_schema.py` extraction and `ComponentInitializer` extraction) and
they may not share identical call shapes.
