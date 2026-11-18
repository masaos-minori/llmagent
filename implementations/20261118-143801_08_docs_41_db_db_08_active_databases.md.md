## Goal
Update the ADR-008 link text to the new title (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the `Separating SQLite into Four Databases` link text near the end of the file (scope amendment).

## Assumptions
- Procedure 02 has changed the ADR-008 title to `Separating SQLite into Six Databases`.

## Design decisions
- Only the link text changes; the link target and file name stay.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/41_db/db_08_active_databases.md`

### Procedure
1. Replace `Separating SQLite into Four Databases` with `Separating SQLite into Six Databases`.

### Method
- `rg -n "Four Databases" docs/41_db/db_08_active_databases.md` returns nothing afterwards.

### Details
- The file already inventories the active databases; no other line changes.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- The link text equals the ADR-008 title; the checkers report no finding.

## Out of Scope
- Any other line.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the link text (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/41_db/db_08_active_databases.md`
