# Command handlers run blocking SQLite work directly on the event loop, and sync handlers cannot be cancelled at shutdown

## Priority
Medium

## Summary
Move blocking storage work out of the event loop for slash commands, and make command execution interruptible
by the shutdown path.

## Background
Slash commands are dispatched from inside the running event loop: `ReplInputLoop._repl_loop` wraps
`_dispatch_line` in a task and waits on it (`scripts/agent/repl_input_loop.py:254-262`), and
`CommandRegistry._invoke_handler` either awaits or calls the handler inline
(`scripts/agent/commands/registry.py:106-113`). `CommandDef.is_async` only selects which of those two
paths is used (`scripts/agent/commands/command_defs.py:65`); it does not describe blocking behavior.
Only `/compact`, `/mcp`, and `/session` are `is_async=True`
(`scripts/agent/commands/command_defs_list.py:85`, `:93`, `:104`); `/memory`, `/context`, `/history`,
`/clear`, `/undo`, `/stats`, `/config`, `/reload`, `/debug`, `/help`, `/plan` are `is_async=False` and
their handlers are plain `def` (e.g. `scripts/agent/commands/cmd_memory.py:88`).

## Problem
- Blocking SQLite work runs on the loop thread. `self._ctx.session.list_sessions(limit)`
  (`cmd_session.py:90`), `DbMaintenanceService().vacuum()` (`db_session_ops.py:45-48`), `purge()`
  (`:50-58`), `checkpoint()` (`:38-43`), `/session load`/`export`, and the `/memory` status/rebuild paths
  (`memory_status.py`, `memory_rebuild_ops.py`) are synchronous calls. An `async def` handler does not make
  them cooperative: they hold the loop for the whole call, so a `VACUUM` or a large export delays signal
  handling and blocks every other coroutine.
- A `is_async=False` handler cannot be interrupted at all: `await task.cancel()` on a task already running a
  sync function has no effect until the function returns. So the graceful-shutdown bound
  (`_GRACEFUL_TIMEOUT_S`, `repl_input_loop.py:55`) and the `asyncio.wait({dispatch_task, shutdown_task})`
  race (`:255-284`) are only meaningful for turn work, not for commands.
- Verified against HEAD, the shutdown race is not even reachable today: `ReplInputLoop` is constructed with
  `None` (`repl.py:82`, `:85`) and `Repl.run()` rewires only `self._signal` (`repl.py:113-114`) and the
  shutdown coordinator (`:121`), so `self._shutdown_event` stays `None` and the condition at
  `repl_input_loop.py:256-257` is always false (`repl001`). The live path is
  `await asyncio.wait_for(dispatch_task, ...)` (`:285-297`), whose `timeout` argument is evaluated **when the
  await starts**: a signal arriving while a command is already running does not bound that command, because
  `timeout` was already computed as `None`. `signal_handler.py:56` sets `ctx.conv.shutdown_requested`, which
  bounds only the *next* dispatch. On expiry the loop logs `_log_graceful_shutdown_timeout()` (`:125`) and
  `break` (`:303-304`); the dispatch task is not cancelled at that point.
- `is_async` is not validated by production code: `await`ing a sync handler raises
  `TypeError: 'NoneType' object can't be awaited` (verified at runtime), so a mismatch between `is_async`
  and the handler kind is a runtime failure of that command rather than a startup error, even though
  `CommandRegistry.__init__` already does fail-fast validation of handler names (`registry.py:67-72`). The
  invariant *is* checked after the fact by tests
  (`tests/agent/commands/test_command_registry_consistency.py:35-49`), which only catches a mismatch when the
  test suite runs, not when the agent starts.

## Reason for Change
The commands most likely to be long-running are maintenance commands an operator runs while the REPL is
live. Blocking the loop makes the REPL unresponsive and makes any shutdown bound ineffective for them.

## Implementation Intent
Keep command handlers synchronous where they are cheap, and route blocking storage work through an
executor or an async service, so the loop stays responsive and cancellation is possible.

## Target Files or Areas
- `scripts/agent/commands/cmd_session.py`, `db_session_ops.py`, `memory_data_ops.py`,
  `memory_rebuild_ops.py`, `memory_status.py`
- `scripts/agent/commands/registry.py` (`_invoke_handler`, `__init__` validation)
- `scripts/agent/repl_input_loop.py` (dispatch/cancel path)

## Required Changes
- Run blocking DB calls from `async` handlers via `asyncio.to_thread`/a dedicated executor, or move them
  into an async service method.
