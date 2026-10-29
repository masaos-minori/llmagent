# Introduce forward-only database migrations and verified recovery drills for canonical SQLite domains

## Priority
High

## Summary
Replace the recreate-on-schema-change policy for `workflow.sqlite` and `eventbus.sqlite` with an ordered, forward-only migration framework that always has a verified recovery point, and add scheduled recovery drills for all four SQLite domains that produce measured restore-time and data-loss evidence.

## Background
Source: `memo-issue.md` item H-02 (which consolidates the memo's original tasks H-02 and M-07), re-verified against current source on 2026-10-29.
- ADR-008 records the current decision: the four databases "have no migration mechanism and are recreated on a schema change. Migration design is out of scope for this ADR" (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md:60`, `Documentation only`). Backups are "periodic file copies (`rotate_all_dbs()`), not continuously verified Snapshots" (same file, line 68).
- `eventbus.sqlite`: a database stamped with a different `PRAGMA user_version` is refused and "must be recreated, never migrated"; a database with the current version is validated against the shared schema fingerprint (`scripts/eventbus/schema.py:71-95`, `Explicit in code`).
- `workflow.sqlite`: `WORKFLOW_SCHEMA_VERSION = "1.1.0"` (`scripts/db/schema_sql.py:25`); `create_schema.py` records the version on a new database and refuses a different one (`scripts/db/create_schema.py:53-66`). `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` states that `workflow.sqlite` "has no migration mechanism; a database older than the supported baseline is recreated" (`Documentation only`).
- `session.sqlite` and `rag.sqlite` use recreate-only DDL, and `schema_sql.py:86-92` says the migration-versus-recreate decision is deliberately deferred (`Explicit in code`).
- Partial recovery building blocks already exist: `scripts/db/recovery.py` runs `PRAGMA integrity_check` on a backup, verifies the backup's domain identity, restores, and verifies again after restore (lines 90, 142, 165-215). `scripts/db/rotation.py` archives database files (`rotate_all_dbs()`).
- No recovery-drill tooling, schedule, or RPO/RTO measurement exists: a search for "recovery drill", "restore drill", and the words RPO and RTO under `scripts/`, `tools/`, `docs/`, and `deploy/` finds nothing (`Explicit by absence search`).

## Problem
`workflow.sqlite` and `eventbus.sqlite` hold canonical recovery state (tasks, attempts, events, delivery state, offsets, DLQ state). A schema change today means recreating the database, which discards that state; there is no supported path that preserves it. Backups are copied but a restore is never exercised end to end, so there is no evidence of how long a restore takes or how much data a restore loses.

## Reason for Change
Every later schema change to a canonical domain (for example the workflow tables planned in `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` or the EventBus outbox in `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`) is forced into destructive recreation until a migration path exists. Severity is High because it affects data integrity of canonical state; it is not tied to a reproduced incident or a date.

## Implementation Intent
Treat migration and recovery as one lifecycle: no migration runs without a verified backup and a deterministic failure path. Start with `workflow.sqlite` and `eventbus.sqlite`, reuse the existing integrity-check and domain-identity helpers in `scripts/db/recovery.py` for backup verification, keep `PRAGMA user_version` and the schema fingerprint as the compatibility contract between binary and database, and keep `session.sqlite` and `rag.sqlite` on their current recreate policy unless the owner extends the scope. Changing ADR-008's recreate-only decision needs a new approval record; record it as part of this work rather than editing the ADR silently.

## Target Files or Areas
- `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`
- `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`
- `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/rotation.py`
- `deploy/init_db.sh`
- `tests/db/test_create_schema.py` and the EventBus schema tests (names to be confirmed)
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` and `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

## Required Changes
- Design an ordered, forward-only migration framework for `workflow.sqlite` and `eventbus.sqlite`, with, per migration, an ID, source and target version, preconditions, postconditions, transaction boundary, and schema fingerprint.
- Before a migration, require a WAL checkpoint, a backup, and an independent integrity verification of that backup.
- Reject downgrades and unknown migration paths; keep the original database when a migration fails or is interrupted.
- Add a dry-run mode that performs no database mutation.
- Validate schema version and fingerprint before the new binary reports ready.
- Define recovery drills for `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, and `eventbus.sqlite`; measure restore time and data-loss window, define RPO and RTO, and retain the results as audit artifacts.
- Record a new approval for the change to ADR-008's recreate-only decision.

## Constraints
- Preserve fail-closed startup behavior: an unsupported or malformed schema must stop startup (existing behavior in `scripts/eventbus/schema.py`).
- No cross-database transactions (ADR-008); each database migrates independently.
- A derived artifact must not replace canonical state; backups are recovery points, not a second source of truth.
- Do not weaken the existing fingerprint check or the refusal of a different version.

## Acceptance Criteria
- Canonical rows survive every supported schema upgrade.
- A failed or interrupted migration leaves the original database intact and diagnosable.
- A binary cannot start against an unsupported or malformed schema.
- Every migration has a verified backup and a tested recovery procedure.
- Dry-run mode leaves the target databases byte-identical.
- Recovery drills show that all four SQLite domains can be restored or manually recovered according to policy, and RPO and RTO measurements are recorded and reviewed.

## Testing Expectations
- Regression tests that fail before the change and pass after: migration success, failure mid-migration, interrupted migration, downgrade rejection, unknown path rejection, dry-run byte preservation.
- Fault-injection tests for failure between backup and migration and during migration.
- Schema-version and fingerprint tests extended to the migrated schemas (`tests/db/test_create_schema.py` and the EventBus schema tests).
- `uv run pytest` for the affected suites, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, and the docs checkers named in `routing.md` for any doc change.

## Documentation Impact
Yes. The ADR-008 decision text and the DB schema and migration document must state the migration contract, the backup and recovery-point requirement, and the failure behavior; the DB operations runbook must describe the drill procedure and where results are retained. Document intent, boundaries, constraints, and failure behavior only, not implementation locations (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Extending migrations to `rag.sqlite` and `session.sqlite` (drills cover them; migrations do not unless the owner decides otherwise).
- Cross-database transactions, replicated storage, or multi-host deployment.
- Automatic restore on corruption beyond the existing `recover_corruption` policy.
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Blocks `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` (new workflow tables should land through migrations, not recreation) and `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md` (the outbox adds a table to `eventbus.sqlite`); recommended order: this issue first.
- Related, in flight: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` and the generated procedures under `implementations/20261029-085348_*` change EventBus code and tests but not the schema; no ordering required.
- Related, archived: `plans/done/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` (last EventBus schema change).

## Unresolved Questions
- `Needs confirmation`: the target RPO and RTO values, and who owns drill scheduling and retention of drill artifacts.
- `Needs confirmation`: whether `rag.sqlite` and `session.sqlite` should also gain migrations, or only drills (this issue assumes drills only).
- `Needs confirmation`: how the existing `workflow_schema_version` table relates to a migration ledger (reuse it or add one).
- `Needs confirmation`: the content of the DB schema and migration document beyond the lines quoted above, and which runbook file carries the operational procedure.

## AI Implementation Instruction
- Read ADR-008, `scripts/db/recovery.py`, and `scripts/eventbus/schema.py` before editing; reuse the existing integrity-check and fingerprint helpers instead of writing parallel ones.
- Keep the change set minimal and phased: the framework with `eventbus.sqlite` first, then `workflow.sqlite`, then drills.
- Do not change the recreate policy of `rag.sqlite` or `session.sqlite`, and do not weaken fail-closed startup.
- Stop and report open questions (RPO and RTO targets, ownership) instead of choosing values.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104500
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `scripts/db/recovery.py`, `scripts/db/recovery_restore.py`, `scripts/db/rotation.py`, `deploy/init_db.sh`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
