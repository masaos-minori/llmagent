## Goal

Replace `CREATE TABLE IF NOT EXISTS` plus `PRAGMA user_version` stamping in
`scripts/shared/mcp_dedup.py` with create-when-absent and fingerprint validation
(`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current open path runs `CREATE TABLE IF NOT EXISTS` and stamps `PRAGMA user_version = 1` on
  every open (lines 48-62, 243-245); an old-shape table passes silently (Plan Background).
- Canonical mcp_dedup DDL is held in module constants here; pass it as the fingerprint input.

## Design decisions
- On open: if the dedup table is absent, create it (create-when-absent); if present, call the generalized `assert_matches(conn, canonical_ddl, label="mcp_dedup.sqlite")` and refuse drift unchanged.
- Remove the `PRAGMA user_version = 1` stamping and the `user_version` check.

## Alternatives considered
- Keeping the stamp as a gate: rejected as a second mechanism (REQ-004).

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
1. Remove `PRAGMA user_version = 1` stamping from the create path (lines 48-62).
2. In the open path, when the table exists, load the canonical DDL (module constant) and call `assert_matches(...)`; raise the archive-and-recreate error on mismatch.
3. Remove any `user_version` read/gate (lines 243-245).

### Method
- Build the canonical DDL string from the existing module constant(s) that define the dedup table; pass it to `assert_matches`. Do not add a new DDL source.

### Details
- The named exception `scripts/shared/execution_snapshot.py` still reads the file-header `user_version` for observability; leave it (AC-04).

## Compatibility considerations
Existing mcp_dedup databases keep their stamp harmlessly; a mismatched-shape database is now refused instead of accepted.

## Security considerations
Read-only fingerprint on open; refusal leaves data intact.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/shared/test_mcp_dedup.py -v` (that row replaces stamp expectations with fingerprint refusal cases); `uv run pytest tests/shared -v` passes.

## Completion criteria
`scripts/shared/mcp_dedup.py` creates when absent and fingerprints when present; no `user_version` stamp/check remains.

## Out of Scope
Changing the dedup business schema.

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
- **Requirement ID**: `REQ-003` / `REQ-004` — mcp_dedup validated by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/shared/mcp_dedup.py`
