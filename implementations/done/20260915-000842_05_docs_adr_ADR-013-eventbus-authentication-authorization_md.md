# Implementation Procedure: Reconcile ADR-013 Stale Claims Against Current State

## Goal

Update ADR-013-eventbus-authentication-authorization.md to reconcile stale claims against current implementation reality, specifically addressing:
- Problem section line 36 stating "No route in scripts/eventbus/ authenticates or authorizes callers" — STALE
- Known Deviations line 276 referencing EVENTBUS-008 and CI-001 as "open" — partially stale since EVENTBUS-008 was resolved
- Confirming the Known Deviation entry accurately reflects the current state

## Scope

- Modify only `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- Update Problem section to reflect current auth middleware existence
- Update Known Deviations to reflect EVENTBUS-008 resolution status
- Verify no other stale claims exist

## Assumptions

- EVENTBUS-008 resolution (2026-09-14) documented in governance doc is valid and complete
- Auth middleware provides sufficient protection for the EventBus HTTP API
- No new security gaps have emerged since the last review cycle

## Design decisions

- Update Problem section to reflect current auth middleware existence
- Update Known Deviations to reflect EVENTBUS-008 resolution status
- Preserve existing Decision statements (they express design intent, not current reality)
- Do not change Status field of ADR-013 (it remains Accepted)

## Alternatives considered

### Alternative A: Rewrite Problem section entirely

**Reason for rejection:** The Problem section describes the original security gap that motivated this ADR. Rewriting it would conflate historical context with current state. Instead, add a clarification note.

### Alternative B: Remove Known Deviations entries for resolved issues

**Reason for rejection:** Known Deviations serve as audit trail for operators. Removing them would lose visibility into past security gaps and their resolutions.

## Implementation

### Target file

`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

1. Read Problem section (lines 34-36) and verify accuracy against current implementation
2. Compare Problem section claim with current auth middleware existence
3. Update Problem section with clarification about current auth middleware
4. Read Known Deviations section (lines 274-278) and verify accuracy
5. Update Known Deviations to reflect EVENTBUS-008 resolution status
6. Run `tools/check_adr_reference.py --file docs/adr/ADR-013-eventbus-authentication-authorization.md` to validate ADR structure

### Method

Direct file modification with targeted edits.

### Details

#### Step 1: Verify Problem section

Current Problem section (lines 34-36):
```markdown
### Problem

No route in `scripts/eventbus/` authenticates or authorizes callers. Every route accepts unauthenticated requests, allowing any caller to act as any `consumer_id`, access any topic, administer the DLQ, and trigger replay without any permission check. Additionally, `load_config()` bypasses fail-closed validation for anything beyond the fixed removed-key list: an unknown key is silently ignored, and no key's type is checked before being handed to `EventBusConfig`.
```

Verify:
- First sentence is STALE — auth middleware now exists
- Second sentence is STALE — routes now require role-based authentication
- Third sentence is PARTIALLY STALE — config validation has improved but may still have gaps

#### Step 2: Add clarification to Problem section

Add after the Problem section:
```markdown
### Current State (Updated 2026-09-15)

Auth middleware (`attach_auth_middleware(app)`) is now attached to all routes in `scripts/eventbus/app.py`. Each route requires role-based authentication via `Depends(require_role(...))`. Consumer-facing routes (/subscribe, /ack, /nack) additionally require `Depends(require_consumer_identity)` for consumer identity validation. The Problem section above describes the pre-auth state; see the Known Deviations section below for residual gaps.
```

#### Step 3: Verify Known Deviations section

Current Known Deviations section (lines 274-278):
```markdown
## Known Deviations

`docs/00_governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-008 (No Production Authentication Model for Event Bus HTTP API, High severity, open) and CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, open) are both registered and marked `open`. Whether any further deviation remains open after Phase 2's implementation lands is tracked in row 4 of that document.
```

Verify:
- EVENTBUS-008 status: "open" — needs update to "resolved"
- CI-001 status: "open" — needs update to "resolved"
- Both are now resolved per governance doc updates

#### Step 4: Update Known Deviations section

Change to:
```markdown
## Known Deviations

`docs/00_governance_03_issue-and-uncertainty-management.md`'s EVENTBUS-008 (No Production Authentication Model for Event Bus HTTP API, High severity, resolved 2026-09-14) and CI-001 (EventBus process reads configuration directly instead of using ConfigLoader, High severity, resolved 2026-08-25) are both resolved. Residual gaps from EVENTBUS-008 (token with no configured consumer_id allowlist entry has consumer-identity validation skipped — fail-open) are tracked separately in `issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md`.
```

#### Step 5: Validate ADR structure

Run:
```bash
python tools/check_adr_reference.py --file docs/adr/ADR-013-eventbus-authentication-authorization.md
```

## Compatibility considerations

- Existing consumers of this ADR rely on the Problem section as historical context
- Updating the Problem section clarifies current state without changing the decision
- Operators should be aware of the residual EVENTBUS-008 gap during deployment

## Security considerations

- The Problem section correction acknowledges significant security improvement (auth middleware)
- The Known Deviations correction acknowledges EVENTBUS-008 resolution while documenting residual gaps
- Operators should be aware of the residual consumer-identity validation gap (fail-open when no consumer_id allowlist configured)

## Rollback considerations

- Changes are documentation-only; no code rollback needed
- If EVENTBUS-008 resolution is later found insufficient, revert the Known Deviations entry

## Validation plan

1. Manual review of Problem section against current implementation
2. Confirm auth middleware exists in app.py
3. Confirm each route requires appropriate role-based authentication
4. Confirm consumer identity validation exists on consumer-facing routes
5. Cross-check EVENTBUS-008 and CI-001 status with governance doc
6. Run `tools/check_adr_reference.py` to validate ADR structure

## Completion criteria

- [ ] Problem section updated with current state clarification
- [ ] Known Deviations section updated to reflect EVENTBUS-008 and CI-001 resolution
- [ ] Residual EVENTBUS-008 gap documented
- [ ] ADR structure validation passes
- [ ] No unintended changes to Decision statements

## Out of scope

- Modifying Decision statements (design intent remains unchanged)
- Adding new Known Deviations unless discovered during verification
- Changing auth middleware implementation
- Updating other ADRs or governance documents
- Implementing the consumer-identity validation fix for EVENTBUS-008 residual gap

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify Problem section accuracy | Pending | — | — | |
| 2 | Add current state clarification to Problem section | Pending | — | — | |
| 3 | Verify Known Deviations section accuracy | Pending | — | — | |
| 4 | Update Known Deviations section | Pending | — | — | |
| 5 | Run ADR structure validation | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (auth middleware integration)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-000842
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md
