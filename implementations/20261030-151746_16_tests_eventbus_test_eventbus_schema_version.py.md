## Goal

Extend `tests/eventbus/test_eventbus_schema_version.py` so startup validation covers registered-path migration while unknown and downgrade versions stay refused (`REQ-003`, refusals; `REQ-005`, fail-closed; `REQ-009`, rows survive).

## Scope

- Modify only `tests/eventbus/test_eventbus_schema_version.py`.

## Assumptions

- Verified (Step 3a): the file pins `eventbus_schema_version() == 3` at `:74-75` and tests refusal of version 99, stamping of an unstamped matching database, and refusal of the rest through `eventbus.db_conn.open_db`.
- These tests are written first (fail-first per Plan Risks) and land before row 03 changes `_init_schema`. The pin changes to 4 with row 04.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Keep the existing refusal tests; change only the pinned value and add the migration cases.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/eventbus/test_eventbus_schema_version.py`

### Procedure

1. Change the contract-lock assertion to version 4 and update its docstring.
2. Add: a version 3 database opened through `open_db` is migrated to 4 behind a verified backup with rows intact; a version 1 database (no registered path) is still refused with the recreate message; a version above the current one (downgrade) is refused; a stamped-current but malformed database is still refused by the shape gate.

### Method

- Build the version 3 database with the previous DDL inline, as in the row 15 document.

### Details

- Run these new cases before applying the row 03 change to confirm they fail for the right reason.

## Compatibility considerations

- Existing tests stay valid except the pinned stamp.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_schema_version.py -v`
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus`

## Completion criteria

- The pin is 4; the migration and refusal cases pass after rows 01-04 and the migration case fails before row 03.

## Out of Scope

- Registry and CLI tests (row 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the tests per Procedure | Pending | — | — | Plan Phase 2; before row 03 |
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
- **Requirement ID**: REQ-003, REQ-005, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/eventbus/test_eventbus_schema_version.py
