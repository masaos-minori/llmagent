## Goal

Update `test_concurrent_dlq_requeue` in `tests/eventbus/test_eventbus_concurrent.py` to match the lineage model (REQ-001, REQ-003).

## Scope

- **In-Scope**: Modifying `tests/eventbus/test_eventbus_concurrent.py` to un-skip and verify the lineage model
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- The lineage model is chosen as the single truth for `/dlq/{event_id}/requeue`
- Each DLQ requeue creates a new event row with `redelivered_from` pointing to the original
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- The `redelivered_from`-existence check in `redeliver_event()` prevents duplicate redeliveries under concurrency
- Only one requeue should succeed; the others should get 409 Conflict

## Design decisions

- Un-skip the `test_concurrent_dlq_requeue` test
- Verify the lineage model response shape (new_event_id, new_seq)
- Verify that only one requeue succeeds and the others get 409 Conflict
- Preserve existing test structure and setup logic

## Alternatives considered

- Keeping the test skipped: would leave the concurrent requeue test incomplete
- Adding a timeout to the test using `pytest-timeout`: would mask the underlying issue rather than fix it

## Implementation

### Target file

`tests/eventbus/test_eventbus_concurrent.py`

### Procedure

1. Un-skip the `test_concurrent_dlq_requeue` test
2. Verify the lineage model response shape
3. Verify that only one requeue succeeds and the others get 409 Conflict
4. Preserve existing test structure and setup logic

### Method

For the test update:
- Remove the `@pytest.mark.skip` decorator from the `test_concurrent_dlq_requeue` test
- Update assertions to verify the lineage model behavior

### Details

#### Step 1: Update test class

```python
# Before:
class TestConcurrentDlqRequeue:
    """Verify concurrent DLQ requeue operations do not cause data corruption."""

    @pytest.mark.skip(
        reason="Asserts the new-event-id lineage requeue model (new_event_id/"
        "new_seq in the response), which conflicts with the in-place requeue "
        "model asserted by test_eventbus_dlq.py and "
        "test_eventbus_requeue_edge_cases.py — see "
        "issues/20260911-142700_ebdlq01_requeue-model-in-place-vs-lineage-"
        "conflict.md for the design decision needed before either side's "
        "tests can be reconciled."
    )
    def test_concurrent_dlq_requeue(self, client: TestClient) -> None:
        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]
        # Nack 3 times to promote to DLQ
        for _ in range(3):
            resp = client.post("/nack", params={"event_id": event_id})
            assert resp.status_code == 200

        results: list[dict[str, Any]] = []

        async def _requeue() -> None:
            resp = client.post(f"/dlq/{event_id}/requeue")
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_requeue() for _ in range(5))))
        finally:
            loop.close()

        # Only one requeue should succeed (event is no longer in DLQ after first requeue)
        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1, (
            f"Expected exactly 1 requeue success, got {len(requeued)}"
        )

        # Successful response includes new_event_id and new_seq
        success_resp = requeued[0]
        assert "new_event_id" in success_resp, (
            "successful response should include new_event_id"
        )
        assert "new_seq" in success_resp, "successful response should include new_seq"
        # Validate new_event_id is a valid UUID v4 string
        uuid.UUID(success_resp["new_event_id"], version=4)
        # Validate new_seq is an integer greater than the original event's seq
        assert isinstance(success_resp["new_seq"], int), "new_seq should be an integer"
        assert success_resp["new_seq"] > resp.json()["seq"], (
            f"new_seq ({success_resp['new_seq']}) should be greater than original seq ({resp.json()['seq']})"
        )

        # The other concurrent requests should fail with 409 Conflict (event no longer in DLQ)
        conflicts = [r for r in results if r.get("detail") == "event is not in DLQ"]
        assert len(conflicts) == 4, f"Expected 4 conflicts, got {len(conflicts)}"

# After:
class TestConcurrentDlqRequeue:
    """Verify concurrent DLQ requeue operations do not cause data corruption."""

    def test_concurrent_dlq_requeue(self, client: TestClient) -> None:
        """Verify only one concurrent requeue succeeds (lineage model with concurrency guard)."""
        body = {**_event("dlq"), "event_id": str(uuid.uuid4())}
        resp = client.post("/publish", json=body)
        assert resp.status_code == 200

        event_id = body["event_id"]
        # Nack 3 times to promote to DLQ
        for _ in range(3):
            resp = client.post("/nack", params={"event_id": event_id})
            assert resp.status_code == 200

        results: list[dict[str, Any]] = []

        async def _requeue() -> None:
            resp = client.post(f"/dlq/{event_id}/requeue")
            results.append(resp.json())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*(_requeue() for _ in range(5))))
        finally:
            loop.close()

        # Only one requeue should succeed (event is no longer in DLQ after first requeue)
        requeued = [r for r in results if r.get("requeued") is True]
        assert len(requeued) == 1, (
            f"Expected exactly 1 requeue success, got {len(requeued)}"
        )

        # Successful response includes new_event_id and new_seq
        success_resp = requeued[0]
        assert "new_event_id" in success_resp, (
            "successful response should include new_event_id"
        )
        assert "new_seq" in success_resp, "successful response should include new_seq"
        # Validate new_event_id is a valid UUID v4 string
        uuid.UUID(success_resp["new_event_id"], version=4)
        # Validate new_seq is an integer greater than the original event's seq
        assert isinstance(success_resp["new_seq"], int), "new_seq should be an integer"
        assert success_resp["new_seq"] > resp.json()["seq"], (
            f"new_seq ({success_resp['new_seq']}) should be greater than original seq ({resp.json()['seq']})"
        )

        # The other concurrent requests should fail with 409 Conflict (event no longer in DLQ)
        conflicts = [r for r in results if r.get("detail") == "event is not in DLQ"]
        assert len(conflicts) == 4, f"Expected 4 conflicts, got {len(conflicts)}"
```

