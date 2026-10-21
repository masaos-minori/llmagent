# The WAL checkpoint timeout guard cannot fire, and `time.sleep()` blocks the loop during shutdown

## Priority
High

## Summary
Make the WAL checkpoint actually bounded and non-blocking, so the shutdown deadline the coordinator already
configures is enforceable.

## Background
`ResourceShutdownCoordinator.close_resources()` wraps the checkpoint with a 30 s bound and the backup with a
10 s bound, and records `wal_checkpoint_timeout` / `wal_backup_timeout` errors when they expire
(`scripts/agent/resource_shutdown_coordinator.py:71-106`).

## Problem
`WalCheckpointManager.checkpoint_sync()` is declared `async` but contains no `await` — verified: `grep -n
'await ' scripts/agent/wal_checkpoint_manager.py` returns no matches. Its body is a single synchronous
`with SQLiteHelper("session").open(...)` block (`scripts/agent/wal_checkpoint_manager.py:57-110`) that
issues `PRAGMA journal_mode`, `db.checkpoint("PASSIVE")`, up to three `db.checkpoint("TRUNCATE")` attempts,
and between them `time.sleep(2**attempt)` (`:100`) — blocking sleeps of 1 s and 2 s on the event loop.
Because the coroutine never yields, `asyncio.wait_for(..., timeout=30.0)` cannot interrupt it: the timeout
branch at `:77-84` is unreachable while the checkpoint itself is running. A checkpoint that blocks for
60 s blocks shutdown for 60 s and reports nothing. The same shape applies to `backup_sync()` (`:112+`).
`close_resources()` also swallows every failure into an `errors` list that is only written to the log
(`:149-151`); the operator sees no indication that the checkpoint failed.

## Reason for Change
The 30 s/10 s bounds are the documented shutdown guarantee for the session database. Today they are
declarative only, and the failure they are meant to detect is invisible to the operator.

## Implementation Intent
Make the blocking DB work interruptible (offload it from the loop or make it yield), and surface the
recorded shutdown errors through the CLI view.

## Target Files or Areas
- `scripts/agent/wal_checkpoint_manager.py` (`checkpoint_sync`, `backup_sync`)
- `scripts/agent/resource_shutdown_coordinator.py` (`close_resources`)
- `scripts/agent/sqlite_helper.py` (connection/checkpoint API, reference)

## Required Changes
- Run the blocking checkpoint/backup in a thread (`asyncio.to_thread` or a dedicated executor) so
  `wait_for` can actually cancel it, or make the coroutine yield between attempts and use
  `asyncio.sleep` instead of `time.sleep`.
- Decide what "timed out" means for the session DB and record it consistently
  (`wal_checkpoint_timeout` vs `wal_checkpoint_truncate`).
- Report the collected shutdown errors through `CLIView` (`scripts/agent/cli_view.py`) rather than only the
  log, since `close_resources()` already receives the view.
- State whether a PASSIVE checkpoint that took over 5 s (`:78-83`) should be reported to the operator.

## Constraints
- SQLite connections are thread-affine and `SQLiteHelper.open()` is a context manager; any offload must keep
  the connection on the thread that opened it.
- Checkpoint semantics must not change: PASSIVE first, TRUNCATE fallback, 3 attempts.
- `checkpoint_sync`'s `(bool, list[tuple[str, str]])` return contract is used by
  `resource_shutdown_coordinator.py:70-76` and by the backup decision at `:89`.
- Do not weaken `_is_db_path_allowed` (`:47-55`).

## Acceptance Criteria
- With a stubbed checkpoint that blocks longer than the configured bound, `close_resources()` returns within
  the bound and records `wal_checkpoint_timeout`.
- No `time.sleep()` remains inside an `async def` shutdown path.
- A failed checkpoint produces a visible operator-facing message, not only a log line.
- The success path writes the same audit/log messages as today.

## Testing Expectations
- Regression test with a stub that blocks past a deliberately small bound, asserting the timeout branch is
  reached (use a large margin so the test is not clock-boundary sensitive).
- Test asserting the operator-visible message exists for a recorded shutdown error.
- Mutation check: removing the offload must fail the timeout test.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the shutdown sequence and its actual bounds for the session DB, what happens when a checkpoint
times out, and that the operator is informed. Update the operations docs' shutdown section.

## Out of Scope
- Retuning `context_compress_turns`, retention, or checkpoint policy.
- Background task cancellation (`turn005`).
- MCP subprocess termination (`shutdown003`).

## Dependencies
- Related to `cmd003` (same "blocking call on the event loop" class) and to `repl001` (SIGKILL is currently
  the only escape from a blocked shutdown).

## Unresolved Questions
- Which bound is authoritative: 30 s here, `_GRACEFUL_TIMEOUT_S = 10.0` in
  `repl_input_loop.py:55` and `resource_shutdown_coordinator.py:29`. Needs confirmation.
- Should a timed-out checkpoint fall back to a backup, or abort the fallback work as well? Needs a decision.

## AI Implementation Instruction
Do not add another timeout layer. Make the existing timeout enforceable, and make the recorded errors
visible. Keep the checkpoint algorithm unchanged.

## Traceability
- **Workflow phase**: `python-code-review` (startup/shutdown lifecycle review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/wal_checkpoint_manager.py`,
  `scripts/agent/resource_shutdown_coordinator.py`, `scripts/agent/cli_view.py`
