# Make Git postconditions, timeout cancellation, and repository resource lifecycle reliable

## Priority
Medium

## Summary
Capture real post-operation repository state, verify each Git write by operation-specific evidence, replace non-cancellable thread-based pull and push timeout behavior, and guarantee repository handles are closed.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 8).

Evidence (`Explicit in code`, by `rg`): `scripts/mcp_servers/git/write_protection_pipeline.py` passes `post_state=self._state` — the same object used as pre-state — at lines 216 and 221. Thread-based pull and push timeout and handle closing claims are from the review and `Needs confirmation`. Related archived work: `plans/done/20261026-223348_mcp005_repositorystate-repo-no-cleanup.md` (re-verify what was already closed).

## Problem
Some operations are reported as verified without fresh evidence; pull and push run in worker threads, so an async timeout leaves the synchronous operation running and a later success; repository-state objects are not closed on all paths (`Needs confirmation`).

## Reason for Change
Reliability and correctness of write outcomes reported to the Agent.

## Implementation Intent
Make outcomes evidence-based and cancellable: a success needs fresh repository or remote state; a timeout either stops the operation or is reported as an unknown outcome that is not retried automatically; handles are released on success, rejection, dry-run, error, and timeout.

## Target Files or Areas
- `scripts/mcp_servers/git/write_protection_pipeline.py`, `repository_state.py`, `git_service.py`
- Git formatter and integration tests under `tests/mcp_servers/git/`

## Required Changes
- Capture a fresh post-operation `RepositoryState`; verify add, commit, checkout, pull, and push by operation-specific postconditions (push by comparing the expected local commit with the remote ref).
- Run pull and push in a cancellable subprocess; terminate the process group on timeout, then reconcile repository and remote state.
- Return separate outcomes for confirmed-not-applied and `outcome_unknown` using the shared vocabulary of `issues/20261119-140513_mcpai006_github-write-retry-policy.md`; never retry `outcome_unknown` automatically.
- Close repository handles on all paths.
- Replace mocks that only simulate postcondition failure with integration tests on a real temporary repository and bare remote.

## Constraints
- Keep Git retry classification aligned with `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`; ADR changes require an approval record (governance_01, governance_05), never a simulated one.
- `repository_state.py` `verify_authorization()` already rejects `git_add` and `git_commit` on a protected HEAD, but no ADR-012 Invariant mandates it and no protected-branch test covers it (governance Known Issue MCP-005, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`). This issue verifies postconditions only: do not change the authorization behavior, and leave the protected-branch tests to the work that follows the maintainer's Invariant decision.

## Acceptance Criteria
- [ ] Pipeline results contain a fresh post-operation state and each Git write has a documented postcondition.
- [ ] Push verifies the remote ref.
- [ ] A timeout cannot leave an unmanaged worker thread continuing the operation.
- [ ] Outcome-unknown writes are not retried automatically.
- [ ] Repeated execution does not leak repository handles or file descriptors.

## Testing Expectations
- Temporary repository integration tests for add, commit, checkout, and pull; bare-remote integration tests for push.
- Timeout-before-application and timeout-near-success tests.
- Resource-close tests for success, rejection, dry-run, exception, and timeout.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Per-operation postconditions and timeout outcomes (failure behavior), not a blanket guarantee (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- Dedup state machine (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); GitHub and File MCP behavior.

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (outcome-unknown and retry/review semantics) and on `issues/20261119-140513_mcpai006_github-write-retry-policy.md` (shared write-outcome vocabulary); otherwise independent.

## Unresolved Questions
- `不明`: whether a subprocess-based pull and push is compatible with the current Git library usage.
- `不明`: which handle leaks remain after the archived mcp005 plan.
- `不明`: whether the maintainer adds an ADR-012 Invariant for the HEAD-destination check or declares it out of scope (MCP-005); the postcondition tests added here must not be read as covering it.

## AI Implementation Instruction
Write the real-repository integration tests first. Keep the change inside the Git MCP server. Stop and report if the cancellable subprocess requires a new dependency.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140515
- **Related target files**: `scripts/mcp_servers/git/write_protection_pipeline.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/git_service.py`
