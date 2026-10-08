## Goal
Remove the EVENTBUS-016 deviation and notes from ADR-013 and cite the production-wiring tests as INV-01 evidence (REQ-005 of the Plan).

## Scope
- Edit the Problem, Failure Policy, Verification, and Known Deviations text only.

## Assumptions
- The route fix and tests have landed; the ledger entry is removed in the same change.

## Design decisions
- The Failure Policy states the Monitoring-role requirement without a deviation note.

## Alternatives considered
- Leave the deviation as historical text: rejected; the ADR must describe current behavior.

## Implementation
### Target file
docs/10_adr/ADR-013-eventbus-authentication-authorization.md

### Procedure
1. Remove the EVENTBUS-016 Known Deviation line.
2. Remove the parenthetical EVENTBUS-016 notes in Problem, Failure Policy, and the INV-01 Verification item; reword the Verification item to cite the production-wiring tests.
3. Run the checkers.

### Method
Unique-string edits.

### Details
Problem: drop the sentence that says health and publish are registered without a role dependency. Current State: restore the statement that each route requires role-based authentication via the role dependency. Failure Policy: "None. /health requires the Monitoring role." Verification: replace the fixture-app caveat with a reference to the production-wiring tests. Known Deviations: keep EVENTBUS-008 and EVENTBUS-015.

## Compatibility considerations
- The sync checker needs the deviation lines to match the ledger.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`; search the ADR for EVENTBUS-016 (expect none).

## Completion criteria
- No EVENTBUS-016 reference remains; INV-01 evidence cites the production-wiring tests; checkers pass (REQ-005, REQ-006).

## Out of scope
- Other ADR sections; adr-index.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the deviation and EVENTBUS-016 notes | Completed | 20261008-114513 | 20261008-114513 |  |
| 2 | Cite the production-wiring tests for INV-01 | Completed | 20261008-114513 | 20261008-114513 |  |
| 3 | Run the checkers | Completed | 20261008-114513 | 20261008-114513 |  |

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
- **Requirement ID**: REQ-005 (ADR update), REQ-006 (checks)
- **Source issue**: issues/20261008-110449_ebroutes01_add-role-dependencies-to-the-eventbus-health-and-publish-routes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-111323_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-111709
- **Related target files**: docs/10_adr/ADR-013-eventbus-authentication-authorization.md