# Sync SQLite writes block event loop

## Priority
Medium

## Summary
Async functions in the turn-execution path call synchronous SQLite-backed diagnostic writes directly, with no executor boundary: `DiagnosticStore.save()` and its siblings (`save_partial_completion`, `save_transport_failure`, `save_serialization_event`) block the asyncio event loop thread for the duration of a SQLite transaction. Route these calls through `asyncio.to_thread` (or an async wrapper). Session message persistence is no longer part of this issue.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's core turn-execution loop, checked against the project's constraint "in `async def` functions, never introduce blocking I/O". A later re-verification found that assistant and tool-message persistence moved to `scripts/agent/turn_persistence.py`, which already wraps its writes in `asyncio.to_thread` (`save`, `save_many`, `replace_messages`, `delete_messages_from`); `llm_turn_runner.run()` no longer calls `ctx.session.save("assistant", ...)`, and the remaining `ctx.session.save_many([])` in `tool_runner.py` is a no-op on an empty list.

## Problem
`DiagnosticStore.save()` (`scripts/agent/diagnostic_store.py`) opens a `SQLiteHelper` connection, executes an `INSERT` and commits synchronously; its siblings are synchronous too. They are called directly from async code in three places: `LLMTurnRunner._handle_llm_error` in `llm_turn_runner.py` (`diagnostics.save`, `save_partial_completion`), `tool_runner.py` (`save_transport_failure`), and `ToolLoopGuard._save_guard_hint` in `tool_loop_guard.py`. `_save_guard_hint` is invoked from the synchronous `check_*` methods, so wrapping it requires an async variant or a change to its callers.

## Reason for Change
Under disk or WAL lock contention these blocking calls stall the whole event loop, delaying scheduled callbacks including the signal-handler callback and the spinner or progress UI. They run on error paths, so the effect is intermittent.

## Implementation Intent
Route the diagnostic writes from async code through `asyncio.to_thread`, or provide async wrappers, so a SQLite transaction never blocks the loop. For `_save_guard_hint`, add an async path at the async call sites or make the guard checks async, whichever is smaller.

## Target Files or Areas
- `scripts/agent/llm_turn_runner.py` (`_handle_llm_error`)
- `scripts/agent/tool_runner.py` (`_record_transport_failure`)
- `scripts/agent/tool_loop_guard.py` (`_save_guard_hint` and the `check_*` callers)
- `scripts/agent/diagnostic_store.py`

## Required Changes
- Wrap the diagnostic writes in `_handle_llm_error` and `_record_transport_failure` in `asyncio.to_thread` (or an async wrapper).
- Provide an async path for `_save_guard_hint` and update its callers.
- Add a test asserting the event loop remains responsive (a concurrently scheduled callback fires on time) while a diagnostic save is in flight, using a slow stub for the underlying SQLite call.

## Constraints
- Do not change `DiagnosticStore`'s own synchronous implementation or SQL; only how it is invoked from async code.
- Preserve the ordering guarantee that a diagnostic save completes before the turn proceeds past the point it is currently called.

## Acceptance Criteria
- No `async def` function in the turn-execution path blocks the event loop thread for a diagnostic SQLite write.
- A concurrently scheduled event-loop callback is not measurably delayed by an in-flight diagnostic save under the added test.

## Testing Expectations
Add a test using a monkeypatched slow save to assert the event loop stays responsive. Run the tests for `llm_turn_runner`, `diagnostic_store` and `tool_loop_guard`, plus the `turn_persistence` tests if present, after the change.

## Documentation Impact
N/A: no operator-facing documentation describes this call path's concurrency behavior today.

## Out of Scope
- `AgentSession`/`turn_persistence` message writes (already off the loop).
- `DiagnosticStore`'s SQL schema or transaction logic.

## Dependencies
Related to `issues/20261101-111720_diagstore001_diagnostic-save-crashes-turn.md`: both change the diagnostic save call sites (`ToolLoopGuard._save_guard_hint`, `LLMTurnRunner._handle_llm_error`) and should be planned together; that issue wraps the saves against runtime errors, this one moves them off the event loop. The related `walsleep001` issue was closed because `WalCheckpointManager` already runs its steps on a worker thread.

## Unresolved Questions
N/A: none; the direct calls were confirmed by reading the files listed above.

## AI Implementation Instruction
Wrap only the identified diagnostic call sites; do not change the underlying synchronous implementations. Confirm the turn still waits for each save to complete. Add the responsiveness test described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180333
- **Related target files**: scripts/agent/llm_turn_runner.py, scripts/agent/tool_runner.py, scripts/agent/diagnostic_store.py, scripts/agent/tool_loop_guard.py
