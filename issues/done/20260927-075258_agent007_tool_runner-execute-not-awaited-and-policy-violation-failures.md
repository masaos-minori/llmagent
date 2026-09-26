# tool_runner execute not awaited and policy violation failures

## Priority
Medium

## Summary
Two unrelated failures in `tests/agent/test_tool_runner.py`: an approval-gate end-to-end test expects `execute` to have been awaited once but it was never awaited, and a DAG-execution test unexpectedly raises `PolicyViolationError: github_push_files: repo not in approval_github_allowed_repos`.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `TestRunApprovalGateEndToEnd::test_run_approval_checks_invoked_exactly_once_through_gateway`: `AssertionError: Expected execute to have been awaited once. Awaited 0 times.` — the approval-gated execution path is not reaching/awaiting the mocked `execute` call.
- `TestExecuteWithDag::test_two_scope_groups_all_execute`: `agent.tool_exceptions.PolicyViolationError: github_push_files: repo not in approval_github_allowed_repos` — a DAG-execution test unexpectedly hits a repo-allowlist policy check, suggesting either the test's config fixture doesn't include the needed repo in `approval_github_allowed_repos`, or the DAG execution path now runs a policy check it previously didn't for this scenario.

These are two distinct, unrelated failures in the same file; investigate and fix independently.

## Reason for Change
The approval-gate test verifies the tool-approval workflow actually invokes the tool exactly once end-to-end — if `execute` is never awaited, either the approval flow is broken (production bug) or the test's mock setup no longer intercepts the real call path. The DAG-execution test failing on a policy check suggests either a fixture gap or an unintended new policy-check code path in DAG-based execution.

## Implementation Intent
For the first: trace the approval-gate code path to see why the mocked `execute` is never invoked/awaited — check for a changed call signature, an early return, or a mock target mismatch. For the second: check the test's config fixture for `approval_github_allowed_repos` and compare against the repo path/name used in the test's `github_push_files` call — confirm whether the fixture is missing the entry or the DAG path is applying policy checks in a new (possibly unintended) way.

## Target Files or Areas
- `scripts/agent/tool_runner.py` (confirm exact path — approval gate and DAG execution logic)
- `tests/agent/test_tool_runner.py`

## Required Changes
- Fix the approval-gate test/mock setup or the production call path so `execute` is awaited exactly once as expected.
- Fix the DAG-execution test's fixture or the production policy-check path so the `github_push_files` call in this scenario does not hit an unintended `PolicyViolationError`.

## Constraints
Do not disable or bypass the `approval_github_allowed_repos` policy check to make the DAG test pass — fix the fixture or the check's applicability to this scenario, whichever is confirmed wrong.

## Acceptance Criteria
- Both listed tests pass without weakening the approval-gate or repo-allowlist policy checks.

## Testing Expectations
Run `tests/agent/test_tool_runner.py` in full; run full suite once after the fix.

## Documentation Impact
N/A: unless the approval-gate or DAG-execution policy-check contract changed and needs documenting (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run, including `agent008` (orchestrator workflow-engine run not invoked) even though both involve execution/approval flows — investigate independently unless evidence shows a shared cause.

## Dependencies
N/A: none confirmed; investigate independently of `agent008` unless a shared cause is found.

## Unresolved Questions
Needs confirmation: whether the DAG test's fixture is missing the repo entry (test bug) or the DAG path added a new policy-check call site (production change) — requires reading current DAG execution code.

## AI Implementation Instruction
Treat as two independent fixes. Read the approval-gate call path and the DAG execution's policy-check call site separately before changing either test or production code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_tool_runner.py
