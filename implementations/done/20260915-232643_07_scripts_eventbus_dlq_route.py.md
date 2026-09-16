## Goal

Evidence for DLQ endpoint contract during eventbus11's API reference documentation. Read-only verification. REQ-006.

## Scope

Verify dlq_route.py's DLQ endpoint contract (pagination, requeue response). This row is read-only evidence gathering.

## Assumptions

- dlq_route.py exists at `scripts/eventbus/dlq_route.py`
- GET /dlq supports pagination with total/limit/offset/items
- POST /dlq/{event_id}/requeue returns {event_id, requeued, new_event_id, new_seq} on success, 409/404 on failure
- Operator role required

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the DLQ endpoints already match the plan's documented contracts, mark this step as complete
- If stale contracts exist, report Plan Gap

## Alternatives considered

- Independently updating dlq_route.py: rejected because eventbus11's scope is documentation only
- Deferring until eventbus11 executes: not viable since eventbus11 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Check whether dlq_route.py defines GET /dlq endpoint
2. Check whether dlq_route.py defines POST /dlq/{event_id}/requeue endpoint
3. Verify DLQ list pagination format
4. Verify DLQ requeue response format
5. If all checks pass, mark this step as complete
6. If any check fails, determine whether eventbus06 has landed:
   - If eventbus06 has not landed: missing endpoints are expected, no action needed
   - If eventbus06 has landed but contracts don't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current dlq_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify DLQ list endpoint**

Expected: GET /dlq handler returning {total, limit, offset, items}.

Pre-migration state: DLQ endpoint was pending per ADR-013 (now stale).

**Step 2: Verify DLQ requeue endpoint**

Expected: POST /dlq/{event_id}/requeue handler returning {event_id, requeued, new_event_id, new_seq} on success, 409/404 on failure.

**Step 3: Verify pagination format**

Expected: total, limit, offset, items fields in list response.

**Step 4: Verify requeue response format**

Expected: Success (HTTP 200), Conflict (HTTP 409), Not Found (HTTP 404) responses.

## Compatibility considerations

- This verification must occur after eventbus06 lands; executing before eventbus06 would produce false positives
- The DLQ endpoints may have been updated since eventbus06's approval — verify alignment rather than duplicating the edit
- If dlq_route.py still lacks expected functionality after eventbus06 lands, the gap belongs to eventbus06's execution, not eventbus11

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If dlq_route.py needs correction, defer to eventbus06's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq_route.py | Manual review: verify DLQ endpoint contracts | Manual inspection | Contracts match documented API reference |

## Completion criteria

- dlq_route.py defines GET /dlq endpoint with correct pagination format
- dlq_route.py defines POST /dlq/{event_id}/requeue endpoint with correct response formats
- Both endpoints require Operator role authentication

## Out of scope

- Modifying dlq_route.py directly (unless stale content requires correction, which should be deferred to eventbus06)
- Re-deciding the DLQ endpoint design (answered by eventbus06)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify DLQ list endpoint exists and matches documented contract | Passed | — | — | dlq_list関数定義済み（dlq_route.py:21） |
| 2 | Verify DLQ requeue endpoint exists and matches documented contract | Passed | — | — | dlq_requeue関数定義済み（dlq_route.py:49） |
| 3 | Verify pagination format alignment | Passed | — | — | {total, limit, offset, items}が計画と一致（dlq_route.py:42-45） |
| 4 | Verify requeue response format alignment | Passed | — | — | 成功: {event_id, requeued, new_event_id, new_seq}（dlq_route.py:80-91）、409: ERR_EVENT_NOT_IN_DLQ（dlq_route.py:98）、404: ERR_EVENT_NOT_FOUND（dlq_route.py:99） |

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
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/dlq_route.py
