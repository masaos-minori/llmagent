# Refine GitHub resource scopes for safe parallelism

## Priority
Low

## Summary
After correctness and authorization are secured, evaluate replacing repository-wide GitHub resource scopes with finer branch, issue, and pull request scopes where independence can be proven.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 13). Related archived work: `issues/done/20261027-104324_mcpcompat003_align-legacy-resource-scope.md`.

## Problem
Repository-level scopes serialize unrelated operations within one repository and reduce throughput. This is not a correctness defect.

## Reason for Change
Throughput only; premature refinement could weaken safety, so it follows the security and idempotency work.

## Implementation Intent
Improve concurrency without weakening read/write conflict protection or repository-wide invariants; keep repository scope for operations that affect shared repository state.

## Target Files or Areas
- GitHub tool metadata, `scripts/shared/resource_scope.py`, `scripts/agent/tool_scheduler.py`, scheduler tests

## Required Changes
- Evaluate branch scope for branch and file operations, issue scope for issue and comment operations, and pull request scope for update and merge; keep repository scope where shared state is affected; document cross-scope conflicts.

## Constraints
- No weakening of existing repository-level safety; optional if independence cannot be proven.

## Acceptance Criteria
- [ ] Same-resource writes and read/write conflicts remain sequential.
- [ ] Independent resources can run concurrently.
- [ ] Repository-wide operations conflict with all relevant finer scopes.
- [ ] Existing repository-level safety is not weakened.

## Testing Expectations
- Same branch write/write, same issue comment, same pull request update/merge serialization; independent branches or issues concurrent; repository-wide operation conflicts with finer scopes. Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Document cross-scope conflicts (boundaries and constraints).

## Out of Scope
- Any correctness or authorization change.

## Dependencies
- Depends on `issues/20261119-140509_mcpai002_github-read-security-boundary.md` and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`; `issues/20261119-140518_mcpai011_round-recording-accuracy.md` is recommended for validating scheduler telemetry. Keep last.

## Unresolved Questions
- `不明`: whether any finer scope can be proven independent for the GitHub API's server-side behavior.

## AI Implementation Instruction
Proceed only if each finer scope has a stated independence argument and a test; otherwise stop and report that the issue should be closed as not applicable.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140520
- **Related target files**: `scripts/shared/resource_scope.py`, `scripts/agent/tool_scheduler.py`
