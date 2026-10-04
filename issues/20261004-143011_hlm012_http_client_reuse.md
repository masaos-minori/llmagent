# HttpServerLifecycleManager: New HTTP client per health-poll session wastes connections

## Background

`HttpServerLifecycleManager._health_poll_until_ready()` in `scripts/agent/http_lifecycle.py` polls the `/health` endpoint of a newly started subprocess MCP server until it becomes healthy.

## Problem

A new `httpx.AsyncClient` is created inside the health-poll loop for each health-poll session. While this is correct for connection management (the client is closed when the context exits), it means connection pooling is lost across health-poll sessions. For servers that need multiple health checks during startup, this creates unnecessary TCP connection overhead.

## Evidence

- File: `scripts/agent/http_lifecycle.py`
- Lines 393-395:

```python
async with httpx.AsyncClient(
    timeout=httpx.Timeout(timeout=hc_timeout)
) as client:
```

This is called once per `_health_poll_until_ready()` invocation, which happens once per server start attempt.

## Impact

- Each health-poll session creates a new TCP connection pool
- Connection establishment latency adds to startup time
- Under high load with many servers, connection pool exhaustion is possible

## Recommended action

Consider reusing a shared HTTP client for health checks across the lifecycle manager. This would require careful lifetime management to avoid holding connections open indefinitely.

Alternatively, document the current behavior as intentional (connection cleanup on failure) and accept the trade-off.

## Acceptance criteria

- [ ] Behavior documented as intentional or changed to reuse client
- [ ] If changed, test verifies no connection leaks on failure paths
- [ ] If changed, test verifies connection reuse across health-poll retries

## Out of scope

- Changes to the health-check polling interval or timeout
- Changes to the HTTP client configuration
