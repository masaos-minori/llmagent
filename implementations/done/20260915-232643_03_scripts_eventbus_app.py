## Goal

Evidence for route registration and middleware wiring during eventbus11's API reference documentation. Read-only verification. REQ-007.

## Scope

Verify app.py's route registration and middleware wiring for EventBus HTTP endpoints. This row is read-only evidence gathering.

## Assumptions

- app.py exists at `scripts/eventbus/app.py`
- app.py registers all EventBus routes (health, replay, DLQ, ACK/NACK)
- app.py attaches auth middleware

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the routing/middleware already matches the plan's documented contracts, mark this step as complete
- If stale wiring exists, report Plan Gap

## Alternatives considered

- Independently updating app.py: rejected because eventbus11's scope is documentation only
- Deferring until eventbus11 executes: not viable since eventbus11 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Check whether app.py registers health endpoint route
2. Check whether app.py registers replay endpoint route
3. Check whether app.py registers DLQ endpoint routes
4. Check whether app.py registers ACK/NACK endpoint routes
5. Check whether app.py attaches auth middleware
6. If all checks pass, mark this step as complete
7. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing routes are expected, no action needed
   - If eventbus02 has landed but routes don't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current app.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1-5: Verify route registration and middleware**

Expected: All EventBus routes registered with proper auth middleware attachment.

Pre-migration state: routes were pending per ADR-013 (now stale).

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The routing may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If app.py still lacks expected routes after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus11

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If app.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Manual review: verify route registration and middleware | Manual inspection | Routes and middleware match documented API reference |

## Completion criteria

- Health endpoint route is registered
- Replay endpoint route is registered
- DLQ endpoint routes are registered
- ACK/NACK endpoint routes are registered
- Auth middleware is attached

## Out of scope

- Modifying app.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the route registration design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify health endpoint route registration | Completed | — | 20260916-153xxx | PASS — @app.get("/health") at line 148 |
| 2 | Verify replay endpoint route registration | Completed | — | 20260916-153xxx | PASS — @app.get("/replay") at line 165 |
| 3 | Verify DLQ endpoint route registration | Completed | — | 20260916-153xxx | PASS — @app.get("/dlq") at line 204, @app.post("/dlq/{event_id}/requeue") at line 216 |
| 4 | Verify ACK/NACK endpoint route registration | Completed | — | 20260916-153xxx | PASS — @app.post("/events/{event_id}/ack") at line 227, @app.post("/nack") at line 245 |
| 5 | Verify auth middleware attachment | Completed | — | 20260916-153xxx | PASS — attach_auth_middleware(app) at line 145 |

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
- **Related target files**: scripts/eventbus/app.py
