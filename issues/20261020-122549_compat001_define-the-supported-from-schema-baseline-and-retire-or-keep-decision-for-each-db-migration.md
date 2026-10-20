# Define the supported-from schema baseline and the retire-or-keep decision for each DB migration

## Priority
High

## Summary
Record, for each SQLite database that carries an upgrade path (`workflow.sqlite`, `eventbus.sqlite`, `mdq.sqlite`), the oldest schema the current release must still upgrade from, why each migration is kept, who owns it, and the condition under which it may be removed. Do not remove any migration in this issue. Where the decision shows a migration is no longer needed, file a separate removal issue.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility features and persistent-data migrations. That investigation read documents only; every claim below was re-checked against the current code on 2026-10-20.
- The migrations are data-preserving upgrade paths, not compatibility shims for an old API. Removing one without knowing which schemas still exist in deployment would make the service fail to start on, or silently misread, an older database. Keeping all of them indefinitely grows the startup path and the test matrix.
- Workflow: the incremental migrations are `_WORKFLOW_MIGRATIONS` applied by `apply_workflow_migrations()` in `scripts/db/schema_sql.py` and invoked from `scripts/db/create_schema.py`. A `workflow_schema_version` table records the version, and `scripts/agent/services/workflow_schema.py` rejects a version mismatch at startup. (Explicit in code)
- EventBus: two migration paths exist. `_EVENTBUS_MIGRATIONS` / `apply_eventbus_migrations()` in `scripts/db/schema_sql.py` runs from `create_schema.py`; `_init_schema()` / `_migrate()` in `scripts/eventbus/schema.py` runs when the service starts against an existing `events` table. Both drop retired columns, and the second also adds columns and converts legacy `consumer_delivery.acked_at`. No schema-version table exists for EventBus. `tests/db/test_eventbus_schema_equivalence.py` checks that bulk initialization and first start produce the same schema. (Explicit in code, Verified by test)
- MDQ: `_migrate_legacy_chunks_schema()` in `scripts/mcp_servers/mdq/db_schema.py` detects the legacy `chunks` shape through `PRAGMA table_info(chunks)` and recreates the tables. It carries no version marker. (Explicit in code)
- A search of `docs/` for a minimum supported schema version, a supported-from version, or a baseline schema found nothing. (Explicit in code: absence verified by search)

## Problem
No document or code defines the oldest schema each database must still be upgraded from. Without that baseline nobody can say which migration is removable, and there is no recorded owner or removal condition for any of them. EventBus additionally has two migration paths and no version marker, so "which version is this database" cannot be answered from the database itself.

## Reason for Change
Migration removal is a data-integrity decision that must rest on a stated baseline, not on the absence of recent complaints. Recording the baseline now lets later cleanup work be filed and reviewed against a fixed criterion, and exposes whether the duplicated EventBus path and the missing version marker are intentional.

## Implementation Intent
- Treat this as a decision-recording task. The output is a short, present-tense statement per database in the canonical database design document: the minimum supported source schema, the reason migrations are kept, the removal condition, and the owner.
- Keep the document at the level of intent and constraints. Do not copy migration identifiers or DDL into documentation; they are derivable from the code.
- The deployed-database inventory lives outside the repository. The issue asks the owner to supply it; it must not be guessed.
- Any follow-up that deletes code is a separate issue, filed only after the baseline shows the migration is unreachable.

## Target Files or Areas
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (canonical place for the migration and recreation policy)
- `docs/90_deployment/deployment_01_deployment.md` (the operator-facing upgrade steps; only to add the read-only schema check an operator runs)
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (read only; the decision must not contradict its invariants)
- Read for evidence: `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/eventbus/schema.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/agent/services/workflow_schema.py`
- Related tests, read only: `tests/db/test_create_schema.py`, `tests/db/test_eventbus_schema_equivalence.py`, `tests/eventbus/test_eventbus_db_migration.py`

