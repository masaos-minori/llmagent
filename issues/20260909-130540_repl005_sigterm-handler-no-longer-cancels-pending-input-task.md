# SIGTERM handler no longer cancels the pending input task — deliberate design change or resource-leak regression?

## Priority
Medium

## Summary
`TestSigtermHandlerTurnActiveGuard::test_input_coro_cancelled_when_turn_not_active`
(`tests/agent/test_repl.py`) fails with `AssertionError: Expected 'cancel' to have been
called once. Called 0 times.` A prior refactor deliberately removed
`_input_coro.cancel()` from `SignalHandler._sigterm_handler()`, replacing it with
shutdown-event-based coordination — but neither the new handler nor
`ReplInputLoop`'s shutdown-watcher path actually cancels a task blocked on a real,
in-flight `input()` call. This may leave an orphaned executor thread after shutdown, or
may be an accepted design tradeoff — **this needs an owner/maintainer decision before
implementation**, not a mechanical test fix.

## Background
Commit `44d7f2e4f` ("refactor: improve agent resource lifecycle...") removed
`_input_coro.cancel()` logic from `SignalHandler._sigterm_handler()`
(`scripts/agent/signal_handler.py`), and updated the module's own docstring
responsibility line from "Cancelling input coroutine during shutdown" to "Coordinating
shutdown with ReplInputLoop via shutdown_event" — confirmed by direct diff inspection to
be a deliberate change, not an accidental deletion.

## Problem
In the new design, neither `SignalHandler._sigterm_handler()` nor
`ReplInputLoop._shutdown_watcher()` (`scripts/agent/repl_input_loop.py`) actually cancels
a task that is currently blocked reading real input via
`loop.run_in_executor(None, lambda: input("> "))`. `_read_input()`'s own comment
("Cancellation handled by shutdown watcher — do not cancel here") implies cancellation
was expected to happen somewhere in the shutdown-watcher path, but no code path
currently performs it. Concretely: if a SIGTERM arrives while the REPL is blocked
waiting for a line of real user input (not a mocked test scenario), the executor thread
running `input()` has no way to be interrupted — it can only complete when the
underlying OS-level `input()` call itself returns (e.g. real EOF, or the process being
killed outright), not via cooperative asyncio cancellation. Whether this is an accepted
consequence of the shutdown-event redesign (with some other mechanism, e.g. process
exit, expected to handle it) or an unaddressed gap is `Needs confirmation` — this issue
does not assert which.

## Reason for Change
If unaddressed, a SIGTERM during blocked input reading may not result in a clean,
timely shutdown of the input-reading thread specifically (though the rest of the
process may still exit via other means) — a resource-lifecycle question worth an
explicit decision rather than silently accepting the stale test's failure as "this test
is just outdated."

## Implementation Intent
**Do not implement a fix without first getting owner/maintainer input on which of these
applies:**
1. **Accepted design change**: the new shutdown-event-based coordination is
   sufficient in practice (e.g. because the process exits by another path shortly
   after, making the orphaned executor thread inconsequential) — in which case
   `test_input_coro_cancelled_when_turn_not_active` and its passing sibling
   `test_input_coro_not_cancelled_when_turn_active` describe removed/superseded
   behavior and should be rewritten or deleted to match the new intended contract,
   with a design note added explaining why cancellation is no longer performed here.
2. **Unaddressed resource-lifecycle gap**: the blocked input-reading thread should
   still be interruptible on shutdown — in which case a mechanism to actually cancel or
   otherwise unblock it needs to be (re)implemented, most likely by wiring
   `ReplInputLoop._shutdown_watcher()` (or a similar shutdown-observing coroutine) to
   call `.cancel()` on the tracked `_input_coro`/`_input_task` when it fires, then
   updating the test to match.

## Target Files or Areas
- `scripts/agent/signal_handler.py` (`SignalHandler._sigterm_handler()`) — reference;
  target only if option 2 is chosen
