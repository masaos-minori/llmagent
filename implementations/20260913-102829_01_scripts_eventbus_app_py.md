## Goal
Close the shutdown-time race (REQ-001; a short one-clause purpose) between `lifespan()`'s
`db.close()` call and `_dlq_loop`'s background sweep thread, without blocking shutdown
indefinitely if a sweep is stuck (REQ-002).

## Scope
Only `lifespan()`'s shutdown sequence in `scripts/eventbus/app.py`. `_dlq_loop()`'s own
sweep-triggering logic (interval, what it sweeps) is unchanged — this is a shutdown-path
fix, not a change to sweep behavior.

## Assumptions
- `scripts/eventbus/db.py`'s `get_db_lock()` returns the same module-level
  `threading.Lock()` instance that `scripts/eventbus/route_helpers.py`'s
  `run_with_db_lock()` already acquires for every DB operation, including
  `_dlq_loop`'s sweep — confirmed by reading `get_db_lock()`.
- `threading.Lock.acquire(timeout=...)` is available and behaves as documented
  (returns `False` on timeout without raising) — standard library behavior, not
  independently verified here.

## Design decisions
Of the three candidate mechanisms the Plan identified, this implementation adopts:
**route `db.close()` through `get_db_lock()`, with a bounded timeout on the
acquisition used for shutdown.** Concretely: acquire the same lock
`run_with_db_lock()` uses (via `asyncio.to_thread`, so the acquisition itself does not
block the event loop) before calling `db.close()`; release it in a `finally` block if
acquired. If a sweep thread is still running, it necessarily holds this lock, so
`db.close()` cannot proceed until the sweep finishes (or the timeout elapses).

## Alternatives considered
- **Track `_dlq_loop`'s in-flight `run_with_db_lock` call directly** (hold a
  thread/future reference, await it specifically on shutdown): rejected as the primary
  mechanism because it requires `_dlq_loop`/`run_with_db_lock` to expose new state
  (the reference itself) that nothing else currently needs, for the same effect the
  lock-based approach achieves with no new state.
- **Cooperative shutdown signal checked between sweep iterations**: rejected as the
  primary mechanism because it only prevents the *next* sweep from starting — it does
  not, by itself, guarantee the *currently running* sweep finishes before
  `db.close()`, which is exactly REQ-001's requirement. (Combining it with the
  lock-based approach was considered but judged unnecessary: the lock alone already
  satisfies REQ-001, and adding a second mechanism would only add complexity without
  closing a gap the lock leaves open.)

## Implementation
### Target file
scripts/eventbus/app.py

### Procedure
1. Import `get_db_lock` from `eventbus.db` alongside this module's other
   `eventbus.db` imports.
2. Add a module-level timeout constant for the shutdown lock acquisition (e.g.
   `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS`), analogous in placement to the existing
   `_DLQ_INTERVAL` constant.
3. In `lifespan()`'s shutdown section (after the `dlq_task` cancel-and-await block,
   in place of the current unconditional `app.state.db.close()`), acquire
   `get_db_lock()` with the timeout constant — via `asyncio.to_thread` so the
   blocking `Lock.acquire()` call does not block the event loop — then close the DB
   inside a `try`/`finally` that releases the lock only if it was actually acquired.
4. If the lock could not be acquired within the timeout, log a warning naming the
   timeout value before still closing the DB (REQ-002: shutdown must not hang
   indefinitely, even though closing without the lock in this fallback case reverts
   to today's unsafe behavior for that one edge case — this is a bounded-wait
   trade-off, not a silent one, since it is logged).

### Method
Reuse `get_db_lock()` exactly as `run_with_db_lock()` already does — do not construct
a second lock or duplicate its acquisition logic. The shutdown path's lock usage is a
one-off acquire/release, not a wrapped-function pattern, so it does not need a helper
shared with `run_with_db_lock()`.

### Details
- The existing `if app.state.dlq_task: ... await app.state.dlq_task ... except
  asyncio.CancelledError: pass` block is unchanged — it still gives the coroutine a
  chance to observe cancellation between sweep cycles; it is simply no longer relied
  upon as the sole guarantee that no sweep is in flight.
- The existing `if app.state.broker: app.state.broker.shutdown()` line is unchanged
  and keeps its current position (before the DB-close block).
- Only the `if app.state.db: app.state.db.close()` block changes, to the
  lock-acquire-then-close-then-release sequence described in Procedure above.
- No change to `_dlq_loop()`, `sweep_orphans()`, `_shared_promote()`, or any route
  handler.

## Compatibility considerations
No change to any HTTP endpoint's request/response contract. Shutdown takes marginally
longer only when a sweep is genuinely in flight at shutdown time (the common case —
no sweep running — adds a negligible lock-acquire/release cost).

## Security considerations
N/A: no change to authentication, authorization, or data exposure. Purely an
internal shutdown-ordering fix.

## Rollback considerations
Single-file, shutdown-path-only change with no schema or on-disk format impact —
revert this file's diff to roll back. No migration or data cleanup is implied.

## Validation plan
- Add a regression test (see the companion test file's Validation plan for exact
  location) that deliberately delays `sweep_orphans`/`_shared_promote` so a sweep is
  guaranteed to still be running when the test's `TestClient` context exits, and
  asserts shutdown completes without a crash.
- Run `uv run pytest tests/eventbus/ -q --timeout=30` at least 10 consecutive times
  (this is a timing-dependent race; a single clean run is not sufficient evidence)
  and confirm no `Fatal Python error: Segmentation fault`.
- Run `uv run pytest tests/eventbus/test_eventbus_dlq*.py -v` to confirm DLQ
  promotion behavior is unaffected by the shutdown-path change.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, full test suite, diff-cover.

## Completion criteria
- The regression test forcing the shutdown-vs-sweep race passes without crashing.
- 10+ consecutive full `tests/eventbus/` runs show no Segmentation Fault.
- `tests/eventbus/test_eventbus_dlq*.py` passes unchanged.
- Standard validation sequence passes with no new findings.

## Out of scope
- The `_ROUTE_ROLE_MAP` routing fix, the per-role token validation fix, and the
  `require_consumer_identity` missing-default fix — each is a separate Plan/issue.
- Any change to `sweep_orphans()`/`_shared_promote()`'s DLQ-promotion correctness.
- Adding the cooperative shutdown-signal mechanism (see Alternatives considered) —
  not required to satisfy REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-093534_eb003_eventbus-dlq-loop-shutdown-segfault.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094951_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-102829
- **Related target files**: scripts/eventbus/app.py
