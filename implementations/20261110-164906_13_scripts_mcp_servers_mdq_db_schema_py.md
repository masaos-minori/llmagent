## Goal

Validate an existing `mdq.sqlite` by fingerprint and refuse a mismatch with the
archive-and-recreate message in `scripts/mcp_servers/mdq/db_schema.py` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current code only runs `CREATE TABLE IF NOT EXISTS` on open (lines 23-99); health checks
  table existence only (`health_check.py:65-67`, a Reference File, not modified here).
- Canonical mdq DDL is held in module constants here.

## Design decisions
- On open of an existing mdq database, call the generalized `assert_matches(conn, canonical_ddl, label="mdq.sqlite")`; on mismatch raise the archive-and-recreate error.
- Keep create-when-absent for a fresh database.

## Alternatives considered
- Extending the existence check inline: rejected; reuse the one mechanism.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_schema.py`

### Procedure
1. Import `assert_matches` from `shared.schema_fingerprint`.
2. In the open/create path, when the mdq tables already exist, fingerprint with the canonical mdq DDL (module constant) and refuse drift.
3. Add the archive-and-recreate refusal message on mismatch.

### Method
- Detect "existing" by presence of the mdq table, then assert the fingerprint; leave the health-check existence path (`health_check.py`) untouched.

### Details
- Ensure the canonical DDL passed matches exactly what `CREATE TABLE IF NOT EXISTS` would create so a freshly-created database fingerprints clean.

## Compatibility considerations
A matching mdq database behaves the same; a mismatched one now fails startup.

## Security considerations
Read-only fingerprint.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/mcp_servers/mdq -v`; the boundary test's allowed-import entry moves to the new module name (its row); `uv run pytest tests/mcp_servers/mdq -v` passes.

## Completion criteria
`scripts/mcp_servers/mdq/db_schema.py` validates existing mdq.sqlite by fingerprint and refuses drift.

## Out of Scope
Changing the mdq business schema or the health-check file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-135256 | mdq DDL consolidated into _CREATE_STATEMENTS (single source); create-when-absent else assert_matches(label='mdq.sqlite'); refusal is the shared archive-and-recreate message |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-135256 | TestFingerprintGate added (columns drift / missing table / extra table / rows intact / clean pass); tests/mcp_servers/mdq 416 passed, full suite 12067 passed (uv run), pre-commit green |

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
- **Requirement ID**: `REQ-003` — validate mdq by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`