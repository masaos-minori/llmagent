# Replace `requeue_event()` call with `redeliver_event()`; publish to EventBroker on success

## Goal

Update `scripts/eventbus/dlq_route.py`'s `dlq_requeue()` to call the new `redeliver_event()` (replacing `requeue_event()`) and, on success, call `EventBroker.publish()` with the new row's data — making the event reachable to active subscribers immediately, and to reconnecting subscribers via the existing `seq > since_seq` replay path.

## Scope

- Modify `dlq_requeue()`: replace `requeue_event()` call with `redeliver_event()` call.
- On successful redelivery, publish the new event to `EventBroker`.
- Update the response body to include the new row's `event_id` and `seq` (per UNK-01 default).

## Assumptions

- `dlq_requeue()` currently calls only `requeue_event()` and never `broker.publish()` or any DLQ-file reconciliation function (confirmed by direct read).
- `EventBroker.publish()`'s signature/behavior needs no change (confirmed by reading `broker.py`).
- `route_helpers.py` provides `get_broker()` as the existing wiring pattern.
- Reconnecting subscribers reach the new row via the existing `seq > since_seq` replay path in `subscribe_route.py` (confirmed by direct read — no code change needed there).

## Design decisions

- Call `redeliver_event(db, event_id)` inside `_requeue()` closure, replacing `requeue_event()`.
- On success, call `broker.publish(new_row_data)` where `new_row_data` is constructed from the new row's fields.
- Add `new_event_id` and `new_seq` fields to the response body per UNK-01 default.
- The response body gains additive fields: `"new_event_id"`, `"new_seq"` alongside existing `"requeued"`, `"dlq_imminent"`.

## Alternatives considered

- Publishing before the DB commit: rejected because the Plan specifies using SQLite as canonical state — the DB operation must succeed first, then publish.
- Using `insert_event()` + `broker.publish()` directly: rejected because `redeliver_event()` encapsulates the conditional-update guard + new-row insert logic, keeping the route handler thin.

## Compatibility considerations

- Active SSE subscribers receive the redelivered event via `EventBroker.publish()` (new behavior — previously invisible).
- Reconnecting subscribers receive it via the `seq > since_seq` replay path (existing mechanism, no change needed).
- The `/dlq/{event_id}/requeue` endpoint response gains new fields but remains backward-compatible (additive).

## Security considerations

- `EventBroker.publish()` validates the event envelope against `schemas/event_envelope.json`'s UUID v4 constraint for `event_id`.
- No user input flows into the published event data.

## Rollback considerations

- Reverting means restoring the `requeue_event()` call and removing the `broker.publish()` call.

## Validation plan

- Run `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -v` to confirm:
  - Redelivery produces a new `seq`/UUID `event_id`/`redelivered_from`.
  - The DLQ JSON file is archived.
  - Active subscribers receive the redelivered event.

## Completion criteria

- `dlq_requeue()` calls `redeliver_event()` instead of `requeue_event()`.
- On success, `EventBroker.publish()` is called with the new row's data.
- Response body includes `"new_event_id"` and `"new_seq"` fields.
- Tests pass confirming actual redelivery reachability.

## Out of scope

- Changes to `redeliver_event()` itself (handled separately in REQ-005).
- DLQ JSON file archival (handled separately in REQ-007).
- Promotion predicate switch (handled separately in REQ-008).
- Changes to `subscribe_route.py` (no change needed).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace requeue_event() with redeliver_event() | Completed | — | — | |
| 2 | Publish new event to EventBroker on success | Completed | — | — | |
| 3 | Update response body with new_event_id/new_seq | Completed | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260907-125042_eb_h03_dlq_requeue_real_redelivery.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-100315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-233401
- **Related target files**: scripts/eventbus/dlq_route.py
