# Align detached-HEAD and dry-run behavior with configuration and safety policy

## Priority
High

## Summary
Make execution context explicit in `RepositoryState`'s precondition evaluation so
`allow_detached_head` is actually evaluated and `dry_run` is actually enforced, instead of the
precondition method silently ignoring both.

## Background
`issues/done/20260823_git_dirty_worktree_detached_head_issue.md` (GIT-001) already resolved a
related dirty-worktree/detached-HEAD issue. This issue is a separate, narrower gap investigation
found in the same area: `RepositoryState.verify_preconditions(self, command: str)`
(`scripts/mcp_servers/git/repository_state.py`) does not accept a `dry_run` parameter at all,
even though its own error message and documentation state that dirty-worktree and
detached-HEAD checks apply only when `dry_run` is false and that `allow_detached_head=true` can
permit detached HEAD.

## Problem
The current precondition method rejects detached HEAD unconditionally even though the error
message states that `allow_detached_head=true` can permit it, and it does not receive or
evaluate `dry_run` despite claiming dry-run-conditional behavior. Configuration, documentation,
and runtime behavior can diverge, and preview operations may be rejected or handled
inconsistently.

## Reason for Change
GIT-001 addressed the immediate dirty-worktree/detached-HEAD scenario; this issue closes the
remaining, more structural gap (the precondition method's inability to even observe `dry_run`
or `allow_detached_head`) that GIT-001 did not scope.

## Implementation Intent
Make execution context explicit and apply configuration-driven, operation-specific
preconditions consistently. Dry-run must remain non-mutating while still enforcing
authorization, and detached-HEAD behavior must be permitted only for operations that have a
documented and testable safety model.

## Target Files or Areas
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/git/git_models.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/format_output.py`
- `config/git_mcp_server.toml`
- `tests/test_git_security_compliance.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Inject `allow_detached_head` into the pipeline policy.
- Pass `dry_run` and the operation type into precondition evaluation.
- Define which operations, if any, may run in detached HEAD when the setting is enabled.
- Keep authorization active during dry-run.
- Define whether dirty-worktree and detached-HEAD checks are required, skipped, or altered for each dry-run operation.
- Ensure every dry-run implementation performs no local or remote mutation.
- Correct runtime messages and documentation so they describe implemented behavior only.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior, including GIT-001's already-resolved dirty-worktree checks.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- `allow_detached_head=false` rejects applicable detached-HEAD write operations.
- `allow_detached_head=true` affects only explicitly documented operations.
- Dry-run requests do not mutate the repository or remote.
- Protected or unauthorized targets remain rejected during dry-run.
- Dirty-worktree and detached-HEAD behavior is covered for both real and dry-run requests.
- Configuration, error messages, documentation, and runtime behavior are consistent.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md`'s dry-run and detached-HEAD description once implementation
and tests establish the current behavior.

## Out of Scope
- GIT-001's already-resolved dirty-worktree/detached-HEAD scenario — do not re-open or re-implement it.
- Protected-branch/ref authorization content itself (`gitauth`).
- The write-protection pipeline's stage ordering (`gitpipeline`).

## Dependencies
Builds on `issues/done/20260823_git_dirty_worktree_detached_head_issue.md` (GIT-001); does not
depend on `gitauth`/`gitpipeline` landing first but should be coordinated with `gitpipeline`
since both touch `RepositoryState`'s precondition/pipeline stages.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, re-confirm `verify_preconditions()`'s current signature and GIT-001's landed
fix (`grep -rn "verify_preconditions\|allow_detached_head" scripts/mcp_servers/git/`), since
this issue's evidence may go stale. Do not alter GIT-001's already-verified dirty-worktree
behavior beyond what is needed to also thread `dry_run` through the same method.
