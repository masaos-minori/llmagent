## Goal

Add a failure-injection test to `tests/eventbus/test_eventbus_crash_ack.py` that simulates an offset-write failure after the delivery-state write succeeds, verifying neither operation commits in that scenario.

## Scope

- Add a new test method in `TestCrashAck` class.
- Mock the SQLite commit to fail after the delivery-state UPSERT but before the offset advancement.
- Assert that neither the delivery nor the offset is committed when the transaction fails.

## Assumptions

- The `consumer_delivery` and `consumer_offsets` tables exist (created by the migration in the related procedure document).
- The `ack_event_for_consumer()` function is available in `eventbus.db`.
- The `insert_event()` function is available in `eventbus.db`.

## Design decisions

- **Failure injection via mock**: Use `unittest.mock.patch` to inject a failure into the SQLite connection's `commit()` method after the delivery-state write.
- **Verify rollback**: After the failed commit, verify that neither the delivery nor the offset was persisted.
- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by the existing `TestCrashAck` class.

## Alternatives considered

- **Simulate disk full**: Write to a read-only filesystem. Rejected because mocking is simpler and more reliable than filesystem manipulation.
- **Simulate network partition**: Not applicable — SQLite is local.

## Implementation

### Target file

`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure

1. Add a new test method `test_offset_write_failure_after_delivery_state` in `TestCrashAck`.
2. Mock the SQLite commit to fail after the delivery-state UPSERT.
3. Assert that neither the delivery nor the offset is committed.

### Method

#### Step 1: Add new test method

After the existing `test_crash_ack` method in `TestCrashAck`:
```python
class TestCrashAck:
    """Tests for crash-recovery of partial acks."""

    def test_crash_ack(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        ...existing test body...

    def test_offset_write_failure_after_delivery_state(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """When offset-write fails after delivery-state write, neither commits."""
        from eventbus.db import ack_event_for_consumer, insert_event  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config
        now = "2026-09-09T10:00:00Z"
        consumer_id = "crash_consumer"

        # Insert an event first
        seq, inserted = insert_event(
            db, "evt-crash-offset", "test-topic", '{"data": "value"}', "producer", now
        )
        assert inserted

        # Mock commit to fail after delivery-state write
        original_commit = db.commit

        def failing_commit():
            raise sqlite3.IntegrityError("simulated commit failure")

        with unittest.mock.patch.object(db, 'commit', side_effect=failing_commit):
            # This should raise an exception
            with self.assertRaises(sqlite3.IntegrityError):
                ack_event_for_consumer(db, "evt-crash-offset", consumer_id, now)

        # Verify neither delivery nor offset was committed
        delivery_row = db.execute(
            "SELECT 1 FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, "evt-crash-offset"),
        ).fetchone()
        assert delivery_row is None, "delivery-state should NOT be committed after failed commit"

        offset_row = db.execute(
            "SELECT 1 FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert offset_row is None, "offset should NOT be committed after failed commit"
```

### Details

The key changes are:

1. **Commit failure injection**: The test replaces `db.commit` with a side-effect that raises `sqlite3.IntegrityError`, simulating a commit failure after the delivery-state UPSERT.
2. **Rollback verification**: After the exception, the test verifies that neither the delivery nor the offset was persisted — confirming the transaction rolled back correctly.
3. **Exception propagation**: The test uses `self.assertRaises(sqlite3.IntegrityError)` to ensure the exception propagates to the caller.

## Compatibility considerations

- The existing `test_crash_ack` test pattern is preserved.
- The `make_eventbus_client()` fixture is reused as-is.
- The test uses `sqlite3.IntegrityError` as the failure type — any SQLite error would work, but IntegrityError is a reasonable choice for a simulated failure.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Mock injection does not affect production code paths.

## Rollback considerations

- To rollback: remove the new test method.
- The rollback restores the pre-change state where only single-operation crash recovery is tested.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_crash_ack.py` | Failure injection test | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` | Offset-write failure after delivery-state write leaves neither committed |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_offset_write_failure_after_delivery_state` asserts neither delivery nor offset is committed on commit failure.
- Exception propagates to the caller.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add failure-injection test | Completed | — | — | Actual test name: 'test_offset_write_failure_rolls_back_delivery_write' |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_crash_ack.py
