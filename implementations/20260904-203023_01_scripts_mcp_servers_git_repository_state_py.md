## Goal

Fix the live authorization path for `git_checkout`, `git_pull`, and `git_push` by adding the missing Stage 3 (`verify_authorization()`) call to `WriteProtectionPipeline.run()`, replacing the placeholder `_is_protected_branch()` with real logic against `GitConfig.protected_branches`, threading `protected_branches` into `RepositoryState.snapshot()`, and introducing an operation-target model for checkout/pull/push.

## Scope

- Add Stage 3 `verify_authorization()` call to `WriteProtectionPipeline.run()` before Stage 5 (REQ-001).
- Replace `_is_protected_branch(repo)`'s placeholder body with a real check against injected `protected_branches` (REQ-002).
- Add `protected_branches: list[str] = []` parameter to `RepositoryState.snapshot()` (REQ-003).
- Replace `ref_valid=True` with real validation: reject option-like/malformed/empty refs per tool semantics (REQ-004).
- Add operation-target resolution for checkout (destination branch), pull (local branch/tracking branch/remote), and push (local source/remote destination ref) ahead of `snapshot()`/authorization (REQ-005).
- Normalize short branch names (`main`) and fully-qualified refs (`refs/heads/main`) to the same comparison form (REQ-006).
- Resolve implicit (empty) targets to the current branch before authorization runs (REQ-007).
- Reject option-like/malformed/ambiguous refs before any GitPython call (REQ-008).
- Ensure an indeterminate target fails closed (denies) rather than proceeding (REQ-009).

## Assumptions

- `GitConfig.protected_branches`'s existing values (`main`, `master`, `release`) are the correct policy to enforce; this Plan does not change what is configured, only makes the configured value take effect.
- The 3 `RepositoryState.snapshot()` call sites in `git_server.py` (lines 169, 173, 184) are the complete set requiring the new `protected_branches` parameter — no other call site exists (confirmed by repository-wide `rg "RepositoryState.snapshot"`).
- Adding a Stage 3 call to `WriteProtectionPipeline.run()` does not require renumbering the documented stage sequence (5→6→7 remain as named); Stage 3 is inserted as a new first step, consistent with the docstring's existing claim that "Stages 1-3 ... are handled before pipeline construction."
- `verify_authorization()` already correctly reads `protected_branch`/`ref_valid` — that logic was never wrong, only unreached.

## Design decisions

- **Threading `protected_branches` through `snapshot()`**: New parameter defaults to `[]` so existing direct-`snapshot()` call sites in tests continue to work unchanged. `git_server.py` supplies the real value from its module-level `_cfg.protected_branches`, following the same pattern already used for `_cfg.allow_detached_head`.
- **Operation-target model**: Scoped narrowly to what checkout/pull/push need — resolved as plain function logic within `repository_state.py`, not a new class/abstraction. Checkout's destination is `req.branch` itself (already explicit); pull's target is the resolved local branch (current branch if `req.branch` is empty) and the selected remote; push's target is the local source (current branch if `req.branch` is empty) and the remote destination ref.
- **Stage 3 insertion**: Inserted as a new early step in `run()`, calling `RepositoryState.verify_authorization()` before Stage 5's precondition checks. No stage renumbering required.
- **Ref normalization**: Short branch names (`main`) and fully-qualified refs (`refs/heads/main`) normalized to the same comparison form before comparing against `protected_branches`.

## Alternatives considered

- **Adding a new `OperationTarget` dataclass**: Would be cleaner but adds abstraction overhead; the Deletion-First spirit favors plain function logic over new objects when scope is narrow.
- **Renaming stages 5→6→7 to 3→4→5**: Would be more semantically accurate but changes the documented stage sequence unnecessarily; inserting Stage 3 without renaming preserves backward compatibility with the existing documentation.
- **Using `GitService._validate_protected()`**: It is unreachable dead code on the live path; this issue's own Constraints prohibit introducing a second authorization mechanism — the fix belongs entirely in the path that actually serves requests.

## Implementation
### Target file

`scripts/mcp_servers/git/repository_state.py`

### Procedure

