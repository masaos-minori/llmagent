## Goal

Describe fingerprint matching as the one drift check and the recreate policy for every database in
`adr_02_05_008` (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The separation decision, per-DB responsibilities, and the `rag.sqlite`/`session.sqlite` recreate
  policy are unchanged; only the drift-check description is unified.
- The superseded `dbmig001` amendment text already states the current-only policy.

## Design decisions
- Replace the "legacy migration marker tables" phrasing with fingerprint matching as the single
  startup drift check; keep the archive-and-recreate consequence.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Context > Constraints, line 60: replace "refuses any file carrying the legacy migration marker
   tables" with "refuses any file whose shape does not match the current canonical schema by the
   shared fingerprint"; keep the archive-and-recreate consequence.
2. Amendment (dbmig001), line 75: confirm the current-only statement ("every database must match the
   current canonical schema at startup; mismatched files are archived and recreated") names the
   fingerprint as the mechanism rather than a marker-table check.

### Method
- Locate the clauses with
  `rg -n 'legacy migration marker tables|current canonical schema' docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
  before editing.

### Details
- The Recovery Category Glossary (line 79-80) already frames schema-repair as archive-and-recreate;
  it stays consistent with the fingerprint mechanism.

## Compatibility considerations
Cross-references to `db_03` section 8 and the DB Recreation Procedure remain valid.

## Security considerations
None beyond the existing safety-boundary narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`check_adr_preservation.py`, `check_adr_authority.py` pass; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Line 60 names fingerprint matching as the single drift check; line 75 states the recreate policy for
every database.

## Out of Scope
Removing the `rag.sqlite`/`session.sqlite` recreate policy or the four-DB separation decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe fingerprint matching as the one drift check | Completed | — | 20261111-145016 | line 60 marker-table phrasing replaced with shared-fingerprint refusal; line 75 amendment now names the shared fingerprint; line 137 mdq 'schema migration' phrasing replaced with create + fingerprint startup validation (only validation mechanism claims removed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-145016 | check_adr_preservation exit 0 (Decision WARNING; mapping: 3 sentences reworded to fingerprint, no other sentence changed); check_adr_authority no findings; no marker/user_version mechanism claims remain in the doc |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-145016 | documentation-only row; db_03 section 8d follow-up belongs to row 39 |

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
- **Requirement ID**: `REQ-006` — describe fingerprint matching as the one drift check and the recreate policy for every database
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`