# Add timeout to CLIView.run_in_executor input() call

## Summary

CLIView.read_multiline calls loop.run_in_executor(None, lambda: input("... ")). With executor=None, this uses the default ThreadPoolExecutor. If the executor is busy or full, input() will block indefinitely waiting for a thread slot. There's no timeout on this operation.

## Background

read_multiline handles multiline input continuation in the REPL. It delegates input() to a thread pool to avoid blocking the event loop.

## Problem

During shutdown, if the executor is saturated, the multiline continuation hangs forever. Users cannot interrupt the REPL during this state.

## Reason for Change

Operational reliability: users should always be able to interrupt the REPL, even during shutdown when resources may be constrained.

## Implementation Intent

Option A: Pass a dedicated ThreadPoolExecutor with bounded queue size and implement a timeout wrapper around run_in_executor. Option B: Use asyncio.to_thread() with a timeout parameter (Python 3.9+). Option C: Check executor status before delegating and fall back to synchronous input if unavailable. Choose the approach that best balances safety with minimal behavioral change.

## Target Files or Areas

- scripts/agent/cli_view.py

## Required Changes

- Add timeout protection to the run_in_executor call in read_multiline
- Handle TimeoutError appropriately (e.g., raise KeyboardInterrupt or log warning)
- Consider adding executor lifecycle management

## Constraints

- Must not change the readline/multiline display behavior
- Must preserve the non-blocking event loop design

## Out of Scope

- Rewriting the entire CLI presentation layer
- Adding new configuration options

## Dependencies

N/A: none

## Acceptance Criteria

- [ ] Multiline input times out after configurable period instead of hanging
- [ ] Timeout is handled gracefully (KeyboardInterrupt or logged warning)
- [ ] No regression in normal multiline input behavior

## Testing Expectations

- Unit test: verify timeout fires when executor is full
- Manual test: interrupt REPL during multiline input

## Documentation Impact

Document the timeout behavior in the read_multiline docstring.

## Priority

Medium

## AI Implementation Instruction

Add timeout only to the run_in_executor call in read_multiline. Do not rewrite the CLI layer. Preserve readline/multiline display behavior. Stop and report if the executor lifecycle is unclear.
