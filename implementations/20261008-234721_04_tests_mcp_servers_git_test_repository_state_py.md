# Implementation Procedure: Async tests for git-mcp event-loop offload, lock type, and timeout

## Goal

Add tests that verify the REQ-001 event-loop offload, the REQ-002 lock type, and the REQ-003 timeout behaviour for the git-mcp write path (`REQ-001` + `REQ-003`).

## Scope

Modify `tests/mcp_servers/git/test_repository_state.py` only.

- In-Scope: add an async test with a slow fake Git operation verifying the write path is dispatched via `asyncio.to_thread()` and `/health` stays responsive (REQ-001); a unit test asserting `_get_repo_lock()` returns an `asyncio.Lock` (REQ-002); an integration test with a slow fake push/pull asserting a `TimeoutError` past the configured timeout (REQ-003).
- Out-of-Scope: modifying `git_service.py`, `repository_state.py`, `format_output.py` (production code); docs.

## Assumptions

- Existing tests use pytest with async support (check whether `pytest-asyncio` / `anyio` is configured in `pyproject.toml`/`conftest.py` before adding `@pytest.mark.asyncio` tests).
- Tests can inject a slow fake Git operation by monkeypatching the GitPython call used by `format_pull`/`format_push` (`state._repo.git.pull/push`) or by stubbing the `op` lambda passed into `WriteProtectionPipeline.run()`.

## Design decisions

- **Slow fake op + event-loop liveness probe.** Register a fake op that sleeps longer than the test's liveness window; concurrently poll a flag set by the event loop (or assert a `/health`-style coroutine completes) to prove the loop was not blocked.
- **Lock-type assertion.** Call `_get_repo_lock()` (or drive a write pipeline) and assert the returned object is an `asyncio.Lock` instance.
- **Timeout assertion.** Drive `format_pull`/`format_push` (or the awaited `to_thread` boundary) with a small timeout against a slow fake op and assert `asyncio.TimeoutError` / `TimeoutError`.

## Alternatives considered

- **Wall-clock timing assertions.** Rejected as flaky; prefer a controllable fake op plus a deterministic liveness probe.

## Implementation

### Target file

`tests/mcp_servers/git/test_repository_state.py`

### Procedure

1. Inspect the existing test module and its fixtures/helpers; match the established style and async configuration.
2. **REQ-001 test:** an async test that runs a slow fake write op and asserts the event loop remains responsive (e.g. a concurrent `asyncio.sleep`/health coroutine completes within the window while the slow op is in flight).
3. **REQ-002 test:** an async/unit test asserting `_get_repo_lock()` returns an `asyncio.Lock` instance.
4. **REQ-003 test:** an async test driving a slow fake push/pull with a small configured timeout and asserting a `TimeoutError` is raised when it is exceeded.
5. Ensure each test uses a deterministic fake (no real network) so it is hermetic and non-flaky.

### Method

New async test functions + fakes/monkeypatches; no changes to production code.

### Details

- **Cross-file dependency:** the REQ-001 test asserts `asyncio.to_thread()` dispatch, which lives in `git_service.py`; the REQ-002 test asserts the `asyncio.Lock` type, which lives in `repository_state.py`. These tests validate changes made in other files — do not add production modification instructions here.
- **Needs confirmation (Plan Gap):** because `asyncio.Lock` cannot be acquired from a worker thread, the REQ-001 test's liveness assertion depends on how the implementer resolves the lock-acquisition-thread question in `REQ-002`. If the implementer keeps `threading.Lock` for in-thread serialization, the lock-type test must assert accordingly. Coordinate with the production procedures.
- Keep timeouts in tests generous enough to avoid CI flakiness but small enough to fail fast.

## Compatibility considerations

- New tests only; existing tests must keep passing. Match the repo's async test runner configuration.

## Security considerations

- Tests use fakes/stubs only; no real repositories or network access.

## Rollback considerations

- Remove the added test functions.

## Validation plan

- Run the new tests with the repo's pytest configuration; confirm they pass.
- Run the full git-mcp test suite to confirm no regressions.
- ruff and mypy pass on the test file.

## Completion criteria

- REQ-001, REQ-002, and REQ-003 tests exist, are hermetic, and pass; the existing suite still passes; ruff/mypy clean.

## Out of scope

- Production code (`git_service.py`, `repository_state.py`, `format_output.py`) and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add async tests (REQ-001/002/003) | Pending | — | — | Match existing async test config |
| 2 | Add/update tests per Validation plan | Pending | — | — | Hermetic fakes only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest, ruff, mypy |
| 4 | Update documentation, if in scope | Pending | — | — | N/A: out of scope for this file |

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
- **Requirement ID**: `REQ-001` (event-loop offload), `REQ-003` (timeout)
- **Source issue**: `issues/done/20261007-154016_gitasync01_move-git-mcp-blocking-operations-off-the-event-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160546_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-234721
- **Related target files**: `tests/mcp_servers/git/test_repository_state.py`
