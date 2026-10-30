## Goal

Replace the recreate-only refusal in `_init_schema` of `scripts/eventbus/schema.py` with a registered-path migration while keeping every unresolved case fail-closed (`REQ-003`, refusals; `REQ-005`, fail-closed startup; `REQ-009`, rows survive).

## Scope

- Modify only `scripts/eventbus/schema.py`.

## Assumptions

- Verified in current source (Step 3a): `_init_schema` raises `RuntimeError` with the text "recreate the database" when `PRAGMA user_version` differs from `_expected_schema_version(sql)` and the unstamped-database check fails; an equal version runs `assert_matches`; version 0 with matching tables is stamped.
- `tests/eventbus/test_eventbus_schema_version.py` pins these behaviors and must be extended first (row 16 document, fail-first per Plan Risks); the `eventbus.db_conn.open_db` caller is the startup entry.
- The running EventBus service holds `eventbus.sqlite` (Plan Risks); startup migration runs in the service's own process through `open_db`, behind the verified-backup gate, so no second writer exists.
- Depends on rows 01 and 02 (`run_migrations`, `EVENTBUS_DOMAIN`, `MIGRATIONS`): flagged by `tools/stale_detector.py` until they exist, acceptable because rows run in order. Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 2), not necessarily the table `seq`.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Keep `_init_schema`'s three existing branches. Replace only the final refusal: when `found` differs from `expected`, ask `resolve_path` for the registered path from `found` to `expected`; if one exists, run it through `run_migrations` with a backup directory next to the database file; if none exists (downgrade, unknown, ambiguous), raise the same `RuntimeError` text as today.
- The new-database branch also calls `ensure_ledger` so a fresh database carries the ledger (REQ-006).

## Alternatives considered

- Migrating inside `open_db` for every version: rejected for unregistered paths, they keep today's refusal.

## Implementation

### Target file

`scripts/eventbus/schema.py`

### Procedure

1. Import `ensure_ledger`, `resolve_path`, `run_migrations`, and `MigrationRefusedError` from `shared.db_migrations` and `MIGRATIONS` from `eventbus.migrations`.
2. After a successful migration re-run `assert_matches(conn)` before returning, so a migrated database is validated exactly like a current one.
3. Update the `_init_schema` docstring: a registered forward path is migrated behind a verified backup; any other version is refused.

### Method

- `run_migrations` opens its own connection, so close or commit the caller's write state first and re-read `PRAGMA user_version` afterwards.
- The backup directory comes from the database file's parent (`Path(db_path).parent / "migration_backups"`), derived from `conn`'s database file via `PRAGMA database_list`; an in-memory database has no file and keeps the refusal.

### Details

- N/A: no further details beyond the other sections.

## Compatibility considerations

- Only the `ledger-baseline` path (3 to 4) is registered at landing; every other mismatch still raises the same `RuntimeError`.
- `RuntimeError` subclasses keep existing handlers working.

## Security considerations

- Migration is only entered for a registered path, after a verified backup; a malformed schema stays refused by `assert_matches`.

## Rollback considerations

- Revert the commit; an applied migration is forward-only, so a database already migrated is restored from its pre-migration backup.

## Validation plan

- `uv run pytest tests/eventbus -v`
- `uv run ruff format scripts/eventbus/schema.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- A version 3 database migrates to 4 through the baseline spec with its rows intact and passes `assert_matches`; unknown path and downgrade raise the existing refusal text; unstamped matching database is still stamped; a new database has the ledger.

## Out of Scope

- The registry content, the CLI (row 05), and `schema.sql` DDL (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rework `_init_schema` per Procedure | Pending | — | — | Plan Phase 2; after rows 01, 02, 04; fail-first tests (row 16) land before this change |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the row 15 and 16 documents |
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
- **Requirement ID**: REQ-003, REQ-005, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/eventbus/schema.py
