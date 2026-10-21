# Session persistence is skipped when startup fails, because it is reached only through the input loop

## Priority
Medium

## Summary
Make session persistence run on every exit path of `AgentREPL.run()`, in the same bracket as resource
shutdown, instead of only when the input loop was entered.

## Background
`AgentREPL._persist_after_loop()` persists session memories and diagnostics
(`scripts/agent/repl.py:105-108`). It is passed as a callback argument to the input loop
(`repl.py:157-160`), and `ReplInputLoop.run()` invokes it in its own `finally`
(`scripts/agent/repl_input_loop.py:111-115`). `AgentREPL.run()` wraps the whole session in one `try:` whose
`finally` calls only `close_resources()` (`repl.py:127-162`), with the deliberate comment at `:124-126` that
cleanup must run "on every exit path (startup failure or interrupt, normal exit) but never ahead of the input
loop".

## Problem
When `startup.run()` raises — a configuration error, an MCP startup failure, or `StartupInterrupted` — the
input loop is never entered (`repl.py:144` is not reached), so its `finally` never runs and neither
`persist_session_memories()` nor `persist_session_diagnostics()` is called. Resource shutdown still runs.
The asymmetry is visible in this environment: recent startup attempts ended with a FATAL
`mcp_tool_discovery` result before the REPL was reached, so whatever the startup path had already written to
in-memory session state was never persisted. Two related gaps:
- `_persist_after_loop` is invoked from a bare `finally` with no `except`, so a persistence failure on the
  normal path propagates out of `run()` and is not reported as a persistence failure. Needs-confirmation: the
  internal error handling of `SessionPersister` was not audited.
- Whether startup work (for example memory ingestion during startup) is expected to be persisted on a failed
  startup is not stated anywhere in code or docs.

## Reason for Change
The persistence step is the only place session memories and diagnostics reach the session DB. Making it
reachable from exactly one code path means any startup failure silently discards that state, while the DB
checkpoint for the same session still runs.

## Implementation Intent
Own the shutdown sequence in `AgentREPL.run()`: persist first, then close resources, on all paths, with each
step reporting its own failure.

## Target Files or Areas
- `scripts/agent/repl.py` (`run`, `_persist_after_loop`)
- `scripts/agent/repl_input_loop.py` (`run`, `persister_callback` parameter)
- `scripts/agent/session_persister.py` (reference)

## Required Changes
- Decide explicitly whether persistence must run after a failed startup, and encode that decision in one
  place rather than through a callback that happens to be nested inside the input loop.
- If persistence must run on all paths, move the call into `AgentREPL.run()`'s bracket before
  `close_resources()`, and remove the `persister_callback` indirection.
- Report persistence failures through the CLI view with a non-fatal severity, and keep them from masking the
  original startup error.
- Document the intended order (persist → checkpoint → close services) and why that order is required.

## Constraints
- Persistence must not run after `close_resources()` closes the shared HTTP client — that ordering constraint
  is the reason the current nesting exists.
- `ReplInputLoop.run(on_startup, persister_callback)` is an existing contract used by `repl.py:157-160` and by
  tests; changing it must be done together with `tests/agent/test_repl.py`.
- A startup failure must not be replaced by a secondary persistence error.
- Do not create a session row or session DB write where no session was created.

## Acceptance Criteria
- For a forced startup failure, the chosen behavior (persist or deliberately skip) is asserted by a test and
  stated in a docstring and in `docs/`.
- On the normal exit path, persistence still runs before `close_resources()`, in that order.
- A persistence failure produces a distinguishable non-fatal message and does not hide the startup error.

## Testing Expectations
- Regression test: `AgentREPL.run()` with `startup.run()` stubbed to raise, asserting the persistence
  decision (either a recorded skip or an actual persist call) — assert on the documented behavior, not on
  incidental calls.
- Ordering test: assert persist is called before `close_resources()` on the normal path.
- `uv run pytest tests/agent/test_repl.py -q` and the full `uv run pytest tests/agent -q`.

## Documentation Impact
Document the shutdown sequence as an ordered contract (what is persisted, what is closed, in which order, on
which exit paths) in the REPL/operations docs, and record whether a failed startup persists state as a Known
Issue or by design.

## Out of Scope
- The persistence content itself (what memories/diagnostics are written).
- WAL checkpoint bounds (`shutdown001`).
- Signal handling (`repl001`).

## Dependencies
- `repl003` provides the wiring-level test harness needed to assert this reliably.

## Unresolved Questions
- Should a failed startup persist anything at all? Needs confirmation; the current code neither intends nor
  documents a choice.
- Should `persister_callback` remain a parameter of `ReplInputLoop.run()`? Needs a design decision.

## AI Implementation Instruction
Make the shutdown bracket explicit in one function instead of relying on nested `finally` blocks. State the
ordering requirement in code comments that match the tests.

## Traceability
- **Workflow phase**: `python-code-review` (startup/shutdown lifecycle review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl.py`, `scripts/agent/repl_input_loop.py`,
  `scripts/agent/session_persister.py`
