# Implementation Procedure: Read DLQ Endpoint Contract Evidence

## Goal

Read `scripts/eventbus/dlq_route.py` to gather evidence for documenting DLQ endpoint contract (pagination, requeue response) in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/dlq_route.py`: understand DLQ endpoint contract (pagination, requeue response)
- No modifications to this file

## Assumptions

- REQ-006 requires documentation of DLQ list pagination and requeue response fields
- The DLQ endpoints are documented in the `Document DLQ Endpoint Contracts (REQ-006)` section of the plan
- Authentication: Operator role required (after eventbus02/03)

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify dlq_route.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/dlq_route.py` (read-only)

### Procedure

#### Step 1: Locate dlq_list function

Find the `dlq_list()` function in `dlq_route.py`. Focus on lines 21-47 as referenced in the plan.

Current state in `dlq_route.py`:
```python
async def dlq_list(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
```

#### Step 2: Verify DLQ list endpoint contract accuracy

Compare the plan's documented contracts against the actual DLQ list endpoint contract:

##### Parameters

Documented parameters:
- `limit` (int, default=100): Maximum items per page (1-1000)
- `offset` (int, default=0): Pagination offset (>=0)

Verify:
- [ ] All parameters present in the documented contract exist in the actual implementation
- [ ] Parameter types match the documented contract
- [ ] Default values match the documented contract
- [ ] Constraints (ge, le) match the documented contract

##### Response

Documented contract:
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

Verify:
- [ ] Response format matches the documented contract
- [ ] Field names match the documented contract
- [ ] Data structure matches the documented contract

#### Step 3: Locate dlq_requeue function

Find the `dlq_requeue()` function in `dlq_route.py`. Focus on lines 50-91 as referenced in the plan.

Current state in `dlq_route.py`:
```python
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
```

#### Step 4: Verify DLQ requeue endpoint contract accuracy

Compare the plan's documented contracts against the actual DLQ requeue endpoint contract:

##### Path Parameters

Documented path parameters:
- `event_id` (str): The event ID to requeue

Verify:
- [ ] Path parameter present in the documented contract exists in the actual implementation
- [ ] Parameter type matches the documented contract

##### Success (HTTP 200)

Documented contract:
```json
{
    "event_id": "evt_xyz",
    "requeued": true,
    "new_event_id": "evt_xyz_redelivered",
    "new_seq": 150
}
```

Verify:
- [ ] Response format matches the documented contract
- [ ] Field names match the documented contract
- [ ] Data structure matches the documented contract

##### Conflict (HTTP 409)

Documented contract:
```json
{
    "detail": "Event is not currently in the dead letter queue"
}
```

Verify:
- [ ] Response format matches the documented contract
- [ ] Error message matches the documented contract

##### Not Found (HTTP 404)

Documented contract:
```json
{
    "detail": "Event not found"
}
```

Verify:
- [ ] Response format matches the documented contract
- [ ] Error message matches the documented contract

##### Idempotency and Race Behavior

Documented behavior:
- Each requeue creates a new event row with `redelivered_from` pointing to the original event_id
- The original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event
- Concurrent requeue attempts on the same event will result in exactly one success; subsequent attempts return HTTP 409
- This behavior is enforced by the database-level constraint that `dlq_at IS NULL` must hold for a successful requeue

Verify:
- [ ] Idempotency behavior matches the documented contract
- [ ] Race behavior matches the documented contract
- [ ] Database-level constraint matches the documented contract

#### Step 5: Document findings for API reference

Record any discrepancies between the documented contract and the actual DLQ endpoint contract. Key questions to answer:
1. Are there any differences in response format?
2. Are there any additional HTTP status codes not documented?
3. Is the authentication requirement accurate?

### Method

Manual code review — read the relevant sections of `dlq_route.py` and verify the DLQ endpoint contract.

### Details

#### Verification checklist

- [ ] dlq_list() function understood
- [ ] dlq_requeue() function understood
- [ ] Parameters verified against documented contract
- [ ] Response formats verified against documented contracts
- [ ] HTTP status codes verified against documented contracts
- [ ] Idempotency and race behavior verified
- [ ] Authentication requirements verified

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `docs/eventbus/` API reference documentation

## Security considerations

- No security impact — this is a read-only step
- Understanding authentication requirements is critical for accurate documentation

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of DLQ endpoint contract matches the documented behavior
2. Verify that response formats match the documented contracts
3. Verify that HTTP status codes match the documented contracts
4. Verify that idempotency and race behavior matches the documented contract

## Completion criteria

- [ ] dlq_list() function understood
- [ ] dlq_requeue() function understood
- [ ] Parameters verified
- [ ] Response formats verified
- [ ] HTTP status codes verified
- [ ] Idempotency and race behavior verified
- [ ] Authentication requirements verified

## Out of scope

- Modifying DLQ endpoint logic
- Adding new DLQ operations
- Changing the DLQ response format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate dlq_list function | Pending | — | — | |
| 2 | Verify DLQ list endpoint contract accuracy | Pending | — | — | |
| 3 | Locate dlq_requeue function | Pending | — | — | |
| 4 | Verify DLQ requeue endpoint contract accuracy | Pending | — | — | |
| 5 | Document findings for API reference | Pending | — | — | |

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
- **Generated at**: 20260915-070526
- **Related target files**: scripts/eventbus/dlq_route.py
