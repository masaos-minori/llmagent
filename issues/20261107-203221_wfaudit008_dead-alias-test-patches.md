# Retarget inert test patches and remove dead adapter aliases

## Priority
Medium

## Summary
The engine adapter's public "backward-compatible" aliases are called by no production code, and a large set of orchestrator tests patches those alias names — patches that are inert because production calls the private methods. Retarget the tests to the real call targets, then delete the aliases.

## Background
Code review evidence (Verified):
- The adapter exposes a public alias block (task-init, activate, halt handler) documented as backward-compatible; production call sites use the private methods exclusively. The public halt alias has zero callers anywhere (scripts or tests) and drops the return value the private handler produces.
- `tests/agent/test_orchestrator.py` patches the alias names at more than ten locations (activation, deactivation, task-init). Because production invokes the private methods, those patches do not intercept anything: the real methods run against the fixture database while the tests present themselves as mocking the workflow lifecycle. Some tests additionally replace the whole turn executor, masking the inertness.
- An archived precedent of patch-target drift: `issues/done/20260919-164144_wfretry01_workflowengine-retry-policy-magicmock-typeerror-breaks-test_orchestrator.py` (resolved) and `issues/done/20260909-130315_startup05_workflow-preflight-tests-target-relocated-symbols.md` (resolved) show patch targets drift after refactors in this domain.
- The project's shim checker does not flag these aliases (`issues/done/20261020-123232_compat007_track-compatibility-exceptions-and-obsolete-symbols-in-a-manifest-with-owner-and-expiry.md` established the compat-manifest expectation; the checker gap is filed separately as `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`).

## Problem
- Dead public API surface advertises compatibility no caller needs.
- Tests that claim to mock activation/deactivation/task-init do not: they execute real workflow-DB writes behind the mock facade, so behavioral assertions on those tests are weaker than they look, and removing the aliases today would not even break them (they would silently keep passing while the intended mock never applied where assumed).

## Reason for Change
This is the unlock step for the whole dead-surface cleanup in the adapter: aliases cannot be removed until the tests patch what production actually calls. Inert patches also mislead future reviewers about what a test constrains.

## Implementation Intent
Two-step, one change set: (1) retarget every test patch to the private methods production invokes, verify previously-masked behavior now gets exercised (or convert to characterization assertions on the fixture-DB behavior); (2) delete the alias block, including the zero-caller halt alias, and any docstring claiming compatibility need.

## Target Files or Areas
- scripts/agent/workflow_engine_adapter.py (alias block)
- tests/agent/test_orchestrator.py (patch targets)
- tests/integration/test_orchestrator_integration.py (already uses private methods; verify only)

## Required Changes
- Replace alias-name patches with private-method patches throughout the orchestrator tests.
- Run the suite after retargeting and investigate any test that newly fails or changes behavior (it was previously unmocked).
- Delete the public alias block.

## Constraints
- No behavior change in production code beyond removing uncalled methods.
- Public/private naming of the real methods stays as-is.
- Keep test intent comments accurate after retargeting.

## Acceptance Criteria
- No test patches a method production code never calls.
- The alias block is gone and the suite passes.
- Grep confirms zero references to the removed names in scripts and tests.

## Testing Expectations
- Full orchestrator + workflow test packages before/after; document any test whose assertions changed meaning because its patch became effective.
- Ruff/mypy clean; compat-shim checker behavior tracked in its own issue.

## Documentation Impact
If any adapter docstring module header describes the alias block, update it. No operator-facing doc changes.

## Out of Scope
- Test-only helper removal in StateStore/attempt ops (separate issue).
- Fixing the shim checker's case sensitivity (separate issue).
- Adapter internals unrelated to the alias block.

## Dependencies
- Precedes any adapter API reshaping from `issues/20261107-203219_wfaudit006_state-store-lifecycle-ownership.md` and resume-path work, to avoid patch-target drift again.
- Pairs with `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md` so future aliases get caught by the checker.

## Unresolved Questions
- Does any external/private consumer of this repository import the public aliases? (Needs confirmation with the owner before deletion.)

## AI Implementation Instruction
Do the test retargeting first and get the suite green before deleting anything. For each retargeted patch, confirm the patched method appears in the production call graph; if a test depended on the inertness (real DB side effects present), convert it to an explicit characterization test rather than silently keeping weaker coverage.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203221
- **Related target files**: scripts/agent/workflow_engine_adapter.py, tests/agent/test_orchestrator.py, tests/integration/test_orchestrator_integration.py
