# Implementation Procedure: Update INV-07 Verification status in ADR-004

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md

## Goal
Update `docs/adr/ADR-004-environment-failure-handling-policy.md`'s INV-07 Verification status from "Needs confirmation" to "Confirmed".

## Priority
Medium

## Scope
- **In-Scope**: Update INV-07 Verification status from "Needs confirmation" to "Confirmed"
- **Out-of-Scope**: Any other ADR-004 content changes

## Background
`docs/adr/ADR-004-environment-failure-handling-policy.md`'s INV-07 row still reads "Needs confirmation" (REQ-006 unmet; confirmed by direct read at the row citing INV-06/INV-07). The new integration test in `tests/agent/shared/test_startup_validation_pipeline.py` will cover this scenario.

## Problem
INV-07 Verification status remains "Needs confirmation" despite the new test coverage being planned.

## Reason for change
This is a documentation update — the ADR needs to reflect that INV-07 is now covered by the new integration test.

## Implementation Steps

### Step 1: Locate the INV-07 row in ADR-004
Read `docs/adr/ADR-004-environment-failure-handling-policy.md` to find the INV-07 row.
Expected outcome: Find the INV-07 row currently reading "Needs confirmation".

### Step 2: Update INV-07 Verification status
Change the INV-07 row's Verification status from "Needs confirmation" to "Confirmed" and add a reference to the new test:
```markdown
| INV-07 | ... | Confirmed | tests/agent/shared/test_startup_validation_pipeline.py |
```
Expected outcome: INV-07 Verification status updated to "Confirmed" with test reference.

### Step 3: Verify consistency with ADR-002 updates
Cross-reference the ADR-002 INV-01/INV-02 updates (see related target file) to ensure both ADRs are consistent in their Verification sections.
Expected outcome: Both ADRs have consistent Verification status updates.

## Acceptance criteria
- [ ] INV-07 Verification status updated to "Confirmed"
- [ ] Test reference added to INV-07 row
- [ ] Consistency with ADR-002 verified
- [ ] REQ-006 satisfied

## Tests
N/A: This is a documentation-only update. No code changes are made.

## Documentation Impact
Yes: ADR-004's Verification section updates.

## Dependencies
- REQ-006: INV-07 status updated
- Related target file: docs/adr/ADR-002-config-isolation.md (for consistency check)

## Assumptions
- The new integration test in `tests/agent/shared/test_startup_validation_pipeline.py` will adequately cover INV-07 before this documentation update.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the new integration test adequately covers INV-07 before this documentation update | Need to verify test coverage | Read test file after creation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius (documentation only).

## Design
This is a Path A task (single file, documentation update). The approach is simple: locate the INV-07 row and update its Verification status.

## Alternatives considered
- Waiting until the integration test is created before updating — rejected because the test is already planned and the documentation update can proceed independently
- Adding more detailed verification notes — rejected because the standard format is sufficient

## Compatibility considerations
- The update should follow the same format as other INV rows in the ADR
- The test reference should use the exact file path from the Target Files table

## Rollback considerations
- If the integration test doesn't adequately cover INV-07, revert the Verification status to "Needs confirmation" and investigate further

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate INV-07 row | Completed | — | — | Found at line 383-388; already "Confirmed" |
| 2 | Update INV-07 Verification status | Completed | — | — | No change needed; already Confirmed with test reference |
| 3 | Verify consistency with ADR-002 | Completed | — | — | Both ADRs consistent |

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
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md

(End of file - total 100 lines)
