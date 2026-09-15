# Refactor scripts/agent/http_lifecycle.py into smaller, testable units

## Priority
Medium

## Summary
Split `scripts/agent/http_lifecycle.py` (532 lines) into focused modules matching its declared six-concern architecture. Eliminate cross-cutting duplication between `HttpServerLifecycleManager`, `ShutdownCoordinator`, and `ProcessSnapshotProvider`. Reduce cyclomatic complexity and improve test isolation.

## Background
The module was extracted from `lifecycle.py` and partially refactored into six concern-specific sub-modules (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ProcessSnapshotProvider, ShutdownCoordinator). However, the main `HttpServerLifecycleManager` class retains ~280 lines of control flow that should have been delegated to those sub-modules. The docstring at line 8 explicitly declares this composition intent but the implementation does not match.

## Problem
The file violates Single Responsibility Principle at multiple levels:

1. **Cross-module duplication**: `shutdown_all()` exists in both `HttpServerLifecycleManager` (line 483) and `ShutdownCoordinator.shutdown_all()` (line 50) — identical SIGINT guard + process iteration logic. `_absorb_sigint_during_shutdown` is similarly duplicated.

2. **Process snapshot responsibility leak**: `_build_snapshot()` (line 188) constructs `ProcessInfoSnapshot` directly instead of delegating to `ProcessSnapshotProvider.get_info()`. This means snapshot construction logic lives in two places simultaneously.

3. **Health check verification duplication**: `verify_running_async()` (line 157) performs HTTP `/health` polling inline instead of using `HealthChecker.verify_running_async()`.

4. **Resource cleanup mixing**: `_cleanup_server_resources()` (line 178) handles both stderr log reading AND health check timestamp clearing — two unrelated concerns.

5. **ProcessTerminator internal duplication**: `terminate()` and `terminate_with_timeout()` share ~40 lines of SIGTERM→SIGKILL escalation logic; `terminate_with_timeout()` adds pgid fallback handling but both methods repeat the same `os.killpg()` → poll loop → SIGKILL escalation pattern.

6. **ProcessSnapshotProvider over-fetching**: Reads ALL fields from `/proc/[pid]` regardless of caller need (20+ fields per snapshot), many of which are never used by any consumer.

7. **Multiple `# noqa` suppressions**: Lines 23, 25, 291 carry security/type suppression comments that are difficult to justify without deeper review.

## Reason for Change
- `HttpServerLifecycleManager.start()` has cyclomatic complexity exceeding 15 (nested loops, conditional branches per section, validator try/catch blocks, outcome classification)
- Two independent shutdown implementations cause maintenance burden and risk of divergence
- Snapshot construction in two places means changes must be applied twice
- The declared six-module architecture is incomplete — several concerns remain un-delegated
- No unit tests exercise `_interruptible_poll_sleep`, `_create_and_validate_proc`, or `_health_poll_until_ready` independently
- ProcessTerminator's dual public methods suggest the class was extended incrementally without a clean design

## Implementation Intent
Extract four concerns into separate modules/functions:

1. **Unified shutdown**: Remove `HttpServerLifecycleManager.shutdown_all()` entirely. Make `ShutdownCoordinator.shutdown_all()` the sole entry point. Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` as a static method only. Delete the duplicate from `HttpServerLifecycleManager`.

2. **Snapshot delegation**: Replace `_build_snapshot()` body with a call to `ProcessSnapshotProvider.get_info(server_key, proc, pgid)`. Keep `_build_snapshot()` as a thin wrapper for backward compatibility. Update `get_process_info()` and `get_process_snapshot()` to use the provider directly.

3. **Health check delegation**: Replace `verify_running_async()` body with a call to `HealthChecker.verify_running_async()`. Keep the rate-limiting wrapper logic (10-second interval) but delegate the actual HTTP request.

4. **Cleanup separation**: Split `_cleanup_server_resources()` into two methods: `_read_stderr_for_cleanup()` (returns stderr content) and `_clear_server_tracking_data()` (removes health check timestamps, stderr file handles, paths). Call them separately where needed.

5. **ProcessTerminator consolidation**: Merge `terminate()` and `terminate_with_timeout()` into a single `terminate_with_timeout()` method. The `terminate()` method's signature difference (no timeout parameter) can be handled by making timeout optional with a default value.

6. **ProcessSnapshotProvider selective fetching**: Add a `fields` parameter to `from_proc_pid()` and `get_info()` so callers can request only needed fields. Default behavior remains full fetch for backward compatibility.

Keep `HttpServerLifecycleManager` as the orchestrator but reduce it to < 150 lines by delegating to the six sub-modules. Keep `StartupFailure`, `HttpStartupError`, `ConfigReloadOutcome`, and `ConfigReloadValidationError` where they are.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` — primary refactor target
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` — consolidate shutdown logic here
- `scripts/agent/http_lifecycle_process_terminator.py` — merge terminate methods
- `scripts/agent/http_lifecycle_health_checker.py` — add rate-limited verify wrapper
- `scripts/agent/http_lifecycle_process_snapshot.py` — add selective field fetching
- `scripts/agent/http_lifecycle_stderr_log_manager.py` — no changes needed (already clean)
- `scripts/agent/http_lifecycle_command_validator.py` — no changes needed (already clean)
- `scripts/agent/http_lifecycle_errors.py` — no changes needed (already clean)
- `tests/agent/` — existing tests must still pass after refactor

## Required Changes
- Remove `HttpServerLifecycleManager.shutdown_all()` — delegate to `ShutdownCoordinator`
- Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` only
- Replace `_build_snapshot()` body with `ProcessSnapshotProvider.get_info()` call
- Replace `verify_running_async()` body with `HealthChecker.verify_running_async()` call
- Split `_cleanup_server_resources()` into two methods
- Merge `ProcessTerminator.terminate()` and `terminate_with_timeout()` into one method
- Add optional `fields` parameter to `ProcessSnapshotProvider.from_proc_pid()` and `get_info()`
- Ensure all existing tests pass without modification (behavior-preserving refactor)
- Add unit tests for each extracted standalone function (minimum coverage)

