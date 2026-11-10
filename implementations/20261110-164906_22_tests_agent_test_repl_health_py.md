## Goal

Replace the table-list and marker-table cases in `tests/agent/test_repl_health.py` with
fingerprint cases (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current cases assert table-list membership and marker-table refusal (Plan: 30 hits); the
  workflow gate now validates by fingerprint.

## Design decisions
- Replace the table-list case with a fingerprint drift case (drop a column / add a legacy table) expecting the archive-and-recreate error; replace the marker-table case with the same fingerprint assertion.

## Alternatives considered
- Deleting these cases: rejected; keep coverage via fingerprint.

## Implementation
### Target file
`tests/agent/test_repl_health.py`

### Procedure
1. Locate the table-list and marker-table cases.
2. Replace each with a workflow-shape drift mutation and an archive-and-recreate assertion.

### Method
- Build a baseline workflow DB, mutate its shape, call the health/repl check, assert refusal.

### Details
- Leave non-schema health checks untouched.

## Compatibility considerations
Test-only.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/agent/test_repl_health.py -v` passes.

## Completion criteria
No table-list/marker-table schema case remains; drift covered by fingerprint cases.

## Out of Scope
Non-schema health assertions.

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
- **Requirement ID**: `REQ-003` / `REQ-004` — workflow health uses fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/agent/test_repl_health.py`
