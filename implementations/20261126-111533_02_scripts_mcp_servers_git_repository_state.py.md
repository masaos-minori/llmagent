## Goal

`verify_postcondition()` checks one operation today (`git_pull`); add operation-specific branches for `git_add`, `git_commit`, `git_checkout`, and `git_push` (REQ-002, operation-specific postconditions).

## Scope
**Release unit**: postcondition-tests-and-implementation

## Assumptions

- Every branch is computable from the two snapshots alone: `self` is the pre-operation state and `post_state` is the fresh post-operation state supplied by procedure 01. No request-model field (message, path list, remote name) is available at Stage 7, so the message and remote-name parts of REQ-002 are verified where the request is in scope — `scripts/mcp_servers/git/format_output.py` (procedure 04) — and Stage 7 verifies the state effect.
- `post_state._repo` can be `None` (a test double, or a snapshot whose handle was closed); every branch must guard for it and pass, as the current `git_pull` branch does.
- Needs confirmation (non-blocking): REQ-002's "expected message" for `git_commit` cannot be read at Stage 7; this procedure verifies HEAD advancement and author state instead.

## Design decisions

- Postconditions are expressed as snapshot comparisons, not as request comparisons, so Stage 7 keeps a single data dependency (`RepositoryState`).
- The checkout exception in the `verify_postcondition()` docstring is removed once the pipeline supplies a real post-state; the exact branch-name match stays enforced in `format_checkout()`, which holds the request.

## Alternatives considered

- Passing the request model into `verify_postcondition()` — rejected: it would add a public-contract parameter that the pipeline does not hold, forcing a call-site change in a file this procedure does not modify.

## Implementation
### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
- Extend `verify_postcondition()` with branches for `git_add`, `git_commit`, `git_checkout`, and `git_push`; keep the existing `git_pull` branch.
- Update the docstring: the method now receives a real post-operation snapshot, so `git_checkout` is checked here.

### Method
- `git_add`: reject when the post-state shows no staged entry, i.e. `post_state.is_dirty` is False while `self.is_dirty` was False before the call.
- `git_commit`: reject when `post_state` HEAD is the same commit as `self` HEAD, or when the new commit's author does not match the repository-configured author.
- `git_checkout`: reject when HEAD did not move (`post_state.active_branch == self.active_branch` on a real checkout) or when the post-state is a detached HEAD and detached HEAD is not allowed by the caller's existing guard path.
- `git_push`: reject when the remote-tracking ref for the post-state's active branch does not equal the post-state HEAD commit.
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
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Needs confirmation: message check is not available at Stage 7 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation is procedure 11 |

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
- **Requirement ID**: `REQ-002` (operation-specific postconditions per write tool)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/repository_state.py`
