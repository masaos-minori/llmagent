## Goal

Remove the `_noop_dlq_loop` monkeypatch and the inline `_do_cleanup` from `tests/eventbus/test_eventbus_app_isolation.py` so the suite drives shutdown through the shared helper with the real `_dlq_loop`, unifying production and test lifecycle (`REQ-005`).

## Scope

- **In-Scope** (`tests/eventbus/test_eventbus_app_isolation.py` only):
  - Delete the `_do_cleanup` helper (unused in this file).
  - Delete the `_noop_dlq_loop` definition and its `monkeypatch.setattr(eb_app, "_dlq_loop", _noop_dlq_loop)` call in `_make_client`.
  - Let the real `_dlq_loop` run; rely on `lifespan()`'s shutdown (which delegates to the shared helper) for teardown.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shared helper `_shutdown_lifespan` (new) that proves exclusive ownership before close (`app.py`, seq 01).
  - The shutdown flag + counter (`db_conn.py`, seq 02) and the fail-fast guard (`route_helpers.py`, seq 03).

## Assumptions

- The segfault the `_noop_dlq_loop` workaround dodged is caused by closing the shared connection while `_dlq_loop`'s sweep thread still runs. The shared helper `_shutdown_lifespan` (new) (seq 01) proves exclusive ownership (acquires `get_db_lock()`, no queued worker) before `db.close()`, so the real loop is now safe — the workaround is redundant.
- `lifespan()` (app.py:69-118) delegates its shutdown tail to `_shutdown_lifespan` (new); a `TestClient(eb_app.app)` context runs that shutdown on exit, so removing the monkeypatch lets the real lifecycle drive teardown.
- This document is implemented after seq 01/02/03, so `_shutdown_lifespan` (new), `set_shutdown_flag` (new), `is_shutting_down` (new) exist.
- The `_dlq_loop` (app.py:121) is the real background sweep; replacing it is what the workaround avoided.

## Design decisions

- **Delete the workaround rather than relocate it.** The `_noop_dlq_loop` exists only to dodge a crash the fix removes; keeping a no-op loop would defeat REQ-005's "prod and tests share one lifecycle" by giving tests a different (non-real) sweep.
- **Delete the unused inline cleanup.** `_do_cleanup` is not called anywhere in this file; the shared helper owns teardown.

## Alternatives considered

- **Keep `_noop_dlq_loop` but route its teardown through the helper.** Rejected: a no-op loop is not the real lifecycle; it would diverge from production and violate REQ-005.
- **Move `_do_cleanup` into a call to `_shutdown_lifespan` (new).** Rejected: the helper is invoked by `lifespan()` on TestClient exit; an explicit call would duplicate teardown.

## Implementation

### Target file

`tests/eventbus/test_eventbus_app_isolation.py`

### Procedure

1. Delete the module-level `_do_cleanup` function (the `async def _do_cleanup() -> None:` block).
2. In `_make_client`, delete the `_noop_dlq_loop` inner coroutine and the `monkeypatch.setattr(eb_app, "_dlq_loop", _noop_dlq_loop)` line, together with the segfault-comment block that introduces them.
3. Run the validation sequence.

### Method

Remove the following from the current file.

`_do_cleanup` (module scope):

```python
# REMOVE — unused in this file; teardown is owned by lifespan()/shared helper
async def _do_cleanup() -> None:
    from eventbus import app as eb_app

    if eb_app.app.state.dlq_task:
        eb_app.app.state.dlq_task.cancel()
        try:
            await eb_app.app.state.dlq_task
        except asyncio.CancelledError:
            pass
    if eb_app.app.state.broker:
        eb_app.app.state.broker.shutdown()
    if eb_app.app.state.db:
        eb_app.app.state.db.close()
```

The `_noop_dlq_loop` block inside `_make_client`:

```python
# REMOVE — real _dlq_loop is safe once the shared helper proves ownership
    async def _noop_dlq_loop(app: Any) -> None:
        await asyncio.sleep(9999)

    monkeypatch.setattr(eb_app, "_dlq_loop", _noop_dlq_loop)
```

After removal, `_make_client` keeps the config build, the schema-path monkeypatches, and `TestClient(eb_app.app)`; the real `_dlq_loop` starts on client enter and is shut down through `_shutdown_lifespan` (new) on client exit.

### Details

- **`REQ-005` (one lifecycle):** with the no-op removed, the test exercises the same `_dlq_loop` + shared-helper shutdown that production `lifespan()` runs.
- **No new teardown code:** the helper is entered by `lifespan()` on `TestClient` exit; adding an explicit call would double-close.
- Blast radius is test-only; repeated full `tests/eventbus/` runs validate that the real loop no longer segfaults.

## Compatibility considerations

- Test-only change. Removing `_do_cleanup` and `_noop_dlq_loop` affects only this file; other test files keep their own `_do_cleanup` copies.

## Security considerations

- No new credentials, secrets, or attack surface.

## Rollback considerations

- Revert the `test_eventbus_app_isolation.py` edit (`git checkout tests/eventbus/test_eventbus_app_isolation.py`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `test_eventbus_app_isolation.py` | Unit: real `_dlq_loop` through shared helper, isolation intact | `uv run pytest tests/eventbus/test_eventbus_app_isolation.py` | passes; no `_noop_dlq_loop` |
| Whole suite | Integration: repeated runs, no SQLite crash | `uv run pytest tests/eventbus/` (repeat) | no `Fatal Python error: Segmentation fault` |
| Static | Complexity/dead code/security | `uv run ruff scripts/eventbus/`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | clean |
| Import boundary | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `_do_cleanup` and `_noop_dlq_loop` are removed from `test_eventbus_app_isolation.py`; no reference to either remains.
- The real `_dlq_loop` runs; shutdown is driven through `_shutdown_lifespan` (new) with proven exclusive ownership.
- Isolation assertions (different db/broker/config per client) still pass.
- ruff, mypy, bandit, vulture, lint-imports pass; repeated full `tests/eventbus/` runs complete without a SQLite crash.

## Out of Scope

- The shared helper `_shutdown_lifespan` (new) (`app.py`, seq 01).
- The shutdown flag + counter (`db_conn.py`, seq 02) and the fail-fast guard (`route_helpers.py`, seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `_do_cleanup` + `_noop_dlq_loop`; let the real `_dlq_loop` run through the shared helper | Pending | — | — | Relies on `_shutdown_lifespan` (new) from lifespan() — implement after seq 01/02/03 |
| 2 | Add/update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `tests/eventbus/test_eventbus_app_isolation.py`
