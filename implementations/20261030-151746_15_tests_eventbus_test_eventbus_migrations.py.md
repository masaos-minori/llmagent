## Goal

Create the eventbus migration registry and CLI tests in `tests/eventbus/test_eventbus_migrations.py` (`REQ-002`, gate; `REQ-003`, refusals; `REQ-009`, rows survive).

## Scope

- Create only `tests/eventbus/test_eventbus_migrations.py`.

## Assumptions

- Depends on rows 01-05. `tests/eventbus/` is type-checked by CI mypy (`files` includes `tests/eventbus`): annotate fully (`rules/coding.md` mypy note).
- Fixtures: build a version 3 database with rows in `events`, `consumer_delivery`, and `consumer_offsets` using the DDL of the previous version (inline in the test), since `schema.sql` now describes version 4.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Row survival is asserted by comparing the full row sets before and after migration.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/eventbus/test_eventbus_migrations.py` (new)

### Procedure

1. Add tests for: the `ledger-baseline` migration moves a version 3 database to 4 and every row survives (AC-1); the result passes `assert_matches`; the ledger has one row with the migration id; a backup file exists and passes `PRAGMA integrity_check` (AC-4); fault injection between backup and migration and during migration leaves the original database intact and the ledger unchanged (AC-2); the CLI `--dry-run` leaves the file byte-identical (AC-5); `--status` prints the ledger; `--apply` refuses when the service port is reachable (exit 4); an unregistered version exits 2.

### Method

- Call `main(argv)` of the CLI directly and assert exit codes; use a local listening socket on an ephemeral port to simulate the running service.

### Details

- Do not touch `/opt/llm`: the repository isolates tests from production paths; use `tmp_path` only.

## Compatibility considerations

- New test module.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_migrations.py -v`
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus`
- `uv run ruff check tests/eventbus/test_eventbus_migrations.py`

## Completion criteria

- The tests above pass and fail when the baseline spec, the gate, or the CLI refusals are removed.

## Out of Scope

- Startup (`_init_schema`) tests live in the row 16 document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests per Procedure | Pending | — | — | Plan Phase 2; with rows 02-05 |
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
- **Requirement ID**: REQ-002, REQ-003, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/eventbus/test_eventbus_migrations.py
