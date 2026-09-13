# Implementation Procedure: Refactor http_lifecycle.py

## Goal

Reduce cyclomatic complexity in `scripts/agent/http_lifecycle.py`, consolidate duplicate resource cleanup and process termination logic into shared helpers, and replace the implicit dict-to-dataclass mapping in `_build_snapshot_dict()` with an explicit `ProcessInfoSnapshot` return path. (REQ-001 through REQ-008)

## Scope

- Modify `scripts/agent/http_lifecycle.py` only
- Extract shared helper methods for duplicate logic
- Replace dict snapshot with typed dataclass where appropriate
- Preserve all public method signatures and behavior

## Assumptions

- The six concern-specific modules (CommandValidator, StderrLogManager, etc.) are stable and their interfaces will not change
- `_build_snapshot_dict()` is called only by `get_process_info()` and `get_process_snapshot()` — verified via grep
- The `shutdown_event` parameter in `_health_poll_until_ready()` is optional and its absence means no shutdown racing
- `ProcessInfoSnapshot` fields map 1:1 with the keys returned by `_build_snapshot_dict()` — confirmed by reading models.py

## Design decisions

- Extract `_do_pgid_terminated(pgid, proc, force=False)` as a private helper to encapsulate pgid-based SIGTERM/SIGKILL logic currently duplicated in `_terminate_with_timeout()`. This keeps the pgid lookup and try/catch around `os.killpg()` in one place.
- Replace `_build_snapshot_dict()`'s dict return with direct `ProcessInfoSnapshot` construction. This makes the type contract explicit rather than implicit through dict mappings, allowing mypy to verify field correspondence.
- Extract early-exit paths from `_health_poll_until_ready()` into named methods (`_handle_early_exit`, `_handle_shutdown_request`) to reduce nesting depth and make control flow readable.

## Alternatives considered

- Returning `ProcessInfoSnapshot` directly from `_build_snapshot_dict()` instead of creating a new `_build_snapshot()` method — rejected because `get_process_snapshot()` callers expect a dict format; converting inside `_build_snapshot()` would break that contract.
- Using asyncio task cancellation instead of SIGINT handler in `shutdown_all()` — rejected because the current approach with `finally` restoration is adequate for the scope and changing it would alter runtime behavior.
- Consolidating all cleanup into `_cleanup_server_resources()` and having every caller use it exclusively — partially adopted but not fully because some callers need stderr content returned alongside cleanup (e.g., `_health_poll_until_ready()`).

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

**Phase 1: Extract shared termination helper**

1. Create `_do_pgid_terminated(self, pgid: int | None, proc: subprocess.Popen[bytes], force: bool = False) -> None` method
   - Encapsulates the pgid-based termination logic currently duplicated in `_terminate_with_timeout()`
   - Handles the try/catch around `os.killpg()` and falls back to `proc.terminate()`/`proc.kill()`
   - When `force=True`, sends SIGKILL instead of SIGTERM
   - REQ-001; File: scripts/agent/http_lifecycle.py

2. Rewrite `_terminate_with_timeout()` to delegate to `_do_pgid_terminated()`
   - Initial termination: call `_do_pgid_terminated(pgid, proc, force=False)`
   - Force-kill escalation: call `_do_pgid_terminated(pgid, proc, force=True)`
   - Remove the duplicate pgid lookup code blocks at lines 140-147 and 161-168
   - REQ-001; File: scripts/agent/http_lifecycle.py

**Phase 2: Consolidate cleanup and replace dict snapshot**

3. Consolidate resource cleanup — ensure `_cleanup_server_resources()` is the single entry point for all cleanup operations including stderr log closing and tracking data removal
   - Currently `_health_poll_until_ready()` calls `_cleanup_server_resources()` directly in two places (early-exit at line 406 and shutdown at line 435)
   - Move stderr log closing and tracking data removal into this method consistently
   - Ensure callers that need stderr content receive it before cleanup completes
   - REQ-002; File: scripts/agent/http_lifecycle.py

