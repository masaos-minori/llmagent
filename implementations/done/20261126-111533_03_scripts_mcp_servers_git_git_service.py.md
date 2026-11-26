## Goal

Remove the `asyncio.wait_for` deadline for pull and push, because the timeout is now enforced inside the synchronous subprocess call in Stage 6's op (REQ-003, cancellable execution), and release the snapshot handle on every path (REQ-005, handle release).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- `asyncio.to_thread` is kept: the pipeline's `run()` is synchronous, and the worker thread is what keeps `/health` and read tools responsive during a network write.
- The subprocess itself is executed inside Stage 6's op, which lives in `scripts/mcp_servers/git/format_output.py` (procedure 04); this procedure changes only the async boundary and the handle lifecycle.
- The per-repository lock still orders writes to the same canonical path, because Stage 6 runs inside `with _get_repo_lock(self._state.path)`.

## Design decisions

- The deadline moves from the async boundary to the subprocess call, so a timeout terminates the process group instead of leaving a thread running.
- The snapshot is held through the context-manager form of `RepositoryState` for the whole `_run_tool()` body, so the handle is released on the read-tool path, the write path, a policy rejection, and a timeout.

## Alternatives considered

- A cooperative cancellation flag inside `asyncio.to_thread` — rejected per the Plan (a synchronous call has no cancellation point).
- Running the pipeline directly on the event loop — rejected: it would block `/health` for the duration of a network write.

## Implementation
### Target file
`scripts/mcp_servers/git/git_service.py`

### Procedure
- In `_run_tool()`, wrap `RepositoryState.snapshot(...)` at line 149 in a `with` block that covers the read-tool return and the write-pipeline call.
- Remove the `asyncio.wait_for(dispatch, timeout)` wrapper; await `asyncio.to_thread(...)` directly.
- Keep `_write_timeout(tool_name)` and pass its value to the op so the subprocess applies the deadline.

### Method
- `dispatch = asyncio.to_thread(pipeline.run, tool_name, lambda: op(state.repo, state), dry_run, self._allow_detached_head, requested_branch=requested_branch, protected_branches=self._protected_branches)`; await it without a timeout.
- The timeout value continues to come from the git MCP server config through `_require_config()` and `_write_timeout()`. The `op` contract stays `Callable[[git.Repo, RepositoryState], str]`: the `git_pull` and `git_push` handlers pass `self._write_timeout(tool_name)` into `format_pull()` / `format_push()` as their `timeout` argument, so the deadline reaches the subprocess without changing the op signature used by the read handlers.

### Details

- Update the comment at lines 157-162: the deadline is enforced inside the subprocess call, not at the async boundary.
- A timeout is reported as `outcome_unknown` through the vocabulary member added by procedure 06; a confirmed non-application is reported as `confirmed-not-applied`.
- `raise ValueError(pipeline_result.rejection_message)` stays, so `dispatch_tool()` still distinguishes a rejection from a successful result.
- Define `WriteOutcomeError` (new), a subclass of `GitServiceError`, in this file with an `outcome: str` attribute, and raise it instead of `ValueError` when `pipeline_result.outcome` is not None. `dispatch_tool()` keeps classifying it as a dispatch error; `scripts/mcp_servers/git/git_server.py` (procedure 05) catches it before the generic `GitServiceError` handler and reads `exc.outcome` for the audit record. This is the only channel available: `DispatchResult` carries `result` and `is_error` only (`scripts/mcp_servers/dedup_gate.py:33`).
- `WriteOutcomeError` stays in this file, not in `scripts/mcp_servers/git/errors.py`: `format_output.py` cannot import this module (the dependency direction is `git_service -> format_output`), and `errors.py` is not a row of the Plan's frozen `Implementation Target Files` table. The formatter never raises it; the pipeline classifies the outcome and this file raises it from `PipelineResult.outcome` (procedure 01).

## Compatibility considerations

- `tests/mcp_servers/git/test_git_service_dispatch.py:867` (`test_slow_pull_raises_timeout`) pins the current thread-based behavior and is replaced by the subprocess timeout cases in procedure 09.
- `tests/mcp_servers/git/test_git_concurrency.py` ordering tests must stay green.
- The `GitServiceError`/`GitPolicyError` exception types and the dispatch table are unchanged.

## Security considerations

- Remote and ref validation (`_authorize_remote()`, `validate_ref_allowlist()`, `validate_protected()`) stays in front of the mutating call; `TestWriteRefAllowlist` cases stay green.

## Rollback considerations

- Revert the commit; the async boundary change is confined to `_run_tool()`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Timeout terminates the process group; no thread continues | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` | Timeout cases pass |
| Handle release on the five paths | `uv run pytest tests/mcp_servers/git/test_git_write_postconditions.py -v` | No leaked `git.Repo` handle |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- A timeout cannot leave an unmanaged worker thread continuing the operation (AC-3).
- Repeated execution does not leak repository handles or file descriptors on success, rejection, dry-run, exception, and timeout (AC-5).

## Out of Scope

- The subprocess call itself (procedure 04).
- The outcome vocabulary member (procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-144426 | 20261126-144426 | WriteOutcomeError (GitServiceError subclass carrying outcome) defined here; _run_tool() uses the context-manager snapshot; asyncio.wait_for removed; raises WriteOutcomeError when pipeline_result.outcome is not None; git_pull/git_push pass timeout=self._write_timeout(...). |
| 2 | Add or update tests per Validation plan | Completed | 20261126-144825 | 20261126-144825 | companion cases are in procedure 09 Companion cases in procedure 09; the six mock dispatch cases were converted to the subprocess path on the test side (scope expansion approved). Companion cases in procedure 09; the six mock dispatch cases were converted to the subprocess path on the test side (scope expansion approved). Post-execution stale-detector note: the pinned case `test_slow_pull_raises_timeout` no longer exists because procedure 09 replaced it with the stub-git timeout cases; the procedure's own Validation plan named that case as one that must change. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-144426 | 20261126-144426 | Static sequence clean. Full suite as recorded on procedure 01 row 3. diff-cover 100%. |
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
- **Requirement ID**: `REQ-003` (cancellable subprocess for pull and push), `REQ-004` (outcome channel to the audit record), `REQ-005` (handle release on every path)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `scripts/mcp_servers/git/git_service.py`