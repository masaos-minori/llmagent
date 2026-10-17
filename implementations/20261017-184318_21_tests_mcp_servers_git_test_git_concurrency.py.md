## Goal

Update the characterization test in `tests/mcp_servers/git/test_git_concurrency.py` that records the
previously accepted behaviour: Stage 5b did not reject a repository HEAD that detached after
authorization. After Plan row 6 makes Stage 5b read the live HEAD identity, that behaviour is a denial
(REQ-008: close the authorization-to-execution window for git-mcp write tools).

## Scope

- Rename `test_head_drift_not_rejected_with_single_snapshot` to
  `test_head_drift_rejected_by_live_recheck` (new).
- Invert its expectations from pass-through to a Stage 5b denial, including the assertion that the
  mutating operation was never invoked.
- Leave the lock and cross-repo-path cases in the same module unchanged.

## Assumptions

- The module's `repo_a` fixture yields a real repository path and `RepositoryState.snapshot(repo_a)`
  stores the live `git.Repo` in `_repo`, so `_live_head_identity` performs a real read instead of being
  skipped.
- `repo.git.checkout(repo.head.commit.hexsha)` detaches HEAD, so the live identity pair becomes
  `("detached", None)` while the snapshot still records `("branch", <name>)`.

## Design decisions

- Assert `op_called is False` in addition to the rejection, because the guard exists to stop the
  mutating Git call, not merely to report drift.
- Keep the `git_pull` and `git_push` parametrization so the denial is pinned per tool rather than once
  per pipeline.

## Alternatives considered

- Delete the case: rejected — it is the only per-tool evidence that Stage 5b now denies drifted HEAD.
- Keep the pass-through assertion and skip the live read for these tools: rejected — it would undo
  REQ-008.

## Implementation

### Target file

`tests/mcp_servers/git/test_git_concurrency.py`

### Procedure

1. Rename the test and rewrite its docstring so it states the live re-check behaviour.
2. Replace the two pass-through assertions with the denial assertions.
3. Keep the fixture usage, the parametrization, and the checkout step unchanged.

### Method

Build the pipeline from a snapshot taken while HEAD is attached, detach HEAD afterwards, and assert the
pipeline denies at Stage 5b before the operation runs.

### Details

- The case at `tests/mcp_servers/git/test_git_concurrency.py:143-165` currently asserts
  `result.ok is True` and `op_called is True`, with a docstring that states the guard is a no-op.
- New expectations: `result.ok is False`, `result.rejected_at_stage == "Stage 5b"`,
  `"HEAD state changed" in result.rejection_message`, and `op_called is False`.
- The `_op` return text changes from `"should run (5b is a no-op)"` to a marker that must never be
  observed, so a pass-through cannot be mistaken for the expected outcome.

## Compatibility considerations

- This is the second of two modules that asserted the no-op; Plan row 10 covers
  `tests/mcp_servers/git/test_repository_state.py`.
- No production code is modified by this document.

## Security considerations

- The case now proves the authorization-to-execution window is closed for the git-mcp write tools it
  parametrizes.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/mcp_servers/git/test_git_concurrency.py`
- `uv run pytest -q tests/mcp_servers/git/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- Both parametrized cases deny at Stage 5b and never invoke the operation (AC-008).
- The lock-contention and cross-repo-path cases in the same module still pass unchanged.

## Out of scope

- The Stage 5b implementation itself, which is Plan row 6.
- The `tests/mcp_servers/git/test_repository_state.py` cases, which are Plan row 10.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename and invert the characterization case | Completed | 20261017-184318 | 20261017-185200 | REQ-008 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-190500 | 20261017-192200 |  |

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
- **Generated at**: 20261017-184318
- **Related target files**: `tests/mcp_servers/git/test_git_concurrency.py`