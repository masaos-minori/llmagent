## Goal

Evidence for health endpoint contract during eventbus11's API reference documentation. Read-only verification. REQ-004.

## Scope

Verify health_route.py's health endpoint contract (status codes, response format). This row is read-only evidence gathering.

## Assumptions

- health_route.py exists at `scripts/eventbus/health_route.py`
- GET /health returns JSONResponse with status_code 200 (ok) or 503 (degraded)
- Response body includes: status, db, dlq_task, active_subscribers, max_queue_depth, slow_consumers, overflow_disconnects, duplicate_connection_rejections, degraded_reasons, metrics

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the health endpoint already matches the plan's documented contract, mark this step as complete
- If stale contract exists, report Plan Gap

## Alternatives considered

- Independently updating health_route.py: rejected because eventbus11's scope is documentation only
- Deferring until eventbus11 executes: not viable since eventbus11 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

1. Check whether health_route.py defines GET /health endpoint
2. Verify response format matches the plan's documented contract
3. Verify status codes (200 ok, 503 degraded)
4. If all checks pass, mark this step as complete
5. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing endpoint is expected, no action needed
   - If eventbus02 has landed but contract doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current health_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify health endpoint**

Expected: GET /health handler returning JSONResponse with status fields.

Pre-migration state: health endpoint was pending per ADR-013 (now stale).

**Step 2: Verify response format**

Expected: Response body matches the plan's documented contract (status, db, dlq_task, active_subscribers, max_queue_depth, slow_consumers, overflow_disconnects, duplicate_connection_rejections, degraded_reasons, metrics).

**Step 3: Verify status codes**

Expected: HTTP 200 for ok, HTTP 503 for degraded.

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The health endpoint may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If health_route.py still lacks expected functionality after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus11

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If health_route.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/health_route.py | Manual review: verify health endpoint contract | Manual inspection | Contract matches documented API reference |

## Completion criteria

- health_route.py defines GET /health endpoint
- Response format matches the plan's documented contract
- Status codes (200 ok, 503 degraded) are correct

## Out of scope

- Modifying health_route.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the health endpoint design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify health endpoint exists and matches documented contract | Passed | — | — | health_check関数（health_route.py:25）、JSONResponse返却 |
| 2 | Verify response format alignment | Passed | — | — | レスポンスボディの全フィールドが計画と一致（status, db, dlq_task, active_subscribers, max_queue_depth, slow_consumers, overflow_disconnects, duplicate_connection_rejections, degraded_reasons, metrics） |
| 3 | Verify status codes | Passed | — | — | HTTP 200 (ok) / 503 (degraded)、health_route.py:91 |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/health_route.py
