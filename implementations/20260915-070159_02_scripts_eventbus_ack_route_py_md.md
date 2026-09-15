# Implementation Procedure: Read ACK Endpoint Contract Evidence

## Goal

Read `scripts/eventbus/ack_route.py` to gather evidence for documenting ACK/NACK endpoint contracts in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/ack_route.py`: understand ACK/NACK endpoint contract (status codes, response format)
- No modifications to this file

## Assumptions

- REQ-007 requires documentation of endpoint role requirements after authorization is corrected
- The ACK/NACK endpoints are documented in the `Document ACK/NACK Endpoint Contracts (REQ-007)` section of the plan
- Authentication: Consumer role required (after eventbus02/03)

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify ack_route.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/ack_route.py` (read-only)

### Procedure

#### Step 1: Locate POST /ack/{event_id} handler

Find the `ack_event()` function in `ack_route.py`. Focus on:
- Function signature and parameters
- Response format (success and error cases)
- HTTP status codes returned
- Any authentication/authorization logic

#### Step 2: Locate POST /nack/{event_id} handler

Find the `nack()` function in `ack_route.py`. Focus on:
- Function signature and parameters
- Response format (success and error cases)
- HTTP status codes returned
- Any authentication/authorization logic

#### Step 3: Verify documented contract accuracy

Compare the plan's documented contracts against the actual implementation:

##### POST /ack/{event_id}

Current state in `ack_route.py`:
```python
async def ack_event(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> JSONResponse:
```

Documented contract:
```markdown
## POST /ack/{event_id}

Acknowledge an event, confirming it has been processed successfully.

### Path Parameters
- `event_id` (str): The event ID to acknowledge

### Authentication
Consumer role required (after eventbus02/03).

### Response

#### Success (HTTP 200)
```json
{
    "event_id": "evt_abc",
    "acked": true
}
```

#### Not Found (HTTP 404)
```json
{
    "detail": "Event not found"
}
```
```

Verify:
- [ ] `_role` parameter exists but is unused (underscore-prefixed convention)
- [ ] Response format matches the documented contract
- [ ] HTTP status codes match the documented contract

##### POST /nack/{event_id}

Current state in `ack_route.py`:
```python
async def nack(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> JSONResponse:
```

Documented contract:
```markdown
## POST /nack/{event_id}

Negative acknowledge an event, indicating processing failure and requesting retry.

### Path Parameters
- `event_id` (str): The event ID to negative acknowledge

### Authentication
Consumer role required (after eventbus02/03).

### Response

#### Success (HTTP 200)
```json
{
    "event_id": "evt_abc",
    "nacked": true
}
```

#### Not Found (HTTP 404)
```json
{
    "detail": "Event not found"
}
```
```

Verify:
- [ ] `_role` parameter exists but is unused (underscore-prefixed convention)
- [ ] Response format matches the documented contract
- [ ] HTTP status codes match the documented contract

#### Step 4: Document findings for API reference

Record any discrepancies between the documented contract and the actual implementation. Key questions to answer:
1. Are there any differences in response format?
2. Are there any additional HTTP status codes not documented?
3. Is the authentication requirement accurate?

### Method

Manual code review — read the relevant sections of `ack_route.py` and verify the documented contracts.

### Details

#### Verification checklist

- [ ] POST /ack/{event_id} handler understood
- [ ] POST /nack/{event_id} handler understood
- [ ] Response formats verified against documented contracts
- [ ] HTTP status codes verified against documented contracts
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

1. Confirm understanding of ACK/NACK endpoint contracts matches the documented behavior
2. Verify that response formats match the documented contracts
3. Verify that HTTP status codes match the documented contracts

## Completion criteria

- [ ] POST /ack/{event_id} handler understood
- [ ] POST /nack/{event_id} handler understood
- [ ] Response formats verified
- [ ] HTTP status codes verified
- [ ] Authentication requirements verified

## Out of scope

- Modifying ACK/NACK handlers
- Adding new authentication logic
- Changing the response format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate POST /ack/{event_id} handler | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Locate POST /nack/{event_id} handler | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Verify documented contract accuracy | Completed | 20260915-230000 | 20260915-230000 |  |
| 4 | Document findings for API reference | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-007 (document endpoint role requirements after authorization is corrected)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-070159
- **Related target files**: scripts/eventbus/ack_route.py