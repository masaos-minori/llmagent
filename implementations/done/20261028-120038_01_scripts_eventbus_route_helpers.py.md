# Procedure: measure lock wait to acquisition and record query duration in a reachable finally

## Goal

Make `run_with_db_lock` observe lock wait only until acquisition, apply the contention threshold to it and always observe query duration (Plan REQ-001).

## Scope

- Modify only `scripts/eventbus/route_helpers.py`.
- In scope: the body of `_locked()` inside `run_with_db_lock`.
- Out of scope: the shutdown re-check (another Plan), metric names, `health_route.py`, tests, docs.

## Assumptions

- Ordering note: write the failing tests (rows 5 and 6) first, then apply this row.
- `vulture` reports the two lines after `return func()` as unreachable, so the histogram currently has no observations.
- The documented definitions are: wait = from thread submit to lock acquisition; query duration = DB execution while holding the lock.
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Observe wait immediately after the `with get_db_lock():` block is entered; observe query duration in a `finally` around `func()` so a raising callback is still measured.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/eventbus/route_helpers.py`

### Procedure

- Restructure `_locked()`: keep `start_time = time.monotonic()` as the first statement; inside `with get_db_lock():` compute `acquired = time.monotonic()` and `wait = acquired - start_time`, then `_db_lock_wait_time.observe(wait)` and `if wait > 0.001: _db_lock_contention.inc()`.
- Keep `bump_active_db_user()` and the inner `try: return func() finally:`; in that `finally`, call `release_active_db_user()` and then `_db_query_duration.observe(time.monotonic() - acquired)`.
- Delete the outer `try`/`finally` that measured `lock_wait` after the query and the unreachable `elapsed` lines.
- Leave the pre-check before `asyncio.to_thread`, the metric names and the `logger.debug` total-time line unchanged.

### Method

Rewrite one nested function; no new imports.

### Details

- If the shutdown procedure has added its guard, keep it between the wait observation and `bump_active_db_user()`.
- `health_route.py` reads the same histograms, so its `lock_wait_high` and `query_duration_high` reasons now reflect the corrected values.

## Compatibility considerations

- Metric values change meaning to the documented definitions; with real query-duration observations `query_duration_high` can appear (capacity-only, still 503 but tolerated by the deployment gate).

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py tests/eventbus/test_eventbus_health.py -q` | Pass |
| 2 | `uv run ruff format scripts/eventbus/route_helpers.py`; `uv run ruff check scripts/eventbus/route_helpers.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/eventbus/route_helpers.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run vulture scripts/eventbus --min-confidence 80` | No finding in `route_helpers.py` |

## Completion criteria

- An uncontended call records a wait below 1 ms and a positive duration; a contended call increments the contention counter; a raising callback still records duration; `vulture` reports no unreachable code in this function.

## Out of Scope

- Shutdown guard, health route, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-165731 | 20261028-165731 | Applied after tests 05 (red confirmed); keeps the shutdown guard between the wait observation and bump_active_db_user; vulture clean |
| 2 | Add or update tests per Validation plan | Completed | 20261028-165731 | 20261028-165731 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-165731 | 20261028-165731 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-165731 | 20261028-165731 |  |

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
- **Requirement ID**: REQ-001 (timing semantics of run_with_db_lock)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: scripts/eventbus/route_helpers.py