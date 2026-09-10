## Goal
Add a test asserting two distinct `consumer_id`s can each independently ACK the same
`event_id` (REQ-001; AC-1, AC-2).

## Scope
In scope: one new test in `TestAckEvent` (or a sibling class) covering multi-consumer
independent ACK. Out of scope: `TestAckHttpBehavior`, `TestNackEvent` — unrelated to
this Requirement.

## Assumptions
- `TestAckEvent`'s existing fixture/setup pattern (single-consumer ACK) can be reused
  with two distinct `consumer_id` values passed to the ack endpoint/function under
  test, without needing a new fixture.

## Design decisions
Add a test that: (1) publishes one event; (2) ACKs it as `consumer_id="a"`; (3) ACKs
the same event as `consumer_id="b"`; (4) asserts both ACKs report `newly_acked=True`
(or the HTTP-level equivalent), i.e. neither consumer's ACK is blocked or silently
no-op'd by the other's — directly exercising `consumer_delivery`'s per-`(consumer_id,
event_id)` primary key (row 03).

## Alternatives considered
Testing this only at the `eventbus.db.ack_event_for_consumer()` unit level (no HTTP
layer) was considered; adding it to `TestAckEvent` instead, following the existing
class's established pattern in this file, keeps consistency with how single-consumer
ACK is already tested here.

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure
1. Add a test method to `TestAckEvent` (e.g. `test_two_consumers_ack_same_event_independently`).
2. Follow the class's existing setup pattern (whatever fixture/client construction
   `TestAckEvent`'s other methods already use) for publishing and acking an event.

### Method
`pytest` test method inside the existing `TestAckEvent` class, matching its current
style.

### Details
```python
class TestAckEvent:
    ...
    def test_two_consumers_ack_same_event_independently(self, client, ...):
        event_id = publish_event(client, topic="t1", payload={...})
        resp_a = ack_event(client, event_id, consumer_id="consumer-a")
        resp_b = ack_event(client, event_id, consumer_id="consumer-b")
        assert resp_a["acked"] is True
        assert resp_b["acked"] is True
        # neither consumer's ack should report "already_acked" due to the other's ack
        assert resp_a.get("already_acked") is not True
        assert resp_b.get("already_acked") is not True
```
Adapt to whatever concrete publish/ack helper functions this test file already uses
(confirm exact helper names at implementation time from the file's existing imports).

## Compatibility considerations
No existing test is modified; this is an additive test asserting new per-consumer
behavior introduced by rows 01-04.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` — new test passes
alongside all existing tests in this file.

## Completion criteria
The new test passes, confirming two distinct `consumer_id`s can each ACK the same
event independently with no collision (AC-1, AC-2).

## Out of scope
Any change to `TestNackEvent`/`TestAckHttpBehavior`, or to production code (covered by
rows 01-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_two_consumers_ack_same_event_independently` to `TestAckEvent` | Pending | — | — | |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
