# Multiline input timeout crashes REPL

## Priority
High

## Summary
`CLIView.read_multiline()` raises a raw `KeyboardInterrupt` when a multiline continuation (a line ending in `\`) sits idle for 30 seconds. The raise happens inside the `except TimeoutError` clause, so it is not caught by the sibling `except (EOFError, KeyboardInterrupt)` clause, and nothing further up the call chain catches it either: it crashes the whole REPL process with a raw traceback. Return gracefully instead of raising.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's core input/turn-execution loop (`scripts/agent/cli_view.py`, `scripts/agent/repl_input_loop.py`).

## Problem
`scripts/agent/cli_view.py::read_multiline` has an `except TimeoutError:` branch that logs "Multiline input timed out" and then does `raise KeyboardInterrupt` (its own docstring documents this). The raise is inside the `except TimeoutError` clause of the same `try`, so it propagates out of `read_multiline()` instead of being caught by the sibling `except (EOFError, KeyboardInterrupt)` clause. The call site, `scripts/agent/repl_input_loop.py::_read_input`, calls `read_multiline` outside any `try` (its `_InputAborted` conversion wraps only the first-line read); `ReplInputLoop._repl_loop` handles `TimeoutError`, `ConversationPersistenceError` and `Exception`, and a raw `KeyboardInterrupt` is a `BaseException`, so it reaches `asyncio.run()` uncaught. Note: an earlier version of this issue also described a starved single-worker `ThreadPoolExecutor`; that no longer exists. `CLIView` now reads stdin through `StdinReader` (`scripts/agent/stdin_reader.py`), a daemon thread with one outstanding request, so there is no permanent starvation (`Explicit in code`).

## Reason for Change
This is reachable by ordinary user hesitation: a user who types a line ending in `\` and pauses for 30 seconds or more triggers an unhandled crash that bypasses the graceful-shutdown and signal-handling machinery built elsewhere in this codebase.

## Implementation Intent
On `TimeoutError`, do not raise `KeyboardInterrupt`; return the already-accumulated `parts` (the same graceful-degradation pattern used for `EOFError` in the sibling clause), and confirm that a following `read_multiline()` still works through `StdinReader` after the abandoned read.

## Target Files or Areas
- `scripts/agent/cli_view.py` (`CLIView.read_multiline`)
- `scripts/agent/stdin_reader.py` (read-only reference for the pending-read behavior)
- `tests/agent/` (find the existing test module for `cli_view`; none named `test_cli_view*.py` was found)

## Required Changes
- Change the `except TimeoutError` branch to return the accumulated `parts` instead of raising `KeyboardInterrupt`.
- Verify what a later read does when the timed-out `StdinReader.read` request is still pending (`wait_for` cancels the wrapped future; confirm no `a stdin read is already pending` error follows) and fix it only if it fails.
- Add a regression test asserting that a multiline-input timeout returns gracefully (no exception propagates) and that a subsequent `read_multiline()` call still succeeds.

## Constraints
- Do not change the 30-second timeout value itself.
- Preserve existing behavior for the `EOFError`/`KeyboardInterrupt` (real Ctrl+C/Ctrl+D) branch.
- Do not change `read_multiline()`'s return type/contract beyond this graceful-degradation path.

## Acceptance Criteria
- A multiline-input timeout no longer crashes the process; `read_multiline()` returns the partial input instead.
- A subsequent call to `read_multiline()` after a timeout succeeds.
- Real Ctrl+C/Ctrl+D handling during multiline input is unaffected.

## Testing Expectations
Unit test simulating a timeout on the stdin read, asserting `read_multiline()` returns instead of raising, and a follow-up call still gets input. Run the tests for `cli_view` and `tests/agent/test_repl_input_loop.py` after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this timeout behavior today.

## Out of Scope
- `ReplInputLoop`'s own shutdown-event wiring (tracked separately).
- Any change to the multiline-continuation syntax (trailing `\`) itself.

## Dependencies
N/A: none.

## Unresolved Questions
- Whether the abandoned `StdinReader.read` request interferes with the next read: `Needs confirmation` (to be settled by the regression test).

## AI Implementation Instruction
Change only the `except TimeoutError` branch's behavior (return instead of raise) and add the regression test; do not touch the `EOFError`/`KeyboardInterrupt` branch or the success path.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180327
- **Related target files**: scripts/agent/cli_view.py
