## Goal

Prove the timeout behavior of the subprocess write path: a timeout before the write is applied and a timeout near success are both reported through the outcome vocabulary, and no thread continues the operation after the deadline (REQ-003, REQ-006, AC-3).

## Scope
**Release unit**: outcome-vocabulary-and-timeout

## Assumptions

- `asyncio.to_thread` is retained, so the existing offload assertion in this file (the case that asserts the blocking call does not run on the event-loop thread) stays valid and must keep passing.
- `test_slow_pull_raises_timeout` at line 867 asserts `asyncio.TimeoutError` from `asyncio.wait_for`, which no longer exists after procedure 03; it is replaced, not supplemented, because the mechanism it pins is removed.
- The subprocess is driven through `scripts/mcp_servers/git/format_output.py` (procedure 04); these cases exercise the service dispatch path, so the subprocess call is the one the pipeline's Stage 6 op runs.
- Needs confirmation (non-blocking): the timeout cases need a way to make the `git` CLI block. The plan's default is a stub executable on `PATH` or a patched `subprocess.run`; the choice does not change the assertions.

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
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the timeout cases against the unmodified dispatch path and record which fail | Pending | — | — | Phase 1 |
| 2 | Re-run after procedures 03 and 04 land | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (cancellable subprocess for pull and push), `REQ-006` (postcondition and timeout tests)
- **Source issue**: issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-004921_mcpai008_git-postcondition-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-111533
- **Related target files**: `tests/mcp_servers/git/test_git_service_dispatch.py`
