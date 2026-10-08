## Goal
Remove the AGENT-003 Known Deviation from ADR-001 and keep the rest of the ADR consistent with the fixed behavior (REQ-005 of the Plan).

## Scope
- Edit the Known Deviations section; check the Implementation Notes for any statement that the fallback exists.

## Assumptions
- The fix landed; the ledger entry is removed in the same change.

## Design decisions
- The ADR already states that the load failure aborts startup; only the deviation line is stale.

## Alternatives considered
- Leaving a historical note: rejected; the ADR describes current behavior.

## Implementation
### Target file
docs/10_adr/ADR-001-workflow-engine-mandatory.md

### Procedure
1. Remove the AGENT-003 line from Known Deviations and replace it with "No confirmed deviations." if it was the only entry.
2. Search the ADR for statements about a fallback in the constructor and correct them.
3. Run the checkers.

### Method
Unique-text edits.

### Details
Known Deviations: if no other entry remains, the section reads that there are no confirmed deviations, followed by the existing sentence about not aligning the ADR to the implementation.

## Compatibility considerations
- The sync checker needs the ledger and ADR to agree.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`.

## Completion criteria
- No AGENT-003 reference remains in the ADR (REQ-005).

## Out of scope
- Decision text and other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the deviation | Completed | 20261008-145219 | 20261008-145219 |  |
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
- **Requirement ID**: REQ-005 (remove the deviation)
- **Source issue**: issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-143632_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-144025
- **Related target files**: docs/10_adr/ADR-001-workflow-engine-mandatory.md