- For long commands (`vacuum`, `purge`, `rag-rebuild-*`, `export`, `reindex`, `rebuild`), make the work
  cancellable and report partial completion when it is cancelled.
- Validate `CommandDef.is_async` against the handler at registry construction
  (`inspect.iscoroutinefunction(handler) == cmd.is_async`) so a mismatch fails at startup.
- State the contract for how long a command may block the loop.

## Constraints
- SQLite connections are thread-affine; any executor offload must respect the existing connection handling
  in `SQLiteHelper` and `rules/env.md`.
- Do not introduce a DB access layer change beyond what offloading requires.
- Keep command output identical for successful runs.
- `is_async` must keep describing how the dispatcher calls the handler; do not overload it.

## Acceptance Criteria
- While `/session vacuum` (or a stubbed long-blocking command) runs, another coroutine on the same loop
  makes progress. Separately: a shutdown request does **not** cut off the in-progress storage call — the
  measured behavior is that the await is bounded while the worker runs to completion and loop shutdown joins
  it. Stating that behavior is part of this issue, not treating it as a defect.
- A `CommandDef` whose `is_async` disagrees with its handler raises at registry construction, not at invoke
  time.
- No `async def` command handler performs a blocking storage call directly on the loop. Scope note verified
  against HEAD: the `is_async=True` group that touches storage is `/session` only
  (`command_defs_list.py:104` → `db_dispatch` at `cmd_session.py:215-232`); `/compact` (`:85`) and `/mcp`
  (`:93`) do no storage work, and the sync `is_async=False` groups (`/memory`, `/context`, `/history`, …) are
  outside this criterion because their handlers are not async and are covered by the `is_async` flip
  question, not by this one.

## Testing Expectations
- Test with a stubbed blocking command: assert a concurrent coroutine advances and that cancellation
  completes within a bounded, generous margin (avoid tight timing asserts).
- Registry construction test for an `is_async`/handler mismatch.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document which commands are potentially long-running and blocking, that maintenance commands can be
cancelled by a shutdown request, and the `is_async` contract in the commands reference.

## Out of Scope
- Speeding up the DB operations themselves.
- Signal handling semantics (`repl001`).
- Command argument validation (`cmd002`).

## Dependencies
- Review after `repl001`: the graceful bound only becomes meaningful for commands once signal handling
  actually reaches the input loop.

## Unresolved Questions
- Is offloading command work to a thread acceptable under the project's SQLite usage rules, or should the
  commands move to async service methods? Needs confirmation against `rules/coding.md`.
  Resolved against HEAD: offloading is compatible with the connection model, because every command-side DB
  access opens its own connection inside the call and closes it before returning —
  `db_maintenance_service.py:35`, `:42`, `:52`, `:61`, `:69`; `rag_maintenance_service.py:26`, `:38`, `:48`,
  `:68`, `:82`; `session.py:126`, `:168`, `:181`, `:208`, `:250`; `memory_data_ops.py:184`, `:366`, `:393`;
  `memory_status.py:87`. `SQLiteHelper._connect` uses `sqlite3.connect(self._db_path, timeout=...)`
  (`db/helper.py:135`), i.e. the default `check_same_thread=True`, so moving the *whole* sync callable to a
  worker thread keeps each connection on one thread and never crosses a connection. No `asyncio.to_thread`
  callable in this repository shares a connection across threads; the only shared-connection case is the
  Event Bus, which uses `check_same_thread=False` plus `get_db_lock()` (`eventbus/db_conn.py:22-38`).
- Should long commands be cancelled at shutdown or allowed to finish (they mutate shared DB state)? Needs a
  decision.
  Measured constraint: cancelling the *await* does not cancel the *work*. A task awaiting
  `asyncio.to_thread(sleep 1.0)` cancelled after 0.1s leaves the worker running, and `asyncio.run()` returns
  only at 1.002s because loop shutdown joins the default executor. So "allow it to finish" is the behavior
  offloading produces, and interrupting an in-progress SQLite call would need
  `sqlite3.Connection.interrupt()` plumbing against per-call connections — which the Constraints section
  excludes. The decision this issue still needs is the *stated* policy, not the mechanism.

## AI Implementation Instruction
Offload the blocking calls, do not restructure the command layer. Make `is_async` a validated contract
rather than metadata.

## Traceability
- **Workflow phase**: `python-code-review` (command dispatch review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/commands/registry.py`, `scripts/agent/commands/db_session_ops.py`,
  `scripts/agent/commands/cmd_session.py`, `scripts/agent/repl_input_loop.py`
