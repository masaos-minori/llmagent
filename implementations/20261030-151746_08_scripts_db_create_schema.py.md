## Goal

Make new `workflow.sqlite` and `eventbus.sqlite` databases ledger-compatible from creation in `scripts/db/create_schema.py` (`REQ-001`, baseline; `REQ-006`, ledger).

## Scope

- Modify only `scripts/db/create_schema.py`.

## Assumptions

- Verified (Step 3a): `create_workflow_schema` runs `build_workflow_schema_sql()` then `_record_workflow_schema_version`; `create_eventbus_schema` runs `build_eventbus_schema_sql()` and, for an existing database, refuses versions other than 0 and `eventbus_schema_version()` with the text "recreate the database".
- Because rows 04 and 09 put the ledger DDL into the canonical DDL, `executescript` already creates `schema_migrations` on a new database; this row adds the ledger baseline row and adjusts the eventbus refusal. Depends on rows 04 and 09. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 3), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- On a new workflow database record the baseline in the ledger as an applied `baseline` entry (from and to equal `WORKFLOW_SCHEMA_VERSION`) through the framework's ledger helper, in the same transaction as the version row.
- For eventbus: an existing database at a version other than the current one is no longer refused here when the registry has a path; it is left for the service's `_init_schema` or `migrate.py` (create_schema must not migrate silently).

## Alternatives considered

- Run migrations from `create_schema`: rejected, bootstrap must stay create-only and idempotent; migrations are explicit (CLI) or startup-gated.

## Implementation

### Target file

`scripts/db/create_schema.py`

### Procedure

1. Import the ledger helper from `shared.db_migrations`; add the baseline insert inside `create_workflow_schema` after `_record_workflow_schema_version`.
2. Update the module docstring (it says schema changes require recreation) to describe the ledger and the migration entry points.

### Method

- Keep `_record_workflow_schema_version` unchanged (it still refuses a mismatched version; migrations go through `migrate_db.py`).
- Keep the `eventbus` unstamped-database behavior exactly as is.

### Details

- Re-running `create_schema()` on an existing database stays a no-op: the baseline insert is `INSERT OR IGNORE` keyed by the baseline id.

## Compatibility considerations

- N/A: no further compat beyond the other sections.

## Security considerations

- Parameterized SQL only.

## Rollback considerations

- Revert the commit; the ledger row on a created database is harmless bookkeeping.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py -v` (row 18 document)
- `uv run ruff format scripts/db/create_schema.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- A new `workflow.sqlite` has the ledger with one baseline row; re-running `create_schema()` adds nothing; mismatched versions are still refused.

## Out of Scope

- Migration logic and CLIs (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the ledger bootstrap per Procedure | In Progress | 20261030-165727 | — | Plan Phase 3; after rows 01, 04, 09 workflow half done (ledger baseline in create_workflow_schema); eventbus half waits for row 04 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the row 18 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Related target files**: scripts/db/create_schema.py