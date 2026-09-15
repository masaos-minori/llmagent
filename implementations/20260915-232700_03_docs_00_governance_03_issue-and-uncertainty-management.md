## Goal

Evidence for EVENTBUS-001 governance doc correction during eventbus14's collision risk bounding. REQ-003.

## Scope

Verify docs/00_governance_03_issue-and-uncertainty-management.md's EVENTBUS-001 correction. This row is read-only evidence gathering.

## Assumptions

- Governance doc exists at `docs/00_governance_03_issue-and-uncertainty-management.md`
- EVENTBUS-001 claims `_sanitize_consumer_id()` can cause silent offset overwriting

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If EVENTBUS-001 has already been corrected, mark this step as complete
- If stale EVENTBUS-001 entry exists, report Plan Gap

## Alternatives considered

- Independently correcting EVENTBUS-001: rejected because eventbus14's scope is documentation only
- Deferring until eventbus14 executes: not viable since eventbus14 depends on eventbus04 landing first

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Check whether EVENTBUS-001 still describes the collision risk as applying to the live ACK path
2. Verify EVENTBUS-001's severity and related references match the plan's documented contract
3. If all checks pass, mark this step as complete
4. If any check fails, determine whether eventbus04 has landed:
   - If eventbus04 has not landed: missing EVENTBUS-001 correction is expected, no action needed
   - If eventbus04 has landed but EVENTBUS-001 doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current governance doc state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify EVENTBUS-001 status**

Expected: EVENTBUS-001 describes the collision risk as applying to the live ACK path.

Pre-migration state: EVENTBUS-001 open per ADR-013 (now stale).

**Step 2: Verify EVENTBUS-001 severity and related references**

Expected: Severity and related references match the plan's documented contract.

## Compatibility considerations

- This verification must occur after eventbus04 lands; executing before eventbus04 would produce false positives
- The EVENTBUS-001 entry may have been updated since eventbus04's approval — verify alignment rather than duplicating the edit
- If governance doc still lacks expected updates after eventbus04 lands, the gap belongs to eventbus04's execution, not eventbus14

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If governance doc needs correction, defer to eventbus04's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual review: verify EVENTBUS-001 correction status | Manual inspection | EVENTBUS-001 matches documented API reference |

## Completion criteria

- EVENTBUS-001 accurately describes the current, narrower risk
- EVENTBUS-001's severity is lowered to reflect one-time-migration-only risk
- Stale Related references removed

## Out of scope

- Modifying governance doc directly (unless stale content requires correction, which should be deferred to eventbus04)
- Re-deciding the EVENTBUS-001 correction design (answered by eventbus04)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify EVENTBUS-001 status | Pending | — | — | |
| 2 | Verify EVENTBUS-001 severity and related references | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-113245_eventbus14_legacy-offset-migration-collision-risk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
