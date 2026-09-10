## Goal

Update `_SLOW_CONSUMER_THRESHOLD` usage; add instrumentation.

## Scope

Modify `scripts/eventbus/broker.py`:
- Update `_SLOW_CONSUMER_THRESHOLD` usage to include instrumentation (REQ-004; `scripts/eventbus/broker.py`).
- Add timing instrumentation around slow consumer detection (REQ-004; `scripts/eventbus/broker.py`).
- Export slow consumer metrics via existing metrics infrastructure (REQ-004; `scripts/eventbus/broker.py`).

## Assumptions

- The replay batch size should be configurable via `EventBusConfig` — default value TBD from load testing.
- The register-before-replay ordering must be preserved exactly — batching the SQLite fetch must not change when the broker subscription is registered relative to the replay query.
- Separate read connections or a connection-pool/manager should only be decided after load-test results are available — do not implement speculatively.
- Database-lock instrumentation should use Python's `time.monotonic()` for accurate timing.

## Design decisions

1. **Slow consumer threshold instrumentation (REQ-004)**: Add timing hooks around `_SLOW_CONSUMER_THRESHOLD` checks. Track:
   - Time spent waiting for slow consumer to catch up.
   - Frequency of slow consumer events.
   - Duration of slow consumer periods.

2. **Metrics export (REQ-004)**: Export the following metrics via existing metrics infrastructure:
   - `eventbus_slow_consumer_total` — counter of slow consumer events.
   - `eventbus_slow_consumer_duration_seconds` — histogram of slow consumer durations.

3. **Backward compatibility**: Ensure existing slow consumer behavior remains compatible with new metrics.

## Alternatives considered

- Using Python's `logging` module instead of metrics: would provide visibility but doesn't enable alerting or dashboards.
- Adding a separate monitoring thread: overkill for current needs; prefer lightweight instrumentation within existing code paths.
- Using `asyncio.current_task()` for task-level tracking: adds complexity without clear benefit over simple timing hooks.

## Implementation
### Target file
`samples/eventbus/broker.py`

### Procedure
Update `_SLOW_CONSUMER_THRESHOLD` usage to include instrumentation; add timing instrumentation around slow consumer detection; export metrics.

### Method
1. Add timing hooks around `_SLOW_CONSUMER_THRESHOLD` checks.
2. Add timing instrumentation around slow consumer detection.
3. Export metrics via existing metrics infrastructure (e.g., Prometheus histograms/counters).

### Details
```python
# In broker.py:
import time
from prometheus_client import Histogram, Counter

# New metrics
_slow_consumer_total = Counter(
    'eventbus_slow_consumer_total',
    'Number of slow consumer events',
)
_slow_consumer_duration = Histogram(
    'eventbus_slow_consumer_duration_seconds',
    'Duration of slow consumer events',
)

class EventBusBroker:
    def __init__(self):
        self._slow_consumer_threshold = _SLOW_CONSUMER_THRESHOLD
    
    async def _check_slow_consumer(self, sub):
        """Check if subscriber is slow and track metrics."""
        start_time = time.monotonic()
        
        # ... existing logic ...
        
        if queue_depth >= self._slow_consumer_threshold:
            # Record slow consumer event
            _slow_consumer_total.inc()
            
            # Record duration
            _slow_consumer_duration.observe(time.monotonic() - start_time)
            
            # ... existing slow consumer handling ...
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

- If the new metrics cause issues (e.g., performance regression, incorrect values), revert to the original `broker.py` without these changes.
- The Prometheus metrics can be disabled by removing the `prometheus-client` dependency.
- Timing hooks can be removed without affecting functionality if reverted.

## Validation plan

- Metrics export test: verify new metrics are exported correctly.
- Slow consumer test: verify slow consumer events are tracked accurately.
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
