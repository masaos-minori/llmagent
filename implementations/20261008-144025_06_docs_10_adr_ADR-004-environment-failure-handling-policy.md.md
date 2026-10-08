## Goal
Remove the AGENT-003 Known Deviation from ADR-004 (REQ-005 of the Plan).

## Scope
- Edit the Known Deviations section only.

## Assumptions
- The fix landed; the ledger entry is removed in the same change.

## Design decisions
- Keep the other deviations unchanged.

## Alternatives considered
- Leaving a historical note: rejected.

## Implementation
### Target file
docs/10_adr/ADR-004-environment-failure-handling-policy.md

### Procedure
1. Remove the AGENT-003 line from Known Deviations, keeping the other lines.
2. Run the checkers.

### Method
A single-line removal.

### Details
The remaining Known Deviation lines are untouched.

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
- Other sections.

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
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md