1. Add `protected_branches: list[str] = []` parameter to `RepositoryState.snapshot()` signature.
2. Replace `_is_protected_branch(repo)`'s body with real logic checking `self.protected_branches`.
3. Add `verify_authorization()` call to `WriteProtectionPipeline.run()` before Stage 5.
4. Replace `ref_valid=True` with real validation rejecting option-like/malformed/empty refs.
5. Add operation-target resolution for checkout/pull/push ahead of snapshot()/authorization.
6. Normalize short branch names and fully-qualified refs to the same comparison form.
7. Resolve implicit (empty) targets to current branch before authorization runs.
8. Reject option-like/malformed/ambiguous refs before any GitPython call.
9. Ensure indeterminate target fails closed (denies) rather than proceeding.

### Method

Modify existing methods/functions in-place; no new public API surface.

### Details

- `snapshot()`: Add `protected_branches` parameter with default `[]`. Pass it to `_is_protected_branch()` and store on `RepositoryState`.
- `_is_protected_branch()`: Replace `return False` with loop over configured `protected_branches`, normalizing both sides to `refs/heads/<name>` form before comparison.
- `WriteProtectionPipeline.run()`: Insert `verify_authorization()` call between pipeline construction and Stage 5 precondition checks.
- `ref_valid`: Replace hard-coded `True` with validation logic checking ref format against tool semantics.
- Operation-target resolution: Add helper functions within `repository_state.py` for checkout/pull/push target resolution.

## Compatibility considerations

- Default parameter value (`[]`) for `protected_branches` preserves every existing direct-`snapshot()` call that does not pass it.
- Existing test fixtures that construct `RepositoryState` without caring about protection continue to work unchanged.
- `verify_authorization()`'s return type (`tuple[bool, str]`) matches the existing pipeline stage contract.

## Security considerations

- Fail-closed: when an effective operation target cannot be uniquely determined, deny rather than proceed.
- Reject option-like, malformed, ambiguous, or indeterminate refs before any GitPython call executes.
- Empty/whitespace-only values where not semantically valid for the tool must be rejected or resolved to the current branch before authorization runs.

## Rollback considerations

- If adding Stage 3 authorization rejects currently-succeeding operations on non-protected branches due to an edge case in `verify_authorization()`, comprehensive HTTP-level tests covering non-protected branches must pass unchanged before considering the fix complete.
- Threading `protected_branches` through `RepositoryState.snapshot()` changes a shape used across 3 call sites and test fixtures — default parameter value (`[]`) preserves every existing direct-`snapshot()` call that does not pass it.

## Validation plan

- Unit: `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — Stage 3 call verified via spy on the operation callable; `_is_protected_branch()` against configured `protected_branches`; `ref_valid` rejecting option-like/malformed refs.
- Integration: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_mcp_git.py -v` — new `/v1/call_tool` tests pass; protected branches denied, non-protected allowed.
- Regression: `uv run pytest tests/mcp_servers/git/ -v` — 184+ tests pass, no new failures.
- Static: `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` — all pass with no new findings.

## Completion criteria

- `WriteProtectionPipeline.run()` invokes Stage 3 authorization before Stage 5/6 for every write tool it dispatches.
- Configured protected branches (`main`, `master`, `release`) are identified and rejected consistently for `git_checkout`, `git_pull`, and `git_push` via the live `POST /v1/call_tool` path.
- `main` and `refs/heads/main` are evaluated consistently as the same protected branch.
- `git_pull` and `git_push` with an empty branch cannot bypass authorization — the implicit (current-branch) target is resolved before the protected-branch check runs.
- A non-protected local source cannot be pushed to a protected remote destination branch.
- Unsafe or ambiguous refs are rejected before Git execution.
- HTTP-level authorization tests cover explicit and implicit targets for checkout, pull, and push via `POST /v1/call_tool`.
- No production protection helper on the live path unconditionally permits protected branches or refs.

## Out of scope

- `WriteProtectionPipeline`'s stage ordering/postcondition verification beyond adding the missing Stage 3 call (`gitpipeline`).
- Detached-HEAD/dry-run precondition behavior (`gitdryrun`).
- Unifying `GitService`'s dead-code dispatch table with the live `call_tool` path (`gitdispatch`).
- Repository-path containment/audit (`gitpathaudit`).
- Remote authorization/concurrency (`gitremote`).
- Deleting the ~60 unused placeholder methods this Plan's investigation found in `RepositoryState`/`WriteProtectionPipeline` (`gitcleanup`).
- Making `git_add`/`git_commit` reachable via `call_tool` (currently not dispatched at all via the live path — `gitdispatch` scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-009
- **Source issue**: issues/20260902-144907_gitauth_complete_protected_branch_and_ref_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-162951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-203023
- **Related target files**: scripts/mcp_servers/git/repository_state.py