4. Replace `_build_snapshot_dict()` with `_build_snapshot()` returning `ProcessInfoSnapshot | None` directly
   - Rename `_build_snapshot_dict()` → `_build_snapshot()`
   - Return `ProcessInfoSnapshot(server_key=..., managed=..., pid=..., pgid=..., running=..., last_exit_code=..., stderr_log=...)` instead of dict
   - Update `get_process_info()` to remove redundant conversion — it can now return the result of `_build_snapshot()` directly
   - Update `get_process_snapshot()` to convert `ProcessInfoSnapshot` to dict if callers need dict format, OR update both callers to accept `ProcessInfoSnapshot`
   - REQ-003; File: scripts/agent/http_lifecycle.py

5. Extract `_handle_early_exit(self, server_key: str, proc: subprocess.Popen[bytes]) -> None` method from `_health_poll_until_ready()`'s early-exit-on-process-death path
   - Current code at lines 405-420: checks `proc.poll()`, reads stderr, logs error, removes tracking entries, raises `HttpStartupError`
   - The method should handle the cleanup and raise the exception
   - REQ-004; File: scripts/agent/http_lifecycle.py

6. Extract `_handle_shutdown_request(self, server_key: str) -> None` method from `_health_poll_until_ready()`'s shutdown-event path
   - Current code at lines 435-443: cleans up resources, creates `StartupFailure`, removes tracking entries, raises `HttpStartupError`
   - The method should handle the cleanup and raise the exception
   - REQ-004; File: scripts/agent/http_lifecycle.py

**Phase 3: Improve SIGINT handling and verification**

7. Improve SIGINT handler in `shutdown_all()` — add additional guard to ensure handler restoration even on unexpected exceptions
   - Current approach at lines 530-579 already restores handler in `finally` block
   - Add a second-level guard: wrap the handler restoration in its own try/except to catch `ValueError` from invalid signal numbers
   - REQ-005; File: scripts/agent/http_lifecycle.py

8. Run test suite — `uv run pytest tests/agent/test_http_lifecycle_* -v`
   - Verify all tests pass after each phase
   - REQ-007; File: scripts/agent/http_lifecycle.py

9. Run mypy — `uv run mypy scripts/agent/http_lifecycle.py --no-error-summary 2>&1`
   - Verify zero new errors
   - REQ-008; File: scripts/agent/http_lifecycle.py

10. Compute cyclomatic complexity of `_health_poll_until_ready()` using radon (if available): `radon cc scripts/agent/http_lifecycle.py -s`
    - Verify `_health_poll_until_ready()` complexity < 15
    - REQ-004; File: scripts/agent/http_lifecycle.py

### Method

Each phase above is independently verifiable. Phase 1 extracts a pure helper with no side effects beyond process termination. Phase 2 changes the internal representation from dict to dataclass — this requires careful testing since callers may depend on dict semantics. Phase 3 improves robustness of the shutdown path.

### Details

**Phase 1 details:**
- `_do_pgid_terminated` signature: `(self, pgid: int | None, proc: subprocess.Popen[bytes], force: bool = False) -> None`
- When `pgid is not None`: attempt `os.killpg(pgid, signal.SIGTERM)` or `signal.SIGKILL`; on failure, fall back to `proc.terminate()` or `proc.kill()`
- When `pgid is None`: always use `proc.terminate()` or `proc.kill()`
- Both paths call `await self._wait_exited(proc, timeout)` and log warnings if termination fails
- The method returns `None` — callers check `proc.poll()` themselves if needed

**Phase 2 details:**
- `_cleanup_server_resources` consolidation:
  - Always close stderr file handle if present
  - Always pop tracking dicts (`_stderr_files`, `_stderr_log_paths`, `_last_health_check`)
  - Return stderr tail content when requested by caller
