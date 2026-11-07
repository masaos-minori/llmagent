## Goal

- Remove the `schema_migrations` and `workflow_schema_version` DDL, the `WORKFLOW_SCHEMA_VERSION` constant, and the `dbmig001` comments from `scripts/db/schema_sql.py` — the canonical Workflow DDL source (REQ-002: remove the marker tables and version constant from the schema layer).

## Scope
**Release unit**: current-schema-only-cutover

- DDL/constant deletion in this file only; its test coverage is the own-document row 19 (`tests/db/test_create_schema.py`, seq 19), not a companion.

## Assumptions

- `tools/check_db_separation.py` allowed-table sets stay permissive (Plan Assumptions) — this document does not touch the checker.
- Repository-wide `dbmig001` prose sweep in ADRs/docs stays with plan compatrm004 (REQ-009 boundary); this document removes only this file's comments.

## Design decisions

- No replacement version store for workflow: shape-only acceptance (sibling document 10) is the workflow gate; `PRAGMA user_version` stays EventBus-only (Plan Design).

## Alternatives considered

- Keeping `WORKFLOW_SCHEMA_VERSION` as a documentation-only constant: rejected — REQ-002 names it for removal, and leaving it invites re-introduction of version comparison.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. In the Phase 3 commit (Plan Phase 3), remove the constant and both CREATE blocks, then land the fingerprint/equivalence verification steps.

### Method
- Delete the `dbmig001` comment block (lines 23-26) and `WORKFLOW_SCHEMA_VERSION = "1.4.0"` (line 27).
- Delete the `CREATE TABLE IF NOT EXISTS workflow_schema_version (version TEXT NOT NULL, applied_at TEXT ...)` block and the `CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT, ...)` block with their `dbmig001 row 09` comments (currently lines 253-261 region onward; remove the complete statements including trailing columns).
- Search the file for any remaining ledger/baseline comment or insert text (`schema_migrations`, `dbmig001`) and remove it.

### Details
- No other table definition changes: task/attempt/lease tables keep their current DDL (REQ-006 preserves workflow operations).

## Compatibility considerations

- Databases created before this change keep their marker tables; the startup/health gates (sibling documents 07, 10) reject them as legacy until operator recreation (Plan Risks row).

## Security considerations

- N/A: DDL text deletion only.

## Rollback considerations

- Revert the commit restores the constant and DDL (single-commit change within the release unit).

## Validation plan

- `uv run pytest tests/db/test_create_schema.py` — fresh workflow database `sqlite_master` contains no marker tables (Plan Validation plan row; test rewrite is sibling document 19).
- `uv run python tools/check_db_separation.py` — clean.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- Freshly created workflow databases contain neither marker table (AC-002), and no workflow importer references `WORKFLOW_SCHEMA_VERSION` (siblings 06, 10, 18, 22, 23 complete this in the same unit).

## Out of Scope

- `scripts/eventbus/schema.sql` ledger removal — sibling document 09.
- `tests/db/test_eventbus_schema_equivalence.py` deletion — sibling document 16.
- `tools/check_db_separation.py` policy tightening — plan compatrm004.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove constant, comment block, and both marker CREATEs (Plan Phase 3) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Verify with `uv run pytest tests/db/test_create_schema.py` (rewritten by document 19) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (remove the marker tables and version constant from the canonical schema layer)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/db/schema_sql.py`
