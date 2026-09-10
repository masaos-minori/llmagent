## Goal
Add a test that injects a failure into the new offset-advancement step after the
delivery-state write, asserting both are rolled back together (REQ-003; AC-3).

## Scope
In scope: one new test in `TestCrashBeforeAck` (or a sibling class) covering a
mid-transaction failure in `ack_event_for_consumer()`. Out of scope: the existing
disconnect-before-ack coverage in `TestCrashBeforeAck` — unmodified.

## Assumptions
- `ack_event_for_consumer()` (row 03) can be tested directly at the `eventbus.db`
  level with a mocked/patched `conn.execute` (or the second `INSERT` specifically)
  raising an exception, without needing to go through the HTTP layer, since the
  failure must be injected precisely between the two writes.

## Design decisions
Add a test that: (1) inserts an event; (2) monkeypatches or mocks the
`consumer_offsets` advancement statement to raise an exception (e.g. by patching
`conn.execute` to raise on its second invocation within the function, or by using a
connection wrapper); (3) calls `ack_event_for_consumer()`; (4) asserts the exception
propagates; (5) asserts, by querying `consumer_delivery` directly, that no delivery
row was left committed (rolled back), and `consumer_offsets` also has no row for that
consumer — confirming the transaction's atomicity rather than a partial write.

## Alternatives considered
Testing this only via `ack_route.py`'s HTTP endpoint (patching `write_offset`-era
code) was considered; testing `ack_event_for_consumer()` directly at the `eventbus.db`
level instead gives a more precise, mechanism-level assertion of the rollback,
independent of the HTTP layer's own error translation — matches this file's existing
`TestCrashBeforeAck` class's apparent scope (crash/failure-injection at the
data-layer/lifecycle level, not HTTP status codes).

## Implementation
### Target file
`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure
1. Add a test method to `TestCrashBeforeAck` (e.g.
   `test_offset_write_failure_rolls_back_delivery_write`).
2. Use `unittest.mock.patch` or a connection subclass to make the offset-advancement
   `INSERT`/`UPDATE` raise `sqlite3.Error` (or a generic exception) while leaving the
   delivery-state `INSERT` unaffected.
3. Assert `ack_event_for_consumer()` raises, and a follow-up query on
   `consumer_delivery`/`consumer_offsets` shows neither row present.

### Method
`pytest` test method inside the existing `TestCrashBeforeAck` class, using
`unittest.mock` for the injected failure, matching whatever mocking style this file's
existing tests already use (confirm at implementation time).

### Details
```python
class TestCrashBeforeAck:
    ...
    def test_offset_write_failure_rolls_back_delivery_write(self, eventbus_db_conn):
        event_id = insert_test_event(eventbus_db_conn, ...)
        real_execute = eventbus_db_conn.execute
        call_count = {"n": 0}

        def flaky_execute(sql, *args, **kwargs):
            call_count["n"] += 1
            if "consumer_offsets" in sql and call_count["n"] > 1:
                raise sqlite3.OperationalError("simulated offset-write failure")
            return real_execute(sql, *args, **kwargs)

        eventbus_db_conn.execute = flaky_execute
        with pytest.raises(sqlite3.OperationalError):
            ack_event_for_consumer(eventbus_db_conn, event_id, "consumer-a", now_iso())

        eventbus_db_conn.execute = real_execute
        delivery_row = eventbus_db_conn.execute(
            "SELECT * FROM consumer_delivery WHERE consumer_id = ? AND event_id = ?",
            ("consumer-a", event_id),
        ).fetchone()
        offset_row = eventbus_db_conn.execute(
            "SELECT * FROM consumer_offsets WHERE consumer_id = ?", ("consumer-a",)
        ).fetchone()
        assert delivery_row is None
        assert offset_row is None
```
Adapt the exact patching mechanism to whatever fixture (`eventbus_db_conn` or
equivalent) and event-insertion helper this file/`tests/eventbus/eventbus_helpers.py`
already provide.

## Compatibility considerations
No existing test is modified; this is an additive failure-injection test targeting the
new function introduced in row 03.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` — new test passes
alongside all existing tests in this file.

## Completion criteria
The new test passes, confirming a failure in the offset-advancement step leaves the
delivery-state write rolled back rather than partially committed (AC-3).

## Out of scope
Any change to `TestCrashBeforeAck`'s existing disconnect-before-ack tests, or to
production code (covered by row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_offset_write_failure_rolls_back_delivery_write` to `TestCrashBeforeAck` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Generated at**: 20260910-092106
- **Related target files**: tests/eventbus/test_eventbus_crash_ack.py
