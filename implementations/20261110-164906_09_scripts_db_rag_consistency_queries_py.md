## Goal

Replace the existence-only `required_tables` check in
`scripts/db/rag_consistency_queries.py` with the fingerprint check for `rag.sqlite`
(`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current `_check_required_tables_exist()`/`_check_read_smoke_test()` verify only table names
  exist (lines ~214-236); no shape comparison.
- Canonical rag DDL comes from `db.schema_sql.build_rag_schema_sql(dims)`.

## Design decisions
- On the startup validation path, call `assert_matches(conn, canonical_ddl, label="rag.sqlite")` before returning a consistent report; a mismatch raises the archive-and-recreate error.
- Keep RAG consistency/orphan queries unchanged.

## Alternatives considered
- Inline shape comparison: rejected; reuse the one mechanism.

## Implementation
### Target file
`scripts/db/rag_consistency_queries.py`

### Procedure
1. Import `assert_matches` from `shared.schema_fingerprint` and the rag accessor from `db.schema_sql`.
2. Insert the fingerprint assertion where the current code returns success after existence/smoke checks.
3. Leave consistency queries unchanged.

### Method
- rag has no single "primary" table; detect an existing database by presence of `documents`, then fingerprint with `build_rag_schema_sql(dims)`.

### Details
- FTS5/vec shadow tables (`chunks_fts_docsize`, `chunks_vec`) are required by name only (UNK-01).

## Compatibility considerations
A matching rag database behaves the same; a mismatched one now fails startup.

## Security considerations
Read-only fingerprint.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v`; `uv run pytest tests/db -v` passes.

## Completion criteria
`scripts/db/rag_consistency_queries.py` validates `rag.sqlite` by fingerprint; existence-only is gone.

## Out of Scope
Changing RAG consistency/orphan logic.

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
- **Requirement ID**: `REQ-003` — validate rag by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/db/rag_consistency_queries.py`
