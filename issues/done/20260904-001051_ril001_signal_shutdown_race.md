# Investigate signal handler + shutdown watcher race condition in REPL input loop

## Summary

During _read_input, a _shutdown_watcher task waits on shutdown_event. When SIGINT/SIGTERM arrives, the signal handler cancels _input_coro directly. But _shutdown_watcher may ALSO be trying to cancel input_coro via asyncio.wait pending cleanup. The double-cancellation of _input_coro is harmless individually, but the order matters for which exception propagates from input_coro.result().

## Background

repl_input_loop.py has two concurrent paths that can cancel _input_coro: the signal handler (signal_handler.py:49-57) and the shutdown watcher (repl_input_loop.py:110-134). Both use asyncio.Task.cancel().

## Problem

Non-deterministic exception propagation: depending on timing, different CancelledError sources propagate through input_coro.result(), making debugging difficult and potentially masking the actual shutdown cause.

## Reason for Change

Debuggability concern: when shutdown happens, the user sees inconsistent error messages depending on which cancellation path won the race.

## Implementation Intent

Option A: Have only ONE source of cancellation — either the signal handler OR the shutdown watcher, not both. Use shutdown_event to coordinate. Option B: Capture the cancellation source in a shared variable and include it in the error message. Option C: Suppress CancelledError from result() and handle shutdown uniformly regardless of source. Choose the approach that best balances simplicity with correctness.

## Target Files or Areas

- scripts/agent/repl_input_loop.py
- scripts/agent/signal_handler.py

## Required Changes

- Eliminate duplicate cancellation paths or unify them under a single coordinator
- Ensure consistent error reporting regardless of shutdown trigger
- Document the coordination mechanism

## Constraints

- Must not change the shutdown semantics (SIGTERM/SIGINT still triggers shutdown)
- Must not increase shutdown latency

## Out of Scope

- Adding new signal handlers
- Changing the shutdown timeout behavior

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Only one cancellation path for _input_coro during shutdown
- [ ] Consistent error message regardless of shutdown trigger
- [ ] No regression in shutdown timing

## Testing Expectations

- Manual test: send SIGINT/SIGTERM during active input, verify consistent behavior
- Race condition stress test: repeated rapid shutdowns

## Documentation Impact

Document the shutdown coordination mechanism in the class docstring.

## Priority

Low

## AI Implementation Instruction

Unify the cancellation paths only. Do not change shutdown semantics or timeouts. Preserve existing signal handler behavior. Stop and report if the coordination intent is unclear from context.
