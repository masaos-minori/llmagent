## Goal

Only remove tracking entries after confirming the process has exited, preventing orphaned processes when getpgid failure leads to failed termination.

## Scope

- Modify `scripts/agent/http_lifecycle.py`: move tracking entry removal from finally block into a conditional path that only executes after confirming process exit
- Add PID logging on termination failure for manual intervention

## Assumptions

- `terminate_with_timeout()` raises an exception on failure rather than returning silently
- The process PID should be logged in the error message for manual intervention
- `proc.poll()` returns None while the process is still running

## Design decisions

- Move tracking entry removal from the finally clause into a conditional path that only executes after confirming `proc.poll()` returns a non-None value (process exited)
- On termination failure, keep tracking entries and log the PID for manual intervention

## Alternatives considered

- Adding a separate "critical cleanup" flag — over-engineering for this use case
- Using a context manager for cleanup ordering — adds complexity without clear benefit

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
Restructure the except OSError block: move tracking removal out of finally, add exit confirmation check. Add PID logging on termination failure.

### Method
1. Locate lines 320-347 in `scripts/agent/http_lifecycle.py` (except OSError block with finally)
2. Move `manager.cleanup_server_key(server_key)` from the finally block into a conditional path after `proc.poll()` check
3. Add PID logging in the termination failure path

### Details
```python
# Before (lines 320-347):
try:
    # ... subprocess creation logic ...
    os.getpgid(proc.pid)
except OSError as e:
    logger.error(f"Failed to get pgid for {server_key}: {e}")
    try:
        await self._terminator.terminate_with_timeout(proc, timeout=5)
    except Exception as term_err:
        logger.error(f"Termination also failed for {server_key}: {term_err}")
    finally:
        manager.cleanup_server_key(server_key)

# After:
try:
    # ... subprocess creation logic ...
    os.getpgid(proc.pid)
except OSError as e:
    logger.error(f"Failed to get pgid for {server_key}: {e}")
    try:
        await self._terminator.terminate_with_timeout(proc, timeout=5)
        # Process terminated successfully — safe to remove tracking
        manager.cleanup_server_key(server_key)
    except Exception as term_err:
        # Termination failed — keep tracking entries for manual intervention
        logger.error(
            f"Termination failed for {server_key} (PID={proc.pid}): {term_err}. "
            f"Tracking entry retained for manual cleanup."
        )
```

The key change is moving `cleanup_server_key()` from the finally block into the try block after successful termination. This ensures tracking data is only removed after confirmed process exit.

## Compatibility considerations

Callers that expect tracking entries to be removed even on failure may need updates. However, keeping the tracking entry is generally safer — it allows subsequent cleanup attempts to find and target the process.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original placement of `cleanup_server_key()` in the finally block if callers depend on immediate tracking removal. This would restore the previous behavior but reintroduce orphaned process risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit test — verify tracking persistence on termination failure | uv run pytest tests/agent/test_http_lifecycle.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Tracking entries are removed only after confirmed process exit (REQ-001)
- [ ] Failed termination leaves process PID logged for manual intervention (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to ProcessTerminator.terminate_with_timeout() behavior
- Changes to subprocess creation parameters
- Creating new test file (handled in separate document)

## Implementation outcome

Implemented against the real source. The procedure draft's API did not match
source: draft assumed `self._terminator`, `terminate_with_timeout(proc,
timeout=5)`, and `manager.cleanup_server_key(...)`; the real API is
`self._process_terminator.terminate_with_timeout(proc, server_key, timeout=...)`
and inline `self._http_procs`/`self._http_pgids` pops. Control flow was
restructured accordingly:

- Tracking removal (`_http_procs.pop`, `_http_pgids.pop`) moved out of `finally`
  into the post-success path (removed only after confirmed process exit).
- New `except Exception as term_err:` logs the PID and retains tracking on
  termination failure, then re-raises.
- Resource cleanup (stderr close, stderr-files pop, log-manager forget) kept in
  `finally` so handles are always released.
- Original `raise e` preserved.

Verified: 50 tests pass across `tests/agent/test_http_lifecycle.py` (+2 new) and
`tests/agent/test_http_lifecycle_integration.py`; `ruff format --check`,
`ruff check`, and `bandit -l -ii` all clean.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-10-05 | 2026-10-05 | Implemented against real API (see Implementation outcome). |
| 2 | Add or update tests per Validation plan | Done | 2026-10-05 | 2026-10-05 | `tests/agent/test_http_lifecycle.py` created (REQ-001, REQ-002). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-05 | 2026-10-05 | ruff/bandit clean; 50 tests pass. mypy environmental noise only. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope per procedure. |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143005_hlm006_orphaned_process_on_getpgid.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182813_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195020
- **Related target files**: scripts/agent/http_lifecycle.py
