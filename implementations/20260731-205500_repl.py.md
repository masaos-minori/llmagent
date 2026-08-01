# Implementation Procedure: Comprehensive Resource Cleanup on System Shutdown

## Goal
Ensure all runtime resources are properly cleaned up during system shutdown, regardless of how shutdown is triggered.

## Scope
- **In scope**: `scripts/agent/repl.py`
- **Out of scope**: refactoring core agent logic, changing shutdown semantics.

## Assumptions
- Signal handlers correctly propagate shutdown requests to the event loop.
- A graceful timeout exists to prevent indefinite hangs during cleanup.

## Design decisions
- Implement explicit cancellation of all pending asynchronous tasks during shutdown.
- Ensure error-resilient cleanup by wrapping individual resource closures in `try/except` blocks.
- Use `asyncio.gather` with `return_exceptions=True` to allow multiple resources to attempt closure.

## Alternatives considered
- Hard exit via `sys.exit()` immediately upon signal (risks data corruption and unclosed handles).

## Implementation
- **Target file**: `scripts/agent/repl.py`
- **Procedure**:
  - Update `_close_resources` to identify and cancel all non-finished tasks in the current loop.
  - Add explicit cleanup calls for database sessions and any remaining open file descriptors.
  - Ensure `SIGINT` and `SIGTERM` handlers effectively trigger the full `_close_resources` sequence.
  - Log detailed information about which resources were successfully closed and which failed.
- **Method**: Asynchronous orchestration of resource teardown.
- **Details**: Utilize `asyncio.wait_for` to enforce strict timeouts on the entire shutdown sequence.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
Revert the updated `_close_resources` and signal handler logic to restore previous behavior.

## Validation plan
- **Integration tests**: Simulate `SIGINT` and `SIGTERM` signals and verify that all resources are released.
- **Resource leak detection**: Monitor open file descriptors and connection counts during repeated restart/shutdown cycles.

## Out of scope
N/A

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-070710_require.md
- Source plan: plans/20260731-085914_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-205500
- Related target files: scripts/agent/repl.py
