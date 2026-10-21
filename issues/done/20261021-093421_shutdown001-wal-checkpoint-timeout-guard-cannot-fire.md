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
`WalCheckpointManager.checkpoint_sync()` is declared `async` but contains no `await`. Its body is a single
synchronous `with SQLiteHelper("session").open(write_mode=True)` block that issues `PRAGMA journal_mode`,
`db.checkpoint("PASSIVE")`, up to three `db.checkpoint("TRUNCATE")` attempts, and between them
`time.sleep(2**attempt)` — blocking sleeps on the event loop. Because the coroutine never yields,
`asyncio.wait_for(..., timeout=30.0)` cannot interrupt it: the timeout branch is unreachable while the
checkpoint itself is running. A checkpoint that blocks for 60 s blocks shutdown for 60 s and reports nothing.
The same shape applies to `backup_sync()`. `close_resources()` also swallows every failure into an `errors`
list that is only written to the log; the operator sees no indication that the checkpoint failed.

### Verification (re-read at HEAD `a559db59c`, 2026-10-22)

Confirmed against the current tree:

- `checkpoint_sync()` (`scripts/agent/wal_checkpoint_manager.py:57-113`) and `backup_sync()` (`:115-172`) are
  `async def` containing no `await`: `grep -n 'await ' scripts/agent/wal_checkpoint_manager.py` → no matches.
- `time.sleep(2**attempt)` at `wal_checkpoint_manager.py:101` is the only `time.sleep` in the whole `scripts/`
  tree (`grep -rn "time.sleep" scripts/` → one match), so the issue's acceptance criterion is exactly scoped.
- `close_resources()` bounds the calls with `asyncio.wait_for(..., timeout=30.0)`
  (`scripts/agent/resource_shutdown_coordinator.py:72-75`) and `timeout=10.0` (`:91-94`), catches
  `TimeoutError` at `:77-84` and `:96-103`, and renders the collected `errors` only into a log call at
  `:149-151`. `self._view` is used only for `write_history()` at `:66`, although `CLIView.write_error`
  (`scripts/agent/cli_view.py:239-241`) and `write_warning` (`:209-211`) already exist.
- Dead constants: `_WAL_CHECKPOINT_TIMEOUT_S` and `_WAL_BACKUP_TIMEOUT_S` (`wal_checkpoint_manager.py:32-33`)
  and `_GRACEFUL_TIMEOUT_S` (`resource_shutdown_coordinator.py:29`) are referenced nowhere in `scripts/`,
  `tests/`, `docs/` or `tools/`. The bounds actually in force are the literals at
  `resource_shutdown_coordinator.py:74` and `:93`.

Measured mechanism (`.venv`, Python 3.14.7; probes at `/tmp/opencode/shutdown001_probe.py`,
`shutdown001_probe2.py`, `shutdown001_probe4.py`, `shutdown001_probe5.py` — deliberately not added to the
repository). A 1.0 s `asyncio.wait_for` bound around a body that blocks for 3.0 s:

| Body shape | awaited elapsed | outcome |
|---|---|---|
| `async def` with no `await` (HEAD shape) | 3.00 s | completed normally; the bound never fired and no `wal_checkpoint_timeout` was recorded |
| same body awaited through `asyncio.to_thread` | 1.00 s | `TimeoutError` branch taken (`wal_checkpoint_timeout` recorded) |
| same body on a plain daemon thread | 1.00 s | `TimeoutError` branch taken |
| process wall time for the whole probe | 6.00 s | the abandoned default-executor worker is still joined at interpreter exit (`concurrent.futures.thread._python_exit`, `/usr/lib/python3.14/concurrent/futures/thread.py:23-31`); the daemon thread is not joined |

So an offload makes the **await** bounded. It does not by itself make the **process exit** bounded — the same
mechanism measured for `repl002` (`issues/done/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`).

Measured against real SQLite (`shutdown001_probe4.py`, `shutdown001_probe5.py`): a real WAL-mode database,
5000 committed rows written while a second connection holds an open read transaction, `sqlite_busy_timeout_ms`
set to the production value (`config/agent.toml:12` = 30000):

