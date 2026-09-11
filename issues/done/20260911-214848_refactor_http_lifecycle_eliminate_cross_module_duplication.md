# Refactor http_lifecycle: eliminate cross-module duplication and delegate to existing concern-specific modules

## Priority
Medium

## Summary
Consolidate duplicated lifecycle logic across `scripts/agent/http_lifecycle*.py` modules so that `HttpServerLifecycleManager` delegates exclusively to its six concern-specific components, removing inline implementations that duplicate those modules' responsibilities.

## Background
`HttpServerLifecycleManager` was refactored to delegate to six concern-specific modules (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ProcessSnapshotProvider, ShutdownCoordinator). However, the main class retains its own inline implementations of termination, shutdown, and snapshot logic that duplicate the work of those delegated modules. Additionally, `ProcessInfoSnapshot` carries 22 fields most of which are unused in practice.

## Problem
Six concrete issues identified through cross-file analysis:

1. **`_terminate_with_timeout()` duplicates `ProcessTerminator.terminate_with_timeout()`** — Both implement SIGTERM → SIGKILL escalation with polling. The main class uses `os.killpg()` + `asyncio.sleep()` while ProcessTerminator does the same.

2. **`shutdown_all()` duplicates `ShutdownCoordinator.shutdown_all()`** — Both iterate over `_http_procs`, send SIGTERM/SIGKILL, poll for exit, and clean up resources. The main class's version handles SIGINT absorption; the coordinator's version does not.

3. **`_build_snapshot_dict()` duplicates `ProcessSnapshotProvider.get_snapshot()`** — Both build a dict snapshot from `_http_procs`/`_http_pgids`. The main class hardcodes 7 fields; the provider reads 22 fields from /proc.

4. **`list_processes()` duplicates `ProcessSnapshotProvider.list_processes()`** — Both iterate over `_http_procs` and produce snapshots. The main class produces `ProcessInfoSnapshot`; the provider does the same via `/proc`.

5. **`verify_running()` and `verify_running_async()` have inconsistent semantics** — One checks `proc.poll()` (process existence), the other makes an HTTP request. Callers cannot know which liveness model applies.

6. **`HealthChecker.compute_health_check_timeout()` has a circular import** — Imports `MCPSERVER_HEALTH_TIMEOUT` from `agent.http_lifecycle` at runtime inside the method body.

## Reason for Change
The dual implementation pattern increases maintenance burden: changes to termination/shutdown logic must be applied in two places. The circular import in `HealthChecker` is fragile and will break under certain import orders. `ProcessInfoSnapshot`'s 22-field structure is unmaintainable and unused beyond a handful of fields.

## Implementation Intent
Establish a single delegation path per concern:

1. **Terminate**: Remove `HttpServerLifecycleManager._terminate_with_timeout()` and `_wait_exited()`. Have callers use `self._process_terminator.terminate_with_timeout()` and `self._process_terminator.wait_exited()` instead. Merge the SIGINT absorption logic from `shutdown_all()` into `ShutdownCoordinator.shutdown_all()` so shutdown cleanup lives in one place.

2. **Shutdown**: Remove `HttpServerLifecycleManager.shutdown_all()`'s inline SIGTERM/SIGKILL loop. Delegate entirely to `ShutdownCoordinator.shutdown_all()`. Move the SIGINT guard logic into the coordinator.

3. **Snapshot**: Remove `HttpServerLifecycleManager._build_snapshot_dict()` and `list_processes()`. Delegate to `ProcessSnapshotProvider.get_snapshot()` and `ProcessSnapshotProvider.list_processes()`.

4. **Liveness**: Unify `verify_running()` and `verify_running_async()` into a single method that always performs an HTTP health check. Remove the `proc.poll()` shortcut from `verify_running()`.

5. **Circular import**: Pass `MCPSERVER_HEALTH_TIMEOUT` as a parameter to `HealthChecker.compute_health_check_timeout()` or extract it to a shared constants module.

6. **ProcessInfoSnapshot**: Reduce to the 7 fields currently used by `_build_snapshot_dict()` (`server_key`, `managed`, `pid`, `pgid`, `running`, `last_exit_code`, `stderr_log`). Deprecate unused fields.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` (primary — remove inline implementations)
- `scripts/agent/http_lifecycle_process_terminator.py` (ensure full coverage of termination logic)
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` (add SIGINT absorption)
- `scripts/agent/http_lifecycle_process_snapshot.py` (reduce ProcessInfoSnapshot fields)
- `scripts/agent/http_lifecycle_health_checker.py` (fix circular import)
- `scripts/agent/http_lifecycle_errors.py` (no changes expected)
- `scripts/agent/http_lifecycle_command_validator.py` (no changes expected)
- `scripts/agent/http_lifecycle_stderr_log.py` (no changes expected)

