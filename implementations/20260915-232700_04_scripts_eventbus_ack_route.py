## Goal

Evidence for ACK route parameter cleanup during eventbus12's security parameter removal. REQ-002.

## Scope

Verify ack_route.py's unused `_role` and `_identity` parameter removal from `_do_ack()`, `ack_event()`, and `nack()`. This row is read-only evidence gathering.

## Assumptions

- ack_route.py exists at `scripts/eventbus/ack_route.py`
- ack_route.py currently has `_role` and `_identity` parameters in all three functions
- These parameters are unused in function bodies

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the `_role` and `_identity` parameters have already been removed, mark this step as complete
- If stale parameters exist, report Plan Gap

## Alternatives considered

- Independently removing `_role` and `_identity` parameters: rejected because eventbus12's scope is documentation only
- Deferring until eventbus12 executes: not viable since eventbus12 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/ack_route.py`

### Procedure

1. Check whether ack_route.py still has `_role` and `_identity` parameters in `_do_ack()`
2. Check whether ack_route.py still has `_role` and `_identity` parameters in `ack_event()`
3. Check whether ack_route.py still has `_role` and `_identity` parameters in `nack()`
4. Verify these parameters are unused in function bodies
5. If all checks pass, mark this step as complete
6. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing parameters are expected, no action needed
   - If eventbus02 has landed but parameters remain: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current ack_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify `_role` and `_identity` parameters in `_do_ack()`**

Expected: Both `_role: Role | None = None` and `_identity: dict[str, Any] | None = None` parameters present and unused.

Pre-migration state: Both parameters exist per ADR-013 (now stale).

**Step 2: Verify `_role` and `_identity` parameters in `ack_event()`**

Expected: Both `_role: Role | None = None` and `_identity: dict[str, Any] | None = None` parameters present and unused.

**Step 3: Verify `_role` and `_identity` parameters in `nack()`**

Expected: Both `_role: Role | None = None` and `_identity: dict[str, Any] | None = None` parameters present and unused.

**Step 4: Verify parameter usage**

Expected: Neither parameter used in any function body.

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The `_role` and `_identity` parameters may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If ack_route.py still has expected parameters after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus12

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If ack_route.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/ack_route.py | Manual review: verify `_role` and `_identity` parameter status | Manual inspection | Parameters match documented API reference |

## Completion criteria

- ack_route.py does not have unused `_role` and `_identity` parameters in `_do_ack()`
- ack_route.py does not have unused `_role` and `_identity` parameters in `ack_event()`
- ack_route.py does not have unused `_role` and `_identity` parameters in `nack()`
- All functions rely exclusively on endpoint-level authorization

## Out of scope

- Modifying ack_route.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the parameter design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `_role` and `_identity` parameters in `_do_ack()` | Pending | — | — | |
| 2 | Verify `_role` and `_identity` parameters in `ack_event()` | Pending | — | — | |
| 3 | Verify `_role` and `_identity` parameters in `nack()` | Pending | — | — | |
| 4 | Verify parameter usage status | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/ack_route.py
