## Goal

Rewrite `tests/eventbus/test_eventbus_shutdown.py` so it asserts the connection-ownership invariant (`REQ-001`) directly and replaces the removed close-on-timeout fallback with an assertion of the documented bounded-shutdown behavior (`REQ-006`), while keeping the real `_dlq_loop` (no no-op replacement).

## Scope

- **In-Scope** (`tests/eventbus/test_eventbus_shutdown.py` only):
  - Keep `test_shutdown_waits_for_inflight_sweep_before_closing_db` asserting the invariant (shutdown completes without crashing while a sweep is in flight).
  - Replace `test_shutdown_logs_warning_when_lock_timeout_exceeded` with a test asserting that lock-acquire timeout raises instead of logging-and-closing.
- **Out-of-Scope** (handled by sibling documents this Plan generates):
  - The shared helper `_shutdown_lifespan` (new) that raises on timeout (`app.py`, seq 01) — this test drives it via `lifespan()`.
  - The shutdown flag + counter (`db_conn.py`, seq 02) and the fail-fast guard (`route_helpers.py`, seq 03).
  - The `_noop_dlq_loop` workaround in `test_eventbus_app_isolation.py` (seq 05).

## Assumptions

- `lifespan()` (app.py:69-118) delegates its shutdown tail to the shared helper `_shutdown_lifespan` (new) (seq 01), which acquires `get_db_lock()` (db_conn.py:13) and, on timeout, raises `RuntimeError` ("could not acquire db lock within …s; refusing to close a connection another worker may own") instead of the old log-and-close fallback. This test asserts that raise.
- The sweep thread holds `_db_lock` while `sweep_orphans()` runs inside `run_with_db_lock()` (route_helpers.py, seq 03); forcing `sweep_orphans` to block keeps the lock held so the shutdown lock-acquire times out.
- This document is implemented after seq 01/02/03, so `_shutdown_lifespan` (new), `set_shutdown_flag` (new), `is_shutting_down` (new), and the counter accessors exist when the test runs.

## Design decisions

- **Keep the in-flight-sweep test as the invariant assertion.** `test_shutdown_waits_for_inflight_sweep_before_closing_db` already proves the invariant: shutdown completes without a crash while the sweep still owns the connection. It needs no change.
- **Convert the timeout test from "log warning + close" to "raise".** The close-on-timeout fallback is removed (REQ-001); the bounded-shutdown policy is refuse-to-close. The new test forces the sweep to hold the lock past the bound and asserts `lifespan()` raises.

## Alternatives considered

- **Assert the old behavior (warning logged, DB closed anyway).** Rejected: that is the unsafe fallback this Plan removes (REQ-001); keeping it would re-enforce the defect.
- **Assert a bare `Exception` instead of `RuntimeError`.** Rejected: the helper raises `RuntimeError` specifically; asserting the concrete type pins the intended policy.

## Implementation

### Target file

`tests/eventbus/test_eventbus_shutdown.py`

### Procedure

1. Leave `test_shutdown_waits_for_inflight_sweep_before_closing_db` unchanged — it already asserts the invariant.
2. Replace `test_shutdown_logs_warning_when_lock_timeout_exceeded` with `test_shutdown_raises_when_lock_timeout_exceeded` (new): set a short `_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS`, force `sweep_orphans` to hold the lock, and assert `lifespan()` raises `RuntimeError` matching "could not acquire db lock within"; release the sweep in a `finally`.
3. Run the validation sequence.

### Method

