# Find the cause of three failing git MCP tests

## Priority
Medium

## Summary
Determine why three tests under `tests/mcp_servers/git/` fail on a clean checkout, then fix the code or the test, or document the environment condition.

## Background
Evidence (`Explicit in code`, by test run): in every full suite run of 2026-11-27 (four runs) these fail, and they also fail on a clean worktree of HEAD, so no recent change caused them. `tests/mcp_servers/git/test_git_service_dispatch.py::TestWriteOffloadAndTimeout::test_pull_timeout_near_success_reports_outcome_unknown` and `::test_push_timeout_near_success_reports_outcome_unknown` fail with `assert False` on `.../applied` `Path.exists()`. `tests/mcp_servers/git/test_repository_state.py::TestPerOperationPostconditions::test_pull_postcondition_fails_on_unresolved_conflict` fails with `assert True is False` on a `PipelineResult(ok=True, ... output='merge conflicted' ...)`.

## Problem
Three tests of the git MCP server do not pass, and each full run needs a manual check that they are not new. The third one may show a real defect: a pull whose output says `merge conflicted` returns `ok=True` where the test expects a failed postcondition.

## Reason for Change
The suite is never clean, which hides new failures and costs a clean-HEAD check per run; the pull postcondition may be a correctness gap.

## Implementation Intent
Reproduce, find the cause, and fix or document it.

## Target Files or Areas
- `tests/mcp_servers/git/test_git_service_dispatch.py`
- `tests/mcp_servers/git/test_repository_state.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/write_protection_pipeline.py`

## Required Changes
- Run the three tests alone and with `-p no:randomly`, on HEAD and with the host `git` version and configuration recorded.
- Decide per test: a product defect (fix the code), a test that depends on the environment (make it self-contained), or an invalid expectation (correct the test with the reason).
- If a production file under `scripts/` changes, follow the deploy step of the workflow.

## Constraints
- Do not skip, xfail, or deselect the tests.
- Do not weaken the pull postcondition to make the test pass.

## Acceptance Criteria
- [ ] Each of the three tests passes or is replaced by a justified, equivalent check.
- [ ] The cause of each is stated in the change description.
- [ ] The full suite shows none of the three as failing.

## Testing Expectations
The three tests, `tests/mcp_servers/git/`, then the full suite once; ruff, mypy, bandit for changed files; diff-cover if `scripts/` changed.

## Documentation Impact
N/A: tests and code only unless the postcondition behavior changes; then the git MCP documentation row of `docs/00_index.md` applies.

## Out of Scope
- Other failing tests; changes to unrelated git MCP behavior.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether the cause is the host git version or configuration, the test setup, or the code.

## AI Implementation Instruction
Find the cause before editing. Stop and report if the pull postcondition is a real defect with a security or data-loss effect.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120103
- **Related target files**: `tests/mcp_servers/git/test_git_service_dispatch.py`, `tests/mcp_servers/git/test_repository_state.py`, `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/write_protection_pipeline.py`
