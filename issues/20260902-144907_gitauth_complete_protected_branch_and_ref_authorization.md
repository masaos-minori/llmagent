# Complete protected-branch and Git ref authorization for all write operations

## Priority
High

## Summary
Establish one fail-closed authorization path that resolves every effective source and
destination ref before execution, applies `GitConfig.protected_branches`, validates refs, and
prevents implicit branch selection from bypassing policy for checkout, pull, and push.

## Background
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` and the earlier
`issues/done/20260902-094746_h01_git_mcp_write_protection_status_contradiction.md`
investigation concluded that write-protection guards are implemented and tested. That
conclusion covered `GitService._validate_protected()` (`scripts/mcp_servers/git/git_service.py`,
used by the checkout/pull/push handlers, backed by `test_check_protected_branch`), which is
real, live, and working. It did not cover a separate, parallel code path: `RepositoryState`'s
own `WriteProtectionPipeline` (see `gitpipeline`, filed alongside this issue) defines its own
`_is_protected_branch()` and a `ref_valid` field that are independent of
`GitService._validate_protected()` and were not exercised by that investigation.

## Problem
`RepositoryState._is_protected_branch()` (`scripts/mcp_servers/git/repository_state.py`)
unconditionally returns `False`, and `ref_valid` is initialized as `True` without validating
the request or resolved refs. Authorization must evaluate the branch or ref that checkout,
pull, or push will actually modify, not only the branch active when the initial snapshot was
captured. `GitService._validate_protected()` is not called for `add`/`commit` at all. Without a
unified fix, a request may pass validation even when its effective destination is protected,
ambiguous, malformed, or option-like.

## Reason for Change
This issue intentionally combines protected-branch resolution, checkout/pull/push target
resolution, and ref validation because these concerns share the same operation-target model and
must be implemented together to avoid inconsistent checks.

## Implementation Intent
Introduce or finalize a structured operation-target model distinguishing the current branch,
requested ref, resolved local source/destination ref, upstream ref, remote name, remote URL,
and remote destination ref. Inject `GitConfig.protected_branches` into the authorization layer
explicitly; normalize short branch names and fully qualified refs before policy comparison.
Resolve and authorize the actual destination for checkout; the local branch/tracking
branch/selected remote for pull; the local source and remote destination ref for push. Reject
empty/whitespace-only values where not valid (resolving implicit targets before authorization
when an empty value means one); reject option-like, malformed, ambiguous, or indeterminate
refs before invoking GitPython; fail closed when an effective target cannot be uniquely
determined.

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
- Remove the `_is_protected_branch()` placeholder that always returns `False`.
- Remove the hard-coded `ref_valid=True` behavior.
- Introduce or finalize a structured operation-target model (current branch, requested ref, resolved local source/destination ref, upstream ref, remote name, remote URL, remote destination ref).
- Inject `GitConfig.protected_branches` into the authorization layer explicitly.
- Normalize short branch names and fully qualified refs before policy comparison.
- Resolve and authorize the destination before execution for checkout; the local branch, tracking branch, and selected remote for pull; the local source and remote destination ref for push.
- Reject empty/whitespace-only values where not valid; resolve implicit targets before authorization.
- Reject option-like, malformed, ambiguous, or indeterminate refs before invoking GitPython.
- Fail closed when an effective operation target cannot be uniquely determined.
- Decide whether this authorization path replaces, wraps, or is consolidated with `GitService._validate_protected()`'s existing, working checks — do not leave two independent protected-branch mechanisms with different coverage (see Unresolved Questions).

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path — this issue's outcome must consolidate with, not duplicate, `GitService._validate_protected()`.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- Configured protected branches are identified and rejected consistently for checkout, pull, push, add, and commit where applicable.
- `main` and `refs/heads/main` are evaluated consistently.
- `git_pull` and `git_push` with an empty branch cannot bypass authorization.
- A non-protected local source cannot be pushed to a protected remote destination.
- Unsafe or ambiguous refs are rejected before Git execution.
- Authorization tests cover explicit and implicit targets for checkout, pull, and push.
- No production protection helper (in either code path) unconditionally permits protected branches or refs.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md` and ADR-012's Known Deviations/Invariant Verification once
implementation and tests establish the current behavior — do not update documentation ahead of
verified code, per Constraints.

## Out of Scope
- The write-protection pipeline's stage ordering and postcondition verification (`gitpipeline`).
- Detached-HEAD/dry-run precondition behavior (`gitdryrun`).
- Tool dispatch unification (`gitdispatch`).
- Repository-path containment and audit hardening (`gitpathaudit`).
- Remote authorization and concurrency control (`gitremote`).

## Dependencies
Related to `gitpipeline` (filed alongside this issue) — both touch
`scripts/mcp_servers/git/repository_state.py`'s `WriteProtectionPipeline`; coordinate to avoid
conflicting edits to the same authorization stage.

## Unresolved Questions
Whether `RepositoryState`'s authorization path (this issue) is meant to be the sole
authorization mechanism going forward, with `GitService._validate_protected()` migrated or
removed, or whether the two are meant to remain as independent, redundant checks — this is an
architecture decision that should be resolved before implementation, not assumed.

## AI Implementation Instruction
Before editing, re-confirm `GitService._validate_protected()`'s current behavior and callers
(`grep -rn "_validate_protected" scripts/mcp_servers/git/`) alongside
`RepositoryState._is_protected_branch()`'s callers, since this issue's evidence may go stale.
Resolve the Unresolved Questions consolidation decision before implementing, rather than
building a second parallel mechanism. Do not modify `GitService._validate_protected()`'s
already-working behavior without explicit justification tied to that decision.