```python
# test_eventbus_shutdown.py — replace test_shutdown_logs_warning_when_lock_timeout_exceeded
@pytest.mark.asyncio
async def test_shutdown_raises_when_lock_timeout_exceeded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the sweep still holds the lock when the shutdown timeout elapses,
    shutdown must refuse to close the connection (REQ-001) by raising, rather
    than logging a warning and closing anyway (the removed fallback)."""
    from eventbus import app as eb_app

    cfg = _make_config(tmp_path)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: _SCHEMA_PATH)
    monkeypatch.setattr(eb_app, "_SHUTDOWN_DB_LOCK_TIMEOUT_SECONDS", 0.05)

    sweep_started = threading.Event()
    release_sweep = threading.Event()

    def blocking_sweep_orphans(db: Any, deadletter_dir: str, max_retry: int) -> int:
        sweep_started.set()
        # Hold the lock (via run_with_db_lock) so the shutdown lock-acquire
        # cannot succeed within the bound, exercising the refuse-to-close path.
        release_sweep.wait(timeout=5)
        return 0

    monkeypatch.setattr(eb_app, "sweep_orphans", blocking_sweep_orphans)
    monkeypatch.setattr(eb_app, "_DLQ_INTERVAL", 3600.0)

    try:
        with pytest.raises(RuntimeError, match="could not acquire db lock within"):
            async with eb_app.lifespan(eb_app.app):
                started = await asyncio.to_thread(sweep_started.wait, 5)
                assert started, "sweep thread did not start within the timeout"
                # Deliberately do not release the sweep here — the shutdown
                # lock-acquire (timeout 0.05s) must exceed its bound while the
                # sweep still holds the lock, so lifespan() raises.
    finally:
        # Let the still-blocked sweep thread exit before the test ends.
        release_sweep.set()
```

### Details

- **`REQ-006` (invariant over fallback):** the rewritten test no longer asserts `"db lock not acquired"` is logged or that the DB is closed on timeout. It asserts the bounded-shutdown policy: a positive lock-acquire timeout means "cannot prove safety", so `lifespan()` (via `_shutdown_lifespan` (new)) raises.
- **No no-op loop:** the real `_dlq_loop` runs; the test only forces its first sweep to block, exactly as the in-flight-sweep test does.
- Blast radius is test-only; the assertion pins production shutdown behavior for all callers of `lifespan()`.

## Compatibility considerations

- Test-only change. The removed test name `test_shutdown_logs_warning_when_lock_timeout_exceeded` must not be referenced elsewhere; the new name `test_shutdown_raises_when_lock_timeout_exceeded` (new) is self-contained.

## Security considerations

- No new credentials, secrets, or attack surface. The asserted error message carries only a numeric timeout, not connection paths or secrets.

## Rollback considerations

- Revert the `test_eventbus_shutdown.py` edit (`git checkout tests/eventbus/test_eventbus_shutdown.py`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `test_eventbus_shutdown.py` | Unit: in-flight-sweep invariant + timeout raises | `uv run pytest tests/eventbus/test_eventbus_shutdown.py` | both tests pass; timeout raises `RuntimeError` |
| Whole suite | Integration: repeated runs, no SQLite crash | `uv run pytest tests/eventbus/` (repeat) | no `Fatal Python error: Segmentation fault` |
| Static | Complexity/dead code/security | `uv run ruff tests/eventbus/test_eventbus_shutdown.py`; `uv run vulture scripts/eventbus/`; `uv run bandit scripts/eventbus/ -c pyproject.toml` | clean |
| Import boundary | Architecture contract | `PYTHONPATH=scripts uv run lint-imports` | `eventbus-is-isolated` KEPT |

## Completion criteria

- `test_shutdown_waits_for_inflight_sweep_before_closing_db` still asserts the invariant (shutdown completes while a sweep is in flight).
- `test_shutdown_raises_when_lock_timeout_exceeded` (new) asserts `lifespan()` raises `RuntimeError` on lock-acquire timeout; no test requires close-on-timeout anywhere in the file.
- The real `_dlq_loop` runs; no `_noop_dlq_loop` remains.
- ruff, mypy, bandit, vulture, lint-imports pass; repeated full `tests/eventbus/` runs complete without a SQLite crash.

## Out of Scope

- The shared helper `_shutdown_lifespan` (new) (`app.py`, seq 01).
- The shutdown flag + counter (`db_conn.py`, seq 02) and the fail-fast guard (`route_helpers.py`, seq 03).
- The `_noop_dlq_loop` workaround in `test_eventbus_app_isolation.py` (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the timeout test to assert refuse-to-close raise; keep the in-flight-sweep invariant test; keep the real `_dlq_loop` | Pending | — | — | Drives `_shutdown_lifespan` (new) via lifespan() — implement after seq 01/02/03 |
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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261023-154326_eventbus004_shutdown-safe-during-sweep.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-113939_eventbus004_shutdown-safe-during-sweep.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-192817
- **Related target files**: `tests/eventbus/test_eventbus_shutdown.py`
