# Implementation Procedure: Ensure Signal Handlers Installed from Main Thread in HTTP Lifecycle

## Goal
Ensure that all `signal.signal()` calls in `HttpServerLifecycleManager` are executed on the main thread to prevent potential race conditions and compliance issues.

## Scope
- `scripts/agent/http_lifecycle.py`

## Assumptions
- `signal.signal()` must be called from the main thread.
- `HttpServerLifecycleManager.shutdown_all` is an `async` method that might be called from within an event loop, potentially making its execution context sensitive to signal handler modifications.

## Design decisions
- Audit `HttpServerLifecycleManager.shutdown_all` for any direct calls to `signal.signal`.
- Use `loop.call_soon_threadsafe` to schedule `signal.signal` calls if they are being executed from a context that is not guaranteed to be the main thread.

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. Locate the block in `HttpServerLifecycleManager.shutdown_all` that manages the `SIGINT` handler (lines 458-469).
2. Wrap the `signal.signal(signal.SIGINT, ...)` calls to ensure they are scheduled on the main thread using `asyncio.get_running_loop().call_soon_threadsafe(...)` if necessary, or ensure the caller guarantees main-thread execution.
3. Verify that the original handler is restored correctly even if an exception occurs.

### Method
Code modification and concurrency verification.

### Details
The current implementation of `shutdown_all` modifies the global `SIGINT` handler to prevent interruption during cleanup. Because this method is `async` and may be invoked from various parts of the lifecycle manager, there is a risk that `signal.signal` is called from a thread other than the main thread, which is prohibited. Ensuring these calls are dispatched to the main thread via the event loop's thread-safe mechanisms will improve robustness.

## Compatibility considerations
- No negative impact on Unix-like systems; the behavior remains functionally identical but more robust.

## Security considerations
- N/A

## Rollback considerations
- Revert the changes to how `SIGINT` is handled in `shutdown_all`.

## Validation plan
- Perform stress tests on the HTTP server startup/shutdown cycle to ensure no `ValueError` is raised due to illegal signal handler registration.
- Verify that `Ctrl+C` still triggers the intended graceful shutdown sequence.

## Out of scope
- N/A

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-0754_require.md
- Source plan: plans/20260731-090405_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-200505
- Related target files: scripts/agent/http_lifecycle.py
