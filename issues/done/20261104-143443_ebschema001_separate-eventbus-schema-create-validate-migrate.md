# Separate EventBus schema creation, validation, and migration

## Priority
High

## Summary
Stop `create_eventbus_schema` from altering an existing EventBus database before its compatibility is established, and strengthen canonical schema validation so fresh and migrated databases converge.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence):

- `create_eventbus_schema` in `scripts/db/create_schema.py` calls `db.executescript(build_eventbus_schema_sql())` for every existing database whose `user_version` is `0` or the current version. `CREATE ... IF NOT EXISTS` can add missing objects to the existing database, and for `user_version == 0` the function then runs `PRAGMA user_version = 0` to undo the stamp, which does not undo the added objects.
- For an existing database at the current version, the fingerprint check (`assert_matches`) runs only after the DDL has executed.
- `dlq_outbox.event_id` declares the foreign key twice: inline `REFERENCES events(event_id)` and table-level `FOREIGN KEY (event_id) REFERENCES events(event_id)`, in both `scripts/eventbus/schema.sql` and `_DLQ_OUTBOX_SQL` of `scripts/eventbus/migrations.py`.
- Whether the fingerprint (`shared.eventbus_schema_fingerprint`) covers `PRAGMA user_version`, views, partial-index predicates, and triggers was not confirmed in this review; the issue records it as a definition task.

## Problem
Rejecting an incompatible existing database can still leave it mutated, and the schema identity contract is not fully defined. The duplicate foreign key makes `PRAGMA foreign_key_list(dlq_outbox)` return two entries.

## Reason for Change
Data-integrity risk on the startup/initialization path of a persisted database; one canonical-schema lifecycle must keep the expected fingerprint, fresh schema, and migration destination synchronized.

## Implementation Intent
Establish three explicit paths: create a fresh canonical database; validate an existing canonical database without mutation; upgrade a legacy database only through registered forward migrations. Canonical schema identity includes the version and every semantic needed to reject incompatible structures before any write.

## Target Files or Areas
- `scripts/db/create_schema.py`
- `scripts/eventbus/migrations.py`, `scripts/eventbus/schema.sql`
- `scripts/shared/eventbus_schema_fingerprint.py` (path as imported; confirm location)
- EventBus database open/initialization path and migration CLI: Unknown, to be located during planning
- `tests/db/test_create_schema.py`, `tests/db/test_eventbus_schema_equivalence.py`

## Required Changes
- Split fresh creation from existing-database validation.
- Run version and fingerprint checks before executing any DDL against an existing database.
- Route version-0 and other legacy databases through the registered migration path; remove the apply-DDL-then-reset-version behavior.
- Include `PRAGMA user_version` in schema validation; define whether views, partial-index predicates, triggers, and normalized DDL hashes belong to the fingerprint contract and implement the decision.
- Remove one of the duplicate `dlq_outbox.event_id` foreign key declarations and update migration steps and expected fingerprints so fresh and migrated schemas converge.

## Constraints
- Do not change the canonical version-5 meaning for databases already in service without a registered migration.
- Fail closed: an unrecognized existing database is rejected unchanged.
- A fingerprint change must be compatible with already-deployed databases (policy: unknown).
- Error messages contain no row content.

## Acceptance Criteria
- Rejecting an existing database leaves its schema and `user_version` unchanged.
- Fresh creation produces the canonical version-5 schema.
- Legacy upgrades execute only registered migrations.
- Validation detects version and partial-index predicate mismatches required by the contract.
- `PRAGMA foreign_key_list(dlq_outbox)` returns only the intended foreign key.
- Fresh and migrated databases produce the same canonical fingerprint.

## Testing Expectations
- Unit tests for each branch; negative tests that snapshot `sqlite_master` and `user_version` before and after a rejection; WAL-mode integration tests; fresh-versus-migrated fingerprint equivalence.
- Run `uv run pytest tests/db/test_create_schema.py tests/db/test_eventbus_schema_equivalence.py -q`, ruff, and mypy.

## Documentation Impact
Update the eventbus schema design document and runbook: the three paths, the fingerprint contract, and the foreign-key change.

## Out of Scope
- New EventBus tables or columns.
- The generic migration runner's backup behavior.

## Dependencies
- `issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md`: both touch `scripts/eventbus/migrations.py`; apply in either order but re-verify the ledger change against the migration registry.

## Unresolved Questions
- Fingerprint compatibility policy for deployed databases: unknown.
- Current fingerprint coverage of views, triggers, and partial-index predicates: not confirmed.
- `dlqbox001` requirements location: unknown (an archived issue may exist).

## AI Implementation Instruction
Verify the fingerprint coverage first and record the result. Do not execute DDL against an existing database before validation. Keep fresh and migrated schemas byte-equivalent in fingerprint.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/db/create_schema.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/schema.sql`, `tests/db/test_create_schema.py`, `tests/db/test_eventbus_schema_equivalence.py`
