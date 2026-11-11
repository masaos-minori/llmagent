## Goal

Replace the stamp assertions in `tests/eventbus/test_eventbus_startup.py` with fingerprint
assertions (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- Current cases assert a version stamp on create / refusal (Plan: 6 hits); eventbus now
  validates by fingerprint only.

## Design decisions
- Replace stamp assertions with fingerprint assertions: a freshly created eventbus database fingerprints clean; a drifted one is refused.

## Alternatives considered
- Deleting startup coverage: rejected; keep it expressed via fingerprint.

## Implementation
### Target file
`tests/eventbus/test_eventbus_startup.py`

### Procedure
1. Locate stamp/version assertions.
2. Replace with: create eventbus DB, assert `assert_matches(conn, canonical_ddl)` passes; mutate shape, assert refusal.

### Method
- Use the real eventbus create/open entry and canonical DDL from `db.schema_sql`/`schema.sql`.

### Details
- Remove any `PRAGMA user_version` read from assertions.

## Compatibility considerations
Test-only.

## Security considerations
None.

## Rollback considerations
Revert the commit (Phase 2 release unit).

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_startup.py -v` passes.

## Completion criteria
Stamp assertions replaced with fingerprint assertions; no `user_version` assertion remains.

## Out of Scope
New eventbus startup behaviors.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-085101 | stamp helper/tests renamed to ddl-only; assert_matches fingerprint assertions added; canonical-shape DDL-only DB now asserted accepted |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-085101 | test file IS the deliverable |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-085101 | uv run pytest tests/eventbus/test_eventbus_startup.py -> 23 passed; no user_version reference remains; full-suite gate rerun at unit end |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — eventbus startup uses fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/eventbus/test_eventbus_startup.py`