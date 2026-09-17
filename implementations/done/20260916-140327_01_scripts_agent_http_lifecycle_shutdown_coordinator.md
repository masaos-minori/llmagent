## Goal

Port `HttpServerLifecycleManager.shutdown_all()`'s cleanup steps into `ShutdownCoordinator.shutdown_all()`, fix its dead `terminator`-parameter override, and switch `HttpServerLifecycleManager.shutdown_all()` to delegate to it — verified against existing assertions.

## Scope

- Port `_http_pgids.pop`, `_stderr_files.pop`+close, `_stderr_log_paths.clear()`, `_last_health_check.clear()` into `ShutdownCoordinator.shutdown_all()`.
- Fix the dead `terminator` parameter override at L85 so a caller-supplied `terminator` is honored.
- Switch `HttpServerLifecycleManager.shutdown_all()` to a thin delegating wrapper calling `self._shutdown_coordinator.shutdown_all(self)`.
- Verify equivalence against `tests/agent/test_http_lifecycle_integration.py`'s existing assertions before switching delegation.

## Assumptions

- The existing `tests/agent/test_http_lifecycle_integration.py` suite asserts on `manager`'s internal state (`_http_pgids`, `_stderr_files`, `_stderr_log_paths`, `_last_health_check`) after `shutdown_all()` runs — this is the equivalence bar REQ-001/REQ-003 must clear.
- `ShutdownCoordinator.shutdown_all()` currently has zero callers anywhere in `scripts/`/`tests/` — only the constructor call at `http_lifecycle.py:90` exists.

## Design decisions

- Move shutdown logic verbatim from the manager into `ShutdownCoordinator` rather than rewriting it — minimizes behavioral drift risk.
- Keep `shutdown_all()` callable on `HttpServerLifecycleManager` and ensure it does not raise after delegation.
- Do not change `HttpServerLifecycleManager.start()` complexity claim — actual measurement shows grade A, complexity 4 (not ">15" as claimed in the Issue).

## Alternatives considered

- Rewriting `ShutdownCoordinator.shutdown_all()` entirely instead of porting verbatim — rejected because it introduces unnecessary behavioral risk for a small scope.
- Adding a new method on `ShutdownCoordinator` instead of modifying `shutdown_all()` — rejected because the goal is to replace the current non-delegated implementation, not add a parallel one.

## Implementation
### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Port `HttpServerLifecycleManager.shutdown_all()`'s cleanup steps into `ShutdownCoordinator.shutdown_all()`:
   - Add `_http_pgids.pop(key, None)` after terminating each process (currently missing).
   - Add `_stderr_files.pop(key, None)` + close the file handle after terminating each process.
   - Add `_stderr_log_paths.clear()` after the per-process loop.
   - Add `_last_health_check.clear()` after the per-process loop.
2. Fix the dead `terminator` parameter override: remove the unconditional overwrite at L85 (`terminator = manager._process_terminator`) so the L76 `or manager._process_terminator` fallback takes effect and a caller-supplied `terminator` is honored.
3. Update the module docstring to describe the now-actually-used responsibility boundary.

### Method

Compare pre-delegation `HttpServerLifecycleManager.shutdown_all()` behavior line-by-line against the ported `ShutdownCoordinator.shutdown_all()`:

1. SIGINT signal handling: both save/restore `old_sigint`; use `ShutdownCoordinator._absorb_sigint_during_shutdown` (already present in the coordinator).
2. Per-process iteration: iterate over `list(manager._http_procs.items())`, skip if `proc is None`, log if `proc.poll() is not None`, then call `terminator.terminate_with_timeout(proc, key, timeout)`.
3. Post-loop cleanup: pop `_http_pgids[key]`, pop `_stderr_files[key]` and close the handle, clear `_stderr_log_paths`, clear `_last_health_check`.
4. Finally block: restore `old_sigint`.

### Details

Current `ShutdownCoordinator.shutdown_all()` (L50-95):
- L76: `terminator = terminator or manager._process_terminator` — sets default.
- L85: `terminator = manager._process_terminator` — **unconditionally overwrites** the above, making the caller-supplied parameter dead code. This is the bug to fix.
- Missing: no `_http_pgids.pop(key, None)` after termination.
- Missing: no `_stderr_files.pop(key, None)` + close after termination.
- Missing: no `_stderr_log_paths.clear()` after the loop.
- Missing: no `_last_health_check.clear()` after the loop.

Required changes:
1. Remove L85: `terminator = manager._process_terminator`.
2. After the per-process `await terminator.terminate_with_timeout(...)` call (L87-89), add:
   ```python
   manager._http_pgids.pop(key, None)
   stderr_fh = manager._stderr_files.pop(key, None)
   if stderr_fh is not None:
       try:
           stderr_fh.close()
       except OSError as close_err:
           logger.warning("Lifecycle: error closing stderr log for %r: %s", key, close_err)
   ```
3. After the per-process loop (before the finally block), add:
   ```python
   manager._stderr_log_paths.clear()
   manager._last_health_check.clear()
   ```

## Compatibility considerations

- `ShutdownCoordinator.shutdown_all()` gains its first real caller via REQ-003's delegation switch. The dead-parameter bug (L85) means the parameter was never actually used — fixing it may affect any future caller that relied on passing a custom terminator (none exists today).
- The added cleanup steps (`_http_pgids.pop`, `_stderr_files.pop`+close, `_stderr_log_paths.clear()`, `_last_health_check.clear()`) are already performed by `HttpServerLifecycleManager.shutdown_all()` — porting them preserves behavioral parity.

## Security considerations

- The SIGINT handler swap (`signal.signal(signal.SIGINT, ...)`) and restore pattern is unchanged — same security posture as the original.
- No new secrets, credentials, or sensitive data exposure.

## Rollback considerations

- If the ported `ShutdownCoordinator.shutdown_all()` fails equivalence validation, revert the coordinator changes and keep the manager's inline implementation until the port is correct.
- The delegation switch in `HttpServerLifecycleManager.shutdown_all()` should only happen after REQ-001 verification passes — rollback is simply reverting the delegation back to the inline implementation.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `http_lifecycle_shutdown_coordinator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` | Cleanup parity with pre-delegation `HttpServerLifecycleManager.shutdown_all()`; `terminator` param honored |
| `http_lifecycle.py` (`shutdown_all` delegation) | Integration (existing regression) | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | All existing shutdown-state assertions still pass |

## Completion criteria

- `ShutdownCoordinator.shutdown_all()` performs the same cleanup as today's `HttpServerLifecycleManager.shutdown_all()`, verified against `tests/agent/test_http_lifecycle_integration.py`'s existing assertions before the delegation switch.
- The `terminator` parameter, when supplied to `ShutdownCoordinator.shutdown_all()`, is actually used.
- `uv run ruff check scripts/agent/http_lifecycle*.py` passes clean.
- `uv run mypy scripts/agent/http_lifecycle*.py` passes (no new regressions vs pre-existing errors).

## Out of scope

- Switching `HttpServerLifecycleManager.shutdown_all()` to delegate — handled in the next procedure document.
- Moving `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` exclusively — handled in the next procedure document.
- Renaming `ProcessInfoSnapshot` to `RawProcessSnapshot` — handled in a separate procedure document.
- Delegating `verify_running_async()` to `HealthChecker` — handled in a separate procedure document.
- Splitting `_cleanup_server_resources()` — handled in a separate procedure document.
- Deleting `ProcessTerminator.terminate()` — handled in a separate procedure document.
- Adding unit tests for this file — handled in the next procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260915-102515_refactor_http_lifecycle_module_split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-140327_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-140327
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
