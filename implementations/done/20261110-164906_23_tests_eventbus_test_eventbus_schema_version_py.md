## Goal

Delete the `user_version` cases in `tests/eventbus/test_eventbus_schema_version.py` and keep
or move the shape-refusal cases (`REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- Current file asserts `PRAGMA user_version` behavior (Plan: 18 hits); eventbus no longer gates
  on `user_version`.

## Design decisions
- Remove the `user_version` test functions/cases. If any case asserts shape refusal, convert it to a fingerprint drift assertion; otherwise delete.

## Alternatives considered
- Keeping a stub: rejected; no `user_version` mechanism remains.

## Implementation
### Target file
`tests/eventbus/test_eventbus_schema_version.py`

### Procedure
1. Delete every test that sets or reads `PRAGMA user_version`.
2. Convert any shape-refusal case to a fingerprint assertion against canonical DDL.
3. Rename the file's intent if the name no longer fits (leave naming if still valid).

### Method
- `rg -n "user_version" tests/eventbus/test_eventbus_schema_version.py` to locate all; remove those blocks.

### Details
- Ensure the file still imports/uses `assert_matches` if shape cases remain.

## Compatibility considerations
Test-only.

## Security considerations
None.

## Rollback considerations
Revert the commit (Phase 2 release unit).

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_schema_version.py -v` passes; no `user_version` reference remains.

## Completion criteria
No `user_version` case remains; shape refusal (if kept) uses fingerprint.

## Out of Scope
Adding new eventbus behaviors.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-084927 | all PRAGMA user_version cases deleted; old-shape/malformed/extra-table cases converted to fingerprint refusals; file name kept for history |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-084928 | test file IS the deliverable |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-084928 | uv run pytest tests/eventbus/test_eventbus_schema_version.py -> 5 passed; full-suite gate rerun at unit end |

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
- **Requirement ID**: `REQ-004` — delete eventbus `user_version` test cases
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/eventbus/test_eventbus_schema_version.py`