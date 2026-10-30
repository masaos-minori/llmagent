## Goal

Create the workflow migration registry and CLI tests in `tests/db/test_migrations_workflow.py` (`REQ-002`, gate; `REQ-003`, refusals; `REQ-009`, rows survive).

## Scope

- Create only `tests/db/test_migrations_workflow.py`.

## Assumptions

- Depends on rows 01, 06, 07, 09. The version store is the `workflow_schema_version` table, so these tests cover the table-based accessors the row 14 tests do not.
- Registered specs do not exist yet for workflow, so the tests register a throwaway spec (for example adding a column) in a test-local registry passed to the runner; they must not mutate the real `MIGRATIONS`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Create the test database from `build_workflow_schema_sql()` plus the baseline version row, with rows in `tasks` and `attempts`.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/db/test_migrations_workflow.py` (new)

### Procedure

1. Add tests for: a throwaway spec upgrades the version row and every task and attempt row survives (AC-1); the ledger records it; `read_version` returns the newest row when two share a second (tie-break by rowid); `verify_shape` detects a dropped column; fault injection between backup and migration and during migration leaves the original intact (AC-2); the CLI `--dry-run` is byte-identical (AC-5); `--status` works on a database without a ledger and `--apply` creates it; a downgrade and an unknown path exit 2.

### Method

- Call `main(argv)` with `--db-path`-style overrides only if the CLI offers them; otherwise patch `build_db_config` at the CLI module's own name.

### Details

- Use `tmp_path`; never the production database path.

## Compatibility considerations

- New test module.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py -v`
- `uv run ruff check tests/db/test_migrations_workflow.py`

## Completion criteria

- The listed cases pass and fail when the accessor, ledger, or refusal logic is removed.

## Out of Scope

- Real specs for attempt numbers or the task key (their own Plans' rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests per Procedure | Completed | 20261030-165727 | 20261030-165727 | Plan Phase 3; with rows 06, 07, 09 tests/db/test_migrations_workflow.py created (13 tests) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-165727 | 20261030-165727 | validators passed; full suite 10485 passed (batched Phase 3 run) |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/db/test_migrations_workflow.py