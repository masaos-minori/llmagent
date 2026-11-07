## Goal

- Replace the ledger/baseline/version expectations in `tests/db/test_create_schema.py` with marker-absence and rejection expectations for fresh 4-database creation (REQ-007 / AC-002: fresh databases carry no marker tables and no baseline rows).

## Scope
**Release unit**: current-schema-only-cutover

- Test-module rework in Phase 1 (RED first); production counterpart is sibling document 06. Own document: the Plan cites this test path in two rows' Related Tests cells (rows 6 and 8).

## Assumptions

- Fail-closed rejection cases already in the module stay; only migration-era assertions change (Plan row evidence cites lines 418, 685-746 region assertions).

## Design decisions

- Rewrite in place (MODIFY row): the module covers all four databases' creation paths, which remain in scope after the cutover.

## Alternatives considered

- Splitting the module: rejected — out of scope for this Plan (no restructuring row).

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Rewrite the expectations (below) in the Phase 1 commit and confirm RED against current `create_schema.py` behavior (Plan Phase 1).
2. After document 06 lands (Phase 2), confirm green.

### Method
- Remove/replace the fixture DDL that creates `workflow_schema_version` (line 418 region) and the assertions `_recorded_versions(db_file) == [WORKFLOW_SCHEMA_VERSION]` and version-mutation cases (lines 685-746 region, incl. `UPDATE workflow_schema_version SET version = '0.0.1'` and the `schema_migrations` presence/id assertions at lines 744-746).
- Remove `from db.schema_sql import WORKFLOW_SCHEMA_VERSION` usages (lines 696, 703, 738) — the constant is deleted by document 08.
- New assertions (new): after creation, `sqlite_master` of fresh workflow and eventbus databases contains neither `schema_migrations` nor `workflow_schema_version`, and no version/ledger row exists; the existing fail-closed fingerprint/version-mismatch refusal cases stay aligned with document 06's preserved behavior.

### Details
- Keep every non-migration creation test byte-identical (rag/session paths unchanged).

## Compatibility considerations

- N/A: test-only change until document 06 lands; RED window is planned (release unit).

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py` — RED in Phase 1, green after document 06 (Plan Validation plan row: no marker tables, no baseline rows, fail-closed paths intact).
- `uv run python tools/check_db_separation.py` — clean (Phase 5).

## Completion criteria

- Fresh 4-DB creation tests prove marker-table absence and preserved refusal behavior (AC-002, AC-006).

## Out of Scope

- `create_schema.py` implementation — sibling document 06.
- `schema_sql.py` DDL — sibling document 08.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace ledger/baseline assertions with marker-absence and rejection assertions (Plan Phase 1) | Pending | — | — | Release unit "current-schema-only-cutover": intentionally RED until document 06 |
| 2 | Confirm green after document 06 lands | Pending | — | — | |
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
- **Requirement ID**: REQ-007 (replace migration-era test expectations), REQ-002 (marker-free fresh databases it asserts)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `tests/db/test_create_schema.py`
