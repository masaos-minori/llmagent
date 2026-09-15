# Implementation Procedure: Read Replay Endpoint Contract Evidence

## Goal

Read `scripts/eventbus/replay_route.py` to gather evidence for documenting replay endpoint contract (SSE/JSON formats, pagination) in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/replay_route.py`: understand replay endpoint contract (SSE/JSON formats, pagination)
- No modifications to this file

## Assumptions

- REQ-005 requires documentation of replay SSE and JSON formats
- The replay endpoint is documented in the `Document Replay Endpoint Contract (REQ-005)` section of the plan
- Authentication: Operator role required (after eventbus02/03)

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify replay_route.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/replay_route.py` (read-only)

### Procedure

#### Step 1: Locate replay function

Find the `replay()` function in `replay_route.py`. Focus on lines 27-63 as referenced in the plan.

Current state in `replay_route.py`:
```python
async def replay(
    request: Request,
    since_seq: int = Query(default=0, ge=0),
    fmt: Literal["sse", "json"] = Query(default="sse", alias="format"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _role: Role | None = None,  # set by app.py wrapper
) -> Any:
```

#### Step 2: Verify replay endpoint contract accuracy

Compare the plan's documented contracts against the actual replay endpoint contract:

##### Parameters

Documented parameters:
- `since_seq` (int, default=0): Sequence number to start from (>=0)
- `format` (str, default="sse"): Response format — "sse" or "json"
- `limit` (int, default=100): Maximum items per page (1-1000)
- `offset` (int, default=0): Pagination offset (>=0)

Verify:
- [ ] All parameters present in the documented contract exist in the actual implementation
- [ ] Parameter types match the documented contract
- [ ] Default values match the documented contract
- [ ] Constraints (ge, le) match the documented contract

##### SSE Format (format=sse)

Documented contract:
```
id:{seq}\ndata:{json_data}\n\n
```

Example:
```
id:42
data:{"event_id":"evt_abc","seq":42,"topic":"orders","payload":{"order_id":123}}

id:43
data:{"event_id":"evt_def","seq":43,"topic":"orders","payload":{"order_id":124}}
```

Verify:
- [ ] SSE format matches the documented contract
- [ ] Example data structure matches the documented contract

##### JSON Format (format=json)

Documented contract:
```json
{
    "total": 1000,
    "limit": 100,
    "offset": 0,
    "items": [
        {"event_id": "evt_abc", "seq": 42, "topic": "orders", "payload": {"order_id": 123}},
        {"event_id": "evt_def", "seq": 43, "topic": "orders", "payload": {"order_id": 124}}
    ]
}
```

Verify:
- [ ] JSON format matches the documented contract
- [ ] Field names match the documented contract
- [ ] Data structure matches the documented contract

##### Notes

Documented notes:
- `total` represents the total count of events with seq > since_seq
- `items` contains at most `limit` entries starting from `offset`
- For paginated consumption, increment `offset` by `len(items)` until `len(items) < limit`

Verify:
- [ ] Notes match the documented contract
- [ ] Pagination behavior matches the documented contract

#### Step 3: Document findings for API reference

Record any discrepancies between the documented contract and the actual replay endpoint contract. Key questions to answer:
1. Are there any differences in response format?
2. Are there any additional HTTP status codes not documented?
3. Is the authentication requirement accurate?

### Method

Manual code review — read the relevant sections of `replay_route.py` and verify the replay endpoint contract.

### Details

#### Verification checklist

- [ ] replay() function understood
- [ ] Parameters verified against documented contract
- [ ] SSE format verified against documented contract
- [ ] JSON format verified against documented contract
- [ ] Notes verified against documented contract
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

1. Confirm understanding of replay endpoint contract matches the documented behavior
2. Verify that response formats match the documented contracts
3. Verify that HTTP status codes match the documented contracts
4. Verify that pagination behavior matches the documented contract

## Completion criteria

- [ ] replay() function understood
- [ ] Parameters verified
- [ ] SSE format verified
- [ ] JSON format verified
- [ ] Notes verified
- [ ] Authentication requirements verified

## Out of scope

- Modifying replay endpoint logic
- Adding new replay features
- Changing the replay response format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate replay function | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Verify replay endpoint contract accuracy | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Document findings for API reference | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-005 (document replay SSE and JSON formats)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-070446
- **Related target files**: scripts/eventbus/replay_route.py