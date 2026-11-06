# Remove database migration compatibility and enforce current-schema-only startup

## Priority
High

## Summary
Remove all Workflow and EventBus data migration capabilities, migration ledgers, migration CLIs, automatic version stamping, and startup upgrade paths, and replace them with one current-schema-only policy that rejects any incompatible existing database without modifying it. Migration-framework removal, ledger removal, legacy-database rejection, migration-only backup cleanup, schema documentation, and migration-test replacement are one issue because they all change the same database lifecycle.

## Background
Initiative issue H-1 of `memo-issue.md` ("Backward Compatibility Removal"), implemented first. Verified 2026-11-06 in the repository: `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `tests/eventbus/test_eventbus_migrations.py`, and `tests/db/test_create_schema.py` exist; `schema_migrations` appears in about 20 files and `dbmig001` in about 16 files under `scripts/`, `tests/`, `tools/`, and `docs/`; `verify_backup_by_path` appears in one file. The shared migration framework, domain registries, ledgers, backup gates, dry-run behavior, and an EventBus migration CLI exist, and EventBus startup can stamp an existing unversioned database whose table shape matches the current schema.

## Problem
These mechanisms preserve database backward compatibility. They add startup complexity, create several schema-management paths, and leave it unclear whether an operator should migrate or recreate an incompatible database. Keeping only part of them would leave contradictory behavior, tests, and documentation.

## Reason for Change
One unambiguous database lifecycle is easier to operate and test than a migration framework, and it matches the repository's current-only policy.

## Implementation Intent
Establish one lifecycle: create a database only when none exists; accept an existing database only when its version and full schema match the current specification; reject every other existing database before mutation; require an operator to archive the incompatible database if needed and recreate it manually; keep rotation, archive validation, and supported corruption recovery.

## Target Files or Areas
`scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`, Workflow and EventBus startup and connection modules, schema fingerprint implementations, `tests/eventbus/test_eventbus_migrations.py`, Workflow migration and shared migration-runner tests, `tests/db/test_create_schema.py`, the database operations runbook, and every reference to `MigrationRunner`, `MigrationSpec`, `schema_migrations`, `shared.db_migrations`, `db.migrations_workflow`, `eventbus.migrations`, `eventbus.migrate`, `verify_backup_by_path`, and `dbmig001`.

## Required Changes
Remove the migration implementation:
- Delete the four migration modules named above.
- Remove `MigrationRunner`, `MigrationSpec`, `MigrationRefusalError`, `MigrationRefusalReason`, `Registry`, `LedgerRow`, `ensure_ledger`, `read_ledger`, `record_applied`, and migration-only backup-gate references.
- Remove Workflow migration paths 0 to 1, 1 to 2, 2 to 3, and 3 to 4, and EventBus migration paths 3 to 4 and 4 to 5, with planning, status, dry-run, resume, and apply behavior.
- Remove `verify_backup_by_path()` if no non-migration caller exists.

Remove migration state from schemas:
- Remove `schema_migrations` from the Workflow DDL in `scripts/db/schema_sql.py` and from `scripts/eventbus/schema.sql`, with the baseline migration-record insertion and the `dbmig001` and ledger comments.
- Regenerate the Workflow and EventBus schema fingerprints without the ledger.
- Keep `PRAGMA user_version` only as the EventBus current-schema identifier; keep Workflow schema-version metadata only if it represents one current schema rather than migration history.

Enforce current-schema-only startup:
- A missing database path creates the current schema.
- An existing database must have the exact current version, then pass a complete schema fingerprint check; missing or altered tables, columns, indexes, triggers, or constraints are rejected.
- Remove automatic migration of registered lower versions and automatic stamping of existing `user_version = 0` databases.
- Never delete, rename, archive, copy, or modify an incompatible database automatically.

Preserve operational data protection: `rotate_workflow_db()`, `rotate_eventbus_db()`, `rotate_all_dbs()`, archive integrity and domain-identity validation, supported RAG and session corruption recovery, and unknown or corrupt archives kept for manual investigation. Do not restore an old Workflow or EventBus archive into the current schema automatically.

Replace tests and documentation: delete the EventBus and Workflow migration tests and the shared migration-runner tests, remove migration assumptions from maintenance tests, replace migration-success tests with legacy-database rejection tests, and add the manual archive-and-recreate procedure to the database runbook.

## Constraints
The rejection error must be clear and equivalent to:

    The database does not match the current schema.
    Automatic migration and version stamping are not supported.
    Stop the service, archive the existing database if required,
    remove or rename it, and create a new database using the current schema.

It may include the database path and the expected and detected versions, and must not expose credentials or unrelated configuration values. The common policy of the initiative applies:

Common policy (shared by all four issues of this initiative):

1. Support only the current database schema, API, import path, and authentication model.
2. Do not provide automatic database migration, version stamping, compatibility aliases, re-export facades, or deprecated call signatures.
3. Reject incompatible existing databases before mutation.
4. Do not automatically delete an incompatible database.
5. Permit an operator to archive an incompatible database and recreate it manually.
6. Preserve rotation, archive validation, and supported corruption recovery: they protect current data and are not backward-compatibility features.
7. Prevent deleted symbols, modules, imports, and specifications from being reintroduced through CI and pre-commit checks.

Persisted-schema change: load `rules/persisted-schema-change.md` before planning (DDL, schema version, and migration changes).

## Acceptance Criteria
- [ ] All migration framework, registry, and CLI modules are deleted.
- [ ] `schema_migrations` is absent from newly created Workflow and EventBus databases, and no migration baseline record is created.
- [ ] No source or test imports a deleted migration symbol.
- [ ] An existing `user_version = 0` database is rejected and not stamped; a lower or higher schema version is rejected; a current-version database with an altered schema is rejected.
- [ ] Rejection performs no write, version update, table change, automatic archive, or deletion (file hash unchanged).
- [ ] A missing database is created with the current schema; current valid databases open normally.
- [ ] Schema fingerprints are regenerated and verified.
- [ ] Rotation, archive validation, and supported recovery tests continue to pass.
- [ ] Active documentation describes only the current-schema and manual-recreation policy.

## Testing Expectations
Create fresh Workflow and EventBus databases and inspect `sqlite_master`; test lower, higher, unversioned, malformed, and current databases; compare the database file hash before and after every rejection case; run the schema fingerprint tests and the database maintenance, rotation, archive, and recovery tests; run the complete test suite and `tools/check_compat_shims.py`.

## Documentation Impact
Yes: the database runbook (manual archive-and-recreate procedure), the Workflow and EventBus schema documentation (current schema only, no migration history, no ledger), and any document that describes migration paths, dry-run, resume, or `dbmig001`. Documentation work that applies the final policy across all active documents belongs to the M-2 issue.

## Out of Scope
Automatic data export from an old schema, automatic import into the new schema, down migrations, a compatibility converter distributed outside the product, and automatic deletion of an incompatible database.

## Dependencies
Complete before the policy-enforcement issue `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`, whose checker must target the final set of deleted migration modules and symbols. May run in parallel with `issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md`.

## Unresolved Questions
- Whether Workflow schema-version metadata represents one current schema or migration history (decide when the Workflow startup module is read).
- Whether any non-migration caller of `verify_backup_by_path()` exists (repository-wide search is required before deleting it).

## AI Implementation Instruction
Follow the Implementation Intent; do not add a conversion path. Run the persisted-schema checklist, regenerate fingerprints with the repository tools, and compare database file hashes in the rejection tests. Respect `rules/env.md` and the four-database separation checked by `tools/check_db_separation.py`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-125142
- **Related target files**: `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_migrations.py`, `tests/db/test_create_schema.py`

## Adversarial Validation

Validated against current source on 2026-11-07.

- The four migration modules (`db_migrations.py`, `migrations_workflow.py`, `eventbus/migrations.py`, `eventbus/migrate.py`) plus `tests/eventbus/test_eventbus_migrations.py` and `tests/db/test_create_schema.py` all exist. — Evidence: `Explicit in code` — Confidence: High
- `schema_migrations` appears in 20 files and `dbmig001` in 16 files under `scripts/`, `tests/`, `tools/`, `docs/` (excl. `done/`); `verify_backup_by_path` is referenced in one file (`scripts/db/migrations_workflow.py`). — Evidence: `Operationally observed` (rg) — Confidence: High
- Scope as a single issue is justified: every listed change touches the database lifecycle (migration framework, ledger, schema, startup). Dependencies (`004` after this; parallel with `002`) are consistent with the other three issues.
- No factual conflict found. The Unresolved Questions (Workflow schema-version metadata meaning, `verify_backup_by_path` caller search) remain appropriately open.

Verdict: accepted as filed.

## Content Analysis

- Type: implementation (removes migration framework, ledger, CLIs, and upgrade paths; enforces current-schema-only startup).
- Pipeline path: issue -> plan -> implementation procedure -> code. Owner: engineer.
- Scope: `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`, `tests/eventbus/test_eventbus_migrations.py`, `tests/db/test_create_schema.py`.
- Dependency: first of the four (initiative H-1); must complete before `004`, runs parallel with `002`.
- Open item before planning: meaning of Workflow schema-version metadata; whether a non-migration caller of `verify_backup_by_path()` exists.
