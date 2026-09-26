# orchestrator_integration NameError orch not defined

## Priority
Low

## Summary
`tests/integration/test_orchestrator_integration.py::TestApprovalWorkflowWithRealDB::test_handle_turn_invokes_workflow_engine_run` fails with `NameError: name 'orch' is not defined` — an apparent test-code bug (a variable referenced without being defined/assigned in that scope).

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`NameError: name 'orch' is not defined` — likely a typo, a renamed local variable, or a missing setup line earlier in the test body.

## Reason for Change
This is very likely a straightforward test-code bug (not a production regression) given the error type, but it blocks this integration test from running at all.

## Implementation Intent
Read the test body to find where `orch` is referenced and determine what it should have been assigned from (e.g. an orchestrator instance created earlier in the test or a fixture) — fix the missing assignment or correct the variable name.

## Target Files or Areas
- `tests/integration/test_orchestrator_integration.py`

## Required Changes
- Fix the undefined `orch` reference (add the missing assignment or correct a typo/rename).

## Constraints
N/A: none

## Acceptance Criteria
- The listed test passes (or fails on a genuine assertion, not a `NameError`).

## Testing Expectations
Run `tests/integration/test_orchestrator_integration.py`; run full suite once after the fix.

## Documentation Impact
N/A: test-code-only fix.

## Out of Scope
`tests/integration/test_orchestrator_integration.py::TestToolCallFlow` failures (tracked under `agent001`, same root cause as ToolLoopGuard signature).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact intended source of `orch` (confirm by reading the test body — not yet read in this investigation, only the error type was captured).

## AI Implementation Instruction
Read the full test body before fixing — confirm whether `orch` should reference an existing local variable/fixture under a different name, or whether a setup line was accidentally deleted.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/integration/test_orchestrator_integration.py
