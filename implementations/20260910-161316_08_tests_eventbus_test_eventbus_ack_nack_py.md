## Goal

Add a test asserting two distinct `consumer_id`s can each independently ACK the same event to `tests/eventbus/test_eventbus_ack_nack.py`, verifying per-consumer delivery-state isolation.

## Scope

- Add a new test method in `TestAckEvent` class.
- Test that two consumers can ACK the same event independently.
- Test that one consumer's ACK does not mark another consumer's delivery as complete.

## Assumptions

- The `consumer_delivery` table exists (created by the migration in the related procedure document).
- The `ack_event_for_consumer()` function is available in `eventbus.db`.
- The `insert_event()` function is available in `eventbus.db`.

## Design decisions

- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by the existing `TestAckEvent` class.
- **Direct function calls**: Use direct `db` calls rather than HTTP requests for clarity and speed.

## Alternatives considered

- **HTTP-level test**: Send two `/events/{event_id}/ack` requests with different `consumer_id` query params. Rejected because direct function calls are faster and easier to reason about.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. Add a new test method `test_two_consumers_ack_same_event` in `TestAckEvent`.
2. Insert an event, then ACK it twice with different consumer_ids.
3. Assert both ACKs succeed independently.

### Method

#### Step 1: Add new test method

After the existing `test_ack_event` method in `TestAckEvent`:
```python
def test_ack_event(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
    ...existing test body...

def test_two_consumers_ack_same_event(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
    """Two distinct consumer_ids can each ACK the same event independently."""
    from eventbus.db import ack_event_for_consumer, insert_event  # noqa: PLC0415

    db = eventbus_client.app.state.db
    now = "2026-09-09T10:00:00Z"

    # Insert an event first
    seq, inserted = insert_event(
        db, "evt-multi-ack", "test-topic", '{"data": "value"}', "producer", now
    )
    assert inserted

    # Consumer A acknowledges
    found_a, newly_acked_a, _ = ack_event_for_consumer(
        db, "evt-multi-ack", "consumer_A", now
    )
    assert found_a
    assert newly_acked_a

    # Consumer B acknowledges the same event
    found_b, newly_acked_b, _ = ack_event_for_consumer(
        db, "evt-multi-ack", "consumer_B", now
    )
    assert found_b
    assert newly_acked_b

    # Both deliveries recorded separately
    row_a = db.execute(
        "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
        ("consumer_A", "evt-multi-ack"),
    ).fetchone()
    assert row_a is not None
    assert row_a["acked_at"] == now

    row_b = db.execute(
        "SELECT acked_at FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
        ("consumer_B", "evt-multi-ack"),
    ).fetchone()
    assert row_b is not None
    assert row_b["acked_at"] == now

    # Offsets advanced independently
    row_off_a = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        ("consumer_A",),
    ).fetchone()
    assert row_off_a is not None
    assert int(row_off_a["offset"]) == seq

    row_off_b = db.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        ("consumer_B",),
    ).fetchone()
    assert row_off_b is not None
    assert int(row_off_b["offset"]) == seq
```

### Details

The key changes are:

1. **Two independent ACKs**: The test inserts one event, then ACKs it twice with different `consumer_id` values.
2. **Both succeed**: Each ACK returns `(True, True, seq)` — the event is found and newly acked by each consumer.
3. **Separate delivery records**: Both `consumer_delivery` rows exist independently.
4. **Independent offsets**: Both `consumer_offsets` rows have the same offset value (the event's seq).

## Compatibility considerations

- The existing `test_ack_event` test pattern is preserved.
- The `make_eventbus_client()` fixture is reused as-is.

## Security considerations

- No new authentication or authorization boundaries introduced.
- SQL values are bound via `?` placeholders — no injection risk.

## Rollback considerations

- To rollback: remove the new test method.
- The rollback restores the pre-change state where only single-consumer ACK testing exists.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_ack_nack.py` | Unit test assertion | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` | Two consumers ACK the same event independently |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_two_consumers_ack_same_event` asserts both consumers can ACK the same event.
- Both `consumer_delivery` rows exist independently.
- Both `consumer_offsets` rows have the correct offset value.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add two-consumer ACK test | Pending | — | — | |
| 2 | Run validation (pytest + regression check) | Pending | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
