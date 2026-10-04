# ShutdownCoordinator: Removes tracking data even when process termination fails

## Background

`ShutdownCoordinator.shutdown_all()` in `scripts/agent/http_lifecycle_shutdown_coordinator.py` coordinates graceful shutdown of HTTP subprocess MCP servers. It delegates termination to `ProcessTerminator.terminate_with_timeout()` and then calls `cleanup_server_key()` to remove tracking entries.

## Problem

When `terminate_with_timeout()` fails (caught by the except block), `cleanup_server_key()` is still called unconditionally. This removes tracking data while the process may still be running, creating orphaned processes.

## Evidence

- File: `scripts/agent/http_lifecycle_shutdown_coordinator.py`
- Lines 105-111:

```python
try:
    await terminator.terminate_with_timeout(proc, server_key, **terminate_kwargs)
except (OSError, TimeoutError) as e:
    logger.warning("Lifecycle: error terminating %r: %s", server_key, e)
manager.cleanup_server_key(server_key)  # Always called, even on termination failure
```

## Impact

- Process continues running without tracking — zombie process
- Subsequent attempts to shut down the same server will not find it
- Resource leak (file descriptors, ports, memory)

## Recommended action

Only call `cleanup_server_key()` after successful termination. On failure, log the issue but keep the tracking entry so subsequent cleanup attempts can target the process:

```python
try:
    await terminator.terminate_with_timeout(proc, server_key, **terminate_kwargs)
    manager.cleanup_server_key(server_key)
except (OSError, TimeoutError) as e:
    logger.warning("Lifecycle: error terminating %r: %s; keeping tracking entry for retry", server_key, e)
    # Do NOT call cleanup_server_key — process may still be running
```

Alternatively, add a separate cleanup method that only removes tracking without requiring termination success.

## Acceptance criteria

- [ ] Tracking data is removed only after confirmed process termination
- [ ] Failed termination leaves tracking entry intact for retry
- [ ] Test verifies no zombie process after shutdown failure scenario
- [ ] Test verifies tracking entry persists on termination failure

## Out of scope

- Changes to `ProcessTerminator.terminate_with_timeout()` itself
- Changes to `cleanup_server_key()` implementation
