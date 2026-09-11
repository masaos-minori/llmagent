# Update `test_nack_event_increments_failure_count`/`test_nack_event_increments_again` for `nack_event()`'s two-value return

## Goal

Update `tests/eventbus/test_eventbus_ack_nack.py` to assert `nack_event()`'s new two-value return `(delivery_failure_count, cycle_failure_count)` instead of the current single-int return.

## Scope

- Modify `test_nack_event_increments_failure_count`: unpack and assert both returned values.
- Modify `test_nack_event_increments_again`: same — assert both counts increment correctly.

## Assumptions

- Both tests currently assert `nack_event()`'s single-int return (confirmed by direct read).
- The `-1` sentinel for not-found events is preserved.

## Design decisions

- Unpack as `result = nack_event(conn, event_id)` then assert `result[0]` (lifetime) and `result[1]` (cycle).
- Both counts should increment together on each NACK call.
- After first NACK: `(1, 1)`, after second NACK: `(2, 2)`.

## Alternatives considered

- Using named tuple unpacking: rejected because it requires importing a namedtuple class and adds complexity for a simple positional pair.
- Asserting only one count: rejected because the breaking change requires verifying both values.

## Compatibility considerations

- These tests are internal unit tests — no external API contract change.
- The tests must be updated simultaneously with the `nack_event()` signature change.

## Security considerations

- No security surface change.

## Rollback considerations

- Reverting means restoring the single-int assertions.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` to confirm both tests pass with two-value assertions.

## Completion criteria

- `test_nack_event_increments_failure_count` asserts both `delivery_failure_count` and `cycle_failure_count` increment to 1.
- `test_nack_event_increments_again` asserts both counts increment to 2 after the second NACK.
- Tests pass.

## Out of scope

- Changes to `nack_event()` itself (handled separately in REQ-003).
- Changes to `ack_route.py` consumer (handled separately in REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update test_nack_event_increments_failure_count | Completed | — | — | |
| 2 | Update test_nack_event_increments_again | Completed | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py
