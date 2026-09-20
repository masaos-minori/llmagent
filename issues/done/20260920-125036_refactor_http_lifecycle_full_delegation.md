# Refactor HttpServerLifecycleManager to fully delegate responsibilities to concern-specific modules

## Priority
Medium

## Summary
Reduce HttpServerLifecycleManager's responsibilities by delegating remaining inline logic to its six concern-specific modules, resolving circular imports, and fixing private attribute access violations.

## Background
HttpServerLifecycleManager was previously extracted from lifecycle.py and partially refactored into six concern-specific modules (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ShutdownCoordinator). However, the refactoring is incomplete: HttpServerLifecycleManager still owns significant responsibilities that should belong to these modules, and there are circular import issues between modules.

## Problem
HttpServerLifecycleManager violates the Single Responsibility Principle despite being described as a "thin composition facade." It retains responsibilities that should be delegated to its injected components:
- Inconsistent constant defaults across modules: `_TERMINATE_POLL_INTERVAL_SEC` (0.05 in http_lifecycle.py vs 0.1 in ProcessTerminator), `HEALTH_POLL_INTERVAL_SEC` (0.5 in http_lifecycle.py vs 1.0 in HealthChecker's `_STARTUP_INTERVAL`). These serve different purposes but create configuration drift risk when developers assume they align.
- Pure delegation wrapper methods that add no value (`_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`)
- Cross-module dependency violation: `HealthChecker.compute_health_check_timeout` imports `MCPSERVER_HEALTH_TIMEOUT` from `http_lifecycle.py`, creating a circular dependency
- `ShutdownCoordinator.shutdown_all` accesses private attributes (`manager._http_procs`, `manager._stderr_files`) directly
- `verify_running_async` mixes manager-level rate-limiting cache with HealthChecker invocation, blurring responsibility boundaries

## Reason for Change
Incomplete refactoring reduces maintainability and testability. Each concern-specific module should own its domain completely. Inconsistent constant defaults across modules create configuration drift risk. Circular imports make modules harder to reason about independently. Private attribute access couples ShutdownCoordinator to HttpServerLifecycleManager's internal state layout.

## Implementation Intent
1. Resolve circular import: move `MCPSERVER_HEALTH_TIMEOUT` out of http_lifecycle.py to HealthChecker or dedicated config module
2. Fix `HealthChecker.compute_health_check_timeout` to not import from http_lifecycle.py — accept timeout as a parameter or use its own constant
3. Remove pure delegation wrapper methods only: `_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`
4. Add public cleanup method to ShutdownCoordinator so it doesn't need private attribute access
5. Clarify responsibility boundary in `verify_running_async`: manager-level rate-limiting cache is separate from HealthChecker invocation — document this separation rather than merging them
6. Do NOT remove `_read_stderr_tail` or `_wait_exited` — they contain custom logic (seek/read/decode and proc.poll() polling) beyond simple delegation
7. Do NOT remove `shutil` import from http_lifecycle.py — confirmed needed for test patching (see noqa comment on line 23)

## Target Files or Areas
- `scripts/agent/http_lifecycle.py`
- `scripts/agent/http_lifecycle_command_validator.py`
- `scripts/agent/http_lifecycle_errors.py`
- `scripts/agent/http_lifecycle_health_checker.py`
- `scripts/agent/http_lifecycle_process_terminator.py`
- `scripts/agent/http_lifecycle_shutdown_coordinator.py`
- `scripts/agent/http_lifecycle_stderr_log_manager.py`

## Required Changes
- Move `MCPSERVER_HEALTH_TIMEOUT` constant out of http_lifecycle.py (to HealthChecker or a dedicated config module)
- Remove `from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT` import from HealthChecker
- Remove pure delegation wrapper methods only: `_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`
- Replace `_open_stderr_log` call sites with direct `self._stderr_log_manager.open_log()` calls
- Replace `_terminate_with_timeout` call sites with direct `ProcessTerminator.terminate_with_timeout()` calls
- Replace `_close_and_forget_stderr` call sites with direct stderr file handle operations
- Add `cleanup_server_key(server_key)` public method to ShutdownCoordinator for process tracking cleanup
- Document responsibility boundary in `verify_running_async`: manager-level rate-limiting cache is separate from HealthChecker invocation
- Keep `_read_stderr_tail` and `_wait_exited` — they contain custom logic beyond simple delegation
- Keep `shutil` import in http_lifecycle.py — confirmed needed for test patching
- Update module docstring to reflect final delegation design

## Constraints
- Preserve all public API behavior of HttpServerLifecycleManager (start, restart, shutdown_all, verify_running, verify_running_async, get_process_info, list_processes)
- Do not change error types or exception messages raised by startup failures
- Do not change subprocess creation semantics (start_new_session=True, etc.)
- Do not change health check HTTP endpoint URLs or status code expectations

## Acceptance Criteria
- No circular imports between modules (verified by importing each module independently)
- Pure delegation wrapper methods removed (`_open_stderr_log`, `_terminate_with_timeout`, `_close_and_forget_stderr`)
- Custom methods preserved (`_read_stderr_tail`, `_wait_exited`) — they perform non-trivial logic
- ShutdownCoordinator does not access private attributes of HttpServerLifecycleManager
- HealthChecker does not import from http_lifecycle.py
- `shutil` import retained in http_lifecycle.py for test patching
- All existing unit tests pass
- Type checking passes (mypy or equivalent)

## Testing Expectations
- Run existing unit tests for HttpServerLifecycleManager
- Run existing unit tests for all six concern-specific modules
- Run integration tests that exercise start/restart/shutdown flows
- Run type checker (mypy) on all modified files
- Verify no regressions in error handling paths (startup failure scenarios)

## Documentation Impact
- Update module docstring of http_lifecycle.py to reflect final delegation design
- Update docstrings of removed wrapper methods (they will be deleted)
- Document responsibility boundaries in each concern-specific module's docstring if they changed

## Out of Scope
- Adding new features or capabilities
- Changing the concern-specific module interfaces (their public APIs remain unchanged)
- Modifying McpServerConfig schema
- Changing subprocess launch arguments or security model
- Adding new error types or changing existing error semantics
- Performance optimization beyond what the refactoring naturally achieves

## Dependencies
- N/A: none

## Unresolved Questions
- Should `MCPSERVER_HEALTH_TIMEOUT` live in HealthChecker or a separate config/constants module?
- Are there any callers outside the agent package that depend on the current private attribute layout accessed by ShutdownCoordinator?

## AI Implementation Instruction
Keep changes minimal: only refactor existing code, do not add new functionality. Preserve all public API behavior exactly. After each change, run the full test suite to confirm no regressions. If any test fails, revert the change and report the failure. Do not modify McpServerConfig or subprocess launch semantics. Stop and report if you find that removing a wrapper method breaks a caller that depends on its specific behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-125036
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_command_validator.py, scripts/agent/http_lifecycle_errors.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_stderr_log_manager.py
