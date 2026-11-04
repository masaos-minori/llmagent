# Stdin line typed after a multiline-input timeout is lost to the stale reader thread

## Priority
Medium

## Summary
After `CLIView.read_multiline` times out on a blocked continuation read, the daemon
`StdinReader` worker thread stays blocked in its blocking `input()` call. A line typed at
the next prompt is consumed by that stale thread instead of the new read, so the next
`read_multiline` hangs until its own timeout and the user's line is effectively lost.

## Background
`CLIView.read_multiline` wraps each continuation read in `asyncio.wait_for(...,
timeout=_INPUT_TIMEOUT_S)` and runs the read on a daemon `StdinReader` worker thread
(`scripts/agent/cli_view.py:285-301`, `scripts/agent/stdin_reader.py:84-107`). The
`cliview001` plan/procedure (`20261103-110436_01_scripts_agent_cli_view.py.md`) changed the
timeout branch from `raise KeyboardInterrupt` to `break` so the accumulated text is
returned. That change was validated with automated tests, but the companion Unknown UNK-01
("does a line typed after the timeout reach the next read?") was settled with a pty-driven
smoke test that instead confirmed the opposite: the line is lost.

## Problem
`asyncio.wait_for` cancels the awaited read future on timeout, but cancellation does not
interrupt the C-level `input()` call running in the worker thread. The thread remains
blocked in `input()` until a real keypress arrives. Because `StdinReader` services one read
per worker invocation, the next `read_multiline` cannot start its own `input()` until the
stale one returns; the keypress the user types at the next `> ` prompt is delivered to the
stale thread (whose waiter was already cleared), so it is discarded and the new read times
out. Observed via pty smoke test: first read returns `"x"`, a supplied `"z"` never appears
in the second read's result which returns `"y"` (timeout).

## Reason for Change
The `cliview001` fix changes observable timeout behavior (partial return instead of raise),
so the post-timeout stdin hand-off must be verified and corrected rather than left to an
unresolved Unknown. Leaving it as-is means every multiline timeout silently drops the user's
next line until the 30s timeout elapses.

## Implementation Intent
Free the stale worker after a timeout so it does not hold a blocking `input()` across reads,
or otherwise guarantee the next read gets the next line. Approach lives in
`scripts/agent/stdin_reader.py` (and minimally `cli_view.py`); do not change the public
`read()` contract or the single-read-per-worker model without an explicit decision. Any fix
that touches a target file requires amending the `cliview001` Plan (currently Out of Scope
for that plan per its own UNK-01 resolution path).

## Target Files or Areas
`scripts/agent/stdin_reader.py`, `scripts/agent/cli_view.py`. Possibly
`scripts/agent/repl_input_loop.py` if the REPL needs to drain a pending read between turns.

## Required Changes
- After a `wait_for` timeout in `read_multiline`, release the in-flight `input()` on the
  worker thread (e.g. a non-blocking cancel that also unblocks the blocking read, or a
  per-read teardown) so no stale `input()` outlives the request.
- Ensure a line typed at the next prompt is delivered to the next `read_multiline`, not
  discarded by a completed request's worker.
- Add regression tests covering: timeout followed by a fresh read that receives a supplied
  line; no non-daemon thread left blocked in `input()` after a timeout.

## Constraints
- Must not change `StdinReader.read()`'s "already pending" semantics for genuinely
  concurrent reads.
- Must not introduce a second blocking read path or leak threads.
- `_INPUT_TIMEOUT_S` default (30s) and the daemon-thread process-exit guarantee must hold.
- Backward compatible: the hook/return contract of `read_multiline` is unchanged.

## Acceptance Criteria
- After a mid-continuation timeout, a line supplied at the next prompt completes the next
  `read_multiline` (returns joined text), not a second timeout.
- No `StdinReader` worker thread remains blocked in `input()` after a timeout.
- Existing `tests/agent/test_stdin_reader.py` and `tests/test_cli_view.py` pass unchanged.

## Testing Expectations
- New unit tests for the timeout-then-fresh-read path (mirroring the pty smoke scenario).
- Full `tests/agent/test_stdin_reader.py` + `tests/test_cli_view.py` green.
- `ruff`, `mypy`, `bandit`, `radon`, module-size gates clean on touched files.

## Documentation Impact
Document the post-timeout stdin behavior and the pending-line guarantee in the agent
reference chapter if one exists; record this as a Known Issue until fixed. No user-facing doc
change required beyond the Known Issue note.

## Out of Scope
- The `cliview001` timeout-return change itself (already implemented).
- Changing `_INPUT_TIMEOUT_S` value or the EOF/KeyboardInterrupt branch.
- Any change to `startup.py`, `repl.py`, `resource_shutdown_coordinator.py`, `context.py`.

## Dependencies
- Filed as a follow-up to `issues/20261003-180327_cliview001_multiline-input-timeout-crashes-repl.md`
  (Plan `20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md`). Amending that
  Plan's target files is required only if the fix lands there.

## Unresolved Questions
- Should the stale read be abandoned (drop its partial text) or retried on the next line?
- Does `repl_input_loop.py` need to drain a pending read between turns to avoid the same
  class of loss for other `read()` call sites?

## AI Implementation Instruction
Reproduce first with a pty or threaded test that times out a `read_multiline` continuation
and then supplies a line to the next read; assert the line is delivered and no worker stays
blocked in `input()`. Prefer fixing the worker lifetime in `stdin_reader.py` over masking in
`cli_view.py`. If a target-file change is required, amend the `cliview001` Plan before
implementing. Keep the diff minimal and re-run the full stdin + cli_view regression sets.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142849_cliview001_multiline-input-timeout-crashes-repl.md
- **Source implementation procedure**: implementations/20261103-110436_01_scripts_agent_cli_view.py.md
- **Generated at**: 20261104-112115
- **Related target files**: scripts/agent/stdin_reader.py, scripts/agent/cli_view.py
