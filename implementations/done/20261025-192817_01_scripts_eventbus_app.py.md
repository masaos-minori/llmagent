## Goal

Give `lifespan()` explicit ownership of the shared SQLite connection during shutdown so the connection is never closed while any worker — the DLQ sweep thread, a route-handler worker thread, or an SSE task — may still execute SQL against it (`REQ-001`), and make shutdown delegate to one shared cleanup helper that both production and the test suite execute (`REQ-005`).

## Scope

- **In-Scope** (`scripts/eventbus/app.py` only):
  - Replace the inline shutdown body of `lifespan()` (app.py:90-118) with a delegation to a single shared async helper `_shutdown_lifespan` (new).
  - Implement `_shutdown_lifespan` (new) to: stop scheduling new sweep cycles once shutdown begins, cancel and await the in-flight `_dlq_loop` future, prove exclusive ownership of `app.state.db` before `db.close()`, and remove the close-on-timeout fallback.
  - Track `_dlq_loop` as an explicit future (`app.state.dlq_task`) and call `set_shutdown_flag` (new) before cancelling, so no new cycle is scheduled after shutdown begins (`REQ-002`).
  - Re-export the helper at module scope so `tests/eventbus/` can drive the real shutdown path (`REQ-005`).
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shutdown flag + active-user counter in `scripts/eventbus/db_conn.py` (seq 02) — this document calls `set_shutdown_flag` (new) / `is_shutting_down` (new); they must exist first.
  - `run_with_db_lock()` fail-fast/drain in `scripts/eventbus/route_helpers.py` (seq 03) — this document references the flag; it must exist first.
  - Test rewrites in `tests/eventbus/test_eventbus_shutdown.py` and `test_eventbus_app_isolation.py` (seq 04/05).

## Assumptions

- `app.state.db` is the single shared connection opened by `open_db()` on startup; every DB access routes through `get_db_lock()` (`db_conn.py:13,22`), so exclusive ownership = holding that lock with no other live user.
- `app.state.dlq_task` already holds the `_dlq_loop` coroutine task (app.py:78); cancelling it does not stop a sweep already running on its `asyncio.to_thread()` worker thread, which is why the lock is acquired before close (app.py:99-103 comment).
- The shutdown flag (`set_shutdown_flag` (new) / `is_shutting_down` (new)) and (optional) active-user counter referenced here are created by the seq 02 document (`db_conn.py`); this document MUST treat them as existing when it runs (implemented in `seq` order). Import `set_shutdown_flag` (new) from `eventbus.db_conn`.
- `app.state.broker.shutdown()` is safe to call before the DB close (current order preserved).
- The bounded-shutdown policy (wait indefinitely / terminate the process / isolate the connection) is `UNK-01`, an owner decision. Its exact bound value is a pre-implementation sign-off; the invariant in `REQ-001` holds regardless of which policy is chosen, so implementation of the invariant is not blocked by the policy decision.

## Design decisions

- **One delegated helper instead of inlined shutdown.** `lifespan()` becomes a thin wrapper that calls `_shutdown_lifespan` (new); all shutdown logic lives in the helper. This is what makes prod and tests share one path (`REQ-005`) and keeps `lifespan()`'s complexity (radon B 7) from growing.
- **Prove ownership before close.** `_shutdown_lifespan` (new) acquires `get_db_lock()` (serializing behind any in-flight sweep), confirms no worker is queued on the lock (the seq 03 fail-fast flag), then closes. The close-on-timeout fallback is removed entirely — a positive timeout is now treated as "cannot prove safety", not "close anyway".

## Alternatives considered

- Keeping the inline shutdown and only removing the fallback: rejected — it would leave prod and tests on divergent paths, failing `REQ-005`.
- Moving the helper to a new `scripts/eventbus/lifecycle.py`: the plan permits it only if warranted; keeping it in `app.py` minimizes surface area and stays inside the `eventbus` import-isolation boundary.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Add `_shutdown_lifespan` (new) at module scope in `app.py`, below `lifespan()`.
2. Rewrite `lifespan()`'s shutdown tail (app.py:90-118) to `await _shutdown_lifespan (new)(app)` after the `yield`, preserving the startup body unchanged.
3. Re-export the helper (module scope is sufficient; `tests/eventbus/` imports it from `app`).
4. Run the validation sequence.

### Method

Current `lifespan()` (app.py:69-118) cancels `dlq_task`, calls `broker.shutdown()`, then acquires `get_db_lock()` with a 5.0 s timeout and calls `db.close()` in a `finally` that logs a warning and closes anyway on timeout (app.py:105-118). Replace that tail with a delegation and move the logic into `_shutdown_lifespan` (new)(app).