- `_build_snapshot` replacement:
  - Directly construct `ProcessInfoSnapshot` from instance state
  - `get_process_info()`: return result of `_build_snapshot()` directly
  - `get_process_snapshot()`: either convert to dict via `dataclasses.asdict()` or update callers to accept `ProcessInfoSnapshot`

**Phase 3 details:**
- SIGINT handler improvement:
  - Current code has outer try/except around `signal.getsignal()` and inner try/finally around handler restoration
  - Add nested try/except specifically around the `signal.signal(signal.SIGINT, old_sigint)` call in the finally block
  - Log debug message if restoration fails rather than silently ignoring

## Compatibility considerations

- **Public API**: All public method signatures must be preserved (`start`, `restart`, `verify_running`, `verify_running_async`, `get_process_info`, `get_process_snapshot`, `list_processes`, `shutdown_all`). Changing any signature breaks backward compatibility.
- **`get_process_snapshot()` return type**: If `_build_snapshot()` returns `ProcessInfoSnapshot` instead of `dict`, callers expecting a dict will break. Either keep dict return in `get_process_snapshot()` by converting the dataclass, or update all callers simultaneously.
- **Injected component contracts**: The six injected components (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ProcessSnapshotProvider, ShutdownCoordinator) must maintain their existing interfaces. Only internal delegation within `HttpServerLifecycleManager` changes.

## Security considerations

- No new security surface introduced — refactoring does not add new external-facing APIs or change authentication/authorization boundaries
- The SIGINT handler improvement in Phase 3 prevents orphaned processes during shutdown, which is a reliability concern rather than a security concern
- `os.killpg()` usage remains unchanged — still gated by `pgid is not None` check

## Rollback considerations

- Each phase is independently revertible: revert the git commit for that phase
- Phase 2 (dict→dataclass) is the riskiest rollback scenario — if callers depend on dict semantics, reverting requires updating those callers again
- All phases preserve existing behavior — rollback means restoring the original code exactly as-is
- Test suite serves as the rollback safety net: if any phase's tests fail, revert that phase immediately

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit + Integration | `uv run pytest tests/agent/test_http_lifecycle_* -v` | All tests pass |
| scripts/agent/http_lifecycle.py | Type checking | `uv run mypy scripts/agent/http_lifecycle.py --no-error-summary 2>&1` | Zero new errors |
| scripts/agent/http_lifecycle.py | Cyclomatic complexity | `radon cc scripts/agent/http_lifecycle.py -s` (if installed) | `_health_poll_until_ready()` < 15 |

## Completion criteria

- [ ] Phase 1 complete: `_do_pgid_terminated()` exists and `_terminate_with_timeout()` delegates to it; no duplicate pgid-based termination logic remains
- [ ] Phase 2 complete: `_cleanup_server_resources()` is the single cleanup entry point; `_build_snapshot()` returns `ProcessInfoSnapshot | None`; `get_process_info()` returns the dataclass directly
- [ ] Phase 3 complete: SIGINT handler restoration is guarded against unexpected exceptions; all tests pass; mypy reports zero new errors
- [ ] All public method signatures preserved
- [ ] Cyclomatic complexity of `_health_poll_until_ready()` below 15

## Out of scope

- Modifying `scripts/agent/services/models.py` (`ProcessInfoSnapshot` schema)
- Adding new features or capabilities
- Changing public API contracts
- Refactoring the six delegated concern modules
- Modifying test files beyond ensuring they still pass
- Changing the SIGINT handler strategy (e.g., switching to asyncio task cancellation)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|

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
- **Requirement ID**: REQ-001 through REQ-008
- **Source issue**: issues/20260913-081127_refactor_http_lifecycle_complexity_type_safety.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-082244_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-082518
- **Related target files**: scripts/agent/http_lifecycle.py
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-121604 | 20260913-121604 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260913-121604 | 20260913-121604 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-121604 | 20260913-121604 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-121604 | 20260913-121604 | N/A: no docs require updating |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs require updating |