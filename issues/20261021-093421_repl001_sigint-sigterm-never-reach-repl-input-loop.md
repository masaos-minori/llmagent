# REPL ignores Ctrl-C and SIGTERM: the shutdown event never reaches the input loop

## Priority
High

## Summary
Make `ReplInputLoop` share the same shutdown event that `SignalHandler` and `StartupOrchestrator`
receive, so that Ctrl-C/SIGTERM actually interrupts the REPL, and so that the existing
signal-coordinated machinery in `repl_input_loop.py` becomes reachable instead of dead code.

## Background
`ReplInputLoop` was extracted from `repl.py` together with its shutdown-race machinery
(`_shutdown_watcher`, the `_InputAborted` sentinel, the bounded `asyncio.wait_for`). Only
`SignalHandler` has a `set_shutdown_event()` rebinding hook (`scripts/agent/signal_handler.py:136-138`);
`ReplInputLoop` has none, and `repl.py` builds it once, in `__init__`, before the event exists.
`scripts/agent/repl.py:144` re-binds `_cmds`/`_orchestrator` after startup, and
`tests/agent/test_repl.py:712-730` (`TestRunBindsStartupResultsToInputLoop`) exists specifically to
guard that wiring — no equivalent guard exists for the shutdown event.

## Problem
- `repl.py:82` sets `self._shutdown_event = None`; `repl.py:85` passes that `None` into
  `ReplInputLoop(self._ctx, self._view, self._shutdown_event)`; `repl.py:113-114` creates the real
  `asyncio.Event` afterwards and re-binds it only on `self._signal`. `ReplInputLoop._shutdown_event`
  stays `None` for the whole session (verified: attribute is `None` after `run()` is entered).
- Consequence 1 — the prompt is uninterruptible. `repl_input_loop.py:138-139` selects the plain
  `run_in_executor(None, input)` branch, so the shutdown-watcher/cancellation path never runs.
  `SignalHandler` replaces the default SIGINT handler (`signal_handler.py:61-63`), so no
  `KeyboardInterrupt` reaches the main thread and the worker blocked in `input()` keeps reading.
  Observed behavior: after Ctrl-C the loop keeps prompting; submitting an empty line re-prompts
  (`_repl_loop` `if not line: continue`), and only a subsequent non-empty line makes the loop exit.
- Consequence 2 — a running turn is never bounded. `repl_input_loop.py:288-297` computes
  `timeout=self._GRACEFUL_TIMEOUT_S` only when `ctx.conv.shutdown_requested` is already true, which
  `_should_exit` (`:243`) has just excluded. A signal arriving during a turn therefore produces
  `timeout=None` and the turn runs to completion; a hung turn can only be escaped with SIGKILL.
- Consequence 3 — a forced kill skips graceful shutdown. `close_resources()` (`repl.py:161-162`) and
  `_persist_after_loop` (`repl.py:157-160`, `repl_input_loop.py:111-115`) run only if `run()`
  returns. The MCP subprocess servers are started with `start_new_session: True`
  (`scripts/agent/http_lifecycle_subprocess_launcher.py:99`) in HTTP/subprocess mode
  (`scripts/agent/startup_mcp_starter.py:66-69`), so they are not signalled with the REPL and are
  left running as orphans when the operator falls back to `kill -9`.
- `deploy/start_agent.sh:195` instructs the operator "Ctrl+C で停止", and
  `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:38,43,49` states that Ctrl-C terminates the
  REPL like EOF and that a running turn is awaited for a bounded grace period. Neither matches the
  implementation.

## Reason for Change
Ctrl-C is the primary exit interaction for this REPL, and the operator-facing instruction in
`start_agent.sh` is currently wrong. Graceful shutdown (WAL checkpoint, session persistence, MCP
termination) is silently skipped whenever the operator gives up and force-kills the process.

