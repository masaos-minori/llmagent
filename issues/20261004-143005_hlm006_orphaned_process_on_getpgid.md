# HttpServerLifecycleManager: Orphaned process on getpgid failure after subprocess creation

## Background

`HttpServerLifecycleManager._create_and_validate_proc()` in `scripts/agent/http_lifecycle.py` creates a subprocess, validates its command, and records its process-group ID via `os.getpgid()`.

## Problem

When `getpgid()` fails after the subprocess has been created, the code attempts cleanup but the process itself may still be running. The tracking entries are removed, but the process continues without being tracked.

## Evidence

- File: `scripts/agent/http_lifecycle.py`
- Lines 320-347:

```python
try:
    self._http_pgids[server_key] = os.getpgid(proc.pid)
except OSError as e:
    logger.warning(...)
    try:
        await self._process_terminator.terminate_with_timeout(proc, ...)
        poll_result = proc.poll()
        if poll_result is not None and poll_result != 0:
            logger.info(...)
    finally:
        stderr_fh.close()
        self._stderr_files.pop(server_key, None)
        self._stderr_log_manager.forget(server_key)
        self._http_procs.pop(server_key, None)
        self._http_pgids.pop(server_key, None)
    raise e
```

## Impact

- If `terminate_with_timeout()` fails (e.g., permission denied), the process runs untracked
- The subprocess consumes resources indefinitely
- Subsequent health checks will fail silently because the key is no longer tracked

## Recommended action

1. After `getpgid()` failure, attempt termination first.
2. Only remove tracking entries AFTER confirming the process has exited.
3. Log the process PID so operators can manually clean up if needed.

```python
try:
    self._http_pgids[server_key] = os.getpgid(proc.pid)
except OSError as e:
    logger.warning(
        "Lifecycle: getpgid() failed for %r pid=%d; attempting cleanup",
        server_key, proc.pid,
    )
    # Attempt termination first
    try:
        await self._process_terminator.terminate_with_timeout(
            proc, server_key, timeout=TERMINATE_TIMEOUT_SEC
        )
    except Exception as term_err:
        logger.error(
            "Lifecycle: failed to terminate orphaned process %r pid=%d: %s",
            server_key, proc.pid, term_err,
        )
        # Do NOT remove tracking — process may still be running
        raise
    # Confirm process exited before removing tracking
    if proc.poll() is None:
        logger.error(
            "Lifecycle: process %r pid=%d did not exit after termination; leaving tracking entry",
            server_key, proc.pid,
        )
        raise e
    # Safe to clean up — process confirmed dead
    stderr_fh.close()
    ...
    raise e
```

## Acceptance criteria

- [ ] Tracking entries are removed only after confirmed process exit
- [ ] Failed termination leaves process PID logged for manual intervention
- [ ] Test verifies no orphaned process after getpgid failure scenario
- [ ] Test verifies tracking entry persists when termination fails

## Out of scope

- Changes to `ProcessTerminator.terminate_with_timeout()` behavior
- Changes to subprocess creation parameters
