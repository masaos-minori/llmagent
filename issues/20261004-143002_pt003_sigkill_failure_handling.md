# ProcessTerminator: SIGKILL escalation does not handle all failure modes

## Background

`ProcessTerminator.terminate_with_timeout()` in `scripts/agent/http_lifecycle_process_terminator.py` implements SIGTERM → wait → SIGKILL escalation for process termination. After the SIGTERM timeout expires, it escalates to SIGKILL.

## Problem

The SIGKILL escalation only handles `ProcessLookupError` (process already exited). Other failures such as permission denied (`PermissionError`) or invalid operation (`OSError`) are not caught, causing the exception to propagate up and leaving the process running.

## Evidence

- File: `scripts/agent/http_lifecycle_process_terminator.py`
- Lines 157-162:

```python
try:
    os.killpg(pgid, signal.SIGKILL)  # nosec B603
    logger.warning("Escalated to SIGKILL for process group %d", pgid)
except ProcessLookupError:
    logger.info("Process group %d already exited after timeout")
```

## Impact

- If SIGKILL fails due to permissions or other OS-level reasons, the exception propagates
- The calling code may abort shutdown entirely
- The process remains running as an orphan
- No warning is logged about the failed escalation

## Recommended action

Catch broader `OSError` (which includes `PermissionError`) during SIGKILL escalation, similar to how SIGTERM failure is handled earlier in the method:

```python
try:
    os.killpg(pgid, signal.SIGKILL)
    logger.warning("Escalated to SIGKILL for process group %d", pgid)
except ProcessLookupError:
    logger.info("Process group %d already exited after timeout")
except OSError as e:
    logger.error(
        "SIGKILL escalation failed for process group %d: %s — process may remain running",
        pgid, e,
    )
```

Also consider adding a final check after SIGKILL to verify the process actually exited:

```python
try:
    os.killpg(pgid, signal.SIGKILL)
    logger.warning("Escalated to SIGKILL for process group %d", pgid)
except ProcessLookupError:
    logger.info("Process group %d already exited after timeout")
except OSError as e:
    logger.error(
        "SIGKILL escalation failed for process group %d: %s — process may remain running",
        pgid, e,
    )
else:
    # Verify SIGKILL took effect
    if not self.wait_exited(proc, server_key, poll_interval=0.1, timeout=1.0):
        logger.error("Process group %d did not exit after SIGKILL", pgid)
```

## Acceptance criteria

- [ ] SIGKILL failure logs an error instead of propagating
- [ ] Test verifies SIGKILL failure is handled gracefully
- [ ] Test verifies process verification after SIGKILL escalation
- [ ] No regression in normal SIGKILL path

## Out of scope

- Changes to SIGTERM handling (already correct)
- Changes to the timeout mechanism
