## Goal

Update the identity tests for the bumped version stamp and prove that a store created at version 1 is refused as `schema_mismatch` while a fresh store initializes at the new version.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: this file only. Verified pin: `assert _user_version(path) == 1` (about line 117); the legacy fixture at version 0 stays valid.

## Assumptions

- Verified: `_STORE_TABLES` lists tables only and stays valid; `test_drifted_ledger_shape_raises_typed_store_error` already covers column drift.

## Design decisions

- Compare the stamp with `mcp_dedup._USER_VERSION` rather than a literal 1; add one test that stamps a healthy store back to version 1 and expects `schema_mismatch`.

## Alternatives considered

N/A: minimal edit.

## Implementation
### Target file
`tests/shared/test_mcp_dedup_identity.py`

### Procedure
1. Replace the literal 1 in the fresh-store assertion with `mcp_dedup._USER_VERSION` and update the module docstring sentence about the stamp.
2. Add a test: create a healthy store, set `PRAGMA user_version = 1`, reopen, and assert `DedupStoreError` with state `schema_mismatch`.
3. Add a test that a pre-change shaped store (without the five columns, at version 1) is refused as `schema_mismatch` or `legacy_or_unverified` per the existing classifier, matching what the code reports.

### Method
Reuse `_make_healthy`, `_user_version`, and `_store_error()` helpers.

### Details
- Do not weaken any existing refusal test.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup_identity.py`

## Completion criteria

- The fresh-store version assertion tracks `_USER_VERSION`; a version-1 store is refused as `schema_mismatch`.

## Out of Scope

Ledger metadata tests (row 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/shared/test_mcp_dedup_identity.py`
