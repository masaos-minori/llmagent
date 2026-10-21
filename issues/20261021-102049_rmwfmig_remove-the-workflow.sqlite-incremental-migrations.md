# Remove the workflow.sqlite incremental migrations

## Priority
Medium

## Summary
Remove the incremental migration list that upgrades an older `workflow.sqlite` in place, now that the supported baseline is the current release schema and no supported database needs it.

## Background
The database design document (section 8e, Supported Upgrade Baseline) states that the minimum supported source schema of `workflow.sqlite` is the current release schema: the recorded workflow schema version equals the current `WORKFLOW_SCHEMA_VERSION`. The owner decided this on 2026-10-21; the only deployment is the single host using `/opt/llm`. A read-only inspection of that host on 2026-10-21 found `workflow.sqlite` recording version `1.1.0`, equal to the constant in `scripts/db/schema_sql.py`. The document classifies every migration of section 8a as removable and tracks each database's removal as its own change; this is the one for `workflow.sqlite`. (Confirmed by code and by read-only inspection)

## Problem
`apply_workflow_migrations()` and the `_WORKFLOW_MIGRATIONS` list in `scripts/db/schema_sql.py` run on every schema bootstrap and upgrade databases that no supported installation holds. They keep dead upgrade code, a step that marks tasks of a removed approval stage as failed, and a test matrix alive for no supported database.

## Reason for Change
Dead upgrade paths on the startup path add risk without value: a migration that runs on every bootstrap can fail or alter data on a database it was never meant to touch. Removing them makes the schema bootstrap create-only plus version recording, which is what the baseline requires.

## Implementation Intent
Delete the incremental migration mechanism for `workflow.sqlite` and its call from the schema bootstrap, keeping the base DDL and the recording of the schema version unchanged. A database older than the baseline is recreated, not migrated, as the design document states. Keep the startup version-mismatch check in place so an older database is still rejected clearly rather than silently misread.

## Target Files or Areas
- `scripts/db/schema_sql.py` (`_WORKFLOW_MIGRATIONS`, `apply_workflow_migrations()`)
- `scripts/db/create_schema.py` (the call that applies the migrations)
- `tools/check_db_separation.py` (reads `_WORKFLOW_MIGRATIONS` to check table ownership; it must read only the base DDL afterwards)
- `tests/agent/workflow/test_workflow_stage_persistence.py` (migration scenario test)
- `tests/db/test_create_schema.py` (workflow migration cases)
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (sections 8a, 8e), `docs/90_deployment/deployment_01_deployment.md` (migration and backup wording)

## Required Changes
- Remove `_WORKFLOW_MIGRATIONS` and `apply_workflow_migrations()` and the call that applies them in the workflow schema creation.
- Update `tools/check_db_separation.py` so it no longer reads the removed list (it also reads the EventBus list; the EventBus removal issue changes that line, so coordinate the two edits).
- Remove or rewrite the tests that exercise the migrations so no test depends on a removed symbol; keep tests of the base DDL and of the version record.
- Update the documentation so section 8a, section 8e, and the deployment guide no longer describe an in-place workflow migration; do not leave a history of the removal.
- Re-verify the `WORKFLOW_SCHEMA_VERSION` rule: the constant stays, and a version mismatch still fails startup.

## Constraints
- The schema version constant and the startup version check (`scripts/agent/services/workflow_schema.py`) must keep working unchanged.
- No public behavior change for a database at the current schema.
- The ADR on the four-database separation must not be contradicted.

## Acceptance Criteria
- `rg "apply_workflow_migrations|_WORKFLOW_MIGRATIONS" scripts tests docs tools` returns no match.
- Creating the schema on an empty path and on a database already at the current schema both succeed, and the recorded version equals `WORKFLOW_SCHEMA_VERSION`.
- A database recording a different version is still rejected at startup with the existing mismatch error.
- The documentation checkers named in `routing.md` Tools pass, and the full test suite, `ruff`, `mypy --no-namespace-packages`, and `lint-imports` pass.

## Testing Expectations
- Run the targeted tests of `tests/db/test_create_schema.py` and `tests/agent/workflow/test_workflow_stage_persistence.py`, then the full suite once.
- Run `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`, `uv run python tools/check_module_size.py`, and the documentation checkers for the touched docs.
- Manual: read the schema version of the deployed `workflow.sqlite` read-only and confirm it equals `WORKFLOW_SCHEMA_VERSION` before deploying the change.

## Documentation Impact
Yes. Update the sections that describe the incremental workflow migration and the deployment guide's statements about applying migrations and backing up before them, as intent and constraints only (a database older than the baseline is recreated). Do not copy migration identifiers or DDL into documentation.

## Out of Scope
- The EventBus migrations and the MDQ legacy rebuild (separate removal issues).
- Changing the workflow schema, the schema version value, or the version check.
- Backup, restore, or rollback tooling.

## Dependencies
- Depends on the baseline recorded in the database design document (section 8e); that documentation change is already merged.
- Independent of the other three removal issues for `eventbus.sqlite`, `mdq.sqlite`, and the legacy offset import; the design document and the deployment guide are shared files, so apply them one after another.
- Sibling-issue check: no open issue under `issues/` touches these files.

## Unresolved Questions
- N/A: none (the baseline and the single-deployment scope are owner decisions recorded in the design document). Re-run the read-only version check on the deployed host immediately before the removal lands.

## AI Implementation Instruction
- Change only the files listed under Target Files or Areas; keep the diff minimal and do not refactor unrelated schema code.
- Do not add a replacement migration mechanism, a compatibility shim, or a fallback for older databases.
- Stop and report if a caller outside the listed files uses the removed symbols.
- Write documentation in English and follow the repository's documentation checkers.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-233138_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-102049
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `tools/check_db_separation.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/db/test_create_schema.py`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/90_deployment/deployment_01_deployment.md`
