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

### Verification (re-read at HEAD `84cf9b580`, 2026-10-22)

Confirmed:

- `ReplInputLoop._read_input` reads stdin on the loop's default executor at `scripts/agent/repl_input_loop.py:144`
  (the shutdown-event branch, which is unreachable until `repl001` lands) and at `:191` (the branch that runs today).
- `AgentREPL.main()` calls `asyncio.run(AgentREPL().run())` (`scripts/agent/repl.py:170-172`);
  `asyncio.run()` closes its `Runner`, and `Runner.close()` calls `loop.shutdown_default_executor(constants.THREAD_JOIN_TIMEOUT)`
  (`/usr/lib/python3.14/asyncio/runners.py:75`) with `THREAD_JOIN_TIMEOUT = 300` (`/usr/lib/python3.14/asyncio/constants.py:34`).
  The loop return is therefore held for up to 300 s by a read that never returns.
- Cancelling does not stop a started worker: `concurrent.futures`' `_WorkItem.run` calls `future.set_running_or_notify_cancel()`
  and a running item is not cancelled (`/usr/lib/python3.14/concurrent/futures/thread.py` `_worker`/`_WorkItem`), which is the same
  effect this repository already documents in `tests/eventbus/test_eventbus_shutdown.py:1-20`.
- After the loop returns, the interpreter still joins the worker: `concurrent.futures.thread._python_exit` puts the queue
  sentinel and then `t.join()`s every thread registered in `_threads_queues` (`/usr/lib/python3.14/concurrent/futures/thread.py:23-31`),
  and a worker blocked inside `input()` never reads that sentinel. The exit path is bounded by keyboard activity, as stated.

Measured in this environment (`.venv`, Python 3.14.7; the blocked read is a 6.0 s sleep so no keyboard is needed;
`/tmp/opencode/repl002_probe.py`, `/tmp/opencode/repl002_probe2.py`, `/tmp/opencode/repl002_probe3.py`):

| Mechanism for the read | `asyncio.run()` returns | Process exits |
|---|---|---|
| `run_in_executor(None, ...)` + cancel (current code) | held for the whole blocked read | 6.09 s |
| private `ThreadPoolExecutor(max_workers=1)` + `shutdown(wait=False, cancel_futures=True)` | 0.20 s | 6.09 s |
| `ThreadPoolExecutor` subclass whose worker threads are daemon | 0.25 s | 6.10 s |
| `sys.stdin.close()` to unblock the blocked worker | n/a | 6.09 s (the worker is not unblocked) |
| plain daemon `threading.Thread` + `loop.call_soon_threadsafe` result bridge | 0.20 s | 0.29 s |

Corrected:

- `Implementation Intent`'s first option ("a dedicated, explicitly managed executor") does not satisfy
  `Acceptance Criteria`. Measured: a private `ThreadPoolExecutor` makes the loop return in 0.20 s while the process still
  waits 6.09 s, and a `ThreadPoolExecutor` subclass with daemon worker threads still waits 6.10 s, because `_python_exit`
  joins every pool worker regardless of its daemon flag. Only a reading thread that is not a `concurrent.futures` pool
  worker and is a daemon thread satisfies the criteria (0.29 s). The issue's second option (a daemon reader thread) is the
  one the measurements support.
- `Required Changes`' "explicit, bounded `wait`, then give up" is achievable only for the awaiting side; no
  `concurrent.futures` executor can bound the process exit while a read is blocked.

Found at HEAD and missing from `Target Files or Areas`:

- `CLIView.read_multiline` (`scripts/agent/cli_view.py:267-300`) owns a private `ThreadPoolExecutor` (`:112`, `:286-288`)
  bounded by `asyncio.wait_for(..., _INPUT_TIMEOUT_S)` with `_INPUT_TIMEOUT_S = 30` (`:24`, `:290-292`), added by
  `issues/done/20260904-001051_cv001_input_executor_timeout.md`. It is a live stdin path: `_read_input` reaches it from
  `scripts/agent/repl_input_loop.py:197`. The same `Acceptance Criteria` gaps apply to it.
- `scripts/agent/tool_approval.py:121-129` prompts with `asyncio.to_thread(input, ...)`, and `asyncio.to_thread` is
  `loop.run_in_executor(None, ...)` (`/usr/lib/python3.14/asyncio/threads.py`), so the approval prompt also reads stdin on the
  default executor.
- Out of scope but recorded: `scripts/agent/commands/memory_data_ops.py:48` reads stdin with a synchronous `input(prompt)`
  on the event-loop thread (no executor involved), and `scripts/agent/startup_validation.py:163-171` uses the default
  executor for a blocking non-stdin call wrapped in `asyncio.wait_for(..., 30.0)`. Neither is a default-executor *stdin* read.

Existing repository precedent for the supported shape:

- `scripts/agent/http_lifecycle_process_terminator.py:105-113` waits by polling with `asyncio.sleep` instead of using a thread.
- `tests/agent/test_lifecycle.py:1040-1057` is an existing regression test that asserts `asyncio.to_thread` is **not** used,
  specifically to avoid leaking a non-daemon `ThreadPoolExecutor` worker.

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
- Added by this verification: `scripts/agent/cli_view.py` (`read_multiline` and the executor it owns),
  `scripts/agent/tool_approval.py` (`_prompt_user_approval`), and one new shared module that owns the
  stdin read primitive both call sites use.
- Removed by this verification: `scripts/agent/repl.py` needs no change for this issue. `main()`
  (`:170-172`) and `run()`'s `finally` are correct as they stand; the "bounded wait, then give up"
  behaviour belongs in the read primitive, and the exit-bound property comes from the reader thread not
  being a pool worker. `repl.py` is only touched by `repl001`.

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
  - Resolved by the measurements above: the dedicated-`ThreadPoolExecutor` option is excluded (it bounds
    the loop return only; the process still waits 6.09 s, and a daemon-threaded `ThreadPoolExecutor`
    subclass still waits 6.10 s). The daemon reader thread is the option the evidence supports.
    `rules/coding.md` contains no executor convention (no matches for `to_thread`, `executor`, or
    `daemon`), so the choice rests on the measurements plus the existing precedent in
    `scripts/agent/http_lifecycle_process_terminator.py:105-113` and `tests/agent/test_lifecycle.py:1040-1057`.
- Whether a daemon reader thread is acceptable for a CLI that must not hold stdin after exit.
  - Partially resolved: the process no longer waits for the reader thread (measured 0.29 s exit with the
    reader blocked), so holding stdin no longer delays exit. What cannot be measured in this environment
    (no TTY) is whether the terminal is left in `readline`'s editing state when the process exits while a
    read is abandoned. That needs an interactive check before the behaviour is documented as safe.

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
