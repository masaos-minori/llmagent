# Duplicate SIGTERM→SIGKILL escalation logic across three locations

## Priority
High

## Summary
Consolidate the SIGTERM→SIGKILL process termination escalation logic currently duplicated in `HttpServerLifecycleManager._terminate_with_timeout`, `ProcessTerminator.terminate_with_timeout`, and `ShutdownCoordinator.shutdown_all` into a single authoritative implementation.

## Background
The SIGTERM→SIGKILL escalation pattern appears in three separate places:

1. `HttpServerLifecycleManager._terminate_with_timeout()` (http_lifecycle.py:132-157): Uses `_do_pgid_terminated()` with pgid-based os.killpg() fallback to proc-level signals.
2. `ProcessTerminator.terminate_with_timeout()` (http_lifecycle_process_terminator.py:125-206): Implements its own SIGTERM→SIGKILL escalation with pgid tracking.
3. `ShutdownCoordinator.shutdown_all()` (http_lifecycle_shutdown_coordinator.py:63-133): Implements its own SIGTERM→SIGKILL escalation with pgid lookup.

Each has slightly different timeout values (RESTART_TERMINATE_TIMEOUT_SEC=3.0s, TERMINATE_TIMEOUT_SEC=5.0s, _SHUTDOWN_TIMEOUT_SEC=30.0s), different poll intervals (0.05s vs 0.1s), and different error handling strategies.

## Problem
Three independent implementations of the same core operation create:

1. **Inconsistent timeouts**: Different methods use different default timeouts (3.0s, 5.0s, 30.0s), leading to unpredictable shutdown behavior depending on which entry point is used.
2. **Divergent error handling**: One uses `os.killpg()` with fallback to `proc.terminate()/proc.kill()`, another checks `proc.poll()` before signaling, another uses `asyncio.get_event_loop().time()` instead of `time.monotonic()`.
3. **Maintenance burden**: Any fix to the escalation logic must be applied in three places; missing one creates inconsistent behavior.
4. **Potential for resource leaks**: If one path fails to terminate a process group while another succeeds, orphaned child processes may remain.

Evidence:
- `http_lifecycle.py:132-157`: `_terminate_with_timeout` — uses `_do_pgid_terminated` with force=True escalation
- `http_lifecycle.py:164-191`: `_do_pgid_terminated` — pgid-based signal sending with fallback
- `http_lifecycle_process_terminator.py:125-206`: `terminate_with_timeout` — own escalation implementation
- `http_lifecycle_shutdown_coordinator.py:63-133`: `shutdown_all` — own escalation with asyncio.get_event_loop().time()

## Reason for Change
Duplicate process termination logic violates DRY and introduces subtle differences in shutdown behavior. A process that exits within 3 seconds under one path may survive until 30 seconds under another, creating operational unpredictability.

## Implementation Intent
Make `ProcessTerminator` the sole authority for SIGTERM→SIGKILL escalation. Have `HttpServerLifecycleManager._terminate_with_timeout` and `ShutdownCoordinator.shutdown_all` delegate to `self._process_terminator.terminate_with_timeout(proc, server_key, timeout)` instead of implementing their own escalation. The timeout parameter should be configurable per-call but share the same underlying escalation mechanism.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle.py`
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle_process_terminator.py`
- `/home/sugimoto/llmagent/scripts/agent/http_lifecycle_shutdown_coordinator.py`

## Required Changes
- Remove SIGTERM→SIGKILL escalation logic from `HttpServerLifecycleManager._terminate_with_timeout` — replace with delegation to `self._process_terminator.terminate_with_timeout`
- Remove SIGTERM→SIGKILL escalation logic from `ShutdownCoordinator.shutdown_all` — replace with delegation to `self._process_terminator.terminate_with_timeout`
- Keep `ProcessTerminator.terminate_with_timeout` as the single source of truth
- Ensure `ProcessTerminator` receives all necessary dependencies (pgid tracking, logger) via constructor injection

## Constraints
- Must preserve existing timeout defaults per-call site (3.0s for restart, 5.0s for startup, 30.0s for full shutdown)
- Must handle the case where pgid is unavailable (fallback to proc-level signals)
- Must not change the public API surface of any class

## Acceptance Criteria
- Only one SIGTERM→SIGKILL escalation implementation exists in the codebase
- All three call sites produce identical termination behavior given the same input
- No regressions in subprocess termination during shutdown
- Timeout defaults are preserved per call site

## Testing Expectations
- Unit test verifying `ProcessTerminator.terminate_with_timeout` handles SIGTERM success
- Unit test verifying `ProcessTerminator.terminate_with_timeout` escalates to SIGKILL on timeout
- Integration test covering shutdown via both `HttpServerLifecycleManager` and `ShutdownCoordinator` produces identical process termination
- Regression test for pgid-unavailable fallback path

## Documentation Impact
Update docstrings for `HttpServerLifecycleManager._terminate_with_timeout` and `ShutdownCoordinator.shutdown_all` to clarify delegation to `ProcessTerminator`.

## Out of Scope
- Refactoring the entire shutdown flow
- Adding new error handling paths
- Changing the SIGTERM→SIGKILL escalation timing algorithm

## Dependencies
N/A: none

## Unresolved Questions
- Should the timeout defaults be centralized in a shared constants module?
- Does `ShutdownCoordinator` have access to `self._process_terminator` when called directly (not via composition)?

## AI Implementation Instruction
Do not remove the SIGTERM→SIGKILL escalation unconditionally — it is essential for preventing orphaned processes. Instead, consolidate into `ProcessTerminator.terminate_with_timeout` and have other classes delegate to it. Preserve backward compatibility: callers calling existing methods should see no behavioral change.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-171806
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_shutdown_coordinator.py
