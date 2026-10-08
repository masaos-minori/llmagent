# Fix failing git MCP tests after the audit record emission change

## Priority
High

## Summary
Six git MCP tests fail on the current upstream head, so the full test suite is red; find which of the recent git MCP changes caused each failure and fix the tests or the code.

## Background
Found during post-sync validation of an unrelated EventBus change. The same tests passed in a full run just before the upstream commit "complete git-mcp audit record emission gaps fix (REQ-005 through REQ-010)" was integrated. To separate causes, five of the six failures were reproduced in a clean checkout of that upstream commit, without any of the local EventBus commits; the sixth passed there and failed only inside the full run, so it may be order-dependent or intermittent.

## Problem
- Failing tests (full run on the rebased head):
  - `tests/mcp_servers/git/test_format_output.py::TestFormatPostconditionFailures::test_push_postcondition_failure_rejection_marker_in_output`
  - `tests/mcp_servers/git/test_mcp_git.py::TestGitPush::test_dry_run_push_current_branch`
  - `tests/mcp_servers/git/test_repository_state.py::TestPostconditionChecks::test_push_postcondition_with_rejection`
  - `tests/mcp_servers/git/test_repository_state.py::TestPostconditionChecks::test_push_postcondition_with_error`
  - `tests/mcp_servers/git/test_git_security_compliance.py::TestDryRunAndDetachedHeadLivePath::test_dry_run_pull_and_push_skip_dirty_precondition`
  - `tests/mcp_servers/git/test_git_security_compliance.py::TestRemoteAuthorizationViaHTTP::test_pull_authorized_remote_proceeds` (passes when run alone)
- Observed message in one reproduction: the git push tool raises a git service error ("git_push failed") where the test expects a result or a rejection marker.
- All six are push/pull related; the shared cause is not yet identified.

## Reason for Change
A red full suite hides new failures and blocks the post-sync validation required before every push.

## Implementation Intent
- Determine, per failing test, whether the test encodes behavior the upstream change deliberately altered (update the test) or the change broke behavior (fix the code).
- Keep the audit-record and error-path contracts intact; do not weaken assertions to make the tests green.

## Target Files or Areas
- `tests/mcp_servers/git/test_format_output.py`, `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/git/test_git_security_compliance.py`
- `scripts/mcp_servers/git/` (git service, repository state, output formatting) only if a code defect is found

## Required Changes
- Reproduce each failure in a clean checkout and record the cause.
- Fix each failing test or the code, whichever violates the documented contract.
- For the order-dependent test, find the shared state (for example a module-level cache or monkeypatch leak) and remove the dependence.

## Constraints
- Do not skip or delete tests to get green.
- Follow the git MCP and audit documentation for the intended error-path behavior.

## Acceptance Criteria
- The six tests pass in isolation and in a full run.
- The full suite (excluding the separately tracked EventBus transition module) passes.

## Testing Expectations
Run the git MCP test directory, then the full suite once; repeat the order-dependent test within a full run.

## Documentation Impact
Only if the intended error-path behavior differs from the current documentation (for example the git MCP document or ADR-012); record such a mismatch as a Known Issue.

## Out of Scope
- The EventBus changes and the other tracked pre-existing problems (timeouts in the EventBus transition tests, tracer type-ignores, the shared-module import contract).

## Dependencies
- Related to the git MCP audit record emission work that landed upstream; coordinate with its author before changing its contracts.

## Unresolved Questions
- Whether the upstream change was meant to alter the error-path behavior these tests assert (unknown).
- Why one test fails only in a full run (unknown).

## AI Implementation Instruction
Reproduce in a clean checkout first. Decide per test whether the contract changed before editing anything, and stop to ask if the intended behavior is unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-125417
- **Related target files**: `tests/mcp_servers/git/test_format_output.py`, `tests/mcp_servers/git/test_mcp_git.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/git/test_git_security_compliance.py`
