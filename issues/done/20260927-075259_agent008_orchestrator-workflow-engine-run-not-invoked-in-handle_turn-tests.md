# orchestrator workflow engine run not invoked in handle_turn tests

## Priority
Medium

## Summary
4 failures in `tests/agent/test_orchestrator.py` (excluding the separately-tracked ToolLoopGuard signature failures) show the workflow engine's `run` never being invoked, a config-restore assertion failing, and an expected exception not being raised — all around `handle_turn`'s workflow-engine invocation.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation. Filed separately from `agent001` (ToolLoopGuard signature) since these 4 failures are not `TypeError: check_all() missing 'message'` errors, though both are in `test_orchestrator.py` and may share an underlying cause — investigate for a common cause before assuming independence.

## Problem
- `TestAllowedToolsOverride::test_original_config_restored_even_on_error`: `Failed: DID NOT RAISE <class 'RuntimeError'>`
- `TestHandleTurnInvokesWorkflowEngine::test_handle_turn_calls_workflow_engine_run_once`: `AssertionError: assert 0 == 1` (`<MagicMock>.call_count`)
- `TestHandleTurnInvokesWorkflowEngine::test_handle_turn_returns_normally_on_genuine_workflow_timeout`: `AssertionError: Expected 'run' to have been called once. Called 0 times.`
- A third `TestHandleTurnInvokesWorkflowEngine` variant with the same "Expected 'run' to have been called once. Called 0 times." pattern.

The three `TestHandleTurnInvokesWorkflowEngine` failures share an identical symptom (`run` never invoked), strongly suggesting one root cause in `handle_turn`'s call path to the workflow engine. The `TestAllowedToolsOverride` failure (missing `RuntimeError`) may be related if it also depends on `handle_turn` reaching the workflow-engine call, or may be independent.

## Reason for Change
If `handle_turn` genuinely never invokes the workflow engine's `run` in production under these scenarios, this is a functional regression in the orchestrator's core turn-handling path — a central, high-traffic code path.

## Implementation Intent
Read `handle_turn`'s current implementation to find why it might return/short-circuit before calling the workflow engine's `run` in these test scenarios — check for a new early-return condition, an exception being silently swallowed before reaching the call, or a changed mock-patch target in the tests (i.e. confirm the tests still patch the correct object/attribute that `handle_turn` actually calls).

## Target Files or Areas
- `scripts/agent/orchestrator.py` (confirm exact path — `handle_turn`)
- `tests/agent/test_orchestrator.py`

## Required Changes
- Trace why `run` is not invoked in the 3 `TestHandleTurnInvokesWorkflowEngine` scenarios.
- Trace why the expected `RuntimeError` is not raised in `test_original_config_restored_even_on_error`.
- Determine whether these 4 failures share a common cause (e.g. one early-return/guard clause added to `handle_turn`) before fixing each independently.

## Constraints
Do not fix by changing the test's mock target to something that no longer verifies the real call path — if the mock patch is stale, confirm the correct current target before updating it.

## Acceptance Criteria
- All 4 listed tests pass.
- If a shared cause with `agent001` is confirmed, cross-reference both issues' resolutions.

## Testing Expectations
Run `tests/agent/test_orchestrator.py` in full; run full suite once after the fix.

## Documentation Impact
N/A: unless `handle_turn`'s workflow-engine invocation contract changed and needs documenting (Needs confirmation).

## Out of Scope
`agent001` (ToolLoopGuard `check_all` signature failures in the same file) — tracked separately.

## Dependencies
Possibly related to `agent001` (same file) — investigate for a shared cause but track/fix separately unless confirmed identical.

## Unresolved Questions
Needs confirmation: whether all 4 failures share one root cause in `handle_turn`, or are 2+ independent issues that happen to co-occur in the same test file.

## AI Implementation Instruction
Read `handle_turn`'s current full implementation before fixing any of the 4 tests — determine whether one code change (e.g. a new guard clause) explains all 4 failures before treating them as separate fixes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_orchestrator.py
