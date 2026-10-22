## Goal
Remove the legacy-shape tests and keep the current-shape re-run test under a correct name (REQ-003).

## Scope
- Delete the legacy helper and the three tests of rebuild, data loss, and detection log; rename and keep `test_new_schema_is_not_treated_as_legacy`; update the module docstring.
- Fresh-creation, idempotence, directory-creation, and error-handling tests stay unchanged.

## Assumptions
- `test_new_schema_is_not_treated_as_legacy` inserts a document and a chunk, re-runs `create_production_tables()`, and asserts the row survives; it stays valid after the change (verified in the test).
- `logging` stays imported because the error-handling tests use `caplog` at ERROR level (verify before removing any import).

## Design decisions
- Rename the kept test to describe its behavior ("rerun on a current-shape database preserves data") and move it into the fresh-DB class or its own small class.

## Alternatives considered
N/A: removal and rename fixed by the Plan.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_db_schema.py`

### Procedure
1. Delete `_make_legacy_db`, `test_rebuilds_chunks_table_with_chunk_id_primary_key`, `test_legacy_data_is_dropped_on_rebuild`, and `test_logs_info_message_on_legacy_schema_detection`.
2. Rename the class holding the kept test (drop "LegacySchemaMigration") and the test, fixing docstrings.
3. Remove the "legacy schema detection/rebuild branch" bullet from the module docstring.
4. Remove imports left unused after the deletions.

### Method
- Delete by symbol; run `ruff` for unused imports.

### Details
- Do not change `_table_names`, `_trigger_names`, or `TestErrorHandling`.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: test-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_schema.py -q`; `uv run ruff check` on the file.

## Completion criteria
- No test seeds an old `chunks` shape or asserts the detection log; the kept re-run test passes.

## Out of Scope
- Other MDQ tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the legacy tests and helper; rename the kept test | Pending | — | — | |
| 2 | Run the file's tests | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (remove legacy-shape tests, keep current-shape re-run test)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: tests/mcp_servers/mdq/test_db_schema.py
