## Goal

Make `WalCheckpointManager.checkpoint_sync` and `backup_sync` yield the event loop
while their SQLite and retry work runs on a worker thread (REQ-001, REQ-002,
REQ-008), read the `WalCheckpointCounts` they already return instead of discarding
them (REQ-006), record a shutdown error when a PASSIVE checkpoint copies zero frames
over a non-empty WAL (REQ-005), and fold the inline `elapsed > 5` literal plus the
two module constants into the single named bound owned by the coordinator
(REQ-003).

## Scope

Production behavior change to `scripts/agent/wal_checkpoint_manager.py` only. Both
`*_sync` bodies are rewritten internally; their signatures and return types are
unchanged. Reference reads only: `scripts/db/helper.py` (the whole step stays on one
thread-affine connection), `agent/context.py` (`ctx.cfg`, `ctx.session`). Dependent
tests: `tests/agent/test_wal_checkpoint_manager.py` (new), `tests/agent/test_repl.py`.

## Assumptions

- `SQLiteHelper.open()` returns a context manager whose `__enter__` yields a
  thread-affine `sqlite3.Connection`; the whole open → checkpoint → close sequence
  must run on one worker thread (REQ-002).
- `SQLiteHelper.checkpoint(mode)` returns `WalCheckpointCounts`
  (`scripts/db/models.py:16-21`); confirm its field names there before referencing
  them — do not assume attribute names.
