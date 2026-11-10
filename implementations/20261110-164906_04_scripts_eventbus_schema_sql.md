## Goal

Remove the `PRAGMA user_version = 6` stamp and its comment from `scripts/eventbus/schema.sql`
(`REQ-004`). The DDL objects themselves are unchanged.

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- Persisted-schema change policy (`rules/persisted-schema-change.md`) applies; the DDL
  objects are unchanged, only the stamp line is removed.
- Existing eventbus databases keep their stamp harmlessly; the fingerprint ignores `user_version` (Plan Assumptions).

## Design decisions
- Delete only the `PRAGMA user_version = 6;` line and the preceding comment block describing the stamp. No other DDL changes.

## Alternatives considered
- Bumping the stamp instead of removing: rejected; there is no schema change and no version gate remains (REQ-004).

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Delete the comment block from `-- Schema version of this DDL...` through the `PRAGMA user_version = 6;` line (lines 61-65).
2. Leave all `CREATE`/`INDEX`/trigger statements untouched.

### Method
- Edit the file to remove exactly the stamp and its comment; verify no other `PRAGMA user_version` remains in the file.

### Details
- After removal, confirm the eventbus schema still applies cleanly to an in-memory database (the fingerprint builds from the DDL without needing a stamp).

## Compatibility considerations
No DDL object changes; only the file-header stamp is gone.

## Security considerations
None.

## Rollback considerations
Revert the commit (Phase 2 release unit).

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_startup.py -v` passes; the persisted-schema checklist in `rules/persisted-schema-change.md` is satisfied.

## Completion criteria
`scripts/eventbus/schema.sql` contains no `PRAGMA user_version` and all DDL objects are intact.

## Out of Scope
Changing any DDL object.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — remove the `PRAGMA user_version` stamp from `schema.sql`
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/eventbus/schema.sql`
