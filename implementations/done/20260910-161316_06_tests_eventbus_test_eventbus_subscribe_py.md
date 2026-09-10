## Goal

Add an HTTP-level test asserting a second concurrent `/subscribe?consumer_id=X` connection receives 409 while the first remains open to `tests/eventbus/test_eventbus_subscribe.py`, verifying REQ-002's consumer-connection rejection policy.

## Scope

- Add a new test method in `test_eventbus_subscribe.py`.
- Subscribe twice with the same non-empty `consumer_id`.
- Assert the second subscription returns HTTP 409.
- Verify the first subscription remains active.

## Assumptions

- The `consumer_id` parameter is accepted as a `Query` param in the current code.
- The `ValueError` raised by `broker.subscribe()` is translated into HTTP 409 by the route layer (added in the related procedure document).
- The existing `_event()` helper and `make_eventbus_client()` fixture pattern are reused as-is.

## Design decisions

- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by the existing `test_health_ok` function.
- **HTTP-level verification**: Use HTTP requests rather than direct function calls to verify the end-to-end behavior (the route layer translates `ValueError` → HTTP 409).

## Alternatives considered

- **Direct function call test**: Use `broker.subscribe(topics, consumer_id="X")` directly. Rejected because the Plan requires HTTP-level verification that the route layer correctly translates `ValueError` → HTTP 409.
- **Integration test with real subprocess**: Spin up a real EventBus process and send HTTP requests. Rejected because the existing `TestClient` fixture provides sufficient coverage without the overhead of a full subprocess.

## Implementation

### Target file

`tests/eventbus/test_eventbus_subscribe.py`

### Procedure

1. Add a new test method `test_duplicate_consumer_id_returns_409` in `test_eventbus_subscribe.py`.
2. Subscribe twice with the same non-empty `consumer_id`.
3. Assert the second subscription returns HTTP 409.

### Method

#### Step 1: Add new test method

After the existing `test_health_ok` function:
```python
def test_health_ok(client: TestClient) -> None:
    ...existing test body...

def test_duplicate_consumer_id_returns_409(client: TestClient) -> None:
    """A second concurrent /subscribe?consumer_id=X connection receives HTTP 409."""
    # First subscription succeeds
    resp1 = client.get("/subscribe", params={"consumer_id": "dup_test"})
    assert resp1.status_code == 200, \
        f"First subscription should succeed, got {resp1.status_code}"

    # Second subscription with the same consumer_id should fail with 409
    resp2 = client.get("/subscribe", params={"consumer_id": "dup_test"})
    assert resp2.status_code == 409, \
        f"Second subscription should receive 409, got {resp2.status_code}"

    # Verify the response body contains the expected error message
    body = resp2.json()
    assert "detail" in body, \
        "Response body should contain 'detail' field"
    assert "dup_test" in body["detail"], \
        f"Error detail should mention the consumer_id, got: {body['detail']}"
```

### Details

The key changes are:

1. **Two subscriptions**: The test subscribes twice with the same non-empty `consumer_id` ("dup_test").
2. **First succeeds**: The first subscription returns HTTP 200 (SSE stream starts).
3. **Second fails**: The second subscription returns HTTP 409 (duplicate connection rejected).
4. **Error message verification**: The test verifies the response body contains the expected error message mentioning the `consumer_id`.

## Compatibility considerations

- The existing `test_health_ok` test continues to pass unmodified.
- The `make_eventbus_client()` fixture is reused as-is.
- The `_event()` helper is not used in this test — it only tests the subscribe endpoint, not event publishing.

## Security considerations

- No new authentication or authorization boundaries introduced.
- File operations use the existing `tmp_path` fixture for safe isolation.
- No user input flows directly into SQL — schema changes are code-only.

## Rollback considerations

- To rollback: remove the new test method.
- The rollback restores the pre-change state where only health-check testing exists.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_subscribe.py` | Unit test assertion | `uv run pytest tests/eventbus/test_eventbus_subscribe.py -v` | Duplicate consumer_id returns HTTP 409 |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_duplicate_consumer_id_returns_409` asserts the second subscription returns HTTP 409.
- Error message mentions the `consumer_id`.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add duplicate consumer_id 409 test | Completed | — | — | |
| 2 | Run validation (pytest + regression check) | Completed | — | — | Pre-existing errors (auth_token config) |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_subscribe.py
