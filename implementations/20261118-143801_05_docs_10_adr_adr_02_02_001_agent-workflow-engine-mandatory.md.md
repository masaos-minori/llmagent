## Goal
Replace the version terminology with the schema-fingerprint terminology of ADR-008 (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the health-check list item `Whether the DB schema version matches` (terminology only).

## Assumptions
- The canonical gate compares the database shape by the shared fingerprint, not a version number (`scripts/shared/schema_fingerprint.py`; checked in Step 3a).

## Design decisions
- New wording: `Whether the DB schema matches the canonical schema (shared fingerprint)`.

## Alternatives considered
N/A: the maintainer's decisions are recorded in the Plan's Design section.

## Implementation
### Target file
`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Procedure
1. Replace the sentence in the startup-check list; change nothing else in the file.

### Method
- `rg -n -i "schema version" docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` must return nothing afterwards.

### Details
- No decision, invariant, or Blocking value changes, so no pending bullet is needed.

## Compatibility considerations
N/A: documentation or comment text only.

## Security considerations
N/A: no approval statement is written or simulated; pending bullets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` and the checkers `routing.md` Tools lists for a `docs/` edit (`uv run python tools/run_validation_gates.py` runs the ones the changed files trigger).

## Completion criteria
- The ADR no longer contains `schema version`; the checkers report no finding.

## Out of Scope
- Any other ADR-001 text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the terminology (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the ADR and documentation checkers (Validation plan) | Pending | — | — | |

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
- **Source issue**: issues/20261117-123008_adrchk008_db-data-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-142957_adrchk008_db-data-lifecycle.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-143801
- **Related target files**: `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
