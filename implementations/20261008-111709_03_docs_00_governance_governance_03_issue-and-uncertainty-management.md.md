## Goal
Remove the resolved EVENTBUS-016 entry from the Known Issue ledger (REQ-004 of the Plan: remove resolved entry).

## Scope
- Delete the EVENTBUS-016 table row and its detail section; touch nothing else.

## Assumptions
- The fix and its tests have landed before this edit; confirm by running the new tests first.

## Design decisions
- Current-Specification-Only policy: resolved items are removed, not marked closed.

## Alternatives considered
- Keeping the entry as resolved: rejected by the ledger policy.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Confirm the production-wiring tests pass.
2. Remove the table row and the detail section for EVENTBUS-016.
3. Run the checkers.

### Method
Two targeted deletions located by the ID.

### Details
Remove the row beginning with the EVENTBUS-016 ID and the section from its heading up to (not including) the closing sentence about other Known Issue IDs. The ceiling in the structure checker is left unchanged.

## Compatibility considerations
- ADR-013 stops citing EVENTBUS-016 in procedure 04; do both in the same change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`, `check_known_deviation_sync.py`, `check_docs_structure.py`, `check_docs_quality.py`.

## Completion criteria
- No EVENTBUS-016 text remains in the ledger and the checkers pass (REQ-004).

## Out of scope
- Other entries and the structure checker ceiling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the EVENTBUS-016 row and section | Completed | 20261008-114513 | 20261008-114513 |  |
| 2 | Run the checkers | Completed | 20261008-114513 | 20261008-114513 |  |

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
- **Requirement ID**: REQ-004 (remove resolved entry)
- **Source issue**: issues/20261008-110449_ebroutes01_add-role-dependencies-to-the-eventbus-health-and-publish-routes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-111323_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-111709
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md