## Required Changes
- Obtain from the owner the schema state of every deployed database: the recorded workflow schema version, the columns of `events` and `consumer_delivery` for EventBus, and the shape of `chunks` for MDQ.
- Decide and record the minimum supported source schema for each database.
- For each database, record why its migrations are kept, the removal condition, and the owner, in the canonical database document, in present tense.
- Add to the operator documentation the read-only check that identifies a database's current schema, so the inventory can be repeated.
- Decide, and record as a decision only, whether EventBus needs a schema-version marker and whether its two migration paths are intentional.
- For each migration that the baseline shows to be unreachable, file a separate removal issue that names the migration, the evidence, and the tests to change.

## Constraints
- No migration, migration SQL, or schema DDL changes in this issue.
- Migrations stay idempotent and keep their existing error handling until a removal issue is approved.
- The decision must be consistent with ADR-008 (one DDL source for `eventbus.sqlite`, no cross-database transactions).
- Documentation follows the docs content policy: no inventory of migration identifiers or DDL, current specification only, no history of what was removed earlier.
- Documentation is written in English.

## Acceptance Criteria
- The canonical database document states, for `workflow.sqlite`, `eventbus.sqlite`, and `mdq.sqlite`, the minimum supported source schema, the keep reason, the removal condition, and the owner.
- The operator documentation states the read-only check that identifies a database's current schema.
- The decisions on the EventBus version marker and on the two migration paths are recorded, or listed as open questions with an owner.
- Every migration is covered by a keep decision or by a filed removal issue; none is left unclassified.
- No file under `scripts/` or `tests/` is changed.
- The documentation checkers pass and no new Needs Confirmation marker is left unregistered.

## Testing Expectations
- Not required for code: documentation-only change.
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_needs_confirmation_inventory.py`, and `uv run python tools/check_db_separation.py`.

## Documentation Impact
Yes. Update the canonical database document with the baseline, keep reasons, removal conditions, and owners (intent, constraints, operational notes), and the operator document with the read-only schema check. Register any item left unconfirmed in the Needs Confirmation inventory instead of leaving an inline marker.

## Out of Scope
- Removing or editing any migration, or changing any schema.
- The legacy file-offset import for EventBus (tracked in `compat002`).
- The operational procedure for the MDQ destructive upgrade (tracked in `compat006`).
- Adding the EventBus schema-version marker itself; this issue only decides whether it is needed.
- Backups, restore, and rollback tooling.

## Dependencies
- Related: `compat002` (legacy offset import) and `compat006` (MDQ destructive upgrade) share the same baseline decision; this issue should be settled first.
- Sibling-issue check: no open issue under `issues/` covers migration baselines. `20261020-115744_ebstart003_...` touches `scripts/eventbus/app.py` startup verification only and does not overlap.
- Blocks: any later issue that removes a migration.

## Unresolved Questions
- Who owns the deployed databases, and can they provide the schema inventory? (Needs confirmation)
- Which releases must the current version upgrade from? Is any installation older than the current baseline still in use? (Needs confirmation)
- Is the second EventBus migration path in `scripts/eventbus/schema.py` intentionally separate from `apply_eventbus_migrations()`, or a leftover? The equivalence test suggests both are maintained on purpose. (Needs confirmation)
- Is the absence of an EventBus schema-version marker intentional?
- Is there a rollback expectation for a failed migration beyond the pre-upgrade backup the deployment document already requires for `workflow.sqlite`?

## AI Implementation Instruction
- Do not change any file under `scripts/` or `tests/`, and do not edit migration SQL.
- Do not guess the deployed schema state. If the owner has not supplied the inventory, record the decision as open with the question, and stop.
- Keep documentation to intent, constraints, and operational notes; do not copy migration identifiers or DDL.
- Do not implement a removal here; file a separate issue per removable migration.
- Run the documentation checkers listed above before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-122549
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/90_deployment/deployment_01_deployment.md`, `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/eventbus/schema.py`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/agent/services/workflow_schema.py`
