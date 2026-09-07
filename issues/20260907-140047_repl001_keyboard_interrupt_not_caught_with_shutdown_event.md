# KeyboardInterrupt during REPL input is not actually caught when a shutdown_event is configured

## Priority
High

## Summary
`ReplInputLoop._read_input()` (`scripts/agent/repl_input_loop.py`) has two code paths: one used
when `shutdown_event is not None` (wraps the input read in `asyncio.ensure_future()` and awaits
it via `asyncio.wait({input_coro, shutdown_coro}, ...)`), and a simpler `else` path (awaits
`loop.run_in_executor(...)` directly) used when no `shutdown_event` is configured. Both paths
contain an `except KeyboardInterrupt:` clause intended to treat Ctrl+C as a graceful end-of-input
signal (mirroring the adjacent `EOFError` handling). `tests/agent/test_repl.py`'s
`test_keyboard_interrupt_breaks_loop` exercises the `shutdown_event is not None` path (via
`_make_bare_repl()`, which always sets `repl._shutdown_event = asyncio.Event()`) and raises a real
`pytest`-session-aborting `KeyboardInterrupt` instead of passing — the exception propagates past
the `except KeyboardInterrupt:` clause at line 154 entirely.

## Background
`Explicit in code`: `scripts/agent/repl_input_loop.py`'s `_read_input()` (`if shutdown_event is
not None:` branch) wraps the input read as an independent Task: `input_coro =
asyncio.ensure_future(_input_task())`, then awaits completion via `asyncio.wait({input_coro,
shutdown_coro}, return_when=asyncio.FIRST_COMPLETED)`, and only afterward calls
`input_coro.result()` inside a `try/except KeyboardInterrupt:` block to retrieve the outcome.
CPython's `asyncio.tasks.Task.__step()` special-cases `(KeyboardInterrupt, SystemExit)`: when a
Task's own coroutine step raises one of these, the Task sets it as its exception **and
re-raises it immediately** through the event loop's callback machinery, rather than merely
storing it for later retrieval via `.result()`. Because `_input_task()` runs as its own
`ensure_future`-wrapped Task, a `KeyboardInterrupt` raised while it awaits
`loop.run_in_executor(...)` triggers this re-raise during the enclosing `asyncio.wait(...)` call
itself — before control ever returns to `_read_input()`'s own frame, and therefore before the
`except KeyboardInterrupt:` clause at line 154 (or the generic `except Exception:` at line 137,
which does not even match `KeyboardInterrupt` since it is a `BaseException`) gets a chance to run.
`Verified by test`: running `uv run pytest tests/agent/test_repl.py -q --timeout=10 -p no:randomly`
reproduces this — the test session aborts immediately with an uncaught `KeyboardInterrupt`
traceback rooted in `_input_task`'s `run_in_executor` call, rather than the test passing.

## Problem
- In production, whenever `shutdown_event` is configured (the path exercised by this test — the
  configuration used whenever graceful-shutdown coordination is wired up), a real Ctrl+C pressed
  while the REPL is waiting for input does not go through the intended graceful-handling path
  (`_abort_input()` + clean return). Instead, the exception propagates out of the event loop
  entirely, bypassing `ResourceShutdownCoordinator`-style graceful cleanup.
- The `else` branch (no `shutdown_event`) does not have this problem, since the input read there
  is awaited directly in the current coroutine's own frame (not wrapped in a separate Task), so
  its `except (EOFError, KeyboardInterrupt):` clause can catch the exception normally. This means
  the two branches have silently diverged in a safety-relevant way.
- This same defect makes `tests/agent/test_repl.py`'s test session for this exact test abort the
  entire pytest run early whenever it lands earlier in test execution order (this repository uses
  `pytest-randomly`), silently truncating the remainder of that run's results — which is how this
  defect was first noticed, as a full-suite run kept stopping partway through with no clear
  "session aborted" signal in a quick read of the tail output.

## Reason for Change
Ctrl+C during REPL input is one of the most common real-world interrupt scenarios. If it bypasses
the intended graceful-shutdown path when `shutdown_event` is configured, any coordinated cleanup
(flushing state, `ResourceShutdownCoordinator.close_resources()`, etc.) that depends on the REPL
loop exiting cleanly through `_abort_input()`'s path may not run, and the process may crash instead
of shutting down gracefully. Additionally, its side effect of terminating pytest sessions early
undermines confidence in every other test-suite report from a run that includes this test.

## Implementation Intent
Ensure `KeyboardInterrupt` raised while reading input is actually handled by the intended
graceful-shutdown path regardless of whether `shutdown_event` is configured. This likely requires
not relying on catching `KeyboardInterrupt` via a separate Task's `.result()` — since asyncio's
Task machinery re-raises `(KeyboardInterrupt, SystemExit)` before that point is ever reached —
and instead catching it at the point where it can actually still propagate through the current
coroutine's own frame (e.g. wrapping the `asyncio.wait(...)` call itself in the `try/except
KeyboardInterrupt:`, if CPython's Task semantics still allow that boundary to catch it; verify
this empirically with a minimal reproduction before assuming any specific fix works, given how
easy this exact case is to get wrong).

## Target Files or Areas
- `scripts/agent/repl_input_loop.py` (`_read_input()`, both branches — `if shutdown_event is not
  None:` primarily, but confirm the `else` branch's handling still holds after any refactor)
- `tests/agent/test_repl.py` (`test_keyboard_interrupt_breaks_loop`, and any sibling tests in the
  same class that share `_make_bare_repl()`'s always-set `shutdown_event`)

## Required Changes
- Fix `_read_input()`'s `shutdown_event is not None` branch so a `KeyboardInterrupt` raised during
  input reading is actually caught and routed through `_abort_input()` + a clean `return None`,
  matching the documented intent and the `else` branch's existing behavior.
- Confirm the fix with a reproduction that does not rely on `pytest`'s own top-level Ctrl+C
  handling — e.g. a minimal standalone `asyncio.run()` script — since `pytest-asyncio`'s task
  wrapping may itself interact with this in ways a test-only fix could mask.
- Re-run `tests/agent/test_repl.py` standalone and confirm the pytest session completes without
  the KeyboardInterrupt escaping (i.e., the full file's test count is reported, not truncated).

## Constraints
- Do not change `EOFError` handling, which already works correctly in both branches.
- Do not remove the intentional Ctrl+C-as-shutdown-signal behavior — the fix must still result in
  a clean, graceful exit, not merely suppress or re-swallow the exception silently.
- Must not change the `shutdown_coro`/`asyncio.wait` FIRST_COMPLETED race behavior for the
  legitimate shutdown-event-signaled case.

## Acceptance Criteria
- [ ] `uv run pytest tests/agent/test_repl.py -q -p no:randomly` completes without an uncaught
      `KeyboardInterrupt` aborting the session, and `test_keyboard_interrupt_breaks_loop` passes.
- [ ] A full `uv run pytest tests/` run (or any subset that happens to execute this test) no
      longer terminates early due to this specific defect.
- [ ] The fixed behavior is verified to actually route through `_abort_input()` (not merely avoid
      raising), by asserting on `_abort_input`/`_view.write_turn_end` having been invoked.

## Testing Expectations
Run `tests/agent/test_repl.py` in isolation (`-p no:randomly` to keep ordering deterministic while
verifying), and confirm no `KeyboardInterrupt` escapes; then run the broader
`tests/agent/` suite to confirm no other test relying on `shutdown_event`-path input handling
regresses.

## Documentation Impact
None expected — this is an internal async-handling correctness fix with no documented external
contract change, unless `repl_input_loop.py`'s module or class docstring specifically describes
the current (broken) Ctrl+C handling, in which case update it to match the corrected behavior.

## Out of Scope
- The `else` (no `shutdown_event`) branch's existing `KeyboardInterrupt` handling, which already
  works.
- Any change to `EOFError` handling.
- The broader test-suite regression tracked separately in
  `issues/20260907-140130_regress001_widespread_test_suite_drift.md` (this issue's early-session-
  abort side effect is one contributing factor to that regression's inflated/undercounted failure
  reports, but the underlying causes of the other ~579 failures are unrelated to this defect).

## Dependencies
N/A: none — self-contained to `repl_input_loop.py` and its direct test file. Related in theme
(graceful shutdown) to `issues/20260907-131840_rsc001b_lifo_order_does_not_satisfy_wal_precedence.md`
and `issues/20260907-131900_rsc002b_settlement_sleep_violates_no_regression_criterion.md`, but
those concern `ResourceShutdownCoordinator`'s internal task-cancellation ordering and settlement
wait, a different mechanism than this issue's `asyncio.ensure_future`/Task-boundary defect.

## Unresolved Questions
Whether the correct fix is to stop wrapping `_input_task()` in a separate Task at all (restructure
the FIRST_COMPLETED race some other way that keeps `KeyboardInterrupt` within the current
coroutine's own catchable frame), or whether there is a way to make the current two-Task
`asyncio.wait()` structure still catch it — this needs to be resolved empirically during
implementation, not assumed.

## AI Implementation Instruction
Before implementing, write a minimal standalone reproduction (not inside pytest) confirming
exactly where `KeyboardInterrupt` currently escapes to, since asyncio's Task/event-loop exception
semantics around `(KeyboardInterrupt, SystemExit)` are easy to misdiagnose from reading code alone.
Do not simply add another `try/except KeyboardInterrupt:` around the `asyncio.wait(...)` call
without first confirming empirically that this boundary can actually catch it, given the
`Task.__step()` re-raise behavior described in Background. If it cannot be caught at any boundary
within `_read_input()` as currently structured, report this back rather than guessing at a
restructure — a wrong fix here could look like it passes the specific unit test while still
failing to shut down gracefully on a real Ctrl+C.
