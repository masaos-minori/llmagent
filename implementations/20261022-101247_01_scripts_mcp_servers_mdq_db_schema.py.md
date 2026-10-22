## Goal
Remove the destructive legacy-`chunks` detection and rebuild from `create_production_tables()` so it is create-only (REQ-001: remove the function and its call; tables, triggers, and index state unchanged).

## Scope
- Delete `_migrate_legacy_chunks_schema()` and its call; update the `create_production_tables()` docstring.
- No change to any `_create_*` helper, the pragma call, error handling, or the health check.

## Assumptions
- The branch only runs when the first `chunks` column is `id` and drops `chunks`, `chunks_fts`, and the three sync triggers; every remaining statement is `IF NOT EXISTS`, so behavior for a current-shape or empty database is unchanged (verified in the module).
- `create_production_tables()` has one production caller, `MdqService._init_db()` (verified).
- After removal a legacy-shape store is not rebuilt and is not detected by the health check (accepted limit, Plan UNK-01).

## Design decisions
- Delete the function and the call together; keep `logger` (still used by the error path).
- The new docstring says the function creates the production tables.

## Alternatives considered
- Replacing the rebuild with a detection that raises: rejected, the Issue forbids a replacement detection.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_schema.py`

### Procedure
1. Delete `_migrate_legacy_chunks_schema()`.
2. Remove its call at the start of the `try` block in `create_production_tables()`.
3. Change the docstring "Create production tables and migrate from legacy schema if needed." to "Create the production tables."

### Method
- Delete by symbol; the `logging` and `sqlite3` imports stay in use (error handling and type hints).

### Details
- Do not reorder the remaining create calls.

## Compatibility considerations
No behavior change for a database at the current shape. A store with the old first column `id` is no longer rebuilt; recovery is deleting the file and re-indexing (documented in `db_08_active_databases.md`).

## Security considerations
N/A: removes an unconditional `DROP` path on the startup path.

## Rollback considerations
Revert the commit; no data is changed by this edit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_schema.py tests/mcp_servers/mdq/test_index_delete.py tests/mcp_servers/mdq/test_mdq_rag_boundary.py -q`, then the full suite once.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- Deploy: read the first column of `chunks` in the deployed `mdq.sqlite` read-only and confirm `chunk_id` before deploying.

## Completion criteria
- `rg "_migrate_legacy_chunks_schema|old chunks schema" scripts` returns no match.
- Tables, triggers, and index state are created exactly as before on an empty path and on a current-shape database.

## Out of Scope
- Health check semantics, schema content, and re-indexing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the function and its call; fix the docstring | Pending | — | — | |
| 2 | Tests are covered by the test-file procedure | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Deploy step: read-only first-column check on `/opt/llm` `mdq.sqlite`, deploy, verify MDQ health | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (remove the legacy detection and rebuild)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: scripts/mcp_servers/mdq/db_schema.py
