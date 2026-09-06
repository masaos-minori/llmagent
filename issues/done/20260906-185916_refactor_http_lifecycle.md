# Refactor http_lifecycle.py: reduce method sizes, eliminate snapshot duplication, simplify signal handling

## Priority
Medium

## Summary
Refactor `scripts/agent/http_lifecycle.py` to reduce large method sizes, eliminate duplicate snapshot construction logic, simplify signal handling in `shutdown_all()`, and improve overall maintainability without changing behavior.

## Background
The file manages HTTP subprocess MCP server lifecycle operations (start, health-poll, restart, shutdown). It was previously extracted from `lifecycle.py` and refactored into a composition facade delegating to six concern-specific modules. However, several methods remain overly large and contain duplicated logic:
- `start()` (164 lines) mixes command validation, environment filtering, process creation, health polling, and error handling
- `shutdown_all()` (61 lines) has complex signal handling with thread-safe fallback mechanisms
- `_snapshot_fields()` returns raw data that both `get_process_info()` and `get_process_snapshot()` duplicate into their respective return types
- Several hardcoded magic numbers are scattered throughout (see specific values below)

Note: `MCPSERVER_HEALTH_TIMEOUT: float = 5.0` (line 46) and `_STDERR_TAIL_BYTES: int = 64 * 1024` (line 48) are already module-level constants and do NOT need replacement.

This makes the code difficult to review, test independently, and extend.

## Problem
The current structure creates three concrete problems:
1. **Method size**: `start()` exceeds 160 lines, making it impossible to understand any single responsibility at a glance. Health polling, process creation, and error cleanup are interleaved.
2. **Snapshot duplication**: `get_process_info()` and `get_process_snapshot()` both unpack `_snapshot_fields()` and construct nearly identical dicts/dataclasses from the same source data. Adding a new field requires updating both.
3. **Signal handling fragility**: `shutdown_all()` uses a complex signal handler swap with thread-safe fallback (`call_soon_threadsafe`). If the fallback fails silently, a second Ctrl-C leaves orphaned subprocesses.

## Reason for Change
The file has accumulated technical debt through incremental changes. A refactor now prevents future bugs and reduces the cost of adding new lifecycle features (e.g., graceful restart with zero-downtime).

