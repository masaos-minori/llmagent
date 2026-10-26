## Goal

Close the queued-thread race (`REQ-004`): make `run_with_db_lock()` in `route_helpers.py`
fail fast once shutdown has begun (so a thread still queued on the DB lock never runs SQL
against the closed connection) and track live DB users via the counter that `db_conn.py`
(seq 01/02) owns, backing the bounded-drain option.

## Scope

- **In-Scope** (`scripts/eventbus/route_helpers.py` only):
  - Import `is_shutting_down` (new), `bump_active_db_user` (new), `release_active_db_user` (new) from
    `eventbus.db_conn`.
  - Add a fail-fast guard at the top of `run_with_db_lock()` that raises when shutdown
    has begun.
  - Wrap the locked critical section in `bump_active_db_user()` / `release_active_db_user()`.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shutdown flag + counter definition (`db_conn.py`, seq 02) — these must exist
    first; this document consumes them.
  - The close orchestration in the shared helper (`app.py`, seq 01).
  - The fail-fast-vs-drain policy choice (`UNK-03`) — recorded, not re-decided here.

## Assumptions

- `run_with_db_lock()` (route_helpers.py:131-151) is the single choke point every route
  module and `_dlq_loop` uses to touch the shared connection, so guarding it covers all
  callers (6 route modules + loop, per the plan's `rg` count).
- The current import is `from eventbus.db import get_db_lock`; `eventbus.db` is a
  re-export facade that forbids new exports (`db.py:3-4`), so the new accessors are
  imported directly from `eventbus.db_conn` (same layer, import-linter clean).
- `is_shutting_down()` (seq 02) returns `False` during normal operation, so the new
  guard is a no-op until shutdown begins and cannot affect in-flight requests outside the
  shutdown window.
- `is_shutting_down` (new), `bump_active_db_user` (new), `release_active_db_user` (new) are created by the
  seq 02 document (`db_conn.py`); this document MUST be implemented after seq 02.

## Design decisions

- **Fail-fast at the async entry, not inside the worker thread.** The `is_shutting_down()`
  check runs before `asyncio.to_thread`, so a post-shutdown call refuses immediately
  instead of spawning a thread that then blocks forever on the lock.
- **Counter scoped to the locked critical section.** `bump_active_db_user()` /
  `release_active_db_user()` wrap `func()` under `get_db_lock()`, so the counter reflects
  threads actually holding the lock — the quantity the bounded-drain path waits on.

## Alternatives considered

- **Bump around the whole `asyncio.to_thread` call (including queue wait).** Rejected: a
  thread blocked on the lock is not yet a live user of the connection; counting it would
  keep the counter non-zero during the very drain the helper is trying to complete.
- **Return an error sentinel instead of raising.** Rejected: raising makes the shutdown
  failure visible to callers and test assertions; a silent sentinel would mask it.

## Implementation

### Target file

`scripts/eventbus/route_helpers.py`

### Procedure

1. Add a local import of `is_shutting_down` (new), `bump_active_db_user` (new), `release_active_db_user` (new)
   from `eventbus.db_conn` next to the existing `from eventbus.db import get_db_lock`
   (route_helpers.py:133).
2. In `_locked()`, increment the counter on entering the `with get_db_lock():` block and
   release it in a `finally` around `func()`.
3. Add the `is_shutting_down()` fail-fast guard at the top of `run_with_db_lock()`, after
   `_locked()` is defined and before `asyncio.to_thread(_locked)` (route_helpers.py:146).
4. Run the validation sequence.

### Method

```python
# route_helpers.py — run_with_db_lock (current lines 131-151)
async def run_with_db_lock(func: Any) -> Any:
    """Execute a function inside get_db_lock() via asyncio.to_thread."""
    from eventbus.db import get_db_lock  # noqa: PLC0415
    # seq 02 (db_conn.py): add a local import of is_shutting_down,
    # bump_active_db_user, release_active_db_user (see Procedure step 1)

    def _locked() -> Any:
        """Execute func while holding the DB lock."""
        start_time = time.monotonic()
        try:
            with get_db_lock():
                bump_active_db_user()
                try:
                    return func()
                finally:
                    release_active_db_user()
        finally:
            elapsed = time.monotonic() - start_time
            _db_query_duration.observe(elapsed)

    # REQ-004 fail-fast: refuse new work once shutdown has begun so a thread
    # queued on the lock never runs SQL against the closed connection.
    if is_shutting_down():
        raise RuntimeError("eventbus shutting down: refusing new DB work")

    start_time = time.monotonic()
    result = await asyncio.to_thread(_locked)
    lock_wait = time.monotonic() - start_time
    _db_lock_wait_time.observe(lock_wait)
    if lock_wait > 0.001:
        _db_lock_contention.inc()
    return result
```

### Details

- **`REQ-004` (queued-thread race):** the `is_shutting_down()` guard rejects new calls
  after shutdown begins, so no thread enqueues on `_db_lock` behind a connection that is
  about to be closed.
- **Counter for the drain path:** `bump_active_db_user()` / `release_active_db_user()`
  (seq 02) track holders of the lock; how the seq 01 helper consumes them (bounded wait
  vs. ignore) is the `UNK-03` owner decision, recorded here as fail-fast-by-default.
- Blast radius is 6 route modules + `_dlq_loop`; the guard only changes behavior once
  `is_shutting_down()` is `True`, i.e. strictly within the shutdown window.

## Compatibility considerations

- Purely additive control flow. `run_with_db_lock()`'s signature and normal-path behavior
  are unchanged; the new raise fires only after shutdown begins.
- Post-shutdown callers now see a `RuntimeError` instead of blocking — the intended
  fail-fast. Confirm route handlers surface it as a clean error rather than crashing.

## Security considerations

- No new credentials, secrets, or attack surface. The raised message carries no
  connection paths or secrets.

## Rollback considerations

- Revert the `route_helpers.py` edit (`git checkout scripts/eventbus/route_helpers.py`).
  Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `route_helpers.py` static | Complexity/dead code/security | `uv run ruff scripts/eventbus/route_helpers.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | clean |
| Import boundary | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Fail-fast | Unit: post-shutdown `run_with_db_lock` refuses | `uv run pytest tests/eventbus/test_eventbus_shutdown.py` | raises `RuntimeError` after flag set |

## Completion criteria

- `run_with_db_lock()` imports `is_shutting_down` (new) / `bump_active_db_user` (new) /
  `release_active_db_user` (new) from `eventbus.db_conn`.
- A call after `set_shutdown_flag()` (seq 02) raises before `asyncio.to_thread`.
- The counter wraps the locked critical section.
- ruff, mypy, bandit, vulture, lint-imports pass.

## Out of Scope

- The shutdown flag + counter definition (`db_conn.py`, seq 02).
- The close orchestration (`app.py`, seq 01).
- The fail-fast-vs-drain policy choice (`UNK-03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `eventbus.db_conn` imports; fail-fast `is_shutting_down()` guard; counter wrap around locked section | Completed | 20261026 | 20261026 | Consumes seq 02 accessors — implement after seq 02 Local db_conn imports + is_shutting_down guard before to_thread + counter wrap verified; added clear_shutdown_flag (db_conn) + lifespan-startup reset + tests/eventbus/conftest.py _reset_db_conn_state fixture so module flag does not leak across test lifecycles |
| 2 | Add/update tests per Validation plan | Completed | — | 20261026 | Ad-hoc unit check passed; guard test added to test_eventbus_shutdown.py via seq 04 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261026 | ruff/mypy clean; vulture: accessors now used; lint-imports 6 kept; route metrics + health + isolation tests 14 passed |
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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `scripts/eventbus/route_helpers.py`