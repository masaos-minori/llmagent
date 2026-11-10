## Goal

Re-express the table parity check in `tests/deploy/test_required_workflow_tables_parity.py`
through the canonical DDL (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current file checks workflow table-name parity (Plan: 8 hits); the deploy gate now uses the
  fingerprint.

## Design decisions
- Replace the table-name parity assertion with a fingerprint comparison against the canonical workflow DDL.

## Alternatives considered
- Deleting the file: rejected; keep parity expressed via fingerprint.

## Implementation
### Target file
`tests/deploy/test_required_workflow_tables_parity.py`

### Procedure
1. Locate the table-name parity assertion.
2. Replace with a fingerprint call against `build_workflow_schema_sql()`.

### Method
- Build a baseline workflow DB, assert `assert_matches` passes; mutate shape, assert refusal.

## Compatibility considerations
Test-only.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/deploy/test_required_workflow_tables_parity.py -v` passes.

## Completion criteria
Parity expressed through canonical DDL fingerprint; table-name-only parity removed.

## Out of Scope
Other deploy tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` — workflow deploy parity via canonical DDL
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/deploy/test_required_workflow_tables_parity.py`