## Implementation Intent
1. Extract health polling loop from `start()` into a private `_health_poll_until_ready()` method.
2. Extract process creation and validation from `start()` into `_create_and_validate_proc()`.
3. Replace `_snapshot_fields()` + dual consumers with a single `_build_snapshot_dict()` method that returns a dict, then have `get_process_info()` convert to `ProcessInfoSnapshot` and `get_process_snapshot()` return the dict directly.
4. Simplify `shutdown_all()` signal handling: use `signal.signal()` once with a simple flag-based approach instead of swapping handlers with thread-safe fallback.
5. Move magic numbers to module-level constants with descriptive names.
6. Ensure all existing tests pass after the refactor.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` (primary)
- `scripts/agent/http_lifecycle_errors.py` (error classes referenced by start/restart)
- `tests/` (existing tests must still pass)

## Required Changes
- Extract `start()` (164 lines) into:
  - `_create_and_validate_proc(server_key, cfg)` — validates command, filters env, creates subprocess, handles getpgid failure
  - `_health_poll_until_ready(server_key, cfg, client, deadline, shutdown_event)` — polls /health until ready or timeout
  - Keep only idempotency check, logging, and result aggregation in `start()`
- Replace `_snapshot_fields()` + dual consumers with:
  - `_build_snapshot_dict(server_key)` — returns `{server_key, managed, pid, pgid, running, last_exit_code, stderr_log}` or None
  - `get_process_info()` calls `_build_snapshot_dict()` and converts to `ProcessInfoSnapshot`
  - `get_process_snapshot()` calls `_build_snapshot_dict()` and returns dict directly
- Simplify `shutdown_all()` signal handling:
  - Use a single `signal.signal(SIGINT, _ignore_handler)` before cleanup
  - Remove the `call_soon_threadsafe` fallback path for signal handler restoration
  - Restore original handler in finally block unconditionally
- Add module-level constants (only these magic numbers need replacement):
  - `HEALTH_POLL_INTERVAL_SEC = 0.5` (line 425: `_interruptible_poll_sleep(0.5, ...)`)
  - `TERMINATE_TIMEOUT_SEC = 5.0` (lines 367, 437, 514: `_terminate_with_timeout(..., timeout=5.0)`)
  - `RESTART_TERMINATE_TIMEOUT_SEC = 3.0` (line 132: default param of `_terminate_with_timeout`)
  - Note: `MCPSERVER_HEALTH_TIMEOUT` (5.0) and `_STDERR_TAIL_BYTES` (64*1024) are already constants — do NOT replace them

## Constraints
- Must not change any external API or behavior — public method signatures and return types must remain identical
- `HttpStartupError` and `StartupFailure` exception semantics must not change
- Process group termination via `os.killpg()` must not change
- SIGINT absorption during shutdown must still prevent orphaned subprocesses
- All existing tests must pass without modification
- No new runtime dependencies may be added

## Acceptance Criteria
- [ ] `start()` method does not exceed 80 lines (excluding blank lines and comments)
- [ ] `_snapshot_fields()` is removed; replaced by `_build_snapshot_dict()` returning a dict
- [ ] `shutdown_all()` no longer uses `call_soon_threadsafe` for signal handler restoration
- [ ] Magic numbers `0.5` (line 425), `5.0` (lines 367/437/514), `3.0` (line 132) are replaced with named constants
- [ ] Each private method has a clear single responsibility documented in its docstring
- [ ] All existing tests pass without modification
- [ ] Type hints are improved where possible (remove unnecessary `object | None` unions)

## Testing Expectations
- Run existing test suite: `uv run pytest tests/` (filter for http_lifecycle tests)
- Verify no behavioral regression by comparing output of `/reload` command before and after refactor
- Add mutation testing coverage for edge cases: early exit, health poll timeout, SIGINT during shutdown

## Documentation Impact
- Update module docstring to describe the new extraction boundaries
- Document the hot-reloadable vs restart-required classification criteria in `ConfigReloadOutcome` docstrings

## Out of Scope
- Adding new lifecycle features (e.g., graceful restart with zero-downtime)
- Changing the behavior of existing fields
- Modifying `HttpStartupError` or `StartupFailure` exception schemas
- Refactoring other files in the agent service layer

## Dependencies
N/A: none

## Unresolved Questions
- Should `_health_poll_until_ready()` accept an `httpx.AsyncClient` parameter or create its own?
- Is there a way to derive field mappings automatically from dataclass fields rather than manual registration?
- Should the signal handler use `asyncio.get_running_loop().call_soon()` instead of `call_soon_threadsafe`?

## AI Implementation Instruction
1. Read `scripts/agent/http_lifecycle.py` and identify all methods exceeding 80 lines.
2. Extract `_create_and_validate_proc()` from `start()`: validate command, filter env, create subprocess, handle getpgid failure.
3. Extract `_health_poll_until_ready()` from `start()`: poll /health until ready or timeout, handle early exit and shutdown event.
4. Replace `_snapshot_fields()` with `_build_snapshot_dict()` that returns a dict; update `get_process_info()` and `get_process_snapshot()` accordingly.
5. Simplify `shutdown_all()` signal handling: remove `call_soon_threadsafe` fallback, use simple flag-based approach.
6. Move magic numbers to module-level constants with descriptive names (only `0.5`, `5.0`, `3.0` — NOT `MCPSERVER_HEALTH_TIMEOUT` or `_STDERR_TAIL_BYTES`).
7. Run `uv run pytest tests/` to verify no regression.
8. Ensure no method exceeds 80 lines after refactor.
