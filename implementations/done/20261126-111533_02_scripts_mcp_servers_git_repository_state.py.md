## Goal

`verify_postcondition()` checks one operation today (`git_pull`); add operation-specific branches for `git_add`, `git_commit`, `git_checkout`, and `git_push` (REQ-002, operation-specific postconditions).

## Scope
**Release unit**: postcondition-tests-and-implementation

## Assumptions

- Every branch is computable from the two snapshots alone: `self` is the pre-operation state and `post_state` is the fresh post-operation state supplied by procedure 01. No request-model field (message, path list, remote name) is available at Stage 7, so the message and remote-name parts of REQ-002 are verified where the request is in scope — `scripts/mcp_servers/git/format_output.py` (procedure 04) — and Stage 7 verifies the state effect.
- `post_state._repo` can be `None` (a test double, or a snapshot whose handle was closed); every branch must guard for it and pass, as the current `git_pull` branch does.
- Confirmed by the user on 20261126: REQ-002's "expected message" for `git_commit` cannot be read at Stage 7, so Stage 7 verifies HEAD advancement and author state instead. The author comparison reads the repository-configured author through `post_state._repo.config_reader()`; the tests set a repository-local `user.name` so they do not depend on the developer's global git config.
- Confirmed by the user on 20261126: `verify_postcondition()` takes `requested_branch` as a third argument, so the `git_checkout` and `git_push` branches compare against the branch the operation targeted rather than against the post-state's active branch. This supersedes the "single data dependency" design decision below, which is recorded as a Step 3b correction.
- Stage 7 is not reached on the dry-run path (procedure 01 skips the postcondition check for a dry run), so no branch here needs a dry-run guard.

## Design decisions

- Postconditions are expressed as snapshot comparisons, not as request comparisons: no request-model field (message, path list, remote name) is read. `requested_branch` is already a `run()` parameter, so passing it to Stage 7 adds no new dependency on a request model (Step 3b correction: the original wording claimed a single `RepositoryState` dependency, which cannot express the checkout and push targets).
- The checkout exception in the `verify_postcondition()` docstring is removed once the pipeline supplies a real post-state; the exact branch-name match stays enforced in `format_checkout()`, which holds the request.

## Alternatives considered

- Passing the request model into `verify_postcondition()` — rejected: it would add a public-contract parameter that the pipeline does not hold. Passing `requested_branch`, which the pipeline already holds as a `run()` parameter, is the accepted form.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
- Extend `verify_postcondition()` with branches for `git_add`, `git_commit`, `git_checkout`, and `git_push`; keep the existing `git_pull` branch.
- Update the docstring: the method now receives a real post-operation snapshot, so `git_checkout` is checked here.

### Method
- Signature: `verify_postcondition(self, post_state, tool_name, requested_branch: str = "")`. The default keeps the existing two-argument call sites working.
- `git_add`: reject when the post-state shows no staged entry, i.e. `post_state.is_dirty` is False while `self.is_dirty` was False before the call.
- `git_commit`: reject when `post_state` HEAD is the same commit as `self` HEAD, or when the new commit's author does not match the repository-configured author.
- `git_checkout`: reject when `requested_branch` is non-empty and the post-state's active branch differs from it. A detached post-state is not rejected here: `allow_detached_head` is not available at Stage 7, and `format_checkout()` already enforces it where the request and the config are in scope (Step 3b correction: the original "HEAD did not move" condition rejected a legitimate no-op checkout onto the branch already checked out).
- `git_push`: reject when the remote-tracking ref for `requested_branch` (falling back to the post-state's active branch when `requested_branch` is empty) does not equal the post-state HEAD commit. A missing remote-tracking ref is a failure, not a pass.
- `git_pull`: unchanged.

### Details
- Read repository objects through `post_state._repo` with the existing `None` guard; do not use `post_state.repo`, which raises `RuntimeError` after `close()`.
- Rejection messages keep the current shape: `"{tool} postcondition failed: {reason}"`.
- Return `(True, "")` for a tool with no branch, as today.

## Compatibility considerations

- `tests/mcp_servers/git/test_repository_state.py:171` (`test_verify_postcondition_passes_for_any_push_result`) pins the current no-check behavior and must change with this procedure.
- `tests/mcp_servers/git/test_git_security_compliance.py:763` (`TestPostConditionBypassPrevention`) is ADR-012 INV-06 cited and must keep passing unchanged.
- Eight test files import this module; only the two assertions above pin the changed behavior.

## Security considerations

- No authorization behavior changes; `verify_authorization()` is untouched. Governance MCP-005 remains open and is not covered by these tests.

## Rollback considerations

- Revert the commit; the branches are additive and independently revertable.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Per-operation postconditions pass and fail as designed | `uv run pytest tests/mcp_servers/git/test_repository_state.py tests/mcp_servers/git/test_git_write_postconditions.py -v` | Each branch rejects the designed failure case |
| ADR-cited bypass prevention still green | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | No change |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- Each of the five write tools has a Stage 7 branch that rejects a designed postcondition failure on a real repository.
- The push branch compares the remote ref with the local commit (AC-2).

## Out of Scope

- The fresh post-state capture itself (procedure 01).
- Protected-branch tests for the HEAD-destination check (governance MCP-005, maintainer decision).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-144426 | 20261126-144426 | Needs confirmation: message check is not available at Stage 7 Resolved by user decision: three-argument signature with requested_branch. head_commit_hexsha added and captured in snapshot() so the git_commit branch compares against the frozen pre-operation HEAD; reading HEAD lazily could never detect an unchanged HEAD (Step 3b correction). Resolved by user decision: three-argument signature with requested_branch. head_commit_hexsha added and captured in snapshot() so the git_commit branch compares against the frozen pre-operation HEAD; reading HEAD lazily could never detect an unchanged HEAD (Step 3b correction). |
| 2 | Add or update tests per Validation plan | Completed | 20261126-144825 | 20261126-144825 | Cases in procedure 08 (unit) and procedure 10 (integration). Post-execution stale-detector note: the pinned case `test_verify_postcondition_passes_for_any_push_result` no longer exists because procedure 08 converted it to the real-repository case `test_push_postcondition_passes_for_a_real_push`; the procedure's own Validation plan named that case as one that must change. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-144426 | 20261126-144426 | Static sequence clean. Full suite as recorded on procedure 01 row 3. diff-cover 95.9% for this file: lines 232 and 275 (unreadable-HEAD defensive branches) are reachable only through a mock repository, which this procedure's completion criteria exclude; recorded as an accepted coverage gap. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: documentation is procedure 11 Documentation is procedure 11. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | 

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (operation-specific postconditions per write tool)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`