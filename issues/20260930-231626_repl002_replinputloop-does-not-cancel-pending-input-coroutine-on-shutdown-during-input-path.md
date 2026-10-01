# ReplInputLoop does not cancel pending input coroutine on shutdown-during-input path

## Priority
Low

## Summary
When a shutdown fires while the REPL is still reading a line of input, `ReplInputLoop._read_input` returns `None` and drops its reference to the input coroutine without cancelling it. The coroutine — running `input("> ")` inside the default executor — is left blocked until the user presses Enter/EOF or the event loop tears down.

## Background
During an adversarial review of `scripts/agent/repl_input_loop.py`, the shutdown-vs-input read race in `_read_input` was examined. When `shutdown_event` is set, `_shutdown_watcher` flips a `shutdown_done` flag; `_read_input` detects it and aborts the read. The design assumes the shutdown watcher also cancels the in-flight input task, but it does not.

## Problem
- `scripts/agent/repl_input_loop.py:_read_input` calls `self._abort_input()` (which sets `self._input_coro = None`) and returns `None` on the shutdown-done path, but never calls `input_coro.cancel()`.
- `scripts/agent/repl_input_loop.py:_shutdown_watcher` only sets the `shutdown_done` boolean; it does not cancel `input_coro`.
- The comment on the shutdown-done branch ("Cancellation handled by shutdown watcher") describes behavior that the code does not perform.

Result: the pending `input("> ")` task keeps running in the default executor after the loop has moved on. There is no correctness bug during normal shutdown (the loop ends), but a dangling executor thread persists until the user submits input or the process exits.

## Reason for Change
The misleading comment invites future readers to assume cancellation happens when it does not. Leaving the input task uncancelled also means the reference is lost, so nothing can ever cancel it even if a later change wanted to. Making the cancellation explicit removes ambiguity and closes the lifecycle gap.

## Implementation Intent
On the shutdown-done path in `_read_input`, explicitly cancel the pending `input_coro` (awaiting it under `try/except asyncio.CancelledError`) before returning `None`, rather than relying on the shutdown watcher or loop teardown. Keep `_shutdown_watcher` responsible only for the flag. Preserve EOF/Error/_InputAborted handling on the success path.

## Target Files or Areas
- `scripts/agent/repl_input_loop.py` (`_read_input`, `_shutdown_watcher`)

## Required Changes
- Cancel `input_coro` on the shutdown-done path in `_read_input` and await its completion.
- Correct the misleading comment so it reflects that `_read_input` performs the cancellation.
- Optionally add a regression test asserting that a shutdown during input read results in `input_coro` being cancelled.

## Constraints
- Do not change the shutdown-flag semantics or the success-path EOF/Error handling.
- Do not introduce a second source of truth for shutdown state; `shutdown_event` remains authoritative.

## Acceptance Criteria
- After a shutdown fires during an in-progress input read, the pending input coroutine is cancelled (not merely abandoned).
- The read returns `None` and the loop proceeds to shutdown as before.
- Success-path input reads (line returned, EOF, error, aborted) are unaffected.

## Testing Expectations
Unit test: start a read with a pending `input_coro`, fire the shutdown, and assert the coroutine is cancelled. Then run `tests/agent/test_repl*.py` once after the change.

## Documentation Impact
N/A: no external documentation references this internal cancellation flow.

## Out of Scope
- Per-turn exception containment (`repl001`).
- Startup `session.start()` exception translation.
- Any change to the shutdown-racing logic in `_repl_loop`.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the lingering executor thread causes any observable effect between shutdown and loop teardown in production (likely none). Confirmed by code structure; runtime observation not required for a Low fix.

## AI Implementation Instruction
In `_read_input`, on the shutdown-done branch, call `input_coro.cancel()` and await it (guarding `asyncio.CancelledError`) before returning `None`. Update the stale comment. Do not touch `_shutdown_watcher`'s flag logic or the success-path handling. Add a focused regression test if feasible.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-231626
- **Related target files**: scripts/agent/repl_input_loop.py