- `-wal` = 53,592 bytes (13 frames) that no checkpoint can reclaim while the reader is open.
- `PRAGMA wal_checkpoint(TRUNCATE)` blocked **30.05 s** and returned `(busy=1, log=13, checkpointed=0)`.
  The busy handler is the blocking source: `PRAGMA busy_timeout=30000` is applied to every connection
  (`scripts/db/helper.py:23-35`, `scripts/db/config.py:31`).
- In the same state the production `checkpoint_sync()` returned `(True, [])` after **0.00 s** and left the
  53,592-byte WAL in place. `PRAGMA wal_checkpoint(PASSIVE)` returns `(0, 13, 0)` — a checkpoint that copied
  0 of 13 frames — `wal_checkpoint_manager.py:71` discards the `WalCheckpointCounts` value that
  `SQLiteHelper.checkpoint()` returns (`scripts/db/helper.py:267-281`, `scripts/db/models.py:16-21`), the code
  logs `WAL checkpoint completed (PASSIVE)` at INFO (suppressed at the default root level) and returns success.
- Consequences: the TRUNCATE fallback and its retry sleeps are never reached in the most likely contention
  case (PASSIVE neither raises nor exceeds the 5 s threshold at `:73`), and `truncated_or_ok=True` at `:89`
  skips the backup step that is supposed to protect an un-reclaimed WAL.
- With `sqlite_busy_timeout_ms = 0` the same state still returns a busy row rather than raising, so the
  3-attempt `time.sleep` retry path only runs when a checkpoint raises `sqlite3.Error` for another reason.
- Live `/opt/llm/db/session.sqlite-wal` is 0 bytes, so the success path works today; it is the failure path
  that is unenforceable.

Corrections to the issue text:

- `scripts/agent/sqlite_helper.py` does not exist. The connection and checkpoint API is
  `scripts/db/helper.py` (`SQLiteHelper.checkpoint` at `:267-281`), imported at
  `wal_checkpoint_manager.py:25`.
- Line drift: the checkpoint body is `wal_checkpoint_manager.py:64-113` (not `:57-110`); `time.sleep` is at
  `:101` (not `:100`); `backup_sync` starts at `:115` (not `:112`); the "PASSIVE took over 5 s" branch is
  `:69-77` (not `:78-83`); the coordinator's two guarded calls are `:71-87` and `:90-106`.
  `:149-151` for the error summary is correct.
- "A checkpoint that blocks for 60 s blocks shutdown for 60 s and reports nothing" is confirmed as a
  mechanism, and the concrete blocking source is the SQLite busy handler, not the retry sleeps: one TRUNCATE
  attempt measured 30.05 s, which is exactly the configured 30 s bound. Reaching the fallback three times
  would be 3 attempts plus 1 s and 2 s of sleeps, but that is arithmetic on a path contention does not
  reach.
- `test_checkpoint_timeout_records_error_and_still_runs_backup` (`tests/agent/test_repl.py:928-955`) does not
  test the bound. Its stub makes `db.checkpoint` raise `TimeoutError`, which propagates through
  `asyncio.wait_for` and is caught by the same `except TimeoutError` at `resource_shutdown_coordinator.py:77`
  (as of Python 3.11 `asyncio.TimeoutError` **is** the builtin `TimeoutError`). The test passes while the
  bound is decorative, and its comment "returns well before the 0.3s blocked checkpoint call finishes"
  describes a code shape that no longer exists.
- There is no `tests/agent/test_wal_checkpoint_manager.py`. The only coverage of either method runs through
  `_make_bare_repl()` fixtures with `SQLiteHelper` patched at the use-site
  (`tests/agent/test_repl.py:876-1030`) — the mirror rule at
  `skills/python-test-and-fix/workflow.md:53-54`. `tests/agent/test_resource_shutdown_coordinator.py` (122
  lines, 5 tests) replaces `wal.checkpoint_sync` with `AsyncMock(return_value=(True, []))` in every case, so
  neither bound branch is exercised there either.
- `sqlite_wal_checkpoint_mode = "TRUNCATE"` (`config/agent.toml:13`) governs only
  `scripts/db/maintenance.py:140-148` (`checkpoint_wal`); the shutdown path hardcodes PASSIVE→TRUNCATE.
  Two checkpoint policies in one repository, one config key.
