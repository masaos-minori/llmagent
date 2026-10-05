# Implementation Procedure: Map per-consumer ACK to `ERR_EVENT_ALREADY_ACKED` in the `nack` route

## Goal

On the invalid-transition branch (`failure_count == -2`), check the requesting consumer's `consumer_delivery.acked_at` first and raise `ERR_EVENT_ALREADY_ACKED` when the per-consumer ACK exists, keeping the events-level and fallback branches intact. REQ-001, REQ-003.

## Scope

Modify the invalid-transition branch in the `nack` route handler in `scripts/eventbus/ack_route.py`.

## Assumptions

- `ERR_EVENT_ALREADY_ACKED` is defined in `scripts/eventbus/route_helpers.py` (confirmed: line 78).
- The `nack_event()` function returns `NackResult(-2, -2)` for the per-consumer ACK case after the delivery_repo change.
- The `consumer_delivery` table has a PRIMARY KEY on `(consumer_id, event_id)` (confirmed in `scripts/eventbus/schema.sql`).

## Design decisions

- On the -2 result, the route first looks up `consumer_delivery.acked_at` for the requesting consumer and raises `ERR_EVENT_ALREADY_ACKED`; only then falls back to the existing `events.acked_at` / `events.dlq_at` inspection.
- This keeps the DLQ 409 and the fallback `invalid NACK transition` branches intact.

## Alternatives considered

- Checking `events.acked_at` first and then `consumer_delivery`: would incorrectly map the per-consumer ACK case to `invalid NACK transition` instead of `event already acknowledged`.
- Adding a new error constant: unnecessary since `ERR_EVENT_ALREADY_ACKED` already exists.

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. In the `nack` route's invalid-transition branch (current `failure_count == -2`), add a lookup for the requesting consumer's `consumer_delivery.acked_at` before the existing `events.acked_at` / `events.dlq_at` check.
2. Raise `HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)` when the per-consumer ACK exists.
3. Keep the existing events-level and fallback branches unchanged.

### Method

Modify the invalid-transition branch in the `nack` route (current lines 174-187):

```python
if failure_count == -2:
    # Invalid transition: event is already ACKed or DLQ'd
    # Determine which state by checking the event directly
    row = await run_with_db_lock(
        lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    )
    if row and row["acked_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    elif row and row["dlq_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
    else:
        raise HTTPException(status_code=409, detail="invalid NACK transition")
```

Replace with:

```python
if failure_count == -2:
    # Invalid transition: event is already ACKed or DLQ'd
    # Check per-consumer ACK first, then events-level state
    if consumer_id is not None:
        consumer_row = await run_with_db_lock(
            lambda: db.execute(
                "SELECT acked_at FROM consumer_delivery "
                "WHERE consumer_id = ? AND event_id = ?",
                (consumer_id, event_id),
            ).fetchone()
        )
        if consumer_row and consumer_row["acked_at"] is not None:
            raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    row = await run_with_db_lock(
        lambda: db.execute(
            "SELECT acked_at, dlq_at FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
    )
    if row and row["acked_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_ALREADY_ACKED)
    elif row and row["dlq_at"] is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_IN_DLQ)
    else:
        raise HTTPException(status_code=409, detail="invalid NACK transition")
```

### Details

- Current `nack` route (lines 118-197): the `failure_count == -2` branch re-reads only `events.acked_at`/`events.dlq_at`, so a per-consumer ACK would fall through to `invalid NACK transition`.
- After the delivery_repo change, `nack_event()` returns `NackResult(-2, -2)` for the per-consumer ACK case.
- The new per-consumer lookup checks `consumer_delivery.acked_at` for the requesting `consumer_id` before the events-level check.
- When `consumer_id is None`, the per-consumer lookup is skipped and the existing events-level check applies.
- The DLQ 409 and fallback `invalid NACK transition` branches are preserved.

## Compatibility considerations

- The events-level ACK case (where `events.acked_at` is set) continues to return `ERR_EVENT_ALREADY_ACKED` as before.
- The DLQ 409 case continues to return `ERR_EVENT_IN_DLQ` as before.
- The fallback `invalid NACK transition` case is preserved for edge cases where neither condition matches.
- The `consumer_id is None` path is unchanged — it uses only the events-level check.

## Security considerations

- The new `consumer_delivery` lookup uses parameterized queries, consistent with the existing code pattern.
- No new credential or secret exposure.

## Rollback considerations

- Revert the invalid-transition branch modification to restore the original behavior.
- No schema changes, so no data migration rollback needed.

## Validation plan

- Route: POST ack then POST nack returns 409 with `event already acknowledged`; counters verified via the database.
- Route: 403 is still returned before the state check for a non-owned `consumer_id`.
- Route: DLQ 409 unchanged.
- Existing suite: `uv run pytest tests/eventbus` passes with no changes to existing tests.

## Completion criteria

- The `nack` route returns HTTP 409 with `event already acknowledged` when the requesting consumer has already ACKed the event.
- The events-level ACK case continues to return `event already acknowledged` as before.
- The DLQ 409 case continues to return `event already in dead letter queue` as before.
- All existing tests pass.

## Out of scope

- Modifying `nack_event()` in delivery_repo.py (handled in a separate procedure document).
- Adding regression tests (handled in a separate procedure document).
- Updating documentation (handled in a separate procedure document).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-164838 | 20261005-164838 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261005-164838 | 20261005-164838 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-164838 | 20261005-164838 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-164838 | 20261005-164838 |  |

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
- **Source issue**: issues/20261005-102244_eb002_eventbus-nack-accepted-after-per-consumer-ack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-103619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-155308
- **Related target files**: scripts/eventbus/ack_route.py