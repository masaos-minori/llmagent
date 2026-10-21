# Remove the eventbus.sqlite schema migrations

## Priority
Medium

## Summary
Remove both EventBus schema migration paths (the bootstrap list and the startup `_migrate()`), including the retired-column drop and the legacy `acked_at` conversion, now that the supported baseline is the current release schema.

## Background
The database design document (section 8e, Supported Upgrade Baseline) states that the minimum supported source schema of `eventbus.sqlite` is the current release schema defined by `scripts/eventbus/schema.sql`. The owner decided this on 2026-10-21; the only deployment is the single host using `/opt/llm`, and its `eventbus.sqlite` was recreated from the current DDL that day (columns of `events`, `consumer_delivery`, and `consumer_offsets` match the current schema; no `retry_count`, no `acked_at`). Section 8b describes two migration paths that both upgrade an existing database: `apply_eventbus_migrations()` with `_EVENTBUS_MIGRATIONS` in `scripts/db/schema_sql.py` (run from the schema bootstrap), and `_migrate()` in `scripts/eventbus/schema.py` (run by `_init_schema()` when the `events` table already exists). The `eventbus-is-isolated` import contract is why the two cannot share code. (Confirmed by code and by read-only inspection)

## Problem
Two parallel migration paths run on the bootstrap and on every service start and keep a conversion for a column (`acked_at`) and a drop of a column (`retry_count`) that no supported database has. Their equivalence needs its own test, and the design document lists "are two paths intentional" as an open decision. Both exist only for databases the baseline excludes.

## Reason for Change
Migration code on the startup path of the EventBus service can alter a database in place; keeping it for databases that do not exist is risk and test cost without benefit. Removing both paths also removes the open decision about their duplication.

## Implementation Intent
Delete both migration paths together, so the two can never diverge, and keep the schema creation from `schema.sql` as the only schema definition (the four-database separation ADR requires one DDL source for `eventbus.sqlite`). `_init_schema()` keeps creating the schema when the `events` table is absent; decide explicitly what it does when the table exists (the simplest correct behavior is to do nothing, since a supported database already has the current schema). A database older than the baseline is recreated, as the design document states.

## Target Files or Areas
- `scripts/db/schema_sql.py` (`_EVENTBUS_MIGRATIONS`, `apply_eventbus_migrations()`)
- `scripts/db/create_schema.py` (the call, and the comment that explains why migrations run before the DDL)
- `scripts/eventbus/schema.py` (`_migrate()` and its call in `_init_schema()`)
- `tools/check_db_separation.py` (reads `_EVENTBUS_MIGRATIONS` to check table ownership)
- `tests/db/test_eventbus_schema_equivalence.py`, `tests/db/test_create_schema.py`, `tests/eventbus/test_eventbus_db_migration.py`
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (sections 8b, 8e, 9), `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` and other EventBus documents that describe the migration

## Required Changes
- Remove `_EVENTBUS_MIGRATIONS`, `apply_eventbus_migrations()`, and its call in the schema bootstrap; remove `_migrate()` and simplify `_init_schema()`.
- Update `tools/check_db_separation.py` so it reads only the base DDL for `eventbus.sqlite` (it also reads the workflow list; the workflow removal issue changes that line, so coordinate the two edits).
- Remove or rewrite the tests that exercise the migrations or compare the two paths; keep tests that the base DDL creates the three tables and the indexes, and that a database at the current schema starts cleanly.
- Update the documentation so sections 8b, 8e, and 9 and the EventBus documents describe a create-only schema, without a history of the removal; remove the open decision about the two paths.
- Confirm that `rg "retry_count|acked_at"` under `scripts/eventbus` and `scripts/db` finds only the active uses that remain.

## Constraints
- `scripts/eventbus/schema.sql` stays the single DDL definition of `eventbus.sqlite`; no cross-database transaction is introduced.
- The `eventbus-is-isolated` import contract must still hold.
- No behavior change for a database at the current schema; the service must start against the recreated host database.

## Acceptance Criteria
- `rg "apply_eventbus_migrations|_EVENTBUS_MIGRATIONS|_migrate\b" scripts tests tools docs` finds no EventBus migration reference.
- Creating the schema on an empty path and starting the service on a database at the current schema both succeed with an unchanged schema.
- `tools/check_db_separation.py`, `ruff`, `mypy --no-namespace-packages`, `lint-imports`, the full test suite, and the documentation checkers pass.

## Testing Expectations
- Run the targeted tests of the three test files above, then the full suite once.
- Run `uv run python tools/check_db_separation.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`, and the documentation checkers for the touched docs.
- Manual: read the columns of `events`, `consumer_delivery`, and `consumer_offsets` of the deployed database read-only (see the Deployment Guide's schema check, or the commands in the EventBus operations document) and confirm they match `schema.sql` before deploying.

## Documentation Impact
Yes. Remove the descriptions of the additive migration, the column removal, the column conversion, and the two initialization paths from the database document, and update the EventBus persistence document accordingly; state only intent and constraints (a database older than the baseline is recreated).

## Out of Scope
- The workflow migrations, the MDQ legacy rebuild, and the legacy offset import (separate issues).
- Changing `schema.sql`, adding an EventBus schema-version marker, or changing the equivalence of a fresh database.

## Dependencies
- Depends on the baseline recorded in the database design document (section 8e); that change is already merged.
- Shares `tools/check_db_separation.py`, `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, and the database design document with the workflow removal issue; apply the two edits one after another.
- Related to the legacy offset import removal issue (same service, different files); independent in order.
- Sibling-issue check: no open issue under `issues/` touches these files.

## Unresolved Questions
- Whether `eventbus.sqlite` needs a schema-version marker is a separate open decision in the database design document; this issue neither adds nor decides it.
- Re-run the read-only column check on the deployed host immediately before the removal lands.

## AI Implementation Instruction
- Change only the files under Target Files or Areas; keep the diff minimal and do not refactor unrelated EventBus code.
- Do not add a compatibility shim, a fallback for older databases, or a new migration mechanism.
- Stop and report if a caller outside the listed files uses a removed symbol.
- Write documentation in English and follow the repository's documentation checkers.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-102130
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/eventbus/schema.py`, `tools/check_db_separation.py`, `tests/db/test_eventbus_schema_equivalence.py`, `tests/db/test_create_schema.py`, `tests/eventbus/test_eventbus_db_migration.py`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
