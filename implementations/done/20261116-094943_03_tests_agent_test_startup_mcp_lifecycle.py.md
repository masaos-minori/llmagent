## Goal

Add one test through `McpServerStarter.start_servers` showing that the retry after an unconfirmed first failure ends in a startup failure and not in a recorded spawn (`REQ-004`: starter-level test).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test in `TestStartupOrchestratorStartServers` in `tests/agent/test_startup_mcp_lifecycle.py`.
- Out of scope: any change to `McpServerStarter`, the retry helper, or the existing tests in that file.

## Assumptions

- Execute after document `01` of this Plan (the manager fix) and after the Plan `startrev002` procedures: the test is written against the final retry shape (first attempt inline, one delayed helper attempt). Plan overlap judgment: `tests/agent/test_startup_mcp_lifecycle.py` is also a target of Plan `startrev002`; both only add tests in different test classes, so they are compatible and sequenced 002 first.
- `_make_startup` builds a `StartupOrchestrator` with `ctx.services_required.lifecycle` as an `AsyncMock`, and `_ServerLifecycleRouter.start_http_subprocess` is `await self._http_mgr.start(...)` followed by `self._http_mgr._http_procs.get(server_key)` (re-read in Step 3a); the test can reproduce that two-line shape over a real `HttpServerLifecycleManager`.
- The test runs with a patched `RETRY_DELAY_SEC` of a small value so it does not sleep for the production delay.

## Design decisions

- Use a real `HttpServerLifecycleManager` (patched launcher and a patched terminator returning `EXIT_UNCONFIRMED`) behind a `start_http_subprocess` side-effect wrapper that mirrors the router's two lines, so the manager's reuse branch is the unit under test.
- Assert on the outcome (startup error, nothing appended to the spawned list), not on internal counters.

## Alternatives considered

N/A: the Plan fixes the approach (one starter-level test over a real manager).

## Implementation
### Target file
`tests/agent/test_startup_mcp_lifecycle.py`

### Procedure
1. In `TestStartupOrchestratorStartServers`, add a test that builds the orchestrator with `_make_startup({"web": cfg})` and replaces `lifecycle.start_http_subprocess` with an async wrapper that awaits a real manager's `start(key, cfg, shutdown_event=...)` and returns `mgr._http_procs.get(key)`.
2. Arrange the manager so the first `start` fails with an unconfirmed exit: a live fake process (`poll()` returns `None`), a patched launcher that returns it and registers it in `_http_procs` and `_http_pgids`, a health poll that times out or a patched `_health_poll_until_ready` that calls `_raise_startup_failure_unconfirmed`, and a terminator `AsyncMock` that always returns `TerminationOutcome.EXIT_UNCONFIRMED`.
3. Run `startup._start_servers()` and assert it raises the `[fatal]`-prefixed startup error (`HttpStartupError` type preserved), that the spawned-process list is empty, and that the fake process is still tracked by the manager.
4. Confirm the test fails on the code before document `01` (the second `start` returns the process and the list is not empty).

### Method
- Place the test after `test_genuine_runtime_error_still_retries`; reuse `_make_startup` and `_http_subprocess_cfg`; patch `agent.startup_mcp_starter.RETRY_DELAY_SEC` to a small value.
- Comments in English; no new import beyond `HttpServerLifecycleManager`, `TerminationOutcome` and `HttpStartupError` from `agent.http_lifecycle` and its errors module (check the file's existing imports first).

### Details
- Do not use a real child process here; the manager-level real-child pattern belongs to the integration test file (document `01` companion).

## Compatibility considerations

N/A: tests only; existing tests in the file are unchanged.

## Security considerations

N/A: no production code, no secrets; the fake process is never signaled for real.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup_rollback.py -q` passes.
- The new test fails on the pre-change manager and passes after document `01`.
- `uv run ruff check tests/agent/test_startup_mcp_lifecycle.py` and `uv run ruff format --check` on it; the file is not in the mypy `files` scope.

## Completion criteria

- The new test exists, passes with the manager fix and fails without it (`REQ-004`, AC-4); all existing tests in the file keep passing.

## Out of Scope

- Production code changes, the manager-level tests, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the starter-level unconfirmed-failure test and confirm it fails on the pre-fix manager | Done | 20261116 | 20261116 | Test added after `test_genuine_runtime_error_still_retries`; confirmed it fails on the pre-fix manager (removed `_failed_start_procs` retention → `DID NOT RAISE`) then restored via `git checkout`. |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the test file | Done | 20261116 | 20261116 | pytest 35 passed (test file + rollback); ruff check/format clean; full `pre-commit run --all-files` passes including mock-patch-targets and check-compat-shims. |

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
- **Requirement ID**: `REQ-004` (starter-level test)
- **Source issue**: issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220300_startrev003_retry-reuses-unconfirmed-process.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-094943
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`
