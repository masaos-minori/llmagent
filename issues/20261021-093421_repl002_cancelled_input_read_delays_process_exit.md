# A cancelled or pending `input()` worker thread keeps the REPL process alive

## Priority
Medium

## Summary
Own the executor used for the blocking `input()` read so that cancelling the read — or leaving it
pending when the REPL loop exits — does not keep `asyncio.run()` from returning.

## Background
`ReplInputLoop._read_input` reads stdin with `loop.run_in_executor(None, ...)`
(`scripts/agent/repl_input_loop.py:138-194`) and cancels the tracking task at `:170`. `AgentREPL.main()`
runs the REPL through `asyncio.run(AgentREPL().run())` (`scripts/agent/repl.py:170-172`), and
`asyncio.run()` shuts down the loop's default executor before returning.

## Problem
Measured in this environment (Python 3.14.7, dev venv): a main coroutine that starts two
`run_in_executor(None, blocking_input)` reads, cancels both, and returns finishes at t=0.30 s, but
`asyncio.run()` returns only at t=6.00 s — the full duration of the blocked read. The interpreter
waits for the default executor's threads, so a read that never returns holds the process open after
`AgentREPL.run()`'s `finally` has already run. The exit path is therefore bounded by user keyboard
activity rather than by the shutdown logic.

## Reason for Change
`repl001` will start cancelling the input read on signals; that fix is incomplete if the process still
cannot exit until the abandoned read returns. This is also what makes a force-kill the only way out of
an idle REPL.

## Implementation Intent
Use a dedicated, explicitly managed executor (or a dedicated reader thread) for stdin so the REPL
controls whether a pending read is waited for at shutdown, instead of inheriting the default executor's
join-on-shutdown behavior.

## Target Files or Areas
- `scripts/agent/repl_input_loop.py` (`_read_input`, `run`)
- `scripts/agent/repl.py` (`main`, `run` finally)

## Required Changes
- Replace the shared `run_in_executor(None, ...)` read with a resource the REPL owns and can shut down
  with an explicit, bounded `wait` (or a daemon reader thread with a queue).
- State the intended shutdown behavior in code: bounded wait, then give up.
- Keep Ctrl-D (EOF) → clean exit behavior unchanged.

## Constraints
- Reading stdin must stay interruptible enough for interactive use; a daemon thread may hold stdin but
  must not spin.
- No new third-party dependency.
- Must not regress the Windows/`add_signal_handler` fallback path.

## Acceptance Criteria
- With a stubbed `input()` that blocks indefinitely, the REPL process exits within the configured bound
  after the loop stops, without further keyboard input.
- Cancelling an in-flight read does not leave an executor thread that `asyncio.run()` must wait for.
- The default loop executor is not used for stdin reads.

## Testing Expectations
- Regression test: a stubbed blocking `input()`, a cancelled read task, and an assertion that the
  enclosing `asyncio.run()` (or `AgentREPL.run()` + loop close) returns within a small bound;
  measure with `time.monotonic()`, and keep the bound far from real timing constants to avoid a
  clock-boundary flake (see `20261020-194610_testflaky001_...` for the pattern to avoid).
- `uv run pytest tests/agent/test_repl.py -q` must stay green.

## Documentation Impact
Record in `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md` how a pending stdin read is released
at shutdown, and that process exit time is bounded by the shutdown path rather than by keyboard input.

## Out of Scope
- Which signal interrupts what (`repl001`).
- MCP subprocess and HTTP client teardown (`shutdown003`).

## Dependencies
- Pairs with `repl001`; the two change the same read/cancel path and should be reviewed together.

## Unresolved Questions
- Preferred mechanism: dedicated `ThreadPoolExecutor(max_workers=1)` owned by `ReplInputLoop`, or a
  daemon reader thread feeding a queue. Needs confirmation against `rules/coding.md` conventions.
- Whether a daemon reader thread is acceptable for a CLI that must not hold stdin after exit.

## AI Implementation Instruction
Do not tune timeouts; remove the dependency on the default executor. Keep the change inside
`repl_input_loop.py` plus the `main()`/`run()` shutdown path, and make the bounded behavior testable
without a real keyboard or real signals.

## Traceability
- **Workflow phase**: `python-code-review` (REPL core-loop review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/repl_input_loop.py`, `scripts/agent/repl.py`
