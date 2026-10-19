## Goal
- Terminate all managed MCP servers concurrently so shutdown time is bounded by one termination timeout and every server is signalled before any wait begins (`REQ-002` (concurrent termination), `REQ-003` (signal every server first), `REQ-004` (keep the SIGKILL backstop and failure handling)).

## Scope
- In scope: `scripts/agent/http_lifecycle_shutdown_coordinator.py` only.
- Out of scope: the process terminator, the lifecycle manager, the callers, tests, and docs (each has its own procedure document).

## Assumptions
- Each `terminate_with_timeout` call sends SIGTERM in its first synchronous segment, before its first `await`, so starting all calls as tasks signals every server on the first event-loop pass.
- The process terminator procedure (reap in the wait loop) is applied, so a well-behaved server returns immediately and the bound is reached only by a server that ignores SIGTERM.

## Design decisions
- Split `shutdown_all` into a synchronous collection pass (pop the tracking entry, skip an already exited process, remember the rest) and one concurrent termination pass over the collected processes.
- Keep the per-server outcome handling exactly as today: success removes the tracking entry through `cleanup_server_key`, an `OSError` or `TimeoutError` keeps it for manual cleanup and logs the same error line.

## Alternatives considered
- Keep the sequential loop and only lower `_SHUTDOWN_TIMEOUT_SEC`: rejected, because total time still grows with the server count and an interruption still leaves later servers unsignalled.
- Add a separate "send SIGTERM to all" method on the terminator: rejected here, because it changes the terminator's public surface; the first synchronous segment of each task already provides signal-before-wait.

## Implementation
### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure
1. Add `import asyncio` (new) to the module.
2. In `ShutdownCoordinator.shutdown_all`, first iterate `manager.iter_processes()` once and, for each process, keep the existing pop-before-terminate step (`remove_process_entry`) and the already-exited branch (`cleanup_server_key`, then continue); collect the remaining `(server_key, proc)` pairs.
3. Add a private coroutine `_terminate_one` (new) that holds the existing per-server body: log `Shutting down {key}...`, build `terminate_kwargs` from `_SHUTDOWN_TIMEOUT_SEC` and `fields`, await `terminator.terminate_with_timeout`, then `cleanup_server_key` on success, and log the retained-entry error for `OSError` or `TimeoutError`.
4. Await all collected `_terminate_one` (new) coroutines together with `asyncio.gather`, then call `manager.clear_all_health_checks()` exactly as before; keep the SIGINT guard and its restore in the existing `try/finally`.
### Method
- `_terminate_one` (new) catches only `OSError` and `TimeoutError` like the current loop, so one server's failure does not stop the others; `asyncio.gather` is awaited without `return_exceptions` only because the coroutine already handles those two errors, and any other exception still propagates as it does today.
- Keep `_SHUTDOWN_TIMEOUT_SEC` at 30 seconds (Plan Assumption); keep `_get_pgid` and `_absorb_sigint_during_shutdown` untouched.
### Details
- Evidence: `shutdown_all` awaits `terminate_with_timeout` per server inside a `for` loop; in the observed run only the first two servers were reached.
- Cancellation: tasks that already started have signalled their servers; this document does not add escalation after a cancellation.

## Compatibility considerations
- Public behavior of `shutdown_all` is unchanged for a single server. For several servers the log order of `Shutting down` and `exited` lines may interleave; no code or test depends on it (checked by the coordinator tests).

## Security considerations
- N/A: no new input or signal target.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py tests/agent/test_http_lifecycle_integration.py tests/agent/test_resource_shutdown_coordinator.py -q`
- `uv run ruff format` and `uv run ruff check` on the file, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, and `uv run bandit scripts/agent/http_lifecycle_shutdown_coordinator.py` per `rules/toolchain.md`.

## Completion criteria
- With several servers, total `shutdown_all` time is bounded by one timeout; a stuck server does not delay the others.
- Every collected server receives its termination call before the first wait completes, and a failure on one server keeps only that server's tracking entry.
- Cyclomatic complexity of `shutdown_all` does not increase.

## Out of Scope
- Modifying any file other than the target file; changing the terminator, `_SHUTDOWN_TIMEOUT_SEC`, or the SIGINT guard; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Restructure `shutdown_all` into a collection pass and a concurrent termination pass with `_terminate_one` (new) | Completed | 20261019-222219 | 20261019-222219 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) including the lifecycle and resource-shutdown tests | Completed | 20261019-222219 | 20261019-222219 | Stale clean. _terminate_one added; shutdown_all collects then gathers. ruff/mypy/lint-imports/bandit ok; complexity C(12) unchanged; targeted 59 passed; full suite 9584 passed. |

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
- **Requirement ID**: `REQ-002` (concurrent termination), `REQ-003` (signal every server first), `REQ-004` (keep the SIGKILL backstop)
- **Source issue**: issues/done/20261019-215906_mcpshut001_make-mcp-server-shutdown-bounded-and-complete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-220318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-220632
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py