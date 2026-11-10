## Goal

Remove the `user_version` mention from `db_01` so it describes the single fingerprint gate
(`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The refusal-and-archive-and-recreate behavior is unchanged; only the mechanism description shifts
  from a `PRAGMA user_version` comparison to fingerprint matching.

## Design decisions
- Delete the EventBus `PRAGMA user_version` clause from the startup-validation sentence; keep the
  "refused file is archived and recreated" consequence.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. Line 32: delete "or a mismatched EventBus `PRAGMA user_version`" from the list of reasons a
   database is refused, leaving the fingerprint-based mismatch as the refusal basis.

### Method
- Locate the clause with
  `rg -n 'PRAGMA user_version' docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
  before editing.

### Details
- The rest of line 32 ("refused with an explicit error and never modified, archived, or deleted
  automatically; the operator archives the file and recreates it from the current canonical DDL")
  stays and now reads against the fingerprint mechanism.

## Compatibility considerations
Cross-references to `eventbus_06` and the runbook remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain db` passes; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Line 32 no longer mentions `PRAGMA user_version`; the refusal-and-archive-and-recreate behavior is
described via the fingerprint mechanism.

## Out of Scope
Changing the workflow/eventbus refusal behavior itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the user_version mention | Pending | — | — | |
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
- **Requirement ID**: `REQ-006` — remove the user_version mention
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
