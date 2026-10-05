## Goal

Only remove tracking entries after confirming the process has exited, preventing orphaned processes when getpgid failure leads to failed termination.

## Scope

- Modify `scripts/agent/http_lifecycle.py`: move tracking entry removal from finally block into a conditional path that only executes after confirmed process exit
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
2. Move `self._http_procs.pop(server_key, None)` and `self._http_pgids.pop(server_key, None)` from the finally block into a conditional path after `proc.poll()` check
3. Add PID logging in the termination failure path

### Details
```python
# Before (lines 320-347):
try:
    # ... subprocess creation logic ...
    os.getpgid(proc.pid)
except OSError as e:
    logger.warning(
        "Lifecycle: getpgid() failed for %r pid=%d; cleaning up",
        server_key,
        proc.pid,
    )
    try:
        await self._process_terminator.terminate_with_timeout(
            proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
        )
        poll_result = proc.poll()
        if poll_result is not None and poll_result != 0:
            logger.info(
                "Lifecycle: subprocess %r (pid=%d) terminated with exit code %d",
                server_key,
                proc.pid,
                poll_result,
            )
    finally:
        # Always cleanup resources if getpgid fails, even if termination fails
        stderr_fh.close()
        self._stderr_files.pop(server_key, None)
        self._stderr_log_manager.forget(server_key)
        self._http_procs.pop(server_key, None)
        self._http_pgids.pop(server_key, None)
    raise e

# After:
termination_succeeded = False
try:
    # ... subprocess creation logic ...
    os.getpgid(proc.pid)
except OSError as e:
    logger.warning(
        "Lifecycle: getpgid() failed for %r pid=%d; attempting cleanup",
        server_key,
        proc.pid,
    )
    try:
        await self._process_terminator.terminate_with_timeout(
            proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
        )
        # Termination succeeded — safe to clean up
        termination_succeeded = True
    except Exception as term_err:
        logger.error(
            "Lifecycle: failed to terminate orphaned process %r pid=%d: %s",
            server_key,
            proc.pid,
            term_err,
        )
        # Do NOT remove tracking — process may still be running
    finally:
        # Always cleanup resources if getpgid fails, even if termination fails
        stderr_fh.close()
        self._stderr_files.pop(server_key, None)
        self._stderr_log_manager.forget(server_key)
    # Only remove tracking if termination succeeded
    if termination_succeeded:
        self._http_procs.pop(server_key, None)
        self._http_pgids.pop(server_key, None)
    raise e
```

The key changes are:
1. Keep the `finally` block for resource cleanup (stderr_fh, _stderr_files, _stderr_log_manager)
2. Add `termination_succeeded` boolean flag to track termination outcome
3. Move tracking entry removal (`_http_procs`, `_http_pgids`) into the success path only
4. Log PID for manual intervention if termination fails

## Compatibility considerations

Callers that expect tracking entries to be removed even on failure may need updates. However, keeping the tracking entry is generally safer — it allows subsequent cleanup attempts to find and target the process.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original placement of tracking entry removal in the finally block if callers depend on immediate tracking removal. This would restore the previous behavior but reintroduce orphaned process risk.

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143005_hlm006_orphaned_process_on_getpgid.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-105000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-080000
- **Related target files**: scripts/agent/http_lifecycle.py
