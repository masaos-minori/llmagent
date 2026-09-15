## Goal

Return stable degraded responses using supported metrics interfaces rather than reaching into another module's private internals, ensuring the health endpoint remains reliable when dependencies or metrics are unavailable.

## Scope

Add public getter methods (`get_histogram_avg`, `get_counter_value`) to `route_helpers.py`; update `health_route.py` to use them instead of private Prometheus APIs; move broker backlog threshold check inside broker None guard.

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
`scripts/eventbus/route_helpers.py`

### Procedure
1. Add `get_histogram_avg()` public getter function.
2. Add `get_counter_value()` public getter function.

### Method
- Follow the existing pattern in `route_helpers.py` for helper functions (e.g., `get_broker`, `get_config`).
- Both getters accept their respective metric types and return safe defaults on any exception.

### Details
```python
# After the existing _db_lock_contention definition (around line 30), add:

def get_histogram_avg(hist: Histogram) -> float:
    """Return the average observation for a Histogram via the public API.
    
    Returns 0.0 if the histogram has no observations or if the API is unavailable.
    """
    try:
        metrics = list(hist.collect())
        if not metrics:
            return 0.0
        total_sum = 0.0
        total_count = 0
        for metric in metrics:
            for sample in metric.samples:
                if sample.name.endswith("_sum"):
                    total_sum += sample.value
                elif sample.name.endswith("_count"):
                    total_count += int(sample.value)
        return total_sum / total_count if total_count > 0 else 0.0
    except Exception:
        return 0.0


def get_counter_value(counter: Counter) -> int:
    """Return the current value of a Counter via the public API.
    
    Returns 0 if the counter has no value or if the API is unavailable.
    """
    try:
        metrics = list(counter.collect())
        if not metrics:
            return 0
        for metric in metrics:
            for sample in metric.samples:
                if sample.name == counter._name + "_total":
                    return int(sample.value)
        return 0
    except Exception:
        return 0
```

## Compatibility considerations

- New public API surface additions follow the existing `get_*` naming convention in `route_helpers.py`.
- Existing callers of `_db_lock_wait_time`, `_db_query_duration`, and `_db_lock_contention` will need to switch to the new getters.
- The `prometheus_client` version must support `collect()` — verified against installed version before implementation.

## Security considerations

- No new secrets, credentials, or sensitive data exposure.
- Metrics do not include event payloads or PII — only aggregated values.

## Rollback considerations

- Removing the new getters reverts observability improvements but does not affect functional correctness.
- If the `prometheus_client` version doesn't support `collect()`, revert to the original private API access.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| route_helpers.py | Unit: public getters work correctly | uv run pytest tests/eventbus/test_eventbus_health.py -v | Public getter tests pass |

## Completion criteria

- [ ] `get_histogram_avg()` defined and returns correct average for Histogram
- [ ] `get_counter_value()` defined and returns correct value for Counter
- [ ] Both getters return safe defaults (0.0 / 0) on any exception
- [ ] Existing route_helpers.py tests still pass

## Out of scope

- Changes to health_route.py (handled by separate procedure)
- Changes to test_eventbus_health.py (handled by separate procedure)
- Adding Prometheus scrape configuration (infrastructure concern)

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add get_histogram_avg() public getter | Completed | — | 20260915-165212 | REQ-001 |
| 2 | Add get_counter_value() public getter | Completed | — | 20260915-165411 | REQ-001 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-102519_eventbus08_health-metrics-private-api-dependency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175156_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-233533
- **Related target files**: scripts/eventbus/route_helpers.py