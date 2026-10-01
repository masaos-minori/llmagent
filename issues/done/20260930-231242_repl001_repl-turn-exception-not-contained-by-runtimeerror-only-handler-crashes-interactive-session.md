# REPL turn exception not contained by RuntimeError-only handler crashes interactive session

## Priority
Medium

## Summary
The agent REPL contains turn-execution exceptions only within a very narrow band: `_repl_loop` catches `TimeoutError` alone, `ReplInputLoop.run()` catches `RuntimeError` alone, and `WorkflowEngineAdapter.execute_turn` handles only three specific workflow errors. Any exception of another type that escapes a turn propagates out of `asyncio.run(AgentREPL().run())` and terminates the entire interactive REPL with a traceback, instead of being reported and the loop continuing.

## Background
Found during an adversarial review of `scripts/agent/repl_input_loop.py` covering agent REPL operation processing. User input flows `ReplInputLoop._dispatch_line` -> `Orchestrator.handle_turn` -> `WorkflowEngineAdapter.execute_turn` -> `WorkflowEngine`. Each layer has its own error handling, but every layer narrows the set of caught exception types rather than widening it, so the effective containment is the intersection of those narrow sets.

## Problem
- `scripts/agent/repl_input_loop.py:_repl_loop` awaits the dispatch task and catches only `TimeoutError` locally (`except TimeoutError`).
- `scripts/agent/repl_input_loop.py:run()` wraps `await self._repl_loop()` in `try/except RuntimeError` only, writing a fatal message and re-raising.
- `scripts/agent/workflow_engine_adapter.py:execute_turn` catches only `WorkflowPendingApprovalError`, `WorkflowHaltError`, and `WorkflowTimeoutError`; other exceptions are re-raised by `WorkflowEngine.run()`.
- `scripts/agent/repl.py:run()` calls `self._input_loop.run(...)` with no surrounding `try/except`, and `main()` runs it directly under `asyncio.run(...)`.

Result: a turn that raises any exception other than `RuntimeError` (or `TimeoutError`) is never surfaced through `view.write_fatal`/`write_warning`; it reaches `asyncio.run()` and ends the whole session.

## Reason for Change
A single unexpected per-turn error currently costs the entire interactive session. Turn-level failures (a bad LLM response, an unhandled tool error, a transient transport fault) should be reported to the operator and the REPL should remain usable for the next command. Containment scoped to one exception type is fragile: adding any new exception type in the turn path silently removes REPL resilience with no warning.

## Implementation Intent
Add a per-turn exception safety net so that an exception escaping `handle_turn`/`_dispatch_line` is surfaced through the CLI view and the loop continues (unless a shutdown was requested). Prefer containing it in `_repl_loop` around the dispatch await, or in `run()` around `_repl_loop()`, without disturbing the existing shutdown-racing logic or the current `RuntimeError` fatal-write path. If the fix belongs in `WorkflowEngineAdapter.execute_turn`, convert unexpected exceptions into an error response/error_kind rather than letting them propagate, and document that contract. Keep the change minimal and localized to the turn-dispatch path.

## Target Files or Areas
- `scripts/agent/repl_input_loop.py` (`_repl_loop`, `run()`)
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn`) — only if the intended fix is to contain the exception at the adapter
- `tests/agent/test_repl_error_handling.py` (regression coverage)

## Required Changes
- Wrap the turn-dispatch await so a non-`RuntimeError`, non-`TimeoutError` exception is caught, written to the view as an error/warning, and does not abort the loop.
- Ensure the loop still exits cleanly when shutdown was requested.
- Add a regression test asserting that `handle_turn` raising a non-`RuntimeError` exception leaves the REPL responsive (waits for the next input) instead of raising out of the loop.

## Constraints
- Do not swallow `asyncio.CancelledError` as a handled turn error.
- Do not mask or bypass the existing `RuntimeError` fatal path or the `TimeoutError` shutdown-race path.
- Do not alter shutdown signaling, multiline continuation, or command routing outside the turn-dispatch path.

## Acceptance Criteria
- A turn that raises a non-`RuntimeError` exception is contained by the REPL loop, reported through the view, and the loop then waits for the next input.
- Shutdown behavior is unchanged: a shutdown request still terminates the loop.
- Existing REPL tests still pass.

## Testing Expectations
Unit test: mock `_orchestrator.handle_turn` to raise a non-`RuntimeError` exception (e.g. `ValueError`) and assert the loop does not propagate it and remains ready for the next input. Then run `tests/agent/test_repl*.py` in full and the affected lifecycle suites once after the fix.

## Documentation Impact
N/A: unless the turn-error-handling contract is documented elsewhere and now needs updating (Needs confirmation).

## Out of Scope
- Startup `session.start()` exception translation in `run()` (same narrow-catch pattern, but a startup-boundary concern, not REPL-operation processing).
- Input-coroutine cancellation on the shutdown-during-input path (separate finding, tracked independently).
- Any change to `WorkflowEngine` internals beyond the adapter's exception handling.

## Dependencies
N/A: none.

## Unresolved Questions
Which exception types actually escape `execute_turn` in practice (for example `LLMTransportError` or other non-transport faults)? Confirm by tracing `_process_turn` / `LlmTurnExecutor` before finalizing severity. The structural gap (containment limited to `RuntimeError` + three workflow errors) is certain regardless; this question determines how often it is reachable.

## AI Implementation Instruction
Make the smallest change that contains a turn-escaping exception and keeps the loop alive. Read `_repl_loop`, `run()`, and `execute_turn` first; decide whether the net belongs in the loop (surface via the view, continue unless shutting down) or in the adapter (convert to an error response). Never catch `CancelledError`. Add a regression test that drives a non-`RuntimeError` exception through `handle_turn` and asserts the REPL stays responsive. Do not touch shutdown racing, multiline, or command routing.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-231242
- **Related target files**: scripts/agent/repl_input_loop.py, scripts/agent/workflow_engine_adapter.py
