# Implementation Procedure: Add per-consumer already-ACKed check in `nack_event()`

## Goal

Reject a NACK from consumer C for event E when C has already ACKed E, returning the invalid-transition sentinel (-2) without incrementing any failure counters. REQ-001, REQ-002, REQ-004, REQ-005.

## Scope

Modify `nack_event()` in `scripts/eventbus/delivery_repo.py` to add a per-consumer already-ACKed check inside the existing UPDATE statement.

## Assumptions

- The `consumer_delivery` table already holds the per-consumer ACK state with a primary key on `(consumer_id, event_id)` (confirmed in `scripts/eventbus/schema.sql`).
- No schema change is needed.
- The `consumer_id is None` path of `nack_event()` keeps its current events-level-only behavior.

## Design decisions

- Put the per-consumer check in the UPDATE itself via a `NOT EXISTS` subquery bound to `consumer_id`, rather than a separate SELECT, so the check and the counter increment cannot interleave with a concurrent ACK.
- When the UPDATE matches no row, the existing follow-up SELECT distinguishes not-found (-1) from invalid transition (-2).

## Alternatives considered

- Separate SELECT before UPDATE: would introduce a TOCTOU race between the check and the counter update.
- Setting `events.acked_at` from the per-consumer ACK path: out of scope for this Plan.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

1. In `nack_event()`, when `consumer_id` is provided, add a `NOT EXISTS` subquery to the UPDATE's WHERE clause that checks `consumer_delivery.acked_at IS NOT NULL` for the requesting `consumer_id`.
2. Keep the existing not-found/invalid-state result handling unchanged.

### Method

Modify the WHERE clause of the UPDATE statement in `nack_event()` (current lines 91-92):

```python
where_clause = (
    f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"
)
```

Add a `NOT EXISTS` subquery when `consumer_id` is provided:

```python
if consumer_id is not None:
    where_clause += (
        f" AND NOT EXISTS ("
        f"SELECT 1 FROM consumer_delivery "
        f"WHERE consumer_id = ? AND event_id = ? AND acked_at IS NOT NULL"
        f")"
    )
    params.append(consumer_id)
    params.append(event_id)
```

### Details

- Current `nack_event()` (lines 68-123): builds `WHERE event_id = ? AND acked_at IS NULL AND dlq_at IS NULL` and never reads `consumer_delivery`.
- When `consumer_id` is provided, the function also increments `consumer_delivery_failure_count` (line 98).
- The new `NOT EXISTS` subquery checks whether the requesting consumer has already ACKed the event. If it has, the UPDATE matches zero rows, and the existing follow-up SELECT returns `NackResult(-2, -2)` (invalid transition).
- The `consumer_id is None` path remains unchanged — it uses only the events-level `acked_at`/`dlq_at` check.
- The `NOT EXISTS` subquery is parameterized with `consumer_id` and `event_id` to prevent SQL injection.

## Compatibility considerations

- The `consumer_id is None` path is unchanged — existing callers that do not provide `consumer_id` see no behavioral difference.
- The return value for the per-consumer ACK case is `-2` (invalid transition), which the route maps to HTTP 409. This is consistent with the existing invalid-transition sentinel used for the events-level ACK case.

## Security considerations

- The `NOT EXISTS` subquery uses parameterized queries, consistent with the existing code pattern.
- No new credential or secret exposure.

## Rollback considerations

- Revert the WHERE clause modification to restore the original behavior.
- No schema changes, so no data migration rollback needed.

## Validation plan

- Unit: `ack_event_for_consumer()` then `nack_event()` for the same consumer returns the invalid-transition result and leaves all counters unchanged.
- Unit: `nack_event()` for a different consumer that has not ACKed still increments counters.
- Unit: `nack_event()` called without `consumer_id` keeps its current behavior.
- Route: POST ack then POST nack returns 409 with `event already acknowledged`; counters verified via the database.
- Existing suite: `uv run pytest tests/eventbus` passes with no changes to existing tests.

## Completion criteria

- `nack_event()` rejects a NACK from a consumer that has already ACKed the event, returning `NackResult(-2, -2)` without incrementing any counters.
- The `consumer_id is None` path is unchanged.
- All existing tests pass.

## Out of scope

- Modifying the `nack` route's 409 detail mapping (handled in a separate procedure document).
- Adding regression tests (handled in a separate procedure document).
- Updating documentation (handled in a separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-155308
- **Related target files**: scripts/eventbus/delivery_repo.py
