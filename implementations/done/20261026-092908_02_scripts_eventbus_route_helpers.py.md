## Goal

Split the single `run_with_db_lock()` duration in `scripts/eventbus/route_helpers.py` into
independent dispatch / lock-wait / DB-execution / total measurements so the
`lock_wait_high` and `query_duration_high` degraded reasons measure distinct quantities
(REQ-004; Acceptance 3).

## Scope

- Modify only `scripts/eventbus/route_helpers.py`: `run_with_db_lock()` (current lines
  131-151) and its timing helper closure.

## Assumptions

- The three existing metric names (`eventbus_db_lock_wait_time_seconds`,
  `eventbus_db_query_duration_seconds`, `eventbus_db_lock_contention_total`) are consumed by
  monitors and must stay stable; the new timing is additive.
- `test_eventbus_route_helpers_metrics.py::test_query_duration_metric_observed` asserts the
  `_db_query_duration` histogram is still observed after any change — the observation must be
  preserved, now measured while holding the lock.

## Design decisions

- **Four independent durations.** Measure (a) total wall time from submit to completion,
  (b) thread-dispatch time (submit → lock-acquire start), (c) lock-wait time (lock-acquire
  start → lock held), (d) DB-execution time (while holding the lock, i.e. the current
  `_db_query_duration` body moved inside the `with`). Compare the degraded thresholds against
  independent measurements so `lock_wait_high` and `query_duration_high` no longer overlap
  (REQ-004; Acceptance 3).
- **Stable names.** Keep the three existing metric names; extract a small `_DbTiming` (new) helper to
  keep `run_with_db_lock` complexity low.

## Alternatives considered

- Measuring only lock-wait separately and leaving `_db_query_duration` spanning the lock
  acquire: rejected — it still overlaps lock wait, the defect being fixed.

## Implementation

### Target file

`scripts/eventbus/route_helpers.py`

### Procedure

1. In `run_with_db_lock()` (lines 131-151), capture `total_start = time.monotonic()` before
   `await asyncio.to_thread(_locked)` and compute total elapsed after it returns.
2. Inside the `_locked()` closure, move `_db_query_duration.observe(elapsed)` to fire AFTER
   `with get_db_lock()` is entered (i.e. observe the duration spent executing `func()` while
   the lock is held), not before acquiring it. This isolates DB-execution time from lock
   wait (REQ-004).
3. Keep `lock_wait` measured as (lock-acquire start → lock held) via a timestamp taken just
   before `with get_db_lock()`, distinct from the total dispatch time measured in the outer
   scope.
4. Preserve the `_db_lock_contention.inc()` branch (line 149-150) unchanged.

### Method

In-place refactor of `run_with_db_lock()`; add a local `_DbTiming` (new) helper if complexity
grows. No new module-level symbols.

### Details

- The current `_db_query_duration.observe(elapsed)` (lines 142-143) measures from before the
  lock to after `func()`; move the observe inside the `with` block so it excludes lock wait.
- Dispatch time = outer `total` minus lock-wait; record it if a fourth metric is desired, but
  keep the three existing metric names stable.

## Compatibility considerations

- `_db_query_duration` now measures execution-only rather than execution-plus-lock-wait.
  Document the semantic change in `docs/24_eventbus/eventbus_10_health_endpoint.md` (seq 13)
  so monitors interpret the histogram correctly.

## Security considerations

- N/A: observability/timing change only; no secrets or token handling (INV-05 satisfied).

## Rollback considerations

- Revert the commit; the previous combined timing is restored.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py` — assert
  `_db_query_duration` is still observed (now inside the lock) and that execution time excludes
  lock wait; `lock_wait_high` and `query_duration_high` are independent.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run radon cc scripts/eventbus/route_helpers.py`; keep `run_with_db_lock` at or below its
  baseline (M, low).
- `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- `run_with_db_lock()` reports four independent durations; DB-execution time excludes lock
  wait, and the two degraded reasons compare independent measurements.

## Out of Scope

- Adding a fourth exported metric beyond the three existing stable names.
- Changing the degraded-threshold values (operational config, out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Split `run_with_db_lock()` into dispatch/lock-wait/execution/total timings | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `scripts/eventbus/route_helpers.py`