- Documentation: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:74-82`
  documents the cleanup order, and `:144` states "The WAL checkpoint and backup timeouts at shutdown are
  fixed in `ResourceShutdownCoordinator.close_resources()` and are not configurable; a timeout is recorded as
  a shutdown error and logged". The first half is accurate; the second half describes a branch that cannot
  fire against the real implementation.
- Current metrics: `radon cc -s -n B` → `close_resources` C (18), `backup_sync` B (8), `checkpoint_sync` B
  (7), `ResourceShutdownCoordinator` C (11), `WalCheckpointManager` B (6). `tools/check_module_size.py`
  reports no new violations.

## Reason for Change
The 30 s/10 s bounds are the documented shutdown guarantee for the session database. Today they are
declarative only, and the failure they are meant to detect is invisible to the operator.

## Implementation Intent
Make the blocking DB work interruptible (offload it from the loop or make it yield), and surface the
recorded shutdown errors through the CLI view.

## Target Files or Areas
- `scripts/agent/wal_checkpoint_manager.py` (`checkpoint_sync`, `backup_sync`, the unused `_WAL_*` constants)
- `scripts/agent/resource_shutdown_coordinator.py` (`close_resources`, the unused `_GRACEFUL_TIMEOUT_S`,
  the error summary at `:149-151`)
- `scripts/db/helper.py` (connection and checkpoint API — reference only)
- `tests/agent/test_wal_checkpoint_manager.py` (new; the mirror file the missing coverage needs)
- `tests/agent/test_resource_shutdown_coordinator.py`
- `tests/agent/test_repl.py` (`TestCloseResourcesWALCheckpoint`, `:876-1030`)
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (`:74-82`, `:144`)

## Required Changes
- Run the blocking checkpoint/backup body in a worker so `wait_for` can actually reach its timeout branch,
  and keep the whole open/use/close sequence inside that worker: `SQLiteHelper` connections are
  thread-affine (`sqlite3.connect` default `check_same_thread=True`, `scripts/db/helper.py:127-135`) and
  `open()`/`__exit__` pair on the calling thread.
- Make one source of truth for the bounds: either use `_WAL_CHECKPOINT_TIMEOUT_S` /
  `_WAL_BACKUP_TIMEOUT_S` or delete them and keep the literals; do not leave three unused timeout constants
  (`wal_checkpoint_manager.py:32-33`, `resource_shutdown_coordinator.py:29`) next to two live literals.
- Ensure a `TimeoutError` that reaches the coordinator can only mean "the bound expired": a timeout raised by
  the DB body itself must arrive as a recorded `wal_checkpoint_error`, not as `wal_checkpoint_timeout`
  (`test_repl.py:928-955` currently reaches the timeout branch through that conflation).
- Report the collected shutdown errors through the `CLIView` the coordinator already holds
  (`resource_shutdown_coordinator.py:61`), using the existing `write_error`/`write_warning` channels, in
  addition to the log summary at `:149-151`.
- Stop discarding the `WalCheckpointCounts` value `SQLiteHelper.checkpoint()` returns: the claim that a
  checkpoint completed must be backed by the counters the code received, so a `log_size > 0` /
  `pages_checkpointed == 0` result is not logged as an unqualified success
  (`wal_checkpoint_manager.py:71`, `:88`).
- Decide what "timed out" means for the session DB and record it consistently
  (`wal_checkpoint_timeout` vs `wal_checkpoint_truncate`).

## Constraints
- SQLite connections are thread-affine and `SQLiteHelper.open()` is a context manager; any offload must keep
  the connection on the thread that opened it.
- Checkpoint semantics must not change: PASSIVE first, TRUNCATE fallback, 3 attempts.
- `checkpoint_sync`'s `(bool, list[tuple[str, str]])` return contract is used by
  `resource_shutdown_coordinator.py:70-76` and by the backup decision at `:89`.
- Do not weaken `_is_db_path_allowed` (`wal_checkpoint_manager.py:47-55`).
- The offload must not abandon a partially-applied SQLite write: `asyncio.to_thread` leaves the worker alive
  and joins it at interpreter exit, a daemon thread does not (measured above). State which guarantee is
  being made.
- Nothing in this scope may open a real config file, database or terminal in tests; `SQLiteHelper` is
  replaced at the use-site (`agent.wal_checkpoint_manager.SQLiteHelper`), the form
  `tools/check_mock_patch_targets.py` enforces.
- `docs/` edits are wording only and must follow `rules/docs-*.md` conventions enforced by
  `tools/check_docs_*.py`.

## Acceptance Criteria
- With a checkpoint body that blocks longer than the configured bound, `close_resources()` returns within
  the bound and records `wal_checkpoint_timeout` — where "blocks" means a body that performs no awaits, not a
  stub that raises `TimeoutError`.
- No `time.sleep()` remains inside an `async def` shutdown path (today: one occurrence,
  `wal_checkpoint_manager.py:101`).
- A failed checkpoint produces a visible operator-facing message, not only a log line.
- The success path writes the same audit/log messages as today; a result whose own counters show nothing was
  checkpointed is not described as a completed checkpoint.
- Exactly one source of the 30 s / 10 s numbers exists in `scripts/`.

## Testing Expectations
- Regression test with a real blocking body (no awaits) past a deliberately small bound, asserting the
  timeout branch is reached; the mutation "remove the offload" must fail this test
  (`skills/python-test-and-fix/SKILL.md` mutation requirement).
- Test asserting the operator-visible message exists for a recorded shutdown error.
- Test asserting `backup_sync` is not silently skipped when the WAL was not reclaimed (the
  `truncated_or_ok=True` path measured above).
- Real-SQLite coverage in `tests/agent/test_wal_checkpoint_manager.py` using `SQLiteHelper(db_path=...)`
  against `tmp_path` and a second connection holding a read transaction, so the PASSIVE-returns-busy case is
  exercised by SQLite rather than a mock.
- No `time.sleep()` or wall-clock arithmetic in new assertions (`skills/python-test-and-fix/SKILL.md:21`);
  use `asyncio.Event` and generous margins instead.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`,
  `uv run python tools/check_mock_patch_targets.py`.

