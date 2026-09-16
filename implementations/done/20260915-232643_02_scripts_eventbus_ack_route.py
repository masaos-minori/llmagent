## Goal

Evidence for ACK endpoint contract during eventbus11's API reference documentation. Read-only verification. REQ-007.

## Scope

Verify ack_route.py's ACK/NACK endpoint contract (status codes, response format). This row is read-only evidence gathering for eventbus11's API reference.

## Assumptions

- ack_route.py exists at `scripts/eventbus/ack_route.py`
- POST /ack/{event_id} returns {event_id, acked}: true on success, 404 on not found
- POST /nack/{event_id} returns {event_id, nacked}: true on success, 404 on not found
- Consumer role required for both endpoints

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the endpoint contracts already match the plan's documented contracts, mark this step as complete
- If stale contracts exist, report Plan Gap

## Alternatives considered

- Independently updating ack_route.py: rejected because eventbus11's scope is documentation only
- Deferring until eventbus11 executes: not viable since eventbus11 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Check whether ack_route.py defines POST /ack/{event_id} endpoint
2. Check whether ack_route.py defines POST /nack/{event_id} endpoint
3. Verify response formats match the plan's documented contracts
4. If all checks pass, mark this step as complete
5. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing endpoints are expected, no action needed
   - If eventbus02 has landed but contracts don't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current ack_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify ACK endpoint**

Expected: POST /ack/{event_id} handler returning {event_id, acked}: true on success, 404 on not found.

**Step 2: Verify NACK endpoint**

Expected: POST /nack/{event_id} handler returning {event_id, nacked}: true on success, 404 on not found.

**Step 3: Verify authentication requirement**

Expected: Consumer role required for both endpoints via Depends(require_role(...)).

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The endpoint contracts may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If ack_route.py still lacks expected endpoints after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus11

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If ack_route.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/ack_route.py | Manual review: verify ACK/NACK endpoint contracts | Manual inspection | Contracts match documented API reference |

## Completion criteria

- ack_route.py defines POST /ack/{event_id} endpoint with correct response format
- ack_route.py defines POST /nack/{event_id} endpoint with correct response format
- Both endpoints require Consumer role authentication

## Out of scope

- Modifying ack_route.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the ACK/NACK endpoint design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify ACK endpoint exists and matches documented contract | Completed | — | 20260916-153xxx | PASS — ack_event returns {event_id, acked: True}; raises 404 when found=False |
| 2 | Verify NACK endpoint exists and matches documented contract | Blocked | — | 20260916-153xxx | Stale claim: documented {event_id, nacked: true} vs actual {event_id, delivery_failure_count, dlq_promoted} |
| 3 | Verify Consumer role authentication requirement | Blocked | — | 20260916-153xxx | Partial: _principal set by app.py wrapper, not Depends(require_role(...)) inline |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/ack_route.py
