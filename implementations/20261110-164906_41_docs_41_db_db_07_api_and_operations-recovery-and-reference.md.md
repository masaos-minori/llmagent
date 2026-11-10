## Goal

Describe the fingerprint gate and the archive-and-recreate failure in `db_07` (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The DB Recreation Procedure (section 11) and the supported-baseline listing (section 11.x) already
  encode the refuse-and-recreate behavior; only the mechanism description shifts to fingerprint
  matching.
- Line 149 names the eventbus `PRAGMA user_version` stamp that this Plan removes.

## Design decisions
- Replace the eventbus `user_version` stamp reference and the marker-table language with the shared
  fingerprint gate; keep the archive-and-recreate runbook.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Section 11 (line 115): replace "carrying the legacy `schema_migrations` or `workflow_schema_version`
   tables" with "whose shape does not match the current canonical schema by the shared fingerprint".
2. Supported baseline, line 145: confirm "a legacy marker table or a shape difference fails startup"
   reads as a fingerprint mismatch.
3. Line 149: remove "`eventbus.sqlite` is stamped with `PRAGMA user_version` (the version in
   `scripts/eventbus/schema.sql`); the EventBus service refuses an unstamped or differently stamped
   database." and replace with "the EventBus service accepts `eventbus.sqlite` only when its shape
   matches the canonical DDL by the shared fingerprint; a mismatch is refused".

### Method
- Locate the clauses with
  `rg -n 'PRAGMA user_version|schema_migrations|workflow_schema_version' docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
  before editing.

### Details
- Section 12 recovery drills are unaffected; they restore from archives created under the new gate.

## Compatibility considerations
Cross-references to db_03 section 8 and the recreate runbook remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain db` passes; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Lines 115 and 149 describe the fingerprint gate and archive-and-recreate failure; the `user_version`
stamp reference is removed.

## Out of Scope
Changing the recreation procedure steps or the supported-baseline table contents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the fingerprint gate and archive-and-recreate failure | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — describe the fingerprint gate and the archive-and-recreate failure
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
