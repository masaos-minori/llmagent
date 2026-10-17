## Goal

Invert the Stage 5b characterization tests in `tests/mcp_servers/git/test_repository_state.py` so they
assert the live HEAD re-check denies drifted HEAD identity, and add the case that a snapshot without a
real repository object is never denied (REQ-008).

## Scope

- Rename and invert `test_head_drift_not_rejected_with_single_snapshot`.
- Keep `test_head_unchanged_during_op_succeeds` unchanged.
- Add a mocked-snapshot case that must not deny.
- Add a branch-name drift case, which the old comparison could not detect.

## Assumptions

- The `working_repo` fixture yields a real repository path, so `RepositoryState.snapshot` stores a real
  `git.Repo` in `_repo` and the live re-read runs.
- `MagicMock(spec=RepositoryState)` doubles never reach the live comparison because the guard tests
  `_repo` with `isinstance(..., git.Repo)`.

## Design decisions

- Assert `result.ok is False`, the rejection stage name, and that the operation never ran, so the test
  pins both the denial and the fact that denial happens before the mutating call.
- Keep the docstring of the inverted test as a description of the guard rather than of the gap, so the
  file no longer documents a no-op.

## Alternatives considered

- Delete the drift test and rely on the new cases: rejected — the existing test is the record of the
  previously accepted behaviour, and inverting it is what shows the gap closed.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Rename `test_head_drift_not_rejected_with_single_snapshot` to
   `test_head_drift_rejected_by_live_recheck` (new) and invert its assertions.
2. Add `test_branch_drift_rejected_by_live_recheck` (new).
3. Add `test_mocked_repo_never_denies_at_stage_5b` (new).

### Method

Reuse the existing snapshot-then-mutate pattern: snapshot while attached, detach HEAD with a real
`git.Repo`, then run the pipeline and assert denial.

### Details

- The test to invert is `test_head_drift_not_rejected_with_single_snapshot` at
  `tests/mcp_servers/git/test_repository_state.py:491-510`; its current assertions are
  `result.ok is True` and `op_called is True`.
- Inverted assertions: `result.ok is False`, the rejection names Stage 5b, `op_called is False`, and the
  rejection message contains `repository HEAD state changed since authorization`.
- Branch drift case: snapshot while on a branch, create and check out a second branch with the real
  repository, run the pipeline, and assert denial.
- Mocked-snapshot case: build a `RepositoryState` with `_repo=MagicMock()` and `head_type` set to
  `"branch"`, run the pipeline, and assert `result.ok is True`.
- `test_head_unchanged_during_op_succeeds` at `tests/mcp_servers/git/test_repository_state.py:481-489`
  stays as written and now also proves the live read does not deny a stable HEAD.

## Compatibility considerations

- This is a deliberate behaviour inversion: the file currently documents the no-op as a known gap, and
  after this change it documents the guard.
- `tests/mcp_servers/git/test_mcp_git.py` and `tests/mcp_servers/git/test_git_service_dispatch.py` use
  `MagicMock(spec=RepositoryState)` snapshots and must keep passing without change.

## Security considerations

N/A: test-only change; the cases assert the TOCTOU guard denies rather than passes.

## Rollback considerations

N/A: revert the commit. Reverting restores the no-op guard, so any rollback must re-register MCP-006 in
the known-issue ledger.

## Validation plan

- `uv run pytest -q tests/mcp_servers/git/test_repository_state.py`
- `uv run pytest -q tests/mcp_servers/git/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- The inverted test denies a detached-HEAD drift and proves the operation never ran (AC-008).
- The branch-drift test denies a case the old comparison could not detect.
- The mocked-snapshot test passes without denial.
- `test_head_unchanged_during_op_succeeds` and the rest of the file still pass.

## Out of scope

- Stage 7 postcondition verification tests.
- Concurrency tests in `tests/mcp_servers/git/test_git_concurrency.py`.
- The swapped request-context binding in `scripts/mcp_servers/git/git_server.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename and invert the drift test | Completed | 20261017-183000 | 20261017-185200 | REQ-008 |
| 2 | Add the branch-drift and mocked-snapshot cases | Completed | 20261017-183000 | 20261017-185200 | REQ-008 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-190500 | 20261017-192200 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`