- `asyncio.to_thread` uses the shared default executor; a worker abandoned by
  `wait_for` keeps running and may finish after the coordinator has reported a
  timeout (REQ-010's abandoned-step behavior, UNK-02).
- The two module constants and the inline `5` are dead / hardcoded-literals today
  (verified at HEAD), so collapsing them changes no observable bound value.

## Design decisions

- Wrap each `*_sync` body in a module-level sync worker function and
  `await asyncio.to_thread(worker, ctx)`. This gives the step await points so
  `wait_for` can reach its `TimeoutError` branch (REQ-001) without changing the
  public contract.
- Keep the connection lifecycle on one thread: the worker opens `SQLiteHelper`,
  checkpoints, and closes; no connection crosses threads (REQ-002). The retry
  `time.sleep(2 ** attempt)` moves inside the worker so no blocking call runs on the
  loop (REQ-008).
- Read `WalCheckpointCounts` after each `checkpoint()` call; when PASSIVE reports
  zero frames copied while the WAL still has frames, append a shutdown-error entry
  naming the frame count (REQ-005, REQ-006).

## Alternatives considered

- Daemon `threading.Thread` vs `asyncio.to_thread`: `to_thread` is the repository
  convention for blocking calls (`rules/coding.md:18`, precedent
  `scripts/mcp_servers/web_search/search_provider.py:45-60`) and needs no new import;
  chosen. A daemon thread would also bound process exit (UNK-02) but introduces this
  module's first `threading` code and a teardown responsibility; out of scope for the
  "await bounds the step" goal.
- Folding the inline `5` into a new named constant vs reusing the coordinator's
  bound: collapse to the single coordinator-owned bound (REQ-003) rather than adding
  a fourth constant.

## Implementation

### Target file

`scripts/agent/wal_checkpoint_manager.py`

### Procedure

Rewrite `checkpoint_sync` and `backup_sync` internals in three passes aligned to the
plan's phases; keep signatures, return types, and imports otherwise intact.

1. **Phase 1 (bound reachable).** Extract the current `checkpoint_sync` body into a
   module-level sync function `_checkpoint_step(ctx)` and the `backup_sync` body into
   `_backup_step(ctx)`. Replace each `async def ..._sync` body with
   `return await asyncio.to_thread(_checkpoint_step, ctx)` /
   `return await asyncio.to_thread(_backup_step, ctx)`. Move the
   `time.sleep(2 ** attempt)` (`:101`) call inside `_checkpoint_step` where it was.
   Add `import asyncio` if the module does not already import it.
2. **Phase 2 (outcome meaningful).** Inside `_checkpoint_step`, capture
   `counts = db.checkpoint("PASSIVE")` and the TRUNCATE result; when the copied-frames
   field is zero while the WAL still has frames (`counts.log > 0`, confirm field name
   at `models.py:16-21`), append `(name, message)` to `errors` naming the frame count
   (REQ-005). Return a success flag derived from the counts rather than a bare `True`.
3. **Phase 3 (bound visible).** Delete the inline `if elapsed > 5:` branch and its
   warning, folding the timing decision into the coordinator's single bound (REQ-003);
   delete the two dead constants `_WAL_CHECKPOINT_TIMEOUT_S` / `_WAL_BACKUP_TIMEOUT_S`
   (`:32-33`).

### Details

- `_checkpoint_step(ctx)` is sync with signature
  `(ctx: AgentContext) -> tuple[bool, list[tuple[str, str]]]`. It reproduces the
  current try / PASSIVE / TRUNCATE / retry logic verbatim except the `await` points
  are gone and the sleeps live here.
- `_backup_step(ctx)` moves `backup_sync`'s path validation, `shutil.copy2` (`:167`),
  and `except Exception` best-effort block unchanged.
- Module docstring: add one sentence stating what a bound-expired checkpoint leaves
  behind (REQ-010, AC-7) — the WAL is replayed or checkpointed on next open; "timed
  out" means "not rolled back", never "left clean".

## Compatibility considerations
Corrections found while implementing: `WalCheckpointCounts` has `busy`, `log_size`, `pages_checkpointed` (no `log`); the step bodies are methods (`_checkpoint_step`, `_backup_step`) rather than module-level functions because they use `self._ctx` and `_is_db_path_allowed`; PASSIVE copying zero frames over a non-empty WAL returns `(False, errors)` so the coordinator runs the defensive backup; a TRUNCATE that returns `busy != 0` (blocked by a reader, no exception) is treated as a failed attempt; the inline `elapsed > 5` branch is deleted as REQ-003 requires.


- Signatures and return types are unchanged, so `resource_shutdown_coordinator.py:72`
  / `:91` call shapes are preserved; no caller edit.
- The change is failure-path only: the live `/opt/llm/db/session.sqlite-wal` is 0
  bytes and the success path still returns `True`; the new zero-frame recording fires
  only under contention.

## Security considerations

- N/A: no auth, secret, or permission change. `allowed_root` validation in
  `backup_sync` is preserved unchanged.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/wal_checkpoint_manager.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_wal_checkpoint_manager.py -q` (new file, must pass).
- `uv run pytest tests/agent/test_repl.py -q` (unchanged files kept as the
  no-production-change proof; must stay green).
- `rg -n "time\.sleep" scripts/agent/wal_checkpoint_manager.py` → only inside the
  worker function; `rg -n "_WAL_CHECKPOINT_TIMEOUT_S|_WAL_BACKUP_TIMEOUT_S" scripts/`
  → empty.
- `uv run ruff format`, `uv run ruff check`,
  `uv run mypy --no-namespace-packages scripts/agent/wal_checkpoint_manager.py`,
  `uv run vulture scripts/agent/wal_checkpoint_manager.py --min-confidence 80`.
- Mutation: deleting the `time.sleep` line must fail the loop-responsiveness test in
  the new file (timing assertion catches it).

## Completion criteria

`checkpoint_sync`/`backup_sync` have await points (run via `to_thread`), no
`time.sleep` runs on the loop, `WalCheckpointCounts` is read, a zero-frame-under
contention checkpoint records a named error, the two constants and the inline `5` are
gone, and the module docstring states the abandoned-step effect. All gates above pass.

## Out of Scope

- The single bound value and its two `wait_for` callers (`resource_shutdown_coordinator.py`) — row 2.
- `scripts/db/helper.py` (REQ-002 is satisfied by keeping the step on one thread).
- Docs updates — rows 6/7. Tests — rows 3/4/5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: wrap both `*_sync` bodies in `asyncio.to_thread` workers, move `time.sleep` inside the worker | Completed | 20261023-144450 | 20261023-144450 | REQ-001, REQ-002, REQ-008 implemented; full suite 9836 passed; procedures corrected (counts field names, step methods, TRUNCATE busy handling, single 30s bound, write_warning, mock counts) |
| 2 | Phase 2: read `WalCheckpointCounts`, record zero-frame-under-contention error, update module docstring | Completed | 20261023-144450 | 20261023-144450 | REQ-005, REQ-006, REQ-010 |
| 3 | Phase 3: fold inline `elapsed > 5` and the two constants into the coordinator's single bound | Completed | 20261023-144450 | 20261023-144450 | Gated on repl001 (REQ-003) |
| 4 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-144450 | 20261023-144450 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 3 | REQ-003 edits `resource_shutdown_coordinator.py`'s bound, which `repl001` holds byte-identical (AC-5) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | Phase 3 | Ordering | Open | implementer | after `plans/20261022-030840_plan.md` implemented |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-005, REQ-006, REQ-008, REQ-003 (bound folding)
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `scripts/agent/wal_checkpoint_manager.py`