## Constraints
- Behavior-preserving: public API (`HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`) must remain unchanged
- No changes to config dataclass schemas or validator functions
- No changes to `StartupFailure` / `HttpStartupError` DTO shape
- Must not introduce new circular imports (current lazy import of `_build_mcp_servers` inside `_classify_mcp_server_changes` must be preserved or resolved)
- Existing test fixtures in `tests/agent/commands/test_agent_cmd_config.py` and `tests/agent/services/test_config_reload*.py` must work without modification
- `shutdown_all()` must remain callable on `HttpServerLifecycleManager` for backward compat — just delegate internally

## Acceptance Criteria
- [ ] `HttpServerLifecycleManager.shutdown_all()` delegates to `ShutdownCoordinator.shutdown_all()` instead of duplicating logic
- [ ] `_absorb_sigint_during_shutdown` exists only in `ShutdownCoordinator`
- [ ] `_build_snapshot()` delegates to `ProcessSnapshotProvider.get_info()`
- [ ] `verify_running_async()` delegates to `HealthChecker.verify_running_async()`
- [ ] `_cleanup_server_resources()` split into two separate methods
- [ ] `ProcessTerminator` has exactly one public termination method
- [ ] `ProcessSnapshotProvider.from_proc_pid()` accepts optional `fields` parameter
- [ ] All existing tests pass: `pytest tests/agent/ -q --ignore=tests/integration/`
- [ ] New unit tests exist for the four extracted standalone functions (minimum 1 test each)
- [ ] No new circular imports introduced
- [ ] `ruff check` and `mypy` pass on all modified/new files

## Testing Expectations
- Run existing test suite: `uv run pytest tests/agent/ -q --ignore=tests/integration/`
- Run existing command-level tests: `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q`
- Add unit tests for each extracted standalone function
- Verify mypy passes: `uv run mypy scripts/agent/http_lifecycle*.py`
- Verify ruff passes: `uv run ruff check scripts/agent/http_lifecycle*.py`

## Documentation Impact
Update module docstrings in the four affected sub-modules to describe responsibility boundaries. No external documentation updates needed — the public API surface is unchanged.

## Out of Scope
- Adding new lifecycle operations (e.g., graceful restart with zero-downtime)
- Changing `StartupFailure` / `HttpStartupError` DTO shape
- Modifying config dataclass definitions
- Adding integration tests for the `/reload` command
- Removing `# noqa` suppressions unless clearly unjustified after refactor
- Changing `McpServerConfig` schema

## Dependencies
N/A: none

## Unresolved Questions
- Should `shutdown_all()` on `HttpServerLifecycleManager` raise if called directly (since the real work is in `ShutdownCoordinator`)? Currently it delegates silently — callers may not realize the coordinator is doing the work.
- Should `ProcessSnapshotProvider.from_proc_pid()` accept a `frozenset[str]` of field names rather than a list? The current approach uses positional args which could break if fields are reordered.
- Is the 10-second rate limit in `verify_running_async()` appropriate for production use, or should it be configurable via `McpServerConfig`?
- Should `ProcessTerminator.terminate_with_timeout()` return a boolean indicating whether the process exited gracefully vs. being killed?

## AI Implementation Instruction
Do not rewrite unrelated files. Preserve the public API: `HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`. Each extracted module must have a clear responsibility boundary — do not create cross-cutting dependencies between the four new modules. Test after each extraction step, not just at the end. Stop and report if you find a circular import that cannot be resolved without changing the config dataclass layer.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-102515
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle_process_snapshot.py
