## Goal

Cover the generalized gate in `tests/deploy/test_init_db_schema_gate.py` and drop the
marker-table cases (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- Current cases include marker-table findings (Plan: 8 hits); the deploy gate now fingerprints.

## Design decisions
- Replace marker-table cases with fingerprint-drift cases for the domains the gate covers.

## Alternatives considered
- Deleting the file: rejected; keep deploy-gate coverage via fingerprint.

## Implementation
### Target file
`tests/deploy/test_init_db_schema_gate.py`

### Procedure
1. Delete marker-table finding cases.
2. Add fingerprint-drift cases: a drifted database is refused by the init_db gate with the archive-and-recreate error.

### Method
- Exercise the deploy gate entry point against a baseline and a mutated DB.

## Compatibility considerations
Test-only.

## Security considerations
None.

## Rollback considerations
Revert the commit (Phase 2 release unit).

## Validation plan
`uv run pytest tests/deploy/test_init_db_schema_gate.py -v` passes.

## Completion criteria
Marker-table cases dropped; gate covered by fingerprint cases.

## Out of Scope
Other deploy tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-091908 | rewritten as fingerprint-gate suite (7 tests pass); marker cases kept as unexpected-table regressions; eventbus delegation pinned; rag/session fixtures canonical+healthy-seeded; prerequisite fix: recovery_drill threads DbConfig.sqlite_vec_so into consistency helpers |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — init_db gate covered by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/deploy/test_init_db_schema_gate.py`