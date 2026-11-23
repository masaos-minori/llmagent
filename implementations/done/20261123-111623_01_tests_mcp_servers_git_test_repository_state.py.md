## Goal

Pin the existing rejection of `git_add` and `git_commit` on a protected HEAD with regression tests at the state level and through the Stage 3 pipeline entry (REQ-001, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one new test class in this existing test module. No production, ADR, or inventory change here.

## Assumptions

- Verified in this cycle: `verify_authorization` takes the current HEAD as the destination for `git_add` and `git_commit`; a run against a real repository on `main` with protected `main` returned a protected-branch denial for both tools, also for the `Main` and `refs/heads/main` forms, and allowed `develop` and no list; no existing test combines protection with these two tools.
- Needs confirmation (non-blocking, Plan UNK-02): on a detached HEAD the active branch is None and Stage 3 denies with a misleading option-injection message, so the allow flag has no effect there. The tests pin the denial only and never assert that message.
- The module already builds `RepositoryState` values directly (for example in `TestVerifyAuthorizationRefGuardCharacterization`) and provides the real-repository fixtures `working_repo` and `detached_repo`; the new class reuses both styles.

## Design decisions

- `TestHeadDestinationProtection`(new) is appended after the last class of the module; every case is parametrized over the two tools.
- State-level cases build a `RepositoryState` with an explicit active branch; real-repository cases derive the protected name from the repository's actual current branch, so the default branch name of the host does not matter.

## Alternatives considered

Rejected: extending the 1900-line `test_git_security_compliance.py` (no reusable repository fixtures); rejected: new Invariant text or a ledger entry (the maintainer's decision, out of scope).

## Implementation
### Target file
`tests/mcp_servers/git/test_repository_state.py`

### Procedure
1. Add a module-level helper in the new class that builds a `RepositoryState` for an active branch, head type, and `ref_valid` value.
2. State-level cases: protected HEAD is rejected with `protected branch` in the message; the forms `Main`, `refs/heads/main`, and `refs/heads/MAIN` are rejected; a different HEAD is allowed; `None` and an empty protected list allow; a `requested_branch` other than HEAD does not change the decision for these two tools.
3. Real-repository cases: a repository snapshot on its current branch is rejected when that name is protected; after creating and checking out a new branch the same protected name allows.
4. Detached HEAD cases: using the detached fixture, both tools are denied by `verify_authorization` and by `WriteProtectionPipeline.run`, with and without `allow_detached_head`; assert only the `ok` outcome and never the message, and keep a comment that the behavior is under review (Plan UNK-02).
5. Pipeline case: a state on a protected HEAD with an operation callable that records a call; `run` returns a result with `ok` false, `rejected_at_stage` equal to `Stage 3`, `protected branch` in `rejection_message`, and the callable was never invoked.

### Method
Plain pytest functions in the style of the surrounding classes; no new fixtures and no change to existing tests.

### Details
- One-time mutation check (Plan AC-1): temporarily neutralize the HEAD-destination branch of `verify_authorization`, run the new class and see it fail, restore the file with a single-path `git checkout`, and confirm `git diff --stat -- scripts/` is empty before finishing.
- Keep the new class self-contained so it does not interact with `mcpai008`'s work in the same directory.

## Compatibility considerations

N/A: no behavior change; production code is untouched.

## Security considerations

N/A: documentation or tests only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_repository_state.py -q` and `uv run pytest tests/mcp_servers/git -q` pass.
- `uv run ruff format` and `uv run ruff check` clean for the test file; mypy passes for the test file path.

## Completion criteria

- The new class passes, covers both tools, the protected and non-protected cases, the normalized forms, the detached HEAD denial, and the pipeline never invoking the operation on rejection.
- The mutation check failed the new class and the file was restored; no file under `scripts/` changed.

## Out of Scope

Production code, ADR-012, the governance inventory, the Invariant decision, and the misleading detached-HEAD message.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-112813 | 20261123-112813 | Changed: tests/mcp_servers/git/test_repository_state.py (TestHeadDestinationProtection, 22 cases) |
| 2 | Run the git server suite, ruff, mypy, and the one-time mutation check described in Details; confirm no change under `scripts/` | Completed | 20261123-112813 | 20261123-112813 | ruff clean; git suite 440 passed; mutation check failed 14 of 22 then restored, scripts/ diff empty; full suite 13408 passed; diff-cover N/A (no source file changed) |

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
- **Requirement ID**: `REQ-001` (regression tests for the protected-HEAD check of `git_add` and `git_commit`), `REQ-004` (no production change)
- **Source issue**: issues/20261123-104601_gov002_git-protected-head-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-110851_gov002_git-protected-head-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-111623
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`
