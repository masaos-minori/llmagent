# Duplicate SIGINT handler between HttpServerLifecycleManager and ShutdownCoordinator

## Priority
High

## Summary
Eliminate duplicate `_absorb_sigint_during_shutdown` SIGINT handler implementations between `HttpServerLifecycleManager.shutdown_all()` and `ShutdownCoordinator.shutdown_all()` to prevent double-signaling and ensure consistent shutdown behavior.

## Background
Both `HttpServerLifecycleManager` (in `http_lifecycle.py`) and `ShutdownCoordinator` (in `http_lifecycle_shutdown_coordinator.py`) implement their own copy of the `_absorb_sigint_during_shutdown` static method and install it via `signal.signal(signal.SIGINT, ...)` in their respective `shutdown_all()` methods. The two implementations are identical in both code and log message text.

## Problem
When `shutdown_all()` is called, either method may be invoked depending on which entry point the caller uses. If `HttpServerLifecycleManager.shutdown_all()` is called directly, it installs its own SIGINT handler. If `ShutdownCoordinator.shutdown_all(manager)` is called instead, it installs its own handler. The duplication means:

1. **Double-signaling risk**: If both methods are called sequentially (e.g., one calls the other), the second call restores the original handler in its finally block, potentially allowing SIGINT to reach the wrong handler.
2. **Maintenance burden**: Any change to the handler logic must be applied in two places; missing one creates inconsistent behavior.
3. **Identical log messages**: Both emit `"Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"` — indistinguishable in logs, making debugging harder.

Evidence:
- `http_lifecycle.py:529-538`: `HttpServerLifecycleManager._absorb_sigint_during_shutdown`
- `http_lifecycle.py:540-589`: `HttpServerLifecycleManager.shutdown_all()` installs/restores handler
- `http_lifecycle_shutdown_coordinator.py:55-60`: `ShutdownCoordinator._absorb_sigint_during_shutdown`
- `http_lifecycle_shutdown_coordinator.py:63-133`: `ShutdownCoordinator.shutdown_all()` installs/restores handler

## Reason for Change
Duplicate signal handlers violate the DRY principle and introduce subtle race conditions during shutdown. If a user presses Ctrl-C twice while shutdown is in progress, the second signal should be absorbed consistently regardless of which shutdown path was taken. Currently, the behavior depends on which method was called first.

## Implementation Intent
Consolidate the SIGINT handler into a single shared location. Since `ShutdownCoordinator` is already a composition dependency of `HttpServerLifecycleManager`, move the handler installation logic into `ShutdownCoordinator` and have `HttpServerLifecycleManager.shutdown_all()` delegate to it entirely. Alternatively, extract the handler to a module-level function in `http_lifecycle_errors.py` or a new `http_lifecycle_signal_handler.py` module.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle.py`
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle_shutdown_coordinator.py`

## Required Changes
- Remove `_absorb_sigint_during_shutdown` from `HttpServerLifecycleManager`
- Have `HttpServerLifecycleManager.shutdown_all()` delegate to `self._shutdown_coordinator.shutdown_all(self)` instead of implementing its own shutdown loop
- Keep `ShutdownCoordinator.shutdown_all()` as the sole SIGINT handler installer
- Update any callers that invoke `HttpServerLifecycleManager.shutdown_all()` directly to use `ShutdownCoordinator.shutdown_all()` if they need the coordinator's shutdown semantics

## Constraints
- Must preserve existing shutdown behavior: graceful SIGTERM → SIGKILL escalation, stderr log cleanup, process tracking data removal
- Must not change the public API surface of `HttpServerLifecycleManager` — callers should still be able to call `manager.shutdown_all()` without knowing about the coordinator
- Must handle the case where `old_sigint` restoration fails silently (ValueError)

## Acceptance Criteria
- Only one SIGINT handler is installed during any shutdown path
- Both direct `HttpServerLifecycleManager.shutdown_all()` and `ShutdownCoordinator.shutdown_all()` produce identical shutdown behavior
- No regressions in subprocess termination during shutdown
- Log messages distinguish which shutdown path was taken (differentiate in logs)

## Testing Expectations
- Unit test verifying only one SIGINT handler is active during shutdown
- Integration test covering shutdown via both entry points produces identical process termination
- Regression test for SIGINT absorption during active shutdown

## Documentation Impact
Update docstrings for `HttpServerLifecycleManager.shutdown_all()` to clarify delegation to `ShutdownCoordinator`.

## Out of Scope
- Refactoring the entire shutdown flow
- Adding new error handling paths
- Changing the SIGTERM→SIGKILL escalation timing

## Dependencies
N/A: none

## Unresolved Questions
- Are there any callers that rely on `HttpServerLifecycleManager.shutdown_all()` NOT using the coordinator?
- Should the log message include which shutdown path was taken (e.g., "via HttpServerLifecycleManager" vs "via ShutdownCoordinator")?

## AI Implementation Instruction
Do not remove the SIGINT handler unconditionally — it protects against orphaned subprocesses on double-Ctrl-C. Instead, consolidate into a single handler in `ShutdownCoordinator` and have `HttpServerLifecycleManager.shutdown_all()` delegate to it. Preserve backward compatibility: callers calling `manager.shutdown_all()` should see no behavioral change.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-171653
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py