## Compatibility considerations

- The test fixture uses the shared token mechanism, which should work alongside per-role tokens
- The test should complete within a bounded time after the client disconnects
- The test should not rely on `pytest-timeout` to unblock it

## Security considerations

- The concurrency guard prevents race conditions where two concurrent requests could both see `dlq_at IS NOT NULL` and both insert new rows
- This improves security by preventing data corruption from concurrent operations

## Rollback considerations

- If the concurrency guard causes issues in production, roll back to the previous state without the guard
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq_route.py::dlq_requeue | Integration: verify response shape matches lineage model | pytest tests/eventbus/test_eventbus_dlq.py::test_dlq_requeue | Test completes without assertion errors |
| scripts/eventbus/db.py::redeliver_event | Integration: verify concurrent requeue operations don't cause data corruption | pytest tests/eventbus/test_eventbus_concurrent.py::TestConcurrentDlqRequeue::test_concurrent_dlq_requeue | Test completes without assertion errors |

## Completion criteria

- [ ] `@pytest.mark.skip` decorator removed from `test_concurrent_dlq_requeue`
- [ ] Test verifies the lineage model response shape
- [ ] Test verifies that only one requeue succeeds and the others get 409 Conflict
- [ ] Tests pass with the new requeue model

## Out of scope

- Changes to `scripts/eventbus/dlq_route.py` (handled in separate procedure document)
- Changes to `scripts/eventbus/db.py` (handled in separate procedure document)
- Changes to other test files (handled in separate procedure documents)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Un-skip test_concurrent_dlq_requeue | Pending | — | — | |
| 2 | Verify lineage model response shape | Pending | — | — | |
| 3 | Verify only one requeue succeeds | Pending | — | — | |
| 4 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260911-142700_ebdlq01_requeue-model-in-place-vs-lineage-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-115455_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-150000
- **Related target files**: tests/eventbus/test_eventbus_concurrent.py