## Required Changes
- Remove `HttpServerLifecycleManager._terminate_with_timeout()` method (~40 lines)
- Remove `HttpServerLifecycleManager._wait_exited()` method (~15 lines)
- Replace calls to `self._terminate_with_timeout()` with `self._process_terminator.terminate_with_timeout()` in `start()`, `_create_and_validate_proc()`, `_health_poll_until_ready()`, and `restart()`
- Remove `HttpServerLifecycleManager.shutdown_all()` method (~45 lines)
- Add SIGINT absorption logic to `ShutdownCoordinator.shutdown_all()`
- Replace `shutdown_all()` callers with `ShutdownCoordinator.shutdown_all()`
- Remove `HttpServerLifecycleManager._build_snapshot_dict()` method (~18 lines)
- Remove `HttpServerLifecycleManager.list_processes()` method (~7 lines)
- Replace `get_process_snapshot()` caller with `ProcessSnapshotProvider.get_snapshot()`
- Replace `list_processes()` callers with `ProcessSnapshotProvider.list_processes()`
- Unify `verify_running()` and `verify_running_async()` — keep HTTP check semantics, remove `proc.poll()` shortcut
- Fix `HealthChecker.compute_health_check_timeout()` circular import — pass timeout constant as parameter
- Reduce `ProcessInfoSnapshot` dataclass to 7 fields: `server_key`, `managed`, `pid`, `pgid`, `running`, `last_exit_code`, `stderr_log`
- Update all `ProcessInfoSnapshot` construction sites to match reduced field set

## Constraints
- Do not change the public API contract: `start()`, `restart()`, `verify_running()`, `verify_running_async()`, `get_process_info()`, `get_process_snapshot()`, `list_processes()` signatures must remain compatible
- `ConfigReloadOutcome`-style reporting is not applicable here — focus on subprocess lifecycle correctness
- `StartupFailure` and `HttpStartupError` must retain their current semantics
- `ProcessTerminator`, `ShutdownCoordinator`, `ProcessSnapshotProvider`, `HealthChecker` public interfaces must not change
- SIGINT absorption during shutdown must continue to prevent orphaned subprocesses
- No behavioral changes to health-check URL construction or timeout computation

## Acceptance Criteria
- [ ] `HttpServerLifecycleManager._terminate_with_timeout()` is removed; all callers use `ProcessTerminator`
- [ ] `HttpServerLifecycleManager._wait_exited()` is removed; all callers use `ProcessTerminator.wait_exited()`
- [ ] `HttpServerLifecycleManager.shutdown_all()` is removed; all callers use `ShutdownCoordinator.shutdown_all()`
- [ ] `HttpServerLifecycleManager._build_snapshot_dict()` is removed; all callers use `ProcessSnapshotProvider`
- [ ] `HttpServerLifecycleManager.list_processes()` is removed; all callers use `ProcessSnapshotProvider.list_processes()`
- [ ] `verify_running()` and `verify_running_async()` share consistent HTTP health-check semantics
- [ ] `HealthChecker.compute_health_check_timeout()` has no circular import
- [ ] `ProcessInfoSnapshot` has exactly 7 fields matching the original `_build_snapshot_dict()` output
- [ ] Existing tests pass without modification
- [ ] No regression in subprocess start/restart/shutdown behavior

## Testing Expectations
- Run existing unit tests for `HttpServerLifecycleManager` and ensure they pass
- Verify termination behavior (SIGTERM → SIGKILL escalation) works identically after delegation
- Verify shutdown behavior including SIGINT absorption after moving logic to `ShutdownCoordinator`
- Verify snapshot output matches original `_build_snapshot_dict()` format for backward compatibility
- Type check all modified files
- Lint check all modified files

## Documentation Impact
Update module docstrings in `http_lifecycle.py` to reflect that the manager now fully delegates to its six components. Update `ProcessInfoSnapshot` docstring to document the reduced field set. No user-facing documentation changes required.

## Out of Scope
- Adding new lifecycle operations (e.g., graceful restart with zero-downtime)
- Changing the MCP server command allowlist
- Modifying stderr log rotation thresholds
- Adding process monitoring metrics or alerting
- Refactoring `McpServerConfig` or `StartupFailure` structures
- Adding support for non-process-based MCP servers (WebSocket, stdio)

## Dependencies
N/A: none

## Unresolved Questions
- Are there external callers outside this repository that depend on `verify_running()` returning `True` based solely on `proc.poll()`? If so, unifying to HTTP-only would be a breaking change requiring deprecation.
- Should `ProcessInfoSnapshot` retain the old fields as deprecated properties for backward compatibility, or should consumers migrate immediately?
- Is `SHUTDOWN_TIMEOUT_SEC = 30.0` in `ShutdownCoordinator` appropriate for production use, or should it be configurable like `TERMINATE_TIMEOUT_SEC`?

## AI Implementation Instruction
Do not rewrite unrelated files. Keep changes minimal and focused on eliminating cross-module duplication. After each removal, verify that the delegated module provides equivalent functionality. Preserve all public method signatures. Before removing any inline method, confirm no external callers exist. Use the delegated modules consistently — do not introduce hybrid patterns where both the inline and delegated versions coexist. After changes, run existing tests and type check.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260911-214848
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_process_snapshot.py, scripts/agent/http_lifecycle_health_checker.py
