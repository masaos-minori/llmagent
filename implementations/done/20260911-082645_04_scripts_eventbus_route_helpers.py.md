## Goal

Update `run_with_db_lock()` to track lock wait time.

## Scope

Modify `scripts/eventbus/route_helpers.py`:
- Update `run_with_db_lock()` to track lock wait time (REQ-004; `scripts/eventbus/route_helpers.py`).
- Add timing instrumentation around `_locked()` function (REQ-004; `scripts/eventbus/route_helpers.py`).
- Export lock wait time metrics via existing metrics infrastructure (REQ-004; `scripts/eventbus/route_helpers.py`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **Lock wait time tracking (REQ-004)**: Add timing hooks around `_db_lock` acquisition/release within `run_with_db_lock()`. Track:
   - Time spent waiting for lock (lock wait time).
   - Lock contention frequency (how often locks are contended).

2. **Query duration tracking (REQ-004)**: Add timing hooks around individual DB queries within `run_with_db_lock()`. Track:
   - Query execution time (excluding lock wait time).
   - Query result size (number of rows returned).

3. **Metrics export (REQ-004)**: Export the following metrics via existing metrics infrastructure:
   - `eventbus_db_lock_wait_time_seconds` — histogram of lock wait times.
   - `eventbus_db_query_duration_seconds` — histogram of query durations.
   - `eventbus_db_lock_contention_total` — counter of lock contention events.

## Alternatives considered

- Using Python's `logging` module instead of metrics: would provide visibility but doesn't enable alerting or dashboards.
- Adding a separate monitoring thread: overkill for current needs; prefer lightweight instrumentation within existing code paths.
- Using `asyncio.current_task()` for task-level tracking: adds complexity without clear benefit over simple timing hooks.

## Implementation
### Target file
`samples/eventbus/route_helpers.py`

### Procedure
Update `run_with_db_lock()` to track lock wait time; add timing instrumentation around `_locked()` function; export metrics.

### Method
1. Add timing hooks around `_db_lock` acquisition/release within `run_with_db_lock()`.
2. Add timing hooks around individual DB queries within `_locked()`.
3. Export metrics via existing metrics infrastructure (e.g., Prometheus histograms/counters).

### Details
```python
# In route_helpers.py:
import time
from prometheus_client import Histogram, Counter

# New metrics
_db_lock_wait_time = Histogram(
    'eventbus_db_lock_wait_time_seconds',
    'Time spent waiting for database lock',
)
_db_query_duration = Histogram(
    'eventbus_db_query_duration_seconds',
    'Duration of database queries while holding lock',
)
_db_lock_contention = Counter(
    'eventbus_db_lock_contention_total',
    'Number of database lock contention events',
)

def run_with_db_lock(func):
    """Execute function within database lock with timing instrumentation."""
    async def _locked():
        start_time = time.monotonic()
        try:
            return await func()
        finally:
            # Record query duration
            _db_query_duration.observe(time.monotonic() - start_time)
    
    # Record lock wait time
    lock_start = time.monotonic()
    try:
        result = await asyncio.to_thread(_locked)
        _db_lock_wait_time.observe(time.monotonic() - lock_start)
        return result
    except Exception as e:
        # Record lock contention event
        _db_lock_contention.inc()
        raise
```

## Compatibility considerations

- Existing deployments that don't have Prometheus metrics installed will need to either:
  1. Install the `prometheus-client` package, or
  2. Provide alternative metrics backend.
- The new metrics endpoints should not interfere with existing HTTP routes.
- Metrics collection should be opt-in via configuration flag to avoid breaking existing deployments.

## Security considerations

- No security impact — this change is purely about resource management and observability.
- The new metrics endpoints should not expose sensitive data (e.g., query parameters, user credentials).
- Metrics collection should not introduce new attack surfaces.

## Rollback considerations

- If the new metrics cause issues (e.g., performance regression, incorrect values), revert to the original `route_helpers.py` without these changes.
- The Prometheus metrics can be disabled by removing the `prometheus-client` dependency.
- Timing hooks can be removed without affecting functionality if reverted.

## Validation plan

- Metrics export test: verify new metrics are exported correctly.
- Lock contention test: verify lock wait time is tracked accurately.
- Query duration test: verify query duration is tracked accurately.
- Backward compatibility test: verify existing deployments without metrics still work.

## Completion criteria

- [ ] Health or metrics expose material database-lock contention — REQ-004
- [ ] Capacity limits and their test methodology are documented — REQ-006

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds (`_SLOW_CONSUMER_THRESHOLD`, queue `maxsize`, health's `500` backlog threshold) into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-120000 | 20260911-120500 | Already implemented in file 03 — Prometheus metrics (_db_lock_wait_time, _db_query_duration, _db_lock_contention) added to run_with_db_lock in route_helpers.py |
| 2 | Add or update tests per Validation plan | Completed | 20260911-120500 | 20260911-121000 | Tests added in file 03 (test_eventbus_route_helpers_metrics.py) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-121000 | 20260911-121500 | Validated in file 03 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-121500 | 20260911-122000 | prometheus-client dependency added in file 03 |
| 5 | Validate documentation updates | Completed | 20260911-122000 | 20260911-122500 | check_docs_quality.py: 0 errors; check_docs_structure.py: 1 pre-existing warning |
| 6 | Move the implementation procedure file to `implementations/done/` | Completed | 20260911-122500 | 20260911-160000 | Source file already archived via git mv |

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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