- `scripts/agent/repl_input_loop.py` (`ReplInputLoop._shutdown_watcher()`,
  `_read_input()`) — reference; target only if option 2 is chosen
- `tests/agent/test_repl.py`
  (`TestSigtermHandlerTurnActiveGuard::test_input_coro_cancelled_when_turn_not_active`,
  `::test_input_coro_not_cancelled_when_turn_active`) — target regardless of which
  option is chosen

## Required Changes
Deferred until the Unresolved Questions below are answered by an owner/maintainer — do
not implement either option speculatively.

## Constraints
Do not implement a fix for this issue without an explicit decision on which of the two
Implementation Intent options applies — this is the primary constraint distinguishing
this issue from a routine stale-test fix.

## Acceptance Criteria
- [ ] An owner/maintainer has explicitly confirmed whether the shutdown-event-only
  coordination (no task cancellation) is an accepted design tradeoff or a gap requiring
  a fix
- [ ] If accepted: `TestSigtermHandlerTurnActiveGuard`'s tests are updated to match the
  confirmed current contract (rewritten or removed, with the design rationale recorded)
- [ ] If a gap: the pending input task is actually cancelled/unblocked on shutdown, and
  the existing tests pass against the corrected behavior
- [ ] Either way, `uv run pytest "tests/agent/test_repl.py::TestSigtermHandlerTurnActiveGuard" -q`
  passes and reflects the confirmed, current intended behavior

## Testing Expectations
- `uv run pytest "tests/agent/test_repl.py::TestSigtermHandlerTurnActiveGuard" -q` —
  must pass against whichever contract is confirmed correct
- If a fix is implemented (option 2): a manual or scripted check confirming a SIGTERM
  delivered while blocked on real input reading results in the process (or at minimum,
  the input-reading task) exiting promptly, not just via unrelated process termination

## Documentation Impact
If option 1 (accepted design change) is confirmed: document the rationale in
`scripts/agent/repl_input_loop.py`'s or `signal_handler.py`'s module docstring (already
partially updated by `44d7f2e4f`) and, if a matching `docs/05_agent_*` row exists per
`docs/00_index.md`'s task-scope mapping, note the current shutdown-coordination
contract there. If option 2 (gap): document the restored cancellation mechanism in the
same locations once implemented.

## Out of Scope
- `TestGetWorkflowStatus`'s 2 failures — tracked separately as `repl002`.
- `TestPersistSessionDiagnostics`'s 2 failures — tracked separately as `repl003`.
- `TestRunSqliteErrorMessage`'s 2 failures — tracked separately as `repl004`.
- Any broader redesign of shutdown coordination beyond this specific
  input-task-cancellation question.

## Dependencies
N/A: none. Discovered while investigating `test_repl.py`'s post-`repl001`-fix remaining
failures — independent of that fix. Related in theme (graceful shutdown) to
`repl001`'s own fixed `KeyboardInterrupt`-escape defect, but a distinct mechanism
(cooperative task cancellation vs. `Task.__step()`'s exception-propagation special
case).

## Unresolved Questions
Whether the removal of `_input_coro.cancel()` from `_sigterm_handler()` in `44d7f2e4f`
was intended to leave blocked-input-thread cancellation permanently unhandled (accepted
tradeoff) or was an oversight expecting some other, not-yet-implemented mechanism to
cover it (gap) — **this must be answered by an owner/maintainer before implementation**,
not inferred from the commit message alone, since the message describes what changed
but not why the cancellation specifically was dropped rather than relocated.

## AI Implementation Instruction
Do not implement a fix for this issue's Required Changes until the Unresolved Question
is explicitly answered — surface the question to a maintainer and stop. If asked only
to "investigate further," re-read `44d7f2e4f`'s full diff and any linked
issue/plan/PR discussion for stated rationale before escalating, but do not guess at an
implementation in the meantime.
