# start() opens an unused httpx.AsyncClient that is shadowed inside _health_poll_until_ready

## Priority
Low

## Summary
`HttpServerLifecycleManager.start()` constructs an `httpx.AsyncClient` and passes it to `_health_poll_until_ready()`, but that method immediately creates and uses its own client, shadowing the parameter. The outer client is opened and closed without ever being used. Remove the dead client construction and the unused parameter.

## Background
In scripts/agent/http_lifecycle.py, `start()` (lines 435-476) calls the health poll under a client:
```python
async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT)) as client:
    await self._health_poll_until_ready(server_key, cfg, proc, client, deadline, shutdown_event)
```
`_health_poll_until_ready()` (lines 363-433) has signature `(self, server_key, cfg, proc, client, deadline, shutdown_event)` and begins its body with:
```python
async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=hc_timeout)) as client:
    ...
```
Line scripts/agent/http_lifecycle.py:393.

## Problem
The `client` argument passed from `start()` is never referenced inside `_health_poll_until_ready()`; the method re-creates its own client via `async with`. Consequences:
- Every successful HTTP-MCP startup opens one extra `AsyncClient` that performs no request, then closes it — wasted connection-setup work on the hot startup path.
- The `client` parameter is misleading: readers assume the caller's client drives the polls.
- `MCPSERVER_HEALTH_TIMEOUT` is used for the dead outer client, while the real client uses `compute_health_check_timeout(...)` — so the outer block's timeout is meaningless.

## Reason for Change
Dead resource setup on the startup path and a misleading signature invite confusion and future bugs (e.g., someone "fixing" the timeout on the wrong client). Removing it makes the actual client authoritative.

## Implementation Intent
Delete the outer `async with httpx.AsyncClient(...)` wrapper in `start()` and pass nothing (or drop the `client` parameter) to `_health_poll_until_ready()`. Keep the single authoritative client inside `_health_poll_until_ready()`. No behavior change to polling, timeouts, or error handling.

## Target Files or Areas
- scripts/agent/http_lifecycle.py (`start` and `_health_poll_until_ready`)

## Required Changes
- Remove the unused `async with httpx.AsyncClient(...)` block in `start()`.
- Drop the now-unused `client` parameter from `_health_poll_until_ready()`.
- Ensure the health-poll loop, deadlines, and shutdown-event racing are unchanged.

## Constraints
- Must not change health-poll timing, timeout computation, or failure semantics.
- Preserve the `shutdown_event` interrupt behavior.

## Acceptance Criteria
- `start()` no longer constructs an `AsyncClient` that is not used.
- Health polling still works end-to-end (startup success and timeout-failure paths).

## Testing Expectations
- Run existing integration tests for HTTP MCP startup (tests/agent/test_http_lifecycle_integration.py) and confirm they pass.
- ruff + mypy on the touched file.

## Documentation Impact
None required.

## Out of Scope
- Any change to health-check logic, timeouts, or the HealthChecker module.
- Refactoring other lifecycle methods.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Only edit scripts/agent/http_lifecycle.py: remove the unused outer AsyncClient in `start()` and the unused `client` parameter of `_health_poll_until_ready()`. Do not alter polling/timeout/interrupt behavior. Verify with the existing integration tests.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-065632
- **Related target files**: scripts/agent/http_lifecycle.py
