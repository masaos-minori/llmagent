# Implementation Procedure — docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

## Goal

Align the mdq runbook rows with the mdq-specific sidecar handling, re-index verification, and
failure rollback, and cross-reference the recreation procedure that owns them (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-005. Acceptance criterion: AC-5.

## Assumptions
- Lightweight fill: the change is prose in two table rows, with no code, persistence, or security
  impact.
- Cross-plan overlap: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md` also targets
  this file. Compatible ordering overlap — this plan owns the runbook rows, and 006 adds the FTS5
  identity statement; this plan executes first per the dependency bullets.
- Runbook ownership: this file keeps the per-store table and cross-references db_07 section 11,
  which owns the procedure steps (the Plan's Design section).

## Design decisions
- The mdq rows name the three missing steps rather than restating the procedure: sidecar
  quarantine before deletion, verification that the recreated store matches the canonical shape,
  and rollback by restoring the archived file.
- The recovery path stays archive-and-recreate: no migration or in-place repair wording is added,
  per ADR-008 Decision Detail 22.

## Alternatives considered
- Write the full mdq procedure in this file: rejected, because section 11 of db_07 owns the
  procedure and duplicating it would create two sources of truth.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
- Extend the mdq row of the accepted-schema table at line 74: archive the file, quarantine its
  `-wal`/`-shm` sidecars, then re-index.
- Extend the mdq row of the recreation-impact table at line 84 with the verification step and the
  rollback step.

### Method
- Both rows keep their existing cross-reference to db_07 section 11, so the procedure steps are
  stated once.

### Details
- Re-index verification for mdq means the recreated store is accepted by the fingerprint gate and
  the re-indexed row counts match the Markdown sources; failure rollback restores the archived file
  and re-runs the re-index.

## Compatibility considerations
- The reference table entries for this file are generated; the row wording must keep the anchors
  that `generate_reference_table.py` reads.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- The mdq rows state sidecar handling, re-index verification, and failure rollback, and the
  scratch-database recreation run per `rules/persisted-schema-change.md` passes against the new
  shape (AC-5).

## Out of Scope
- The procedure steps themselves (seq 20); the canonical DDL (seq 01).

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
- **Requirement ID**: REQ-005 (mdq runbook alignment)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
