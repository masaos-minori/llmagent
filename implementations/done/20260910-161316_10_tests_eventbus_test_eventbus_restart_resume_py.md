## Goal

Add a test asserting a consumer can resume from its last-committed offset after a simulated restart to `tests/eventbus/test_eventbus_restart_resume.py`, verifying the SQLite-backed offset path works end-to-end.

## Scope

- Add a new test method in `TestRestartResume` class.
- Simulate a consumer ACKing events, then restarting and resuming from the last-committed offset.
- Verify the SSE stream delivers only unacked events starting from the correct offset.

## Assumptions

- The `consumer_offsets` table exists (created by the migration in the related procedure document).
- The `ack_event_for_consumer()` function is available in `eventbus.db`.
- The `_get_offset_from_sqlite()` helper function is available in `subscribe_route.py`.
- The `insert_event()` function is available in `eventbus.db`.

## Design decisions

- **Reuse existing test patterns**: Follow the same `tmp_path`-based isolation pattern established by the existing `TestRestartResume` class.
- **Direct function calls**: Use direct `db` calls rather than HTTP requests for clarity and speed.
- **SSE stream verification**: Use the existing `sse_stream()` helper to verify the SSE stream content.

## Alternatives considered

- **HTTP-level test**: Send `/events/{event_id}/ack` and `/events?consumer_id=X&since_seq=0` requests. Rejected because direct function calls are faster and easier to reason about.

## Implementation

### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

1. Add a new test method `test_resume_from_sqlite_offset` in `TestRestartResume`.
2. Simulate a consumer ACKing events, then restarting and resuming from the last-committed offset.
3. Verify the SSE stream delivers only unacked events starting from the correct offset.

### Method

#### Step 1: Add new test method

After the existing `test_restart_resume` method in `TestRestartResume`:
```python
class TestRestartResume:
    """Tests for consumer resume-after-restart."""

    def test_restart_resume(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        ...existing test body...

    def test_resume_from_sqlite_offset(self, tmp_path: pathlib.Path, eventbus_client: Any) -> None:
        """Consumer resumes from SQLite-backed offset after restart."""
        from eventbus.db import ack_event_for_consumer, insert_event  # noqa: PLC0415
        from eventbus.subscribe_route import _get_offset_from_sqlite  # noqa: PLC0415

        db = eventbus_client.app.state.db
        cfg = eventbus_client.app.state.config
        now = "2026-09-09T10:00:00Z"
        consumer_id = "resume_consumer"

        # Insert three events
        seq1, _ = insert_event(db, "evt-resume-1", "test-topic", '{"data": "1"}', "producer", now)
        seq2, _ = insert_event(db, "evt-resume-2", "test-topic", '{"data": "2"}', "producer", now)
        seq3, _ = insert_event(db, "evt-resume-3", "test-topic", '{"data": "3"}', "producer", now)
        assert seq1 < seq2 < seq3

        # Consumer AACKs evt-resume-1 and evt-resume-2
        _, newly_acked_a, _ = ack_event_for_consumer(db, "evt-resume-1", consumer_id, now)
        assert newly_acked_a
        _, newly_acked_b, _ = ack_event_for_consumer(db, "evt-resume-2", consumer_id, now)
        assert newly_acked_b

        # Verify offset was advanced to seq2
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        assert row is not None
        assert int(row["offset"]) == seq2

        # Simulate restart: read offset via SQLite path
        start_seq = _get_offset_from_sqlite(db, consumer_id)
        assert start_seq == seq2

        # Subscribe with since_seq=start_seq — should deliver only evt-resume-3
        response = eventbus_client.get(
            "/events",
            params={"topic": ["test-topic"], "consumer_id": consumer_id, "since_seq": start_seq},
        )
        assert response.status_code == 200

        # Parse SSE stream and verify only evt-resume-3 is delivered
        lines = response.text.split("\n")
        data_lines = [line[5:] for line in lines if line.startswith("data:")]
        assert len(data_lines) == 1
        assert '"event_id":"evt-resume-3"' in data_lines[0]
```

### Details

The key changes are:

1. **Three events inserted**: The test inserts three events with increasing seq values.
2. **Two ACKs performed**: The consumer ACKs the first two events using `ack_event_for_consumer()`.
3. **Offset verified**: The offset is confirmed to be set to seq2 (the second event's seq).
4. **SQLite offset read**: The test reads the offset via `_get_offset_from_sqlite()` to simulate the subscribe route's offset lookup.
5. **SSE stream verification**: The test subscribes with `since_seq=start_seq` and verifies only the third event is delivered.

## Compatibility considerations

- The existing `test_restart_resume` test pattern is preserved.
- The `make_eventbus_client()` fixture is reused as-is.
- The `sse_stream()` helper is reused as-is.

## Security considerations

- No new authentication or authorization boundaries introduced.
- SQL values are bound via `?` placeholders — no injection risk.

## Rollback considerations

- To rollback: remove the new test method.
- The rollback restores the pre-change state where only file-based offset resume testing exists.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_restart_resume.py` | Integration test | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` | Resume-from-offset works against the SQLite-backed store |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass |

## Completion criteria

- `test_resume_from_sqlite_offset` asserts the consumer can resume from the SQLite-backed offset.
- SSE stream delivers only unacked events starting from the correct offset.
- No regressions in existing tests.

## Out of scope

- Modifying `nack_event()` behavior — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add resume-from-SQLite-offset test | Completed | — | — | |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: tests/eventbus/test_eventbus_restart_resume.py
