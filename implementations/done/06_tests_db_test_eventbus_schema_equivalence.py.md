## Goal
Remove the test that asserts an existing database is migrated, fix the migration wording, and add a test that an existing current database is left unchanged (REQ-005).

## Scope
- Edit `tests/db/test_eventbus_schema_equivalence.py` only; keep the DDL-reader test and the fresh-bootstrap equivalence test.

## Assumptions
- `open_db()` runs `_init_schema()`, which after the change returns early when `events` exists (see the `scripts/eventbus/schema.py` procedure).
- `schema.sql` creates the three tables and the indexes; an existing database created from it must be unchanged after `open_db()`.

## Design decisions
- Replace the migration assertion with an "unchanged on restart" assertion: schema listing and a stored row are identical before and after a second `open_db()`.

## Alternatives considered
N/A: contract change; no alternative keeps the migration test valid.

## Implementation
### Target file
`tests/db/test_eventbus_schema_equivalence.py`

### Procedure
1. Delete `test_existing_database_without_consumer_delivery_index_is_migrated`.
2. Fix the module docstring (remove "and an existing database must be migrated to it") and the comment in `test_bootstrap_paths_produce_same_schema` that says start-up "applies _migrate()" (it now leaves an existing database unchanged).
3. Add a test: create a database through `open_db`, insert one event row, record `_schema(conn)`, reopen with `open_db` on the same path, assert the schema listing and the row are unchanged.

### Method
- Reuse the module's `_schema` helper and `open_db`; use `tmp_path`.
- Insert a row with the minimum columns required by `schema.sql` (read the DDL first to supply NOT NULL columns).

### Details
- The test must not depend on SQLite version-specific behavior.

## Compatibility considerations
N/A: test-only.

## Security considerations
N/A: temporary files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_eventbus_schema_equivalence.py -q`; `uv run ruff check` on the file.

## Completion criteria
- No test or comment mentions migration of an existing database; the new unchanged-on-restart test passes.

## Out of Scope
- Other tests and `schema.sql`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the migrated-index test and fix the wording | Done | 20261022-101015 | 20261022-101015 | Deleted `test_existing_database_without_consumer_delivery_index_is_migrated`; fixed module docstring and the `_migrate()` comment. |
| 2 | Add the unchanged-on-restart test | Done | 20261022-101015 | 20261022-101015 | Added `test_existing_database_is_unchanged_on_restart`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261022-101015 | 20261022-101015 | 3 passed; ruff clean. |

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
- **Requirement ID**: `REQ-005` (remove migration assertions, keep equivalence tests)
- **Source issue**: `issues/20261021-102130_rmebmig_remove-the-eventbus.sqlite-schema-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093935_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101015
- **Related target files**: tests/db/test_eventbus_schema_equivalence.py
