# Implementation: scripts/agent/http_lifecycle_shutdown_coordinator.py

## Goal

Add SIGINT absorption logic to `ShutdownCoordinator.shutdown_all()` static method — move the `_absorb_sigint_during_shutdown` handler from `HttpServerLifecycleManager.shutdown_all()` into the coordinator so shutdown cleanup lives in one place.

## Scope

- Modify `scripts/agent/http_lifecycle_shutdown_coordinator.py` only.
- Add SIGINT signal handler to `shutdown_all()` static method.
- Move the `_absorb_sigint_during_shutdown` logic from `HttpServerLifecycleManager.shutdown_all()` into the coordinator.

## Assumptions

- The SIGINT handler must be installed before iterating over processes and restored afterward.
- The handler should log a warning instead of propagating the exception.
- The handler must be thread-safe (installed in main thread, called from any thread).

## Design decisions

- Add the SIGINT handler as a static method on `ShutdownCoordinator` (similar to how `_absorb_sigint_during_shutdown` is a static method on `HttpServerLifecycleManager`).
- Install the handler at the start of `shutdown_all()` and restore the previous handler in a `finally` block.
- Use `signal.signal(signal.SIGINT, ...)` to install the handler and `signal.getsignal(signal.SIGINT)` to retrieve the previous handler.

## Alternatives considered

- **Keep SIGINT handling in HttpServerLifecycleManager**: Would preserve the current separation but contradicts the goal of consolidating shutdown logic.
- **Use asyncio signal handlers**: Would work for async code but `shutdown_all()` is a static method that may be called from sync contexts.

## Implementation

### Target file

`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure

1. Add import for `signal` module (verify if already present — it is, imported at line 10).
2. Add a static method `_absorb_sigint_during_shutdown(signum: int, frame: object) -> None` to `ShutdownCoordinator`.
3. In `shutdown_all()`, wrap the process iteration loop with SIGINT handler installation/restoration.

### Method

```python
# Step 2: Add SIGINT handler static method
# After the class definition (around line 55):
@staticmethod
def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
    """Silently absorb SIGINT signals during shutdown_all() to prevent orphaned subprocesses."""
    logger.warning(
        "Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"
    )

# Step 3: Wrap shutdown_all() with SIGINT handler
# Before (lines 56-107):
#     @staticmethod
#     async def shutdown_all(manager: HttpServerLifecycleManager) -> None:
#         """Gracefully shut down every managed server."""
#         procs = manager._http_procs
#         for server_key, proc in list(procs.items()):
#             ...

# After:
#     @staticmethod
#     async def shutdown_all(manager: HttpServerLifecycleManager) -> None:
#         """Gracefully shut down every managed server."""
#         old_sigint: object | None = None
#         try:
#             old_sigint = signal.getsignal(signal.SIGINT)
#         except ValueError:
#             old_sigint = None
#
#         if old_sigint is not None:
#             try:
#                 signal.signal(signal.SIGINT, ShutdownCoordinator._absorb_sigint_during_shutdown)
#             except ValueError:
#                 logger.debug("Lifecycle: could not set SIGINT guard handler")
#
#         try:
#             procs = manager._http_procs
#             for server_key, proc in list(procs.items()):
#                 if proc is None:
#                     continue
#                 pgid = manager._http_pgids.get(server_key) or _get_pgid(proc)
#                 logger.info("Shutting down %s...", server_key)
#                 try:
#                     if pgid is not None:
#                         _kill_pg(pgid)
#                     else:
#                         proc.terminate()
#                 except _TERMINATE_ERRORS as exc:
#                     logger.warning("%s: failed to send SIGTERM: %s", server_key, exc)
#
#                 deadline = asyncio.get_event_loop().time() + _SHUTDOWN_TIMEOUT_SEC
#                 while asyncio.get_event_loop().time() < deadline:
#                     poll_result = proc.poll()
#                     if poll_result is not None:
#                         logger.info(
#                             "%s terminated gracefully with code %d", server_key, poll_result
#                         )
#                         break
#                     await asyncio.sleep(0.05)
#                 else:
#                     logger.warning(
#                         "%s did not stop within %.1fs, sending SIGKILL",
#                         server_key,
#                         _SHUTDOWN_TIMEOUT_SEC,
#                     )
#                     try:
#                         if pgid is not None:
#                             _kill_pg_force(pgid)
#                         else:
#                             proc.kill()
#                     except _KILL_ERRORS as exc:
#                         logger.warning("%s: failed to send SIGKILL: %s", server_key, exc)
#
#                     kill_deadline = asyncio.get_event_loop().time() + _KILL_TIMEOUT_SEC
#                     while asyncio.get_event_loop().time() < kill_deadline:
#                         poll_result = proc.poll()
#                         if poll_result is not None:
#                             logger.info("%s killed with code %d", server_key, poll_result)
#                             break
#                         await asyncio.sleep(0.05)
#                     else:
#                         logger.error("%s could not be killed after SIGKILL", server_key)
#         finally:
#             if old_sigint is not None:
#                 try:
#                     signal.signal(signal.SIGINT, old_sigint)
#                 except ValueError:
#                     pass
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- The SIGINT handler must be installed before iterating over processes and restored afterward.
- The `try/finally` pattern ensures the handler is always restored even if an exception occurs during shutdown.
- Need to handle the case where `signal.getsignal(signal.SIGINT)` raises `ValueError` (e.g., when called from a non-main thread).

## Compatibility considerations

- **No breaking change** for existing callers of `shutdown_all()` — the method signature remains the same.
- The added SIGINT handler will appear in logs but does not change the return value or exception behavior.

## Security considerations

- No new security surface introduced. Adding SIGINT handling does not introduce new attack vectors.
- The handler silently absorbs SIGINT signals, which is intentional to prevent orphaned subprocesses during shutdown.

## Rollback considerations

- Revert the SIGINT handler addition and remove the `try/finally` wrapper around the process iteration loop.
- If the SIGINT handler causes unexpected behavior, investigate further before reverting.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Shutdown behavior | Integration test | Manual verification + existing tests | SIGINT absorbed during shutdown_all() |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] SIGINT handler static method added to `ShutdownCoordinator`.
- [ ] `shutdown_all()` wraps process iteration with SIGINT handler installation/restoration.
- [ ] Handler is installed before iterating and restored in `finally` block.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/http_lifecycle.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_terminator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_snapshot.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_health_checker.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/factory.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add SIGINT handler static method | Pending | — | — | |
| 2 | Wrap shutdown_all() with SIGINT handler | Pending | — | — | |
| 3 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005035
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
