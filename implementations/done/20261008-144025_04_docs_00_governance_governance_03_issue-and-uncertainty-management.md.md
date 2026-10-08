## Goal
Remove the resolved AGENT-003 entry from the Known Issue ledger (REQ-005 of the Plan).

## Scope
- Delete the AGENT-003 table row and detail section; touch nothing else.

## Assumptions
- The fix and its tests have landed before this edit.

## Design decisions
- Current-Specification-Only policy: resolved items are removed.

## Alternatives considered
- Keeping the entry as resolved: rejected by the ledger policy.

## Implementation
### Target file
docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Procedure
1. Confirm the construction-failure tests pass.
2. Remove the row and the section for the ID.
3. Run the checkers.

### Method
Two targeted deletions located by the ID; entries that list it in Related fields are checked and updated.

### Details
Remove the row beginning with the AGENT-003 ID and the section from its heading up to the next entry heading; search the ledger for other mentions in Related or Target fields and correct them.

## Compatibility considerations
- ADR-001 and ADR-004 stop citing the ID in the same change.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_issue_inventory_conformance.py`, `check_known_deviation_sync.py`, `check_docs_structure.py`, `check_docs_quality.py`.

## Completion criteria
- No AGENT-003 text remains and the checkers pass (REQ-005).

## Out of scope
- Other entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the AGENT-003 row and section | Completed | 20261008-145219 | 20261008-145219 |  |
| 2 | Run the checkers | Completed | 20261008-145219 | 20261008-145219 |  |

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
- **Requirement ID**: REQ-005 (remove the resolved entry)
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md