## Goal

Stage 7 compares two distinct snapshots: the pipeline captures a fresh post-operation `RepositoryState` after Stage 6 and reports it as `PipelineResult.post_state` (REQ-001, fresh post-operation snapshot).

## Scope
**Release unit**: postcondition-tests-and-implementation

## Assumptions

- The post-state is captured inside the per-repository lock, so it reflects the state immediately after the mutating call.
- `PipelineResult.post_state` keeps the object after `close()`; only its `git.Repo` reference is released, so the audit serialization in `scripts/mcp_servers/git/git_server.py` still reads the captured fields.
- The post-state's `ref_valid` is derived from `requested_branch`, which is the requested ref for `git_pull`/`git_push`/`git_checkout` and empty for `git_add`/`git_commit`.
- Stage 7 is skipped when `dry_run` is True: a dry-run performs no write, so an operation-specific postcondition would reject every dry-run. This is recorded in the Execution Status Notes as a Step 3b correction (the original text did not cover the dry-run path).
- The pipeline owns the outcome classification, per the Plan's frozen row for this file ("carry the write outcome in `PipelineResult`"): a `subprocess.TimeoutExpired` raised by Stage 6's op is `outcome_unknown`, and a Stage 7 rejection is `confirmed-not-applied`.

## Design decisions

- The pipeline, not the caller, owns the post-operation snapshot (`Plan > Design`, Post-state ownership).
- The post-state handle is released through the context-manager form of `RepositoryState` after Stage 7 has read it (REQ-005, handle release).

## Alternatives considered

- Refresh the fields of the pre-state object in place — rejected: `RepositoryState` is a frozen dataclass, and Stage 7 could still not distinguish pre from post.

## Implementation
### Target file
`scripts/mcp_servers/git/write_protection_pipeline.py`

### Procedure
- In `run()`, after Stage 6 (`output = self._execute(tool_name, op)`), capture a second snapshot as `post_state`.
- Call `self._state.verify_postcondition(post_state, tool_name, requested_branch)` instead of passing `self._state` as both arguments.
- Pass `post_state` to `PipelineResult.ok_result()` and to the Stage 7 rejection result.
- Add `outcome: WriteOutcome | None = None` to `PipelineResult` (Plan row 44: "carry the write outcome in `PipelineResult`"), and pass it through `ok_result()` and `reject()`.
- Catch `subprocess.TimeoutExpired` around Stage 6: capture `post_state` for reconciliation and return a rejection result with `rejected_at_stage = "Stage 6"` and `outcome = OUTCOME_UNKNOWN`, without running Stage 7. The failed stage is not recorded, per the pipeline's rule that `stages` holds only stages that ran.

### Method
- Capture with `RepositoryState.snapshot(self._state.path, protected_branches=protected_branches, active_ref=requested_branch or "")` inside the `with _get_repo_lock(self._state.path)` block.
- Wrap the capture in `with ... as post_state:` so the handle is released on the success path, the Stage 7 rejection path, the Stage 6 timeout path, and an exception raised by Stage 6.
- Import `subprocess` and the vocabulary constants from `scripts/shared/write_outcome.py` (procedure 06) for the Stage 6 timeout classification.
- Update the Stage 7 comment: the pipeline now captures two snapshots per write request.

### Details
- `run()`'s signature is unchanged; `protected_branches` and `requested_branch` are already parameters.
- Results rejected before Stage 6 keep `post_state=None`, matching current behavior.
- `PipelineResult` gains one field, `outcome` (Step 3b correction: the original text said the fields were unchanged, which contradicted the Plan's frozen row for this file). Existing callers read `ok`, `output`, `repository_state`, and `post_state` unchanged.

## Compatibility considerations

- `tests/mcp_servers/git/test_repository_state.py:371` (`test_pipeline_result_ok_has_post_state`) must assert the stored post-state is a distinct object from `repository_state`.
- Consumers that read `PipelineResult.post_state` for audit serialization see the same field types.

## Security considerations

- Stage order is unchanged; ADR-012 INV-09 (Stage 6 before Stage 7) is preserved.

## Rollback considerations

- Revert the commit; the change is confined to `run()`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Post-state is a distinct object | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | Stage 7 receives a different `RepositoryState` |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- For a write that reaches Stage 7, `PipelineResult.post_state` is a different object from `PipelineResult.repository_state`.
- The post-state handle is closed on every path.

## Out of Scope

- The operation-specific postcondition branches (`scripts/mcp_servers/git/repository_state.py`, procedure 02).
- The subprocess execution path (`scripts/mcp_servers/git/format_output.py`, procedure 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-144426 | 20261126-144426 | Post-state captured inside the per-repository lock; PipelineResult.outcome added and passed through ok_result()/reject(); TimeoutExpired classified at Stage 6 as outcome_unknown with no Stage 7 record; Stage 7 skipped on dry_run; _execute() re-raises TimeoutExpired unchanged. |
| 2 | Add or update tests per Validation plan | Completed | 20261126-144426 | 20261126-144426 | Cases live in procedure 10 (tests/mcp_servers/git/test_git_write_postconditions.py); targeted run 17 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-144426 | 20261126-144426 | Static sequence clean (ruff, mypy, lint-imports, bandit with the B404 justification). Full suite: 14771 passed; the 26 failures and 44 errors are pre-existing baseline failures in tests/agent/commands/ and tests/docs/ (RuntimeToolRegistry NameError in scripts/agent/commands/cmd_mcp.py, identical to master), none in the changed files. diff-cover 98%. |
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
- **Requirement ID**: `REQ-001` (fresh post-operation snapshot in the write pipeline)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/write_protection_pipeline.py`