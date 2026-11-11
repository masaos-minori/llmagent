## Goal

Align `db_02`'s workflow validation statement to the single fingerprint mechanism (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The workflow create path and CHECK-constraint descriptions are unchanged; only the startup
  validation description shifts from marker-table rejection to fingerprint matching.
- Line 46 is the validation statement that names the legacy marker-table rejection.

## Design decisions
- Replace "no legacy migration markers" / "rejects `schema_migrations` or `workflow_schema_version`
  outright" with fingerprint matching as the single drift check; keep the archive-and-recreate
  consequence.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. Section 7 (line 46): replace "accepts only databases that carry the current required tables and
   columns and no legacy migration markers, and the deploy pre-flight rejects `schema_migrations` or
   `workflow_schema_version` outright" with "accepts only databases whose shape matches the current
   canonical schema by the shared fingerprint; a mismatch is refused". Keep the following sentence
   that such a database must be archived and recreated by the operator.

### Method
- Locate the clause with
  `rg -n 'legacy migration markers|schema_migrations|workflow_schema_version' docs/41_db/db_02_architecture_and_schema-schema-reference.md`
  before editing.

### Details
- The CHECK-constraint descriptions above line 46 are unaffected by the fingerprint cutover.

## Compatibility considerations
Cross-references to [db_07 section 11](db_07_api_and_operations-recovery-and-reference.md#11-db-recreation-procedure) remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain db` passes; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Line 46 describes fingerprint matching as the single drift check; the archive-and-recreate
consequence remains.

## Out of Scope
Changing the workflow create path or CHECK constraints.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align the workflow validation statement to fingerprint matching | Completed | — | 20261111-145201 | section 7 validation sentence replaced with shared-fingerprint shape matching; archive-and-recreate consequence kept; CHECK-constraint descriptions untouched |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-145201 | check_docs_consistency --domain db: No issues found; no schema_migrations/workflow_schema_version/marker claims remain in db_02 |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-145201 | documentation-only row |

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
- **Requirement ID**: `REQ-006` — align the workflow validation statement to fingerprint matching
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/41_db/db_02_architecture_and_schema-schema-reference.md`