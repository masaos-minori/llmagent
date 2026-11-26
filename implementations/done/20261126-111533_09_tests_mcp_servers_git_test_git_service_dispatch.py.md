## Goal

Prove the timeout behavior of the subprocess write path: a timeout before the write is applied and a timeout near success are both reported through the outcome vocabulary, and no thread continues the operation after the deadline (REQ-003, REQ-006, AC-3).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- `asyncio.to_thread` is retained, so the existing offload assertion in this file (the case that asserts the blocking call does not run on the event-loop thread) stays valid and must keep passing.
- `test_slow_pull_raises_timeout` at line 867 asserts `asyncio.TimeoutError` from `asyncio.wait_for`, which no longer exists after procedure 03; it is replaced, not supplemented, because the mechanism it pins is removed.
- The subprocess is driven through `scripts/mcp_servers/git/format_output.py` (procedure 04); these cases exercise the service dispatch path, so the subprocess call is the one the pipeline's Stage 6 op runs.
- Confirmed by the user on 20261126: the timeout cases use a stub `git` executable created under `tmp_path` and prepended to `PATH`, not a patched `subprocess.run`. The stub blocks until released, so `os.killpg()` is exercised against a real process group and the recorded PID can be checked for termination.

## Design decisions

- Two cases are required by REQ-003: timeout before application (the process is terminated before it writes anything, so the outcome is `outcome_unknown`) and timeout near success (the process applies the change and then blocks, so the outcome is `outcome_unknown` with the repository effect observable). A single timeout case would not distinguish them.
- The assertions read the outcome value, not the message text, so the vocabulary is the contract under test.

## Alternatives considered

- Assert only that a timeout is raised — rejected: AC-3 is about the process group being terminated and no thread continuing, which a raise-only assertion does not check.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure
- Replace `test_slow_pull_raises_timeout` (line 867) with `test_pull_timeout_terminates_process_group` (new) and `test_pull_timeout_near_success_reports_outcome_unknown` (new).
- Add the same two cases for `git_push`.
- Keep the worker-thread offload case unchanged.

### Method
- Run the service against a real temporary repository and a stub `git` executable that blocks until released, so the timeout fires while the process is alive; assert the process group is gone after the timeout (`os.killpg` path) by checking that the stub's recorded PID no longer exists.
- For the near-success case, the stub writes a marker commit and then blocks; assert the outcome is `outcome_unknown` while the repository effect is present.
- Assert no worker thread is still running after the timeout by checking the thread count or by joining the `to_thread` executor.

### Details

- Use `pytest.mark.asyncio` as the existing async cases in this file do.
- Timeout value comes from `GitConfig.pull_timeout` / `push_timeout`, as the current case does (`pull_timeout=0.1`).
- The outcome assertion reads the value from the exception raised by `scripts/mcp_servers/git/git_service.py` (procedure 03).

## Compatibility considerations

- `tests/mcp_servers/git/test_git_concurrency.py` ordering tests must stay green with the subprocess path.
- The existing `_pull_snap()` helper is still used by the offload case; the new cases do not patch `RepositoryState.snapshot`, because the subprocess path needs a real repository.

## Security considerations

- Remote-allowlist and ref-allowlist cases in this file (`TestWriteRefAllowlist`) stay green: validation still runs before the subprocess is started.

## Rollback considerations

- Revert the commit; the replaced test returns to its previous form with the reverted implementation.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Timeout cases on the subprocess path | `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -v` | Process group terminated; outcomes reported per the vocabulary |
| Concurrency ordering unchanged | `uv run pytest tests/mcp_servers/git/test_git_concurrency.py -v` | No change |
| Static sequence | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Changed-line coverage | `uv run diff-cover coverage.xml --compare-branch=master` | >= 90% |

## Completion criteria

- A timeout cannot leave an unmanaged worker thread continuing the operation (AC-3).
- Timeout-before-application and timeout-near-success are distinguished in the test results (REQ-003).

## Out of Scope

- The subprocess implementation itself (`scripts/mcp_servers/git/format_output.py`, procedure 04).
- The resource-close tests (`tests/mcp_servers/git/test_git_write_postconditions.py`, procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|---|
| 1 | Write the timeout cases against the unmodified dispatch path and record which fail | Completed | 20261126-144426 | 20261126-144426 | Phase 1 Phase 1: the six mock dispatch cases recorded as failing on the subprocess path; fixed on the test side by patching subprocess.Popen with a fake process (scope expansion approved). The offload case keeps its thread-identity intent by recording the thread inside communicate(). Phase 1: the six mock dispatch cases recorded as failing on the subprocess path; fixed on the test side by patching subprocess.Popen with a fake process (scope expansion approved). The offload case keeps its thread-identity intent by recording the thread inside communicate(). |
| 2 | Re-run after procedures 03 and 04 land | Completed | 20261126-144825 | 20261126-144825 | Four timeout cases added with a stub git under PATH that delegates every non pull/push call to the real binary. The stub records its process-group pid and the marker landing; the deadline is 1.0s so the marker lands before the deadline - the earlier 0.1s deadline raced under parallel execution (one full-suite failure). 101 passed. Post-execution stale-detector note: `test_slow_pull_raises_timeout` was replaced by this procedure's stub-git timeout cases, so the stale finding is the procedure's own result, not a prerequisite failure. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-144426 | 20261126-144426 | Static sequence clean. Full suite as recorded on procedure 01 row 3. |
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
- **Requirement ID**: `REQ-003` (cancellable subprocess for pull and push), `REQ-006` (postcondition and timeout tests)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `tests/mcp_servers/git/test_git_service_dispatch.py`