## Documentation Impact
Document the shutdown sequence and its actual bounds for the session DB, what happens when a checkpoint
times out, and that the operator is informed. The concrete home is
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`: the "Resource Cleanup on
Shutdown" sequence (`:74-82`) and the Known Limitations bullet at `:144` that currently asserts a timeout is
recorded. `docs/23_agent/agent_02_runtime-architecture.md:163-167` states the same guarantee at the
architecture level; verify its wording against whatever the plan settles.

## Out of Scope
- Retuning `context_compress_turns`, retention, or checkpoint policy.
- Changing whether a busy/no-op checkpoint counts as a failure of the shutdown (surfaced by this
  verification; needs its own decision — see Unresolved Questions).
- `sqlite_wal_checkpoint_mode` and `scripts/db/maintenance.py::checkpoint_wal` (a different caller).
- Background task cancellation (`turn005`).
- MCP subprocess termination (`shutdown003`).

## Dependencies
- Related to `cmd003` (same "blocking call on the event loop" class) and to `repl001` (SIGKILL is currently
  the only escape from a blocked shutdown).
- Shares its measured exit-cost mechanism with `repl002`
  (`issues/done/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`, now
  `plans/20261022-040200_plan.md`); the two Plans touch disjoint files.
- `repl003` (`plans/20261022-043008_plan.md`) owns the assertion-quality rules this issue's test work must
  follow, and it is the reason the existing `test_repl.py:928-955` stub has to be replaced rather than
  extended.

## Unresolved Questions
- Which bound is authoritative: 30 s here, `_GRACEFUL_TIMEOUT_S = 10.0` in
  `repl_input_loop.py:55` and `resource_shutdown_coordinator.py:29`. Needs confirmation.
- Should a timed-out checkpoint fall back to a backup, or abort the fallback work as well? Needs a decision.
- Which guarantee is intended: `close_resources()` returning within the bound while the checkpoint itself is
  allowed to finish (the default `asyncio.to_thread` behaviour, measured), or the whole process exit being
  bounded at the cost of abandoning a partially-applied write (a daemon thread). Needs a decision.
- Is a PASSIVE checkpoint that copies 0 frames of a non-empty WAL a shutdown failure? Today it is recorded as
  success and the backup step is skipped; treating it as a failure changes `close_resources()`'s behaviour and
  the issue's own "success path unchanged" criterion. Needs a decision.

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
  `scripts/agent/resource_shutdown_coordinator.py`, `scripts/db/helper.py`,
  `tests/agent/test_wal_checkpoint_manager.py`, `tests/agent/test_resource_shutdown_coordinator.py`,
  `tests/agent/test_repl.py`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