## Implementation Intent
Deliver one shared shutdown event to every consumer of shutdown signaling. Choose one owner for the
event and construct `ReplInputLoop` after it exists (or add a `set_shutdown_event()` hook to
`ReplInputLoop` and call it at the same place `SignalHandler`'s is called, `repl.py:113-114`), so the
existing input-cancellation and mid-turn race paths become live. Keep `SignalHandler` as the only
signal entry point.

## Target Files or Areas
- `scripts/agent/repl.py` (`__init__`, `run()` startup block)
- `scripts/agent/repl_input_loop.py` (`__init__`, `_read_input`, `_repl_loop`)
- `scripts/agent/signal_handler.py` (setter contract only)
- `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`, `deploy/start_agent.sh`

## Required Changes
- Pass the same `asyncio.Event` instance to `ReplInputLoop` that `SignalHandler` and
  `StartupOrchestrator` receive; remove the permanently-`None` field or make it explicit.
- Ensure a signal delivered while the prompt is waiting aborts the pending input read and ends the
  loop (the `_InputAborted` / `_abort_input` path) rather than waiting for user input.
- Ensure a signal delivered during a turn cancels the in-flight dispatch and is bounded by
  `_GRACEFUL_TIMEOUT_S`, with `_log_graceful_shutdown_timeout()` reachable when the bound is exceeded.
- Decide and state the intended difference (if any) between SIGINT and SIGTERM handling;
  `signal_handler.py:61-63` currently registers one handler documented as SIGTERM-only for both.
- Correct `deploy/start_agent.sh`'s operator instruction and the doc claims listed above.

## Constraints
- `loop.add_signal_handler()` only works in the main thread and raises `NotImplementedError` on
  Windows; the existing fallback path (`signal_handler.py:64`) must keep working.
- `asyncio.run()` shuts down the loop's default executor when `run()` returns; a read still blocked in
  `input()` delays exit (see `repl002`). The two must be fixed consistently.
- `/exit`, Ctrl-D (EOF), and multi-line continuation behavior must stay unchanged.
- Do not change the public `ReplInputLoop.run()` signature used by `repl.py:157-160` unless the call
  site is updated in the same change.

## Acceptance Criteria
- `ReplInputLoop._shutdown_event` is the same object as `SignalHandler._shutdown_event` after
  `AgentREPL.run()` starts (assert identity, not truthiness).
- Sending SIGINT or SIGTERM while the REPL is waiting at the prompt ends the loop within the graceful
  bound, without requiring any further keyboard input.
- Sending SIGINT or SIGTERM during a turn stops that turn within `_GRACEFUL_TIMEOUT_S` and emits the
  graceful-timeout warning if the bound is exceeded.
- `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` and `deploy/start_agent.sh` describe the
  behavior the tests assert.

## Testing Expectations
- Regression test that drives the real wiring: construct `AgentREPL()` and, with startup and the input
  read stubbed, assert `repl._input_loop._shutdown_event is repl._signal._shutdown_event`.
- Integration-style async test: start the loop with a stubbed blocking read, deliver a real
  `loop.add_signal_handler`-registered SIGINT (or call the registered handler directly), assert the
  loop returns within a small bound and that the graceful-timeout warning path is exercised by a
  dedicated test with a shortened `_GRACEFUL_TIMEOUT_S`.
- Manual check: `uv run python -c` REPL session, press Ctrl-C with no further input, confirm exit.
- `uv run ruff check scripts/agent`, `uv run mypy --no-namespace-packages scripts/agent`,
  `uv run pytest tests/agent/test_repl.py tests/agent/test_signal_handler.py -q`.

## Documentation Impact
Update `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` ("Shutdown Behavior", "Ctrl-C" bullets)
to state the actual contract: which signal interrupts what, the grace bound and what happens when it
expires, and what graceful shutdown performs. Update the operator hint in `deploy/start_agent.sh`.
Record the shutdown-event owner in the REPL component boundaries.

## Out of Scope
- Signal handling during startup (`StartupInterrupted`) — already functional.
- MCP subprocess termination policy and shutdown timeouts (`shutdown003`).
- Command-argument parsing and command error surfacing (`cmd001`, `cmd002`).

## Dependencies
- `repl002` (the pending `input()` worker thread) must be settled together with this change.
- `repl003` supplies the test harness that this issue's acceptance criteria rely on.

## Unresolved Questions
- Should Ctrl-C during a turn interrupt the turn (cancel immediately) or only prevent the next turn?
  The current docs imply "handled differently from interruption during tool loop execution" without
  defining it. Needs confirmation.
- `_GRACEFUL_TIMEOUT_S` (10.0 s, `repl_input_loop.py:55`) is duplicated in
  `scripts/agent/resource_shutdown_coordinator.py:29`. Which value is authoritative? Needs confirmation.
- Whether the REPL should terminate MCP subprocesses it started when it is force-killed (orphan
  avoidance) is an operational decision, deferred to `shutdown003`.

## AI Implementation Instruction
Do not add a second shutdown flag or a second event. One event, constructed before any consumer is
built, with one owner and explicit wiring asserted by a test. Keep `SignalHandler` the only place that
touches OS signals, and make every claim added to `docs/23_agent/agent_07_05_*.md` match a test.

## Traceability
- **Workflow phase**: `python-code-review` (REPL core-loop review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl.py`, `scripts/agent/repl_input_loop.py`,
  `scripts/agent/signal_handler.py`, `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md`,
  `deploy/start_agent.sh`
