## Goal

Create the `workflow.sqlite` migration CLI in `scripts/db/migrate_db.py` (`REQ-001`, explicit entry point; `REQ-002`, gate; `REQ-004`, dry-run; `REQ-006`, ledger status).

## Scope

- Create only `scripts/db/migrate_db.py`.

## Assumptions

- Depends on rows 01, 06, and 09. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 3), not necessarily the table `seq`.
- The workflow database is opened by the agent process; an apply requires the agent stopped (the CLI states this in its help text; no port probe exists for the agent), while `--dry-run` and `--status` are always safe.
- Database path comes from `build_db_config().workflow_db_path` (`scripts/db/config.py`, as `scripts/db/rotation.py` uses it).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Same CLI contract as row 05: `--dry-run`, `--apply`, `--status`, with the same exit-code classes (0, 2 refusal, 3 failed), so operators learn one interface.

## Alternatives considered

- Share one CLI module across domains: rejected, `eventbus` cannot import `db` and the domains resolve paths differently.

## Implementation

### Target file

`scripts/db/migrate_db.py` (new)

### Procedure

1. Add `main` (new)(argv) and a `__main__` guard; target version defaults to `WORKFLOW_SCHEMA_VERSION` from `scripts/db/schema_sql.py`.
2. `--apply` backs up beside the database file and prints the report; `--status` prints the ledger and the current version.

### Method

- Follow the argument-handling style of `scripts/db/create_schema.py` (`logging.basicConfig`, `sys.exit` on error).

### Details

- Run `ensure_ledger` before reading the ledger so `--status` works on an existing database that has no ledger yet (the read must not mutate in `--dry-run`: use a copy there).

## Compatibility considerations

- New module; no caller.

## Security considerations

- Operates on the local database path from configuration only; no network.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py -v` (row 17 document)
- `uv run ruff format scripts/db/migrate_db.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- `--dry-run` is byte-identical, `--apply` migrates a registered path behind a verified backup, `--status` prints the ledger and version.

## Out of Scope

- Deployment wiring (row 13).
- Registered specs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the CLI per Procedure | Completed | 20261030-165727 | 20261030-165727 | Plan Phase 3; after rows 01, 06, 09 migrate_db.py created; ledger is created by the first applied migration, not by a no-op apply |
| 2 | Add or update tests per Validation plan | Completed | 20261030-165727 | 20261030-165727 | Covered by the row 17 document covered by row 17 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-165727 | 20261030-165727 | validators passed; full suite 10485 passed (batched Phase 3 run); coverage 95% |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-006
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/db/migrate_db.py