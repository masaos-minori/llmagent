## Goal

Replace the eventbus `user_version` cases in `tests/db/test_create_schema.py` with fingerprint
cases (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current cases assert a `PRAGMA user_version` mismatch is refused (Plan: 50 hits); eventbus no
  longer gates on `user_version`.

## Design decisions
- Replace the eventbus `user_version` assertion with a fingerprint drift assertion (e.g. drop a column or add an extra table) expecting the archive-and-recreate error.

## Alternatives considered
- Deleting the eventbus case: rejected; keep coverage expressed through the fingerprint mechanism.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Find the eventbus `user_version` case(s); replace the `PRAGMA user_version` mutation with a shape drift.
2. Update assertions to expect the fingerprint refusal message.

### Method
- Mutate the created eventbus database shape (extra table/column) before re-opening via `create_schema`; assert refusal.

### Details
- Leave non-eventbus cases untouched.

## Compatibility considerations
Test-only; mirrors the `create_schema.py` / `schema.py` changes.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` passes.

## Completion criteria
No `user_version` assertion remains for eventbus in this file; drift is covered by fingerprint cases.

## Out of Scope
Other databases' cases here.

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
- **Requirement ID**: `REQ-003` / `REQ-004` — eventbus cases use fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/db/test_create_schema.py`
