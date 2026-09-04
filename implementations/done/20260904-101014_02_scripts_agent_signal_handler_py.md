# Implementation Procedure: Remove direct _input_coro.cancel() from signal handler

## Target file
- `scripts/agent/signal_handler.py`

## Source plan
- `plans/20260904-001051_ril001_plan.md`

## Related requirements
- REQ-RIL001-1: Only one cancellation path for _input_coro during shutdown

## Background
`SignalHandler._sigterm_handler` directly calls `self._input_coro.cancel()` (lines 49-57), creating a duplicate cancellation path alongside the shutdown watcher in `repl_input_loop.py`. This causes non-deterministic exception propagation.

## Adversarial Verification
- Plan claim "signal_handler.py:49-57 has _input_coro.cancel()" → Verified: lines 49-57 confirm `_sigterm_handler` calls `self._input_coro.cancel()` under guard conditions (not turn_active, coro exists, not done)
- Guard conditions checked: `not self._turn_active and self._input_coro is not None and not self._input_coro.done()` — these prevent cancellation during active turns
- No additional target files discovered during investigation

## Design decisions
- Remove the entire `_input_coro.cancel()` block from `_sigterm_handler` — the shutdown watcher in `repl_input_loop.py` will handle cancellation via `shutdown_event.set()`
- Preserve the `shutdown_event.set()` call — this is the key coordination point that triggers the shutdown watcher
- Preserve the `shutdown_requested` flag setting — required for graceful shutdown timeout logic

## Alternatives considered
- Replace `_input_coro.cancel()` with `shutdown_event.set()` only → rejected: this would require passing `_input_coro` reference to SignalHandler, coupling SignalHandler to ReplInputLoop internals
- Add a new method on SignalHandler to delegate cancellation → rejected: adds unnecessary indirection; shutdown_event.set() already achieves the goal

## Compatibility considerations
- Signal handler registration unchanged
- `shutdown_event.set()` behavior unchanged
- `shutdown_requested` flag setting unchanged
- Windows console control handler path unchanged

## Security considerations
- No security impact: cancellation logic change does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring the entire `_input_coro.cancel()` block (lines 49-57)
- No database schema changes, no config changes

## Method

### Step 1: Remove _input_coro.cancel() from _sigterm_handler

Change lines 49-57 from:
```python
            if (
                not self._turn_active
                and self._input_coro is not None
                and not self._input_coro.done()
            ):
                try:
                    self._input_coro.cancel()
                except RuntimeError:
                    pass
            logger.info("SIGTERM received; graceful shutdown initiated")
```
to:
```python
            logger.info("SIGTERM received; graceful shutdown initiated")
```

Rationale: Removing the entire `_input_coro.cancel()` block eliminates the duplicate cancellation path. The shutdown watcher in `repl_input_loop.py` will handle cancellation via `shutdown_event.set()`. The `logger.info()` call is preserved for observability.

### Step 2: Verify shutdown_event.set() is called before any async work

Confirm that `self._shutdown_event.set()` (line 48) executes synchronously before the `_input_coro.cancel()` block. This is critical because:
- `asyncio.Event.set()` wakes up all waiters immediately
- The shutdown watcher in `_read_input` will detect this and set `shutdown_done=True`
- Without this guarantee, there could be a window where signal handler returns before shutdown is coordinated

Verification: Line 48 confirms `set()` is called before the cancelled block at lines 49-57. After removal, this ordering remains intact.

### Step 3: Update class docstring

Update `SignalHandler.__init__` docstring (around line 24-28) to reflect the changed responsibility:

Change from:
```
    Encapsulates platform-specific signal handling for graceful shutdown.

    Encapsulates the signal registration logic extracted from AgentREPL.run().
```
to:
```
    Encapsulates platform-specific signal handling for graceful shutdown.

    Responsibilities:
      - Registering SIGTERM/SIGINT handlers on Unix (loop.add_signal_handler)
      - Registering Windows console control handler fallback
      - Setting shutdown_event to coordinate with ReplInputLoop shutdown watcher
```

Note: Removed "Cancelling input coroutine during shutdown" since this is now delegated to the shutdown watcher.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove _input_coro.cancel() from _sigterm_handler | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Eliminates duplicate cancellation path; single source via shutdown watcher |
| 2 | Verify shutdown_event.set() ordering | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Line 57 set() executes synchronously before removed block |
| 3 | Update class docstring | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Removed "cancelling input coroutine"; added shutdown_event coordination note |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
