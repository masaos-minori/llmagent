## Goal
- Verify completeness of operational regression test set for Event Bus; add missing test scenarios

## Findings

### Gap 1: Slow consumer threshold → HTTP 503 not tested
`tests/test_eventbus_slow_consumer.py:L70`: `test_health_reports_slow_consumer_count` only verifies that the `slow_consumers` field exists in the health response — it does NOT verify that HTTP 503 is returned when slow consumer threshold is exceeded.

### Gap 2: DLQ task stopped → health 503 not tested
`tests/test_eventbus_health.py:L94`: `test_health_degraded_when_db_unavailable` tests DB unavailability → 503, but no test for DLQ task stopped → 503.

## Changes
- `tests/test_eventbus_slow_consumer.py`: Added `test_health_503_when_slow_consumer_threshold_exceeded` — publishes 120 events and verifies HTTP 503 when slow consumer threshold exceeded
- `tests/test_eventbus_health.py`: Added `test_health_503_when_dlq_task_stopped` — cancels DLQ task and verifies HTTP 503 with `dlq_task_stopped` in degraded_reasons
