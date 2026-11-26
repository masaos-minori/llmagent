## Goal

`format_pull()` and `format_push()` run the mutating Git call through a synchronous `subprocess` call that can be terminated on timeout, and report the write outcome instead of assuming success (REQ-003, REQ-004, AC-2, AC-3).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- The subprocess call is executed inside Stage 6's `op` (`Callable[[], str]`), so `WriteProtectionPipeline.run()` stays synchronous and no async seam is added (Step 3a design decision).
- The process-group pattern follows `scripts/mcp_servers/shell/subprocess_runner.py` (`run_subprocess()`, lines 54-111): `start_new_session=True` and `os.killpg()` on timeout. The pattern is reused; its async call form is not.
- `confirmed-not-applied` and `outcome_unknown` come from `scripts/shared/write_outcome.py` (procedure 06).
- `format_checkout()`'s own snapshot refresh at line 152 is released through `RepositoryState`'s context-manager form (REQ-005).

## Design decisions

- The deadline is applied inside the call, so a timeout terminates the process group rather than leaving a worker thread running past `asyncio.wait_for` (AC-3).
- `GitPython` is kept for the read tools and for the state snapshot; only the two network write calls move to the `git` CLI, because GitPython has no cancellation point.
- Remote and branch validation stays in front of the call: `_authorize_remote()` and `validate_ref_allowlist()` are called before the subprocess is started, so the security controls are unchanged.

## Alternatives considered

- `asyncio.subprocess` — rejected in Step 3a: Stage 6's op is synchronous and must stay inside the per-repository lock, so an awaited op would require an async seam in `scripts/mcp_servers/git/write_protection_pipeline.py`, which is outside that row's change responsibility.
- Keeping GitPython with a cooperative cancellation flag — rejected per the Plan (no cancellation point in a synchronous call).

## Implementation
### Target file
`scripts/mcp_servers/git/format_output.py`

### Procedure
- In `format_pull()` and `format_push()`, replace the GitPython mutating call with a synchronous `subprocess.run()` of the `git` CLI (`git pull <remote>`, `git push <remote> -- <branch>`) using `start_new_session=True` and `timeout=timeout`.
- On `subprocess.TimeoutExpired`, terminate the process group with `os.killpg()` and return the outcome for the timeout case instead of a success message.
- Report the outcome through the vocabulary: `confirmed-not-applied` when the call completed and the postcondition confirms the effect, `outcome_unknown` when the call ended without a verifiable effect.
- Release the snapshot refresh in `format_checkout()` (line 152) with the context-manager form.

### Method
- Build argv from the request model fields (`GitPullRequest.remote`, `GitPushRequest.branch`) with `--` separators, so no user-supplied value is interpreted as an option.
- Run with `cwd=state.path`, `capture_output=True`, `text=True`; on a non-zero exit raise `GitServiceError` with the stderr text, matching the current `git_push failed: ...` shape.
- After a successful call, re-read the state for the postcondition: pull checks `unmerged_blobs()`, push compares the remote-tracking ref with the local HEAD commit (AC-2).
- Update the `timeout` docstrings: the deadline is now applied inside the helper, not at the async boundary.

### Details

- Dry-run paths keep the current GitPython behavior (`git fetch --dry-run`); dry-run is not a write and does not need the subprocess path.
- The `timeout` parameter keeps its `float | None` signature; `None` means no deadline.
- Outcome reporting is returned as the formatter result string; the audit outcome mapping is done in `scripts/mcp_servers/git/git_server.py` (procedure 05).

## Compatibility considerations

- `tests/mcp_servers/git/test_format_output.py` is the row's related test file; the pull and push cases there currently assert GitPython call shapes and must be rewritten against the subprocess path.
- Rejection message text is not stable by contract (`docs/22_mcp/mcp_04_05_git.md`, "Callers must not depend on message text"), so message-shape changes are acceptable.
- `format_checkout()`'s postcondition message stays as it is; only the handle release changes there.

## Security considerations

- `allowed_remote_urls` and the ref allowlist are enforced before the subprocess starts; the subprocess never receives a raw URL from the caller.
- `shell=False` (the default) is used, so no shell interpretation of branch or remote names.

## Rollback considerations

- Revert the commit; the two formatters are independent of the read formatters.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Subprocess path and outcome reporting | `uv run pytest tests/mcp_servers/git/test_format_output.py tests/mcp_servers/git/test_git_write_postconditions.py -v` | Timeout terminates the process group; outcomes reported per the vocabulary |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- A pull or push timeout terminates the process group and does not leave a thread continuing the operation (AC-3).
- Push verifies the remote ref against the expected local commit before reporting success (AC-2).

## Out of Scope

- The async boundary and `asyncio.wait_for` removal (`scripts/mcp_servers/git/git_service.py`, procedure 03).
- The outcome vocabulary member (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (cancellable subprocess for pull and push), `REQ-004` (write-outcome reporting), `REQ-005` (handle release)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/format_output.py`
