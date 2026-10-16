## Goal

Add a regression test asserting that when `StartupOrchestrator.run()` raises `StartupInterrupted`, `AgentREPL.run()` emits a non-"Startup failed" non-fatal message and re-raises, and that a genuine failure still prints "Startup failed" (`REQ-002`).

## Scope

One new test in `tests/agent/test_repl.py`, near `TestRunSqliteErrorMessage`. No changes to existing tests.

## Assumptions

- `run()` wraps `await startup.run()` and reports failures through `self._view.write_fatal`; `StartupInterrupted` is a `RuntimeError` subclass raised during startup.
- `run()`'s outer `finally` calls `self._shutdown.close_resources()`, so the test must stub that to avoid WAL-cleanup side effects (as the existing `_run_and_capture_handler` helper does).

## Design decisions

- Patch `agent.repl.StartupOrchestrator` so `MockStartup.return_value.run` raises `StartupInterrupted`, drive `run()`, assert `write_fatal` was not called with a "Startup failed:" message, `write_warning` carried a non-fatal shutdown message, and the exception re-propagates. Add a parallel case with a real failure to lock the "Startup failed:" behavior.

## Alternatives considered

- Raise `StartupInterrupted` from a real MCP starter: rejected — unit-level patching of `StartupOrchestrator.run()` isolates the `run()` branch without spinning up servers. `N/A: patch StartupOrchestrator.run()`.

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure
Append a test class/method that exercises `run()` under `StartupInterrupted` and under a genuine failure.

### Method
1. Reuse `_make_bare_repl()` and the `DbConfig` / `build_db_config` patching pattern from `TestRunSqliteErrorMessage` so `run()` reaches the `startup.run()` call.
2. Set `MockStartup.return_value.run = AsyncMock(side_effect=StartupInterrupted("shutdown requested"))`; stub `repl._shutdown.close_resources = AsyncMock()`.
3. Assert the call re-raises (match on `StartupInterrupted`, or `RuntimeError` since it is a subclass), that `write_fatal` was not called with a message containing "Startup failed:", and that `write_warning` was called once with a non-fatal shutdown message.
4. Add a second case with `side_effect=sqlite3.Error(...)` (or `RuntimeError`) asserting `write_fatal` IS called with "Startup failed:".

### Details
- Import `StartupInterrupted` from `agent.startup` in the test.
- Because `StartupInterrupted` subclasses `RuntimeError`, prefer matching the specific type (or its message) over a generic `pytest.raises(RuntimeError)` so the test does not accidentally pass if the branch is missing.
- The existing `TestRunSqliteErrorMessage` tests catch the re-raised error around `await repl.run()`; follow the same shape.
- This fills the current gap: no existing test covers `AgentREPL.run()`'s `StartupInterrupted` handling (`test_startup_rollback.py` covers `StartupOrchestrator.run()`, a different `run()`).

## Compatibility considerations
Purely additive test; no existing test or production signature changes.

## Security considerations
`N/A: test-only addition`.

## Rollback considerations
`N/A: revert the commit`.

## Validation plan
- `pytest tests/agent/test_repl.py` — new assertions pass; existing `TestRunSqliteErrorMessage` and `TestSigtermHandlerShutdownCoordination` still pass.

## Completion criteria
The new test locks the non-"Startup failed" + re-raise behavior for `StartupInterrupted` and the "Startup failed:" behavior for a real failure, and `test_repl.py` passes.

## Out of scope
Changing startup control flow, rollback, or signal-handling semantics; treating other exceptions as non-fatal.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261016-164911 | 20261016-164911 | changed: tests/agent/test_repl.py (class with 2 tests). red check on HEAD: interrupted test failed (Startup failed was reported), genuine-failure test passed; mypy errors at baseline 46 after switching to patch.object and cast |
| 2 | Add or update tests per Validation plan | Completed | 20261016-164911 | 20261016-164911 | changed: tests/agent/test_repl.py (class with 2 tests). red check on HEAD: interrupted test failed (Startup failed was reported), genuine-failure test passed; mypy errors at baseline 46 after switching to patch.object and cast |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-164911 | 20261016-164911 | changed: tests/agent/test_repl.py (class with 2 tests). red check on HEAD: interrupted test failed (Startup failed was reported), genuine-failure test passed; mypy errors at baseline 46 after switching to patch.object and cast |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261016-164911 | 20261016-164911 | changed: tests/agent/test_repl.py (class with 2 tests). red check on HEAD: interrupted test failed (Startup failed was reported), genuine-failure test passed; mypy errors at baseline 46 after switching to patch.object and cast |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261016-134010_startup002_clarify-startup-status-reporting-for-skipped-checks-and-shutdown-during-startup.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-141320_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-152216
- **Related target files**: `tests/agent/test_repl.py`