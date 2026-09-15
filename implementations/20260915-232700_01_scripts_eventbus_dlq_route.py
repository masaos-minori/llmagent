## Goal

Evidence for DLQ parameter cleanup during eventbus12's security parameter removal. REQ-002.

## Scope

Verify dlq_route.py's unused `_role` parameter removal from `dlq_list()` and `dlq_requeue()`. This row is read-only evidence gathering.

## Assumptions

- dlq_route.py exists at `scripts/eventbus/dlq_route.py`
- dlq_route.py currently has `_role` parameters in both `dlq_list()` and `dlq_requeue()`
- These parameters are unused in function bodies

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the `_role` parameters have already been removed, mark this step as complete
- If stale parameters exist, report Plan Gap

## Alternatives considered

- Independently removing `_role` parameters: rejected because eventbus12's scope is documentation only
- Deferring until eventbus12 executes: not viable since eventbus12 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Check whether dlq_route.py still has `_role` parameter in `dlq_list()`
2. Check whether dlq_route.py still has `_role` parameter in `dlq_requeue()`
3. Verify these parameters are unused in function bodies
4. If all checks pass, mark this step as complete
5. If any check fails, determine whether eventbus06 has landed:
   - If eventbus06 has not landed: missing `_role` parameters are expected, no action needed
   - If eventbus06 has landed but parameters remain: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current dlq_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify `_role` parameter in `dlq_list()`**

Expected: `_role: Role | None = None` parameter present and unused.

Pre-migration state: `_role` parameter exists per ADR-013 (now stale).

**Step 2: Verify `_role` parameter in `dlq_requeue()`**

Expected: `_role: Role | None = None` parameter present and unused.

**Step 3: Verify parameter usage**

Expected: Neither parameter used in function body.

## Compatibility considerations

- This verification must occur after eventbus06 lands; executing before eventbus06 would produce false positives
- The `_role` parameters may have been updated since eventbus06's approval — verify alignment rather than duplicating the edit
- If dlq_route.py still has expected parameters after eventbus06 lands, the gap belongs to eventbus06's execution, not eventbus12

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If dlq_route.py needs correction, defer to eventbus06's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/dlq_route.py | Manual review: verify `_role` parameter status | Manual inspection | Parameters match documented API reference |

## Completion criteria

- dlq_route.py does not have unused `_role` parameter in `dlq_list()`
- dlq_route.py does not have unused `_role` parameter in `dlq_requeue()`
- Both functions rely exclusively on endpoint-level authorization

## Out of scope

- Modifying dlq_route.py directly (unless stale content requires correction, which should be deferred to eventbus06)
- Re-deciding the parameter design (answered by eventbus06)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `_role` parameter in `dlq_list()` | Completed | — | — | Stale claim: no _role parameter; params are request, limit, offset |
| 2 | Verify `_role` parameter in `dlq_requeue()` | Completed | — | — | Stale claim: no _role parameter; params are request, event_id |
| 3 | Verify parameter usage status | Completed | — | — | Parameters removed before this verification cycle |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-102654_eventbus12_remove-misleading-security-parameters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-183834_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: scripts/eventbus/dlq_route.py
