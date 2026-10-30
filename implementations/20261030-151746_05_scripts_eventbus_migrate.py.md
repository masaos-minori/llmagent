## Goal

Create the `eventbus.sqlite` migration CLI in `scripts/eventbus/migrate.py` (`REQ-001`, explicit entry point; `REQ-002`, gate; `REQ-004`, dry-run; `REQ-006`, ledger status).

## Scope

- Create only `scripts/eventbus/migrate.py`.

## Assumptions

- Depends on rows 01 and 02. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 2), not necessarily the table `seq`.
- The EventBus service must be stopped for an apply (Plan Risks; check with `ss -ltnpH 'sport = :<PORT>'`); the CLI refuses an apply when it can open a TCP connection to the configured listener, and `--dry-run` and `--status` do not need the service stopped because they never mutate the original.
- `eventbus` must not import `db`: database path and port come from `eventbus.config` (read its loader before writing), not `db.config`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- `argparse` with mutually exclusive `--dry-run`, `--apply`, and `--status`; distinct exit codes: 0 success, 2 refusal class (downgrade, unknown path, no verified backup), 3 failed migration, 4 service running.

## Alternatives considered

- A subcommand per action: rejected, three flags on one command match the Plan's CLI contract.

## Implementation

### Target file

`scripts/eventbus/migrate.py` (new)

### Procedure

1. Add `main` (new)(argv) and a `if __name__ == "__main__"` guard.
2. `--status` prints the ledger rows and the current version; `--dry-run` calls `run_migrations` with `dry_run=True`; `--apply` calls it with the real database and a backup directory beside the file.

### Method

- Return exit codes from `main` (new); map `MigrationRefusedError` to 2 and `MigrationFailedError` to 3.

### Details

- Log through `logging`, not `print`, except the `--status` table (a CLI result): follow how other scripts in `scripts/eventbus/` report results (read one first).

## Compatibility considerations

- New module; no caller.

## Security considerations

- No network access; the service-running check is a local socket probe to the configured host and port only. Paths come from configuration, never from request data.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_migrations.py -v` (row 15 document)
- `uv run ruff format scripts/eventbus/migrate.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- `--dry-run` leaves the database byte-identical, `--apply` migrates a registered path behind a verified backup, `--status` prints the ledger, and refusal classes map to distinct exit codes.

## Out of Scope

- Deployment wiring (row 13) and the registry content (row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the CLI per Procedure | Pending | — | — | Plan Phase 2; after rows 01-03 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the row 15 document |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-006
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/eventbus/migrate.py
