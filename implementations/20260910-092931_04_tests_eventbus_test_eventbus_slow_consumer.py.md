## Goal
Extend `TestSlowConsumer` to assert the overflowing subscription is actually
disconnected (not only that `slow_consumer_count()`/health `503` is reported); add
reconnect-after-disconnect coverage (REQ-004, REQ-006; AC1, AC2, AC5).

## Scope
In scope: new test methods in `TestSlowConsumer`. Out of scope:
`test_broker_queue_maxsize_limit`, `test_slow_consumer_threshold_detection`,
`test_health_reports_slow_consumer_count`,
`test_health_503_when_slow_consumer_threshold_exceeded` — these four existing tests
continue to pass unmodified; they test `maxsize=1000`/threshold-detection/health
reporting, none of which change.

## Assumptions
- The existing `client: TestClient` fixture pattern already used by all four current
  tests in this class can drive an overflow scenario (publish enough events to exceed
  `maxsize=1000` for one subscriber) and then observe the SSE stream ending.

## Design decisions
Add:
1. A test that overflows one subscriber's queue and asserts its SSE
   `StreamingResponse` actually terminates (the generator ends / no more events are
   yielded) rather than continuing silently (AC1).
2. A test that, after such a disconnect, reconnects with the same `consumer_id` and
   `since_seq=0` (letting offset-based resume take over) and asserts every event
   published after the last-committed offset is received — confirming
   reconnect-after-disconnect resumes correctly (AC2, REQ-004).

## Alternatives considered
Adding these as a new top-level test class (e.g. `TestOverflowDisconnect`) instead of
extending `TestSlowConsumer` was considered; extending the existing class is preferred
since these tests are a direct behavioral extension of the same overflow scenario the
existing tests already set up (`test_broker_queue_maxsize_limit`), avoiding duplicated
overflow-scenario setup code.

## Implementation
### Target file
`tests/eventbus/test_eventbus_slow_consumer.py`

### Procedure
1. Add `test_overflow_disconnects_subscriber` to `TestSlowConsumer`, reusing
   whatever overflow-inducing setup `test_broker_queue_maxsize_limit` already
   establishes.
2. Add `test_reconnect_after_overflow_disconnect_resumes_from_offset`, chaining a
   disconnect scenario with a fresh `/subscribe` call using the same `consumer_id`.

### Method
`pytest` test methods inside the existing `TestSlowConsumer` class, matching its
current style.

### Details
```python
class TestSlowConsumer:
    ...
    def test_overflow_disconnects_subscriber(self, client: TestClient) -> None:
        # publish enough events to exceed maxsize=1000 for one subscriber connection,
        # then assert the SSE stream for that subscriber ends (no further reads block
        # forever; the generator terminates)
        ...

    def test_reconnect_after_overflow_disconnect_resumes_from_offset(
        self, client: TestClient
    ) -> None:
        # trigger an overflow-disconnect for consumer_id="c1", ack some events to
        # advance its offset, then reconnect with consumer_id="c1" and assert only
        # events after the committed offset are received
        ...
```
Adapt exact overflow-inducing mechanics (how many events, what timing) to whatever
`test_broker_queue_maxsize_limit` already establishes as the working pattern for this
test client/fixture setup.

## Compatibility considerations
No existing test in this class is modified.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_slow_consumer.py -v` — all six tests
(four existing + two new) pass.

## Completion criteria
Both new tests pass, confirming overflow triggers an actual disconnect (AC1) and
reconnect-after-disconnect resumes from the last committed offset (AC2).

## Out of scope
The four pre-existing tests in this class — unmodified.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_overflow_disconnects_subscriber` | Pending | — | — | |
| 2 | Add `test_reconnect_after_overflow_disconnect_resumes_from_offset` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-006
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: tests/eventbus/test_eventbus_slow_consumer.py
