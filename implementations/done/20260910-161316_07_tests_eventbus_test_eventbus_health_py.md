## Goal

Add assertions that the health response surfaces the new overflow-disconnect/duplicate-rejection counters to `tests/eventbus/test_eventbus_health.py`, verifying REQ-005's observability requirement.

## Scope

- Add a new test method in `TestHealth` class.
- Assert both `overflow_disconnects` and `duplicate_rejections` fields are present in the health response.
- Verify their values are integers (not None or missing).

## Assumptions

- The `broker.overflow_disconnect_count()` and `broker.duplicate_rejection_count()` getter methods are available (added in the related procedure document).
- The existing `make_eventbus_client()` fixture pattern is reused as-is.

## Design decisions

- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by the existing `TestHealth` class.
- **Simple presence checks**: Only verify the fields are present and have integer values — no need to trigger actual overflow/rejection events to test the counter increment logic (that's covered by other tests).

## Alternatives considered

- **Integration test with real subprocess**: Spin up a real EventBus process and send HTTP requests. Rejected because unit tests with direct function calls are faster and easier to reason about.
- **Single comprehensive test**: Combine all counter assertions into one test. Rejected because each counter has distinct requirements that are clearer when separated.

## Implementation

### Target file

`tests/eventbus/test_eventbus_health.py`

### Procedure

1. Add a new test method `test_health_surfaces_new_counters` in `TestHealth`.
2. Assert both `overflow_disconnects` and `duplicate_rejections` fields are present in the health response.
3. Verify their values are integers (not None or missing).

### Method

#### Step 1: Add new test method

After the existing `test_health_503_when_dlq_task_stopped` method:
```python
    def test_health_503_when_dlq_task_stopped(self, client: TestClient) -> None:
        ...existing test body...

    def test_health_surfaces_new_counters(self, client: TestClient) -> None:
        """Health response includes overflow_disconnects and duplicate_rejections counters."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()

        # Both new counter fields should be present
        assert "overflow_disconnects" in body, \
            "Health response should include 'overflow_disconnects' field"
        assert "duplicate_rejections" in body, \
            "Health response should include 'duplicate_rejections' field"

        # Values should be integers (not None or missing)
        assert isinstance(body["overflow_disconnects"], int), \
            f"'overflow_disconnects' should be an integer, got {type(body['overflow_disconnects'])}"
        assert isinstance(body["duplicate_rejections"], int), \
            f"'duplicate_rejections' should be an integer, got {type(body['duplicate_rejections'])}"

        # In a healthy state with no overflow/rejection events, both should be zero
        assert body["overflow_disconnects"] == 0, \
            f"'overflow_disconnects' should be 0 in healthy state, got {body['overflow_disconnects']}"
        assert body["duplicate_rejections"] == 0, \
            f"'duplicate_rejections' should be 0 in healthy state, got {body['duplicate_rejections']}"
```

### Details

The key changes are:

1. **Presence checks**: The test verifies both `overflow_disconnects` and `duplicate_rejections` fields are present in the health response.
2. **Type checks**: The test verifies both fields have integer values (not None or missing).
3. **Zero-value check**: In a healthy state with no overflow/rejection events, both counters should be zero.

## Compatibility considerations

- The existing `test_health_ok`, `test_health_degraded_when_db_unavailable`, and `test_health_503_when_dlq_task_stopped` tests continue to pass unmodified.
- The `make_eventbus_client()` fixture is reused as-is.

## Security considerations

- No new authentication or authorization boundaries introduced.
- File operations use the existing `tmp_path` fixture for safe isolation.
- No user input flows directly into SQL — schema changes are code-only.

## Rollback considerations

- To rollback: remove the new test method.
- The rollback restores the pre-change state where only `slow_consumers` counter testing exists.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_health.py` | Unit test assertion | `uv run pytest tests/eventbus/test_eventbus_health.py -v` | New counter fields present and correct in health response |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_health_surfaces_new_counters` asserts both `overflow_disconnects` and `duplicate_rejections` fields are present.
- Values are integers (not None or missing).
- Zero-value check passes in healthy state.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add new counter fields test | Completed | — | — | Actual test name: 'test_health_reports_overflow_and_duplicate_counters' |
| 2 | Run validation (pytest + regression check) | Completed | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_health.py
