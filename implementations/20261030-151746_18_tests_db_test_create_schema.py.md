## Goal

Extend `tests/db/test_create_schema.py` for ledger creation, baseline stamping, and fingerprints of migrated schemas (`REQ-001`, baseline; `REQ-006`, ledger).

## Scope

- Modify only `tests/db/test_create_schema.py`.

## Assumptions

- Verified (Step 3a): the file is large (about 60 KB, workflow tests plus the eventbus stamp and fingerprint classes near `:998-1280`); it reads the eventbus stamp through `eventbus_schema_version()`, so the version bump needs no change there, but the fingerprint tests that build a canonical connection must still pass with the ledger table in `schema.sql`.
- Four Frozen Plans target this file (check_plan_target_overlaps): add new test functions in a new class and do not reformat neighbouring tests, to keep rebases trivial.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add one new test class for the ledger behaviors; leave existing tests untouched.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. Add tests for: a new `workflow.sqlite` created by `create_workflow_schema` has `schema_migrations` with one baseline row; running `create_schema()` twice adds no second baseline row; the `schema_migrations` DDL in `scripts/db/schema_sql.py` equals `LEDGER_DDL` from `shared.db_migrations`; a new `eventbus.sqlite` has the ledger and the new stamp; the EventBus fingerprint of a migrated database (from the row 15 fixtures) equals the canonical fingerprint.

### Method

- Reuse the module's existing fixtures for temporary databases rather than adding new ones.

### Details

- Existing tests must keep passing unmodified.

## Compatibility considerations

- Additive tests only.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v`
- `uv run ruff check tests/db/test_create_schema.py`

## Completion criteria

- The new class passes and every pre-existing test in the file still passes.

## Out of Scope

- Migration CLI tests (row 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tests per Procedure | In Progress | 20261030-165727 | — | Plan Phase 3; with rows 08, 09 workflow ledger tests and fixture DDL done; eventbus ledger/fingerprint tests wait for rows 04 and 15 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/db/test_create_schema.py