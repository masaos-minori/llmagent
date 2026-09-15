## Goal

Return stable degraded responses using supported metrics interfaces rather than reaching into another module's private internals, ensuring the health endpoint remains reliable when dependencies or metrics are unavailable.

## Scope

Replace private Prometheus API access in `health_route.py` with supported public interfaces; add graceful degradation for metric-read failures; move broker backlog threshold check inside broker None guard.

## Assumptions

- A: The Prometheus Histogram class has a public `.metrics()` method that returns metric objects — confirmed by prometheus_client library documentation
- B: The Prometheus Counter class has a public `.metrics()` method that returns metric objects — confirmed by prometheus_client library documentation
- C: The health endpoint already guards broker property access with `if broker is not None:` at line 53, but line 65 accesses `broker.backlog_health_threshold` outside this guard — confirmed by `health_route.py:53-65`
- D: The `_hist_avg()` function at line 71-84 already catches `(AttributeError, TypeError, ZeroDivisionError)` — confirmed by `health_route.py:83`
- E: The `_db_lock_contention._value.get()` at line 88 is the only place where a private Counter attribute is accessed directly — confirmed by code inspection

## Design decisions

- Use `prometheus_client.Counter.collect()` and `prometheus_client.Histogram.collect()` public APIs instead of private `_samples()` and `_value.get()` access.
- Add public getter functions in `route_helpers.py` following the existing `get_*` naming convention.
- Move the broker backlog threshold check inside the `if broker is not None:` guard to prevent AttributeError when broker is None.

## Alternatives considered

- Keep the existing `_hist_avg()` private function and add a similar `_counter_get()` private helper: rejected because it still relies on private Prometheus internals and doesn't solve REQ-001.
- Access metrics via the `prometheus_client.REGISTRY` registry: rejected because it adds unnecessary complexity and coupling to global state.
- Embed metric-read logic directly in `health_route.py`: rejected because it duplicates logic and makes testing harder; route_helpers.py is the appropriate location for shared helpers.

## Implementation
### Target file
`scripts/eventbus/health_route.py`

### Procedure
1. Update imports: remove private metric object imports (`_db_lock_contention`, `_db_lock_wait_time`, `_db_query_duration`), add public getter imports (`get_histogram_avg`, `get_counter_value`).
2. Replace `_hist_avg(_db_lock_wait_time)` with `get_histogram_avg(_db_lock_wait_time)`.
3. Replace `_hist_avg(_db_query_duration)` with `get_histogram_avg(_db_query_duration)`.
4. Replace `_db_lock_contention._value.get()` with `get_counter_value(_db_lock_contention)`.
5. Remove the local `_hist_avg()` function definition (no longer needed).
6. Move the broker backlog threshold check (`max_queue_depth >= broker.backlog_health_threshold`) inside the `if broker is not None:` guard.

### Method
- Follow the existing pattern in `health_route.py` for imports and usage.
- The broker guard fix prevents AttributeError when broker is None.

### Details
```python
# Updated imports (lines 11-19):
from eventbus.route_helpers import (
    get_broker,
    get_config,
    get_db,
    run_with_db_lock,
    get_histogram_avg,
    get_counter_value,
)

# Removed: _db_lock_contention, _db_lock_wait_time, _db_query_duration imports

# Updated metric reads (around lines 86-88):
lock_wait_avg = get_histogram_avg(_db_lock_wait_time)
query_dur_avg = get_histogram_avg(_db_query_duration)
lock_contention_total = get_counter_value(_db_lock_contention)

# Removed: the local _hist_avg() function definition (lines 71-84)

# Broker backlog threshold check (line 65) — move inside broker guard:
# Current (problematic):
#     if max_queue_depth >= broker.backlog_health_threshold:
#         degraded_reasons.append("broker_queue_backlog_high")
# 
# Fix (move inside the existing if broker is not None: block at line 53):
#     if broker is not None:
#         ...existing broker properties...
#         if max_queue_depth >= broker.backlog_health_threshold:
#             degraded_reasons.append("broker_queue_backlog_high")
```

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original private API access patterns.
- The revert is mechanical — no semantic changes beyond restoring original code structure.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| health_route.py | Unit: public API access; Integration: graceful degradation | uv run pytest tests/eventbus/test_eventbus_health.py -v | New health tests pass; existing tests unchanged |

## Completion criteria

- [ ] Private metric imports removed from health_route.py
- [ ] Public getter imports added to health_route.py
- [ ] `_hist_avg()` calls replaced with `get_histogram_avg()`
- [ ] `_db_lock_contention._value.get()` replaced with `get_counter_value()`
- [ ] Local `_hist_avg()` function definition removed
- [ ] Broker backlog threshold check moved inside `if broker is not None:` guard
- [ ] Existing health tests still pass

## Out of scope

- Changes to route_helpers.py (handled by separate procedure)
- Changes to test_eventbus_health.py (handled by separate procedure)
- Adding Prometheus scrape configuration (infrastructure concern)

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace private Prometheus API access with public getters | Completed | — | 20260915-170044 | REQ-001 |
| 2 | Move broker backlog threshold check inside broker guard | Completed | — | 20260915-170101 | REQ-002 |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260914-102519_eventbus08_health-metrics-private-api-dependency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175156_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-233533
- **Related target files**: scripts/eventbus/health_route.py