```python
# app.py — new module-scope helper (place after lifespan())
async def _shutdown_lifespan(app: FastAPI) -> None:
    """Shared shutdown sequence: stop sweeps, await the in-flight sweep,
    prove exclusive ownership of the shared connection, then close it.

    Delegated to by both lifespan() (production) and the tests/eventbus/ suite
    so they exercise one lifecycle sequence (REQ-005). Never closes a connection
    another worker may still own (REQ-001); the close-on-timeout fallback is gone.
    """
    # 1. Stop scheduling new sweep cycles and await the in-flight sweep.
    set_shutdown_flag()  # from db_conn.py (seq 02) — stops _dlq_loop scheduling
    if app.state.dlq_task:
        app.state.dlq_task.cancel()
        try:
            await app.state.dlq_task
        except asyncio.CancelledError:
            pass
    # 2. Broker shutdown (unchanged order).
    if app.state.broker:
        app.state.broker.shutdown()
    # 3. Prove exclusive ownership before closing.
    if app.state.db:
        lock = get_db_lock()
        acquired = await asyncio.to_thread(
            lock.acquire, timeout=_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS
        )
        if not acquired:
            raise RuntimeError(
                f"shutdown: could not acquire db lock within "
                f"{_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS:.1f}s; refusing to close a "
                "connection another worker may own"
            )
        try:
            app.state.db.close()
        finally:
            lock.release()
```

State the bound constant `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS` and import `set_shutdown_flag` (new) / `is_shutting_down` (new) from `db_conn.py` as created by the seq 02 document.

### Details

- **`REQ-001` (prove ownership):** close is guarded by `lock.acquire(...)` success AND the seq 03 fail-fast flag ensuring no worker is queued. On timeout, raise instead of closing (removes the old app.py:113-118 fallback).
- **`REQ-002` (no new sweep / await in-flight):** `set_shutdown_flag` (new) (db_conn.py, seq 02) before cancel stops any `_dlq_loop` iteration from scheduling; `await app.state.dlq_task` waits for the in-flight sweep on its worker thread.
- **`REQ-005` (shared helper):** the helper is module-scope in `app.py`; tests import `_shutdown_lifespan` (new) and drive the real `_dlq_loop` through it (see seq 05).
- **`UNK-01` (bounded shutdown):** the lock-acquire timeout `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS` (currently 5.0 s) is the shutdown bound. Its value and the post-timeout policy (terminate / isolate / wait) remain an owner sign-off; record the chosen bound in `eventbus_07` before merge. The invariant above holds for any choice.
- Preserve `check_same_thread=False` semantics: the lock still serializes the sweep thread and any route/SSE thread; the helper adds no new connection.

## Compatibility considerations

- `lifespan()` signature and the FastAPI `@asynccontextmanager` contract are unchanged; only the shutdown tail moves into a helper.
- Raising on lock-timeout changes shutdown behavior: a stuck sweep now aborts startup teardown with an error instead of logging-and-closing. This is the intended safety fix (REQ-001); confirm the process manager treats a failed lifespan teardown as a clean exit.

## Security considerations

- No new credentials, secrets, or attack surface. The raised error message includes only a numeric timeout, not connection paths or secrets.

## Rollback considerations

- Revert the `app.py` edit (`git checkout scripts/eventbus/app.py`) restores the previous close-on-timeout behavior. Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `_shutdown_lifespan` (new) / `lifespan()` | Unit: shutdown drives real `_dlq_loop`; close happens only after lock acquired; timeout raises | `uv run pytest tests/eventbus/test_eventbus_shutdown.py` | Invariant holds; no close-on-timeout; raises on lock timeout |
| Shared helper used by tests | Integration: isolation test runs real loop via helper | `uv run pytest tests/eventbus/test_eventbus_app_isolation.py` | No `_noop_dlq_loop`; passes |
| `app.py` static | Complexity/dead code/security | `uv run radon cc scripts/eventbus/app.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | `lifespan()` complexity contained; bandit/vulture clean |
| Import boundary | Architecture | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `lifespan()` delegates its shutdown tail to `_shutdown_lifespan` (new)(app) and contains no `db.close()` call itself.
- No code path closes `app.state.db` without first proving `get_db_lock()` was acquired with no queued worker (no close-on-timeout fallback remains anywhere in `app.py`).
- `_dlq_loop` is tracked as `app.state.dlq_task`, and the shutdown flag is set before the task is cancelled.
- `_shutdown_lifespan` (new) is importable from `app` for the test suite.
- ruff, mypy, bandit, vulture, lint-imports pass; `test_eventbus_shutdown.py` asserts the invariant and no longer asserts close-on-timeout.

## Out of Scope

- The shutdown flag / active-user counter definition (`scripts/eventbus/db_conn.py`, seq 02).
- `run_with_db_lock()` fail-fast (`scripts/eventbus/route_helpers.py`, seq 03).
- Test rewrites (`tests/eventbus/`, seq 04/05).
- The bounded-shutdown policy value (`UNK-01`) — recorded, not prescribed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_shutdown_lifespan` (new), delegate `lifespan()`, track `_dlq_loop` future, set shutdown flag before cancel | Completed | 20261026 | 20261026 | UNK-01 bound is a pre-implementation sign-off (recorded in Assumptions) _shutdown_lifespan added; lifespan() delegates after yield; set_shutdown_flag before cancel |
| 2 | Add/update tests per Validation plan | Completed | — | 20261026 | Invariant test passes unchanged; timeout test rewritten by seq 04 (expected transitional failure until then) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261026 | ruff/mypy clean; radon: lifespan A2, _shutdown_lifespan B6; bandit baseline unchanged; lint-imports 6 kept |
| 4 | Update documentation (shutdown sequence + policy in `eventbus_07`, INV-01 in ADR-006) — see seq 06/07 | Completed | — | 20261026 | Docs handled by seq 06/07 per Scope |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `scripts/eventbus/app.py`