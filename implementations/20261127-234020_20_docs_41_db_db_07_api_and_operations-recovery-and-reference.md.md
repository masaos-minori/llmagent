# Implementation Procedure — docs/41_db/db_07_api_and_operations-recovery-and-reference.md

## Goal

Add the mdq steps to the recreation procedure: sidecar quarantine, re-index verification, and
failure rollback for the delete-and-recreate path (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-005. Acceptance criterion: AC-5.

## Assumptions
- Lightweight fill: the change is prose in one section, with no code, persistence, or security
  impact.
- No cross-plan overlap: this file is targeted by this Plan only.
- Section 11 owns the recreation procedure, so the mdq steps are written here and db_03's mdq rows
  cross-reference them (the Plan's Design section, runbook ownership).

## Design decisions
- The mdq steps follow the shape of the existing notes: quarantine before deletion, verify the
  recreated store, and roll back by restoring the archive — the same three steps the workflow note
  at line 125 already models.
- mdq is not covered by `rotate_all_dbs()`, so the archive step for mdq names the operator archive
  of the refused file rather than the rotation function.

## Alternatives considered
- State the mdq steps only in db_03's table: rejected, because section 11 is the procedure the
  operator follows and mdq appears there only in the read-only inspection subsection.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
- Extend the notes list that begins at line 120 with an mdq note covering the three steps.
- In the step paragraph at line 118, state that mdq's delete step includes its `-wal`/`-shm`
  sidecars, which are quarantined before the file is removed.

### Method
- The note is added to the existing list rather than as a new subsection, so the section's anchor
  and the reference table entries stay unchanged.

### Details
- Re-index verification for mdq means the recreated store is accepted by the fingerprint gate at
  `create_production_tables` and the re-indexed counts match the Markdown sources; failure rollback
  restores the archived file and re-runs the re-index.

## Compatibility considerations
- The reference table reads this section's anchors; adding a bullet does not change them.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- Section 11 states the mdq sidecar quarantine, re-index verification, and failure rollback, and
  the scratch-database recreation run per `rules/persisted-schema-change.md` passes (AC-5).

## Out of Scope
- The per-store table rows in db_03 (seq 19); the canonical DDL (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Documentation gates: `check_docs_content_policy.py` and `generate_reference_table.py --check` |

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
- **Requirement ID**: REQ-005 (mdq steps in the recreation procedure)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
