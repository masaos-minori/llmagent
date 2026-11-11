## Goal

Describe one validation mechanism (fingerprint matching) in `db_03` instead of the coexisting
`user_version` / marker-table / existence mechanisms (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Each database accepts the current shape only; older or marker-carrying databases are refused and
  archived-and-recreated, not migrated.
- Lines 43-52 describe the per-domain startup validation that currently mixes marker-table checks
  (workflow) and `PRAGMA user_version` + fingerprint (eventbus).

## Design decisions
- Replace the workflow marker-table refusal and the eventbus `user_version` gate with a single
  fingerprint comparison; keep the archive-and-recreate runbook references.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Section 8b, line 49: remove "`.sql` ends with `PRAGMA user_version = 6;`: new databases receive
   that stamp from the canonical DDL itself."
2. Line 51: replace "accepted only when `PRAGMA user_version` equals the version stamped by the
   canonical DDL and its tables, columns, and indexes match the `shared/eventbus_schema_fingerprint.py`
   fingerprint" with "accepted only when its shape matches the canonical DDL by the shared
   fingerprint".
3. Line 52: delete the "unstamped existing database (`user_version 0`) is refused" bullet; a shape
   mismatch is refused by the fingerprint regardless of any file-header field.
4. Line 69: confirm the current-only statement names the fingerprint as the mechanism.

### Method
- Locate the clauses with
  `rg -n 'PRAGMA user_version|eventbus_schema_fingerprint|user_version 0' docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
  before editing.

### Details
- The workflow section 8a (line 45) marker-table refusal is aligned by its own row; here keep the
  unified statement consistent across both domains.

## Compatibility considerations
Cross-references to the section 8 runbook and db_07 section 11 remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain db` passes; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Lines 49-52 describe fingerprint matching as the single drift check; the `user_version` gate and
stamp language are removed.

## Out of Scope
Adding a migration mechanism or changing the recreate policy.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe one validation mechanism | Completed | — | 20261111-145400 | 8a rewritten to shared-fingerprint gate (check_workflow_schema + init_db.sh); 8b user_version stamp sentence, user_version acceptance bullet, and unstamped-0 bullet removed, fingerprint acceptance kept; 8d adds fingerprint acceptance for existing mdq.sqlite; 8e and the accepted-schema table rows now name the shared fingerprint for all five domains |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-145400 | check_docs_consistency --domain db: No issues found; rg user_version/marker/eventbus_schema_fingerprint in db_03 returns no matches |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-145400 | documentation-only row; adr_008 mdq cross-reference aligned in row 36 |

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
- **Requirement ID**: `REQ-006` — describe one validation mechanism
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`