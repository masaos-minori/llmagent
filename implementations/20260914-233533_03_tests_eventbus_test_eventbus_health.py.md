## Goal

Return stable degraded responses using supported metrics interfaces rather than reaching into another module's private internals, ensuring the health endpoint remains reliable when dependencies or metrics are unavailable.

## Scope

Add compatibility tests for the metrics implementation used by the project; verify graceful degradation on metric-read failures.

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
`tests/eventbus/test_eventbus_health.py`

### Procedure
1. Add test: Health endpoint returns valid response when Prometheus Histogram samples are inaccessible (REQ-002).
2. Add test: Health endpoint returns valid response when Prometheus Counter value is inaccessible (REQ-002).
3. Add test: Health endpoint returns valid response when all metrics are inaccessible (REQ-002).
4. Add test: Metrics values in response reflect actual metric readings when accessible (REQ-001).
5. Add test: Broker backlog threshold check handles broker being None (REQ-002).
6. Add test: Prometheus compatibility test for public API (REQ-003).

### Method
- Follow the existing fixture pattern (`client`, `tmp_path`, `monkeypatch`) in `test_eventbus_health.py`.
- For metric-inaccessibility tests: mock the `collect()` method to raise an exception.
- For metrics-accessible test: verify the public API returns correct values.
- For broker None test: set broker to None and verify graceful degradation.

### Details
```python
    def test_health_endpoint_metrics_accessible(self, client: TestClient) -> None:
        """Health endpoint reads metrics via public API without accessing private internals."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        # Verify metrics section exists and contains expected fields
        assert "metrics" in body
        assert "lock_wait_avg_seconds" in body["metrics"]
        assert "query_duration_avg_seconds" in body["metrics"]
        assert "lock_contention_total" in body["metrics"]
        # Values should be non-negative numbers
        assert body["metrics"]["lock_wait_avg_seconds"] >= 0
        assert body["metrics"]["query_duration_avg_seconds"] >= 0
        assert body["metrics"]["lock_contention_total"] >= 0


    def test_health_endpoint_metrics_unavailable_degrades_gracefully(self, client: TestClient) -> None:
        """Health endpoint returns stable response when metrics are inaccessible."""
        from unittest.mock import MagicMock
        
        import eventbus.app as eb_app
        
        # Mock the collect() method to raise an exception
        original_hist_collect = eb_app.Histogram.collect
        original_counter_collect = eb_app.Counter.collect
        
        def failing_collect(self):
            raise Exception("metric read failure")
        
        try:
            eb_app.Histogram.collect = failing_collect
            eb_app.Counter.collect = failing_collect
            
            resp = client.get("/health")
            assert resp.status_code == 503  # degraded due to DLQ task not running
            body = resp.json()
            
            # Metrics should have default values (0.0, 0)
            assert body["metrics"]["lock_wait_avg_seconds"] == 0.0
            assert body["metrics"]["query_duration_avg_seconds"] == 0.0
            assert body["metrics"]["lock_contention_total"] == 0
        finally:
            eb_app.Histogram.collect = original_hist_collect
            eb_app.Counter.collect = original_counter_collect


    def test_health_broker_backlog_threshold_with_none_broker(self, client: TestClient) -> None:
        """Broker backlog threshold check does not raise AttributeError when broker is None."""
        from unittest.mock import MagicMock
        
        import eventbus.app as eb_app
        
        # Save original broker reference
        original_broker = eb_app.app.state.broker
        
        try:
            # Set broker to None to simulate unavailability
            eb_app.app.state.broker = None
            
            resp = client.get("/health")
            # Should not raise AttributeError
            assert resp.status_code == 503
            body = resp.json()
            assert body["status"] == "degraded"
            assert "dlq_task_stopped" in body["degraded_reasons"]
        finally:
            eb_app.app.state.broker = original_broker
```

Note: The existing `test_health_503_when_dlq_task_stopped` test (lines 114-129) already covers some of REQ-002 but doesn't specifically test metric-inaccessibility scenarios. The new `test_health_endpoint_metrics_unavailable_degrades_gracefully` test above specifically validates the metric fallback behavior.

## Compatibility considerations

- Tests follow the existing fixture pattern (`client`, `tmp_path`, `monkeypatch`).
- New tests are additive — no changes to existing test behavior.
- Mocking `Histogram.collect()` and `Counter.collect()` may need adjustment if prometheus_client changes its internals.

## Security considerations

- No secrets or credentials in test code.
- Test fixtures use temporary directories (`tmp_path`) — no shared state.

## Rollback considerations

- Removing these tests reverts coverage gains but does not affect production code.
- If the prometheus_client API changes, metric mocking may need updating.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| test_eventbus_health.py | Integration: all new tests pass; existing tests unchanged | uv run pytest tests/eventbus/test_eventbus_health.py -v | All 6 new tests pass; existing tests unchanged |

## Completion criteria

- [ ] `test_health_endpoint_metrics_accessible` — verifies public API works correctly
- [ ] `test_health_endpoint_metrics_unavailable_degrades_gracefully` — verifies graceful degradation
- [ ] `test_health_broker_backlog_threshold_with_none_broker` — verifies broker None handling
- [ ] All existing health tests still pass

## Out of scope

- Changes to health_route.py (handled by separate procedure)
- Changes to route_helpers.py (handled by separate procedure)
- Adding Prometheus scrape configuration (infrastructure concern)

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add metrics-accessible health endpoint test | Pending | — | — | REQ-001 |
| 2 | Add metrics-unavailable graceful degradation test | Pending | — | — | REQ-002 |
| 3 | Add broker None backlog threshold test | Pending | — | — | REQ-002 |
| 4 | Add Prometheus compatibility test for public API | Pending | — | — | REQ-003 |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-102519_eventbus08_health-metrics-private-api-dependency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-175156_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-233533
- **Related target files**: tests/eventbus/test_eventbus_health.py
