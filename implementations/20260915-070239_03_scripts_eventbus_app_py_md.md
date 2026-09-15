# Implementation Procedure: Read Route Registration and Middleware Wiring Evidence

## Goal

Read `scripts/eventbus/app.py` to gather evidence for documenting route registration and middleware wiring in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/app.py`: understand route registration and middleware wiring
- No modifications to this file

## Assumptions

- REQ-007 requires documentation of endpoint role requirements after authorization is corrected
- The route registration and middleware wiring are documented in the `Document ACK/NACK Endpoint Contracts (REQ-007)` section of the plan
- Authentication: Consumer role required (after eventbus02/03)

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify app.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/app.py` (read-only)

### Procedure

#### Step 1: Locate route registration for ACK/NACK endpoints

Find the route registration for POST /ack/{event_id} and POST /nack/{event_id} in `app.py`. Focus on:
- How the routes are registered
- Any middleware or dependency injection applied
- Authentication/authorization wiring

#### Step 2: Verify route registration accuracy

Compare the plan's documented contracts against the actual route registration:

##### POST /ack/{event_id}

Current state in `app.py`:
```python
app.post("/ack/{event_id}")(lambda req, eid, _role=None: ack_event(req, eid, _role=_role))
```

Verify:
- [ ] Route path matches the documented contract (/ack/{event_id})
- [ ] Lambda function passes `_role` parameter to the handler
- [ ] Handler name matches the documented contract (ack_event)

##### POST /nack/{event_id}

Current state in `app.py`:
```python
app.post("/nack/{event_id}")(lambda req, eid, _role=None: nack(req, eid, _role=_role))
```

Verify:
- [ ] Route path matches the documented contract (/nack/{event_id})
- [ ] Lambda function passes `_role` parameter to the handler
- [ ] Handler name matches the documented contract (nack)

#### Step 3: Document findings for API reference

Record any discrepancies between the documented contract and the actual route registration. Key questions to answer:
1. Are there any differences in route paths?
2. Are there any additional middleware or dependencies not documented?
3. Is the authentication requirement accurate?

### Method

Manual code review — read the relevant sections of `app.py` and verify the route registration.

### Details

#### Verification checklist

- [ ] POST /ack/{event_id} route registration understood
- [ ] POST /nack/{event_id} route registration understood
- [ ] Route paths verified against documented contracts
- [ ] Middleware/dependency injection verified

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `docs/eventbus/` API reference documentation

## Security considerations

- No security impact — this is a read-only step
- Understanding middleware/dependency injection is critical for accurate documentation

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of route registration matches the documented behavior
2. Verify that route paths match the documented contracts
3. Verify that middleware/dependency injection is accurate

## Completion criteria

- [ ] POST /ack/{event_id} route registration understood
- [ ] POST /nack/{event_id} route registration understood
- [ ] Route paths verified
- [ ] Middleware/dependency injection verified

## Out of scope

- Modifying route registration
- Adding new middleware or dependencies
- Changing the authentication wiring

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate route registration for ACK/NACK endpoints | Pending | — | — | |
| 2 | Verify route registration accuracy | Pending | — | — | |
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
- **Requirement ID**: REQ-007 (document endpoint role requirements after authorization is corrected)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-070239
- **Related target files**: scripts/eventbus/app.py
