# Implementation Procedure: Read DLQ Internal Operations Evidence

## Goal

Read `scripts/eventbus/dlq.py` to gather evidence for documenting DLQ internal operations in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/dlq.py`: understand DLQ task logic (not exposed via API directly)
- No modifications to this file

## Assumptions

- REQ-006 requires documentation of DLQ list pagination and requeue response fields
- The DLQ internal operations are documented in the `Document DLQ Endpoint Contracts (REQ-006)` section of the plan
- The DLQ task logic is not exposed via API directly but informs the DLQ endpoint behavior

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify dlq.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/dlq.py` (read-only)

### Procedure

#### Step 1: Locate DLQ task logic

Find the DLQ task logic in `dlq.py`. Focus on:
- How DLQ entries are managed
- The relationship between DLQ entries and active event queue
- Any atomicity guarantees during requeue operations

#### Step 2: Verify DLQ internal operations accuracy

Compare the plan's documented contracts against the actual DLQ internal operations:

##### DLQ List Pagination

Current state in `dlq_route.py` (referenced from `dlq.py`):
```python
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
```

Documented contract:
```markdown
## GET /dlq

List dead-letter queue entries with pagination support.

### Parameters
- `limit` (int, default=100): Maximum items per page (1-1000)
- `offset` (int, default=0): Pagination offset (>=0)

### Authentication
Operator role required (after eventbus02/03).

### Response
```json
{
    "total": 50,
    "limit": 100,
    "offset": 0,
    "items": [
        {"event_id": "evt_xyz", "seq": 100, "topic": "orders", "payload": {...}, "dlq_at": "2026-09-14T10:00:00Z"},
        {"event_id": "evt_abc", "seq": 101, "topic": "orders", "payload": {...}, "dlq_at": "2026-09-14T10:05:00Z"}
    ]
}
```
```

Verify:
- [ ] `_role` parameter exists but is unused (underscore-prefixed convention)
- [ ] Response format matches the documented contract
- [ ] HTTP status codes match the documented contract

##### DLQ Requeue

Current state in `dlq_route.py` (referenced from `dlq.py`):
```python
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
```

Documented contract:
```markdown
## POST /dlq/{event_id}/requeue

Requeue a dead-letter queue entry back into the active event queue.

### Path Parameters
- `event_id` (str): The event ID to requeue

### Authentication
Operator role required (after eventbus02/03).

### Response

#### Success (HTTP 200)
```json
{
    "event_id": "evt_xyz",
    "requeued": true,
    "new_event_id": "evt_xyz_redelivered",
    "new_seq": 150
}
```

#### Conflict (HTTP 409)
The event exists but is not currently in DLQ (already redelivered or acked):
```json
{
    "detail": "Event is not currently in the dead letter queue"
}
```

#### Not Found (HTTP 404)
The event does not exist:
```json
{
    "detail": "Event not found"
}
```

### Idempotency and Race Behavior
- Each requeue creates a new event row with `redelivered_from` pointing to the original event_id
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- Concurrent requeue attempts on the same event will result in exactly one success; subsequent attempts return HTTP 409
- This behavior is enforced by the database-level constraint that `dlq_at IS NULL` must hold for a successful requeue
```

Verify:
- [ ] `_role` parameter exists but is unused (underscore-prefixed convention)
- [ ] Response format matches the documented contract
- [ ] HTTP status codes match the documented contract
- [ ] Idempotency and race behavior matches the documented contract

#### Step 3: Document findings for API reference

Record any discrepancies between the documented contract and the actual DLQ internal operations. Key questions to answer:
1. Are there any differences in response format?
2. Are there any additional HTTP status codes not documented?
3. Is the authentication requirement accurate?
4. Does the idempotency and race behavior match the documented contract?

### Method

Manual code review — read the relevant sections of `dlq.py` and verify the DLQ internal operations.

### Details

#### Verification checklist

- [ ] DLQ list pagination understood
- [ ] DLQ requeue understood
- [ ] Response formats verified against documented contracts
- [ ] HTTP status codes verified against documented contracts
- [ ] Idempotency and race behavior verified

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `docs/eventbus/` API reference documentation

## Security considerations

- No security impact — this is a read-only step
- Understanding DLQ internal operations is critical for accurate documentation

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of DLQ internal operations matches the documented behavior
2. Verify that response formats match the documented contracts
3. Verify that HTTP status codes match the documented contracts
4. Verify that idempotency and race behavior matches the documented contract

## Completion criteria

- [ ] DLQ list pagination understood
- [ ] DLQ requeue understood
- [ ] Response formats verified
- [ ] HTTP status codes verified
- [ ] Idempotency and race behavior verified

## Out of scope

- Modifying DLQ task logic
- Adding new DLQ operations
- Changing the DLQ response format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate DLQ task logic | Pending | — | — | |
| 2 | Verify DLQ internal operations accuracy | Pending | — | — | |
| 3 | Document findings for API reference | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (document DLQ list pagination and requeue response fields)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-070312
- **Related target files**: scripts/eventbus/dlq.py
