# Mandate and test the protected-branch check for git_add and git_commit

## Priority
Medium

## Summary
`verify_authorization()` rejects `git_add` and `git_commit` when the current HEAD is a protected branch, but no ADR-012 Invariant requires it and no test covers it. Record the maintainer's decision and add the matching tests.

## Background
Source: governance Known Issue MCP-005 (Medium) and the pending ledger entries AAL-014, AAL-015, AAL-036. Evidence (`Explicit in code`, by reading and `rg`): `scripts/mcp_servers/git/repository_state.py` `verify_authorization()` treats the current HEAD (`self.active_branch`) as the destination for `git_add` and `git_commit` (lines 137 to 145); ADR-012 INV-03 names only `git_checkout`, `git_pull`, `git_push`; in `tests/mcp_servers/git/test_git_security_compliance.py` the `git_add` and `git_commit` cases are dirty-worktree reachability probes and the protected-branch tests cover `validate_protected` only. `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md` edits the same source file for postconditions and explicitly leaves this check and its tests to this issue.

## Problem
A safety-relevant enforcement has no Invariant and no regression test, so it can drift or regress silently.

## Reason for Change
Enforcement without a mandate or a test is unprotected against change; a regression would allow a write on a protected branch.

## Implementation Intent
The maintainer either adds an Invariant for the HEAD-destination check (a pending amendment through the ADR Approval Ledger) or records it as out of scope; protected-branch tests for both tools follow the recorded decision.

## Target Files or Areas
- `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
- `tests/mcp_servers/git/test_git_security_compliance.py` (or a new sibling test file)
- `scripts/mcp_servers/git/repository_state.py` (read; changed only if a defect is found)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (MCP-005)

## Required Changes
- Confirm the current behavior with a failing-first test before any documentation change.
- After the maintainer decision, add protected-branch tests for `git_add` and `git_commit`: rejected on a protected HEAD, allowed otherwise, and the detached-HEAD policy of ADR-012 Decision Detail 5.
- Record the decision in ADR-012 (Invariant plus pending amendment, or an explicit out-of-scope statement) and remove MCP-005 with its evidence.

## Constraints
- The Invariant text and its approval are the maintainer's; the ledger entry stays unapproved until the maintainer states it.
- Do not change `verify_authorization()` behavior in the same change as the postcondition work of `mcpai008`.

## Acceptance Criteria
- [ ] ADR-012 states the decision for the HEAD-destination check.
- [ ] Tests for `git_add` and `git_commit` on a protected HEAD exist and pass.
- [ ] MCP-005 is removed from the inventory.

## Testing Expectations
The new tests pass with the git server suite, and ruff and mypy pass for the changed test file.

## Documentation Impact
Yes: ADR-012 and the governance inventory.

## Out of Scope
- Other git tools' authorization rules and postcondition verification (`mcpai008`).

## Dependencies
- Sequence with `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md` (same server file and test directory); no hard dependency.
- The resulting ledger entry is handled in `issues/20261123-104604_gov005_adr-approval-ledger.md`.

## Unresolved Questions
- `不明`: whether the maintainer adds the Invariant or declares the check out of scope.

## AI Implementation Instruction
Write the failing-first protected-HEAD tests, then stop for the Invariant decision. Do not write approval text, and do not change authorization behavior.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-104601
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `tests/mcp_servers/git/test_git_security_compliance.py`, `scripts/mcp_servers/git/repository_state.py`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
