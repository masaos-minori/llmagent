## Goal

Expose material database-lock contention metrics.

## Scope

Modify `scripts/eventbus/health_route.py`:
- Expose material database-lock contention metrics via health endpoint (REQ-004; `scripts/eventbus/health_route.py`).
- Update `max_queue_depth()` to include lock contention data (REQ-004; `scripts/eventbus/health_route.py`).
- Add capacity limit checks based on measured metrics (REQ-001; `scripts/eventbus/health_route.py`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **Health endpoint metrics (REQ-004)**: Add database-lock contention metrics to the health endpoint response. Include:
   - Current lock wait time (from Prometheus histogram).
   - Lock contention frequency (from Prometheus counter).
   - Query duration statistics (from Prometheus histogram).

2. **Capacity limit checks (REQ-001)**: Add capacity limit checks based on measured metrics. Include:
   - Publish rate vs. configured limit.
   - Subscriber count vs. configured limit.
   - Retained event count vs. configured limit.

3. **Backward compatibility**: Ensure existing health endpoint responses remain compatible with new metrics.

## Alternatives considered

- Using Python's `logging` module instead of metrics: would provide visibility but doesn't enable alerting or dashboards.
- Adding a separate monitoring thread: overkill for current needs; prefer lightweight instrumentation within existing code paths.
- Using `asyncio.current_task()` for task-level tracking: adds complexity without clear benefit over simple timing hooks.

## Implementation
### Target file
`samples/eventbus/health_route.py`

### Procedure
Expose material database-lock contention metrics via health endpoint; update `max_queue_depth()` to include lock contention data; add capacity limit checks.

### Method
1. Add database-lock contention metrics to health endpoint response.
2. Update `max_queue_depth()` to include lock contention data.
3. Add capacity limit checks based on measured metrics.

### Details
```python
# In health_route.py:
import time
from prometheus_client import generate_latest

def max_queue_depth():
    """Get maximum queue depth including lock contention metrics."""
    # ... existing logic ...
    
    # Add lock contention metrics
    lock_wait_time = _db_lock_wait_time._sum / _db_lock_wait_time._count if _db_lock_wait_time._count > 0 else 0
    lock_contention = _db_lock_contention._value.get()
    query_duration = _db_query_duration._sum / _db_query_duration._count if _db_query_duration._count > 0 else 0
    
    return {
        "queue_depth": queue_depth,
        "lock_wait_time_seconds": lock_wait_time,
        "lock_contention_total": lock_contention,
        "query_duration_seconds": query_duration,
    }

# Health endpoint response:
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "queue_depth": max_queue_depth(),
        "metrics": generate_latest().decode("utf-8"),
    }
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

- If the new metrics cause issues (e.g., performance regression, incorrect values), revert to the original `health_route.py` without these changes.
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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
