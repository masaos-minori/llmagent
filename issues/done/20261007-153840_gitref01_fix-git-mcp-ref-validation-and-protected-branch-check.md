# Fix git-mcp ref validation and protected-branch check

## Priority
High

## Summary
Make git-mcp validate refs with an allow-list and evaluate the protected-branch rule against the branch an operation actually changes (the destination), not against the current HEAD, so that protected branches cannot be force-updated through the branch argument.

## Background
Source: local investigation notes (memo1.md, ISSUE-02), consolidating MCP-004 (raised from Low to High), MCP-002, and two earlier findings. ADR-012 makes server-side protection of protected branches its central control; its Rationale states that removing a force option from the schema is not a control if the branch argument can reach the same effect.

## Problem
- `_validate_ref()` rejects only values starting with `-`, and values containing NUL or newline (Explicit in code — `scripts/mcp_servers/git/git_service.py`, `_validate_ref`).
- Protected-branch checking exists in two places with different subjects: `_validate_protected()` compares the branch argument by exact string match, while `RepositoryState._is_protected_branch()` checks the current HEAD.
- `format_push()` runs `git push <remote> -- <branch>`; arguments after `--` are still parsed as refspecs.
- Per investigation notes (not re-verified in a real environment): while on an unprotected branch, `branch="+main"`, `"feature:main"`, `"HEAD:main"` or `"refs/heads/main"` passes both checks and can force-update the remote main.
- Conversely, when HEAD is on a protected branch, Stage 3 rejects all write operations, including checkout to another branch, so the tool cannot leave the protected branch.
- git_pull/git_push schemas make `branch` optional (empty means current branch), but `_validate_protected("")` always rejects an empty branch (MCP-002).
- `WriteProtectionPipeline.run()` is not given `protected_branches`, `requested_branch`, or `active_ref`, so the Stage 5b re-check and part of the checkout postcondition do not run.
- The protected-branch error message hard-codes `'main'`; `RepositoryState.snapshot()` is taken up to six times per call.

## Reason for Change
- Force-pushing a protected branch is the exact threat ADR-012 exists to prevent, and it is currently reachable.
- The check inspects the wrong subject: it does not protect the destination, yet it blocks the harmless escape from a protected branch.
- A schema default that always fails is a contract contradiction that teaches the LLM wrong calling patterns.
- The TOCTOU re-check was built but receives no inputs, so it provides no protection.
- Repeated snapshots let the audited state differ from the state used for the decision.

## Implementation Intent
- One consistent model: the caller names the branch to modify, and the protected-branch decision is made against that destination.
- Refs are accepted only as simple branch names (allow-list), not by rejecting known-bad characters.
- From a protected branch, read operations and checkout to an unprotected branch remain possible.

## Target Files or Areas
- `scripts/mcp_servers/git/git_service.py`, `repository_state.py`, `git_tools.py`, `git_models.py`, `format_output.py`
- git-mcp tool schemas for git_pull and git_push
- ADR-012 and the MCP git documentation (Known Deviations / invariants)

## Required Changes
- Validate refs with an allow-list equivalent to `git check-ref-format --branch`; reject `+`, `:`, `^`, `~`, `?`, `*`, `[`, backslash, `..`, `@{`, whitespace, control characters, values starting with `refs/`, and `HEAD`. Validate remote names against a conservative pattern.
- Evaluate the protected-branch rule on the operation target: argument branch for push/pull, switch target for checkout, current HEAD for commit/add; normalize names before comparing.
- Limit the Stage 3 "HEAD is protected" rejection to commit and add; allow checkout away from a protected branch.
- Make `branch` required (non-empty) in the git_pull/git_push schemas and Pydantic models; fix descriptions; remove the unreachable `or state.active_branch` in `format_push()`.
- Pass `protected_branches`, `requested_branch`, and `active_ref` to `pipeline.run()`.
- Take one `RepositoryState.snapshot()` in the server and pass it down.
- Report the actually rejected branch name in errors.
- Remove the duplicated compatibility guards (`_check_repo_path`, `_is_safe_ref`, `_check_protected_branch`) and `RepoValidationResult`.

## Constraints
- Security-sensitive: fail closed on any ambiguity.
- No backward-compatibility layers (repository policy).
- Behavior of read-only git tools must not regress.

## Acceptance Criteria
- Pushes with `+main`, `feature:main`, `HEAD:main`, `refs/heads/main`, and `main~1` are rejected (tests).
- With HEAD on main, checkout to an unprotected branch succeeds (test).
- A push/pull without `branch` is rejected at schema validation (test).
- The stage re-check receives its inputs (test).

## Testing Expectations
- Unit tests for the allow-list and the destination-based protection check; integration test against a temporary repository for push refspec forms; ruff, mypy, targeted pytest.

## Documentation Impact
Update ADR-012 Known Deviations (MCP-002, MCP-004 until fixed), the adr-index verification status for INV-01 to INV-04, and the git-mcp documentation describing ref validation and protection semantics.

## Out of Scope
- Audit record and error-path changes (separate issue).
- Moving blocking git work off the event loop (separate issue).
- Idempotency cache changes.

## Dependencies
- Verify behavior after the MCP idempotency issue is fixed.
- Shares files with the git-mcp audit/error-path issue; may be worked on together.

## Unresolved Questions
- How a `+main` argument after `--` is actually interpreted by `git push` via GitPython in a real environment must be confirmed before finalizing severity wording.

## AI Implementation Instruction
Keep changes inside the git-mcp files listed. Do not weaken any existing rejection. Add the rejection tests first, then fix. Stop and report if the real git behavior differs from the assumptions above.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-153841
- **Related target files**: `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/git_tools.py`, `scripts/mcp_servers/git/git_models.py`, `scripts/mcp_servers/git/format_output.py`
