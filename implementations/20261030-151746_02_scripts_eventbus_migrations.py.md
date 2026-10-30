## Goal

Create the `eventbus.sqlite` migration registry in `scripts/eventbus/migrations.py` (`REQ-001`, domain registry; `REQ-009`, rows survive registered upgrades).

## Scope

- Create only `scripts/eventbus/migrations.py`.

## Assumptions

- Plan Dependencies: lands before `dlqbox001`, which registers the first spec here (outbox table). Execution order follows the Plan's `Implementation steps` phases (this row is in Phase 2), not necessarily the table `seq`.
- Depends on row 01: `MigrationDomain` (new in row 01) and `MigrationSpec` (new in row 01) come from `shared.db_migrations`; `tools/stale_detector.py` flags them until row 01 is executed, which is acceptable because rows run in order.
- Plan overlap judgment (Step 2): `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` also targets this file and `schema.sql`: a sequencing dependency, this Plan lands first and `dlqbox001` adds its spec to the registry.
- `eventbus` must not import `db` (`eventbus-is-isolated`), so the module imports `shared.db_migrations` and the standard library only.
- `eventbus.sqlite` stores its version as `PRAGMA user_version` (`scripts/eventbus/schema.sql`, currently 3).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Export one module-level `MIGRATIONS` (new) tuple of specs (one `ledger-baseline` spec at landing: version 3 to 4, applying only the `schema_migrations` DDL of row 04, because adding the ledger table to `schema.sql` changes the canonical fingerprint and the stamp, so existing version 3 databases need a registered path; Step 3a correction of the Plan Assumption "no registered migration steps exist yet") and one `EVENTBUS_DOMAIN` (new) `MigrationDomain` whose `read_version` and `write_version` use `PRAGMA user_version` (as text) and whose `verify_shape` calls `assert_matches` from `scripts/shared/eventbus_schema_fingerprint.py` for the target version's DDL.
- A registered spec's `postcondition` reuses `build_fingerprint`; no second fingerprint implementation.

- Correction (Step 3b): `EVENTBUS_DOMAIN` must pass a `connect` callable (a function in `scripts/eventbus/` that opens the path with `sqlite3`, WAL, busy timeout, and foreign keys as `_apply_eventbus_pragmas` in `schema.py` does) to `MigrationDomain`; see the row 01 document.

## Alternatives considered

- Recreating version 3 databases for the ledger: rejected, it discards canonical rows (REQ-009).
- A registry inside `schema.py`: rejected, the CLI and startup both need it without importing the schema loader.

## Implementation

### Target file

`scripts/eventbus/migrations.py` (new)

### Procedure

1. Create the module with `EVENTBUS_DOMAIN` (new), `MIGRATIONS` (new), and a small `current_target_version` (new)() that returns the version stamped by `scripts/eventbus/schema.sql` through `_expected_schema_version` of `scripts/eventbus/schema.py`.

### Method

- Keep the registry declarative: specs are data, applied by the framework only.

### Details

- `verify_shape` compares against the DDL of the target version; with no registered spec the only target is the current `schema.sql`.
- Do not import `scripts/eventbus/schema.py` at module import time in a way that creates a cycle: `schema.py` imports this module, so read the version lazily inside `current_target_version` (new).

## Compatibility considerations

- New module; the baseline spec only creates an empty table, so no row changes.

## Security considerations

- N/A: no input boundary; no SQL beyond `PRAGMA user_version`.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_migrations.py -v` (row 15 document)
- `uv run ruff format scripts/eventbus/migrations.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- `scripts/eventbus/migrations.py` exports `EVENTBUS_DOMAIN` (new) and `MIGRATIONS` (new) containing the `ledger-baseline` spec, and `PYTHONPATH=scripts uv run lint-imports` keeps `eventbus-is-isolated` KEPT.

## Out of Scope

- Registering any spec other than the ledger baseline (first other consumer is `dlqbox001`).
- `schema.py` and CLI wiring (rows 03 and 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the registry per Procedure | Pending | — | — | Plan Phase 2; after row 01 |
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
- **Requirement ID**: REQ-001, REQ-009
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: scripts/eventbus/migrations.py
