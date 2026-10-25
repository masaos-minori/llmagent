## Goal

Give the connection layer (`db_conn.py`) ownership of the shutdown signal and the
optional active-user counter so the shared cleanup helper (`app.py`, seq 01) can prove
exclusive connection ownership before close (`REQ-001`) and `run_with_db_lock()`
(`route_helpers.py`, seq 03) can fail fast for a thread still queued on the lock after
shutdown begins (`REQ-004`). Co-locate the flag with `get_db_lock()` where the lock
lives.

## Scope

- **In-Scope** (`scripts/eventbus/db_conn.py` only):
  - Add module-level `_shutting_down` flag and `_active_db_users` (new) counter next to
    `_db_lock`.
  - Add `set_shutdown_flag()`, `is_shutting_down()`, `bump_active_db_user()`, and
    `release_active_db_user()` after `get_db_lock()`.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The close orchestration in the shared helper `_shutdown_lifespan` (new) (`app.py`, seq 01)
    — this document supplies the flag/accessors it consumes; it must exist first.
  - The `run_with_db_lock()` flag-check and counter update (`route_helpers.py`, seq 03).
  - The bounded-shutdown policy value (`UNK-01`) and fail-fast-vs-drain choice (`UNK-03`)
    — recorded, not prescribed here.

## Assumptions

- `get_db_lock()` returns the same module-level `threading.Lock()` (`_db_lock`,
  `db_conn.py:13`) that every DB operation acquires, including `_dlq_loop`'s sweep —
  confirmed by reading `db_conn.py`. Exclusive ownership of the shared connection =
  holding `_db_lock` with no other live user.
- The shutdown flag and counter live in `db_conn.py` because the lock does; `app.py`'s
  `_shutdown_lifespan` (new) (seq 01) imports `set_shutdown_flag` (new) / `is_shutting_down` (new) from
  here, and `route_helpers.py`'s `run_with_db_lock` (seq 03) reads the flag and updates
  the counter. This document MUST be implemented before those two.
- The counter supports the bounded-drain option only. Whether shutdown fails fast or
  drains in-flight work is an owner decision (`UNK-03`); the flag alone closes the
  queued-thread race (`REQ-004`) regardless of that choice.

## Design decisions

- **Flag co-located with the lock.** `_shutting_down` and `_active_db_users` (new) sit directly
  after `_db_lock` so callers read them without importing across layers and without
  crossing the `eventbus` import-linter boundary.
- **Accessors instead of bare attributes.** `set_shutdown_flag()` / `is_shutting_down()`
  encapsulate the flag so a future change (e.g. an `asyncio.Event`) does not ripple to
  every caller; the counter gets symmetric `bump_active_db_user()` /
  `release_active_db_user()`.

## Alternatives considered

- **`asyncio.Event` instead of a bool flag.** Rejected: the lock and the shutdown signal
  are synchronous and single-process, so a plain bool is sufficient and matches the
  `threading.Lock` model already in the file.
- **Counter in `app.state`.** Rejected: the plan keeps the flag + counter in the
  connection layer; `app.state` stays application-level.

## Implementation

### Target file

`scripts/eventbus/db_conn.py`

### Procedure

1. Add `_shutting_down = False` and `_active_db_users = 0` immediately after
   `_db_lock = threading.Lock()` (db_conn.py:13).
2. Add `set_shutdown_flag()`, `is_shutting_down()`, `bump_active_db_user()`, and
   `release_active_db_user()` immediately after `get_db_lock()` (db_conn.py:28).
3. Run the validation sequence.

### Method

```python
# db_conn.py — add right after `_db_lock = threading.Lock()` (line 13)
_shutting_down = False
_active_db_users = 0


# db_conn.py — add immediately after get_db_lock() (line 28)
def set_shutdown_flag() -> None:
    """Mark shutdown as begun.

    Called by the shared cleanup helper (app.py, seq 01) before closing the shared
    connection. Makes run_with_db_lock() refuse new work for any thread still queued
    on the lock (REQ-004). Idempotent.
    """
    global _shutting_down
    _shutting_down = True


def is_shutting_down() -> bool:
    """Return True once shutdown has begun."""
    return _shutting_down


def bump_active_db_user() -> None:
    """Increment the count of live DB users (called by run_with_db_lock())."""
    global _active_db_users
    _active_db_users += 1


def release_active_db_user() -> None:
    """Decrement the count of live DB users after the locked critical section."""
    global _active_db_users
    if _active_db_users > 0:
        _active_db_users -= 1
```

### Details

- **`REQ-004` (queued-thread race):** `is_shutting_down()` lets `run_with_db_lock()`
  refuse to enqueue once shutdown has begun, so a thread blocked on `_db_lock` never runs
  SQL against the closed connection.
- **`REQ-001` (prove ownership):** `set_shutdown_flag()` is called first by the seq 01
  helper before `db.close()`, so no new user can start while the close proves exclusive
  ownership.
- **Counter semantics:** `bump_active_db_user()` / `release_active_db_user()` wrap the
  locked critical section in `run_with_db_lock()` (seq 03); they back the bounded-drain
  option and are inert under a fail-fast policy.

## Compatibility considerations

- Purely additive. `get_db_lock()`, `open_db()`, `check_db()`, and `_db_lock` are
  unchanged; existing callers are unaffected.

## Security considerations

- No new credentials, secrets, or attack surface.

## Rollback considerations

- Revert the `db_conn.py` edit (`git checkout scripts/eventbus/db_conn.py`). Single
  logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `db_conn.py` static | Complexity/dead code/security | `uv run ruff scripts/eventbus/db_conn.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | clean |
| Import boundary | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |
| Types | Quality gate | `uv run mypy scripts/eventbus/db_conn.py` | Pass |

## Completion criteria

- `_shutting_down` and `_active_db_users` (new) exist at module scope next to `_db_lock`.
- `set_shutdown_flag()`, `is_shutting_down()`, `bump_active_db_user()`, and
  `release_active_db_user()` are defined and importable from `eventbus.db_conn`.
- ruff, mypy, bandit, vulture, lint-imports pass.

## Out of Scope

- The close orchestration in `app.py`'s `_shutdown_lifespan` (new) (seq 01).
- The `run_with_db_lock()` flag-check / counter update (`route_helpers.py`, seq 03).
- The bounded-shutdown policy value (`UNK-01`) and fail-fast-vs-drain choice (`UNK-03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_shutting_down` flag + `_active_db_users` (new) counter next to `_db_lock`; add `set_shutdown_flag` (new) / `is_shutting_down` (new) / `bump_active_db_user` (new) / `release_active_db_user` (new) | Pending | — | — | Accessors consumed by seq 01 (app.py) and seq 03 (route_helpers.py) — implement in `seq` order |
| 2 | Add/update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation (shutdown sequence + policy in `eventbus_07`, INV-01 in ADR-006) — see seq 06/07 | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `scripts/eventbus/db_conn.py`
