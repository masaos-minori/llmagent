# Provide durable, transactionally verified database migrations

## Priority
High

## Summary
Make the migration runner's recovery point, dry-run, integrity verification, checkpoint reporting, version reporting, and ledger ordering form one auditable migration-safety workflow.

## Background
Verified against current source on 2026-11-04 (confirmed by repository evidence):

- `_run_pre_migration_gate` in `scripts/shared/db_migrations.py` writes the SQLite backup-API copy to a `tempfile.mkstemp` file and always deletes it in `finally`; no durable pre-run recovery point survives, so a later failing step cannot be undone to the pre-run state.
- `MigrationRunner.apply` runs `spec.postcondition(conn)` after `_apply_step` has committed the step and ledger row. The workflow migrations in `scripts/db/migrations_workflow.py` use `postcondition=` for their `user_version`/fingerprint assertions (`_postcondition_fingerprint`, `_postcondition_tool_state`, `_postcondition_task_nonce`, `_postcondition_attempt_lease`), so a failed assertion cannot roll back. `pre_commit_verification` exists but those specs do not use it.
- The dry-run path uses `shutil.copyfile(db_path, tmp_path)`, which copies only the main file and omits committed content still in the WAL.
- The gate refuses on a non-zero `wal_checkpoint(FULL)` busy count with `NO_VERIFIED_BACKUP`, the same reason code as a backup or integrity failure; the requirement for FULL (versus PASSIVE) is not documented here.
- `read_ledger` orders by `applied_at, id` and `applied_at` has one-second granularity, so same-second steps are ordered by id text, not application order.
- `scripts/db/migrate_db.py` prints `user_version=` and ledger rows only; the integer workflow code and the semantic `workflow_schema_version` string are not both shown together with documented meaning.

## Problem
Whole-run recoverability, mutation rejection before commit, WAL-consistent dry-run, distinguishable refusal reasons, and deterministic audit order are not guaranteed. These concerns share one execution boundary, so backup, verification, and ledger changes must stay compatible.

## Reason for Change
Data-integrity and audit risk on a forward-only migration path that is executed against production databases.

## Implementation Intent
Create a migration process that is recoverable at whole-run level while preserving step-level atomicity: every run operates on a WAL-consistent state, retains a verified pre-run recovery point per retention policy, rejects invalid mutations before commit, and emits an ordered audit trail whose version semantics are clear to operators and automation. Keep the temporary gate copy separate from the durable archive.

## Target Files or Areas
- `scripts/shared/db_migrations.py`
- `scripts/db/migrations_workflow.py`
- `scripts/db/migrate_db.py`
- `scripts/eventbus/migrations.py` (shares the runner; ledger change must remain compatible)
- `tests/db/test_migrations_workflow.py` and the runner tests (path: Unknown)

## Required Changes
- Create a durable pre-migration archive with the SQLite backup API and record archive path, SHA-256, source version, creation time, and retention status in an audit artifact.
- Use the backup API for dry-run snapshots instead of copying only the main file.
- Move mutation-integrity assertions from `postcondition` to `pre_commit_verification`; restrict postconditions to observational checks or define an explicit failed-ledger state.
- Document and test whether `PRAGMA wal_checkpoint(FULL)` is mandatory; give checkpoint-busy and backup-failure distinct machine-readable refusal reasons.
- Add deterministic ledger ordering (monotonic sequence or high-resolution key) and make `read_ledger` use it.
- Document the integer workflow migration code and show it with the semantic schema version in CLI status.
- Add restoration validation for a migration that fails after at least one earlier step committed.

## Constraints
- Preserve step-level transactions and the existing public interfaces unless an acceptance criterion requires a contract change.
- Fail closed for mandatory integrity verification.
- Dry-run must not modify the live database.
- Ledger schema change must keep existing ledgers readable (forward-only; no table rebuild outside the runner contract).
- Error messages contain no secrets or row content.

## Acceptance Criteria
- A verified pre-migration archive remains available per the retention policy after success or failure.
- A partial multi-step migration can be restored to the exact pre-run logical state.
- A failed pre-commit verification changes neither schema, `user_version`, nor ledger.
- Dry-run includes committed rows still in the WAL and leaves the live database unchanged.
- Checkpoint refusal and backup failure have different machine-readable reasons.
- Ledger output preserves actual application order when several steps finish within one second.
- CLI output shows both the internal migration code and the semantic schema marker, both documented.

## Testing Expectations
- Unit tests for each changed branch; integration tests in WAL mode with the production-equivalent workflow schema.
- Fault-injection tests for each fail-closed path, including a late-step failure after earlier commits.
- Run the runner and workflow migration tests, ruff, and mypy per `rules/toolchain.md`.

## Documentation Impact
Update the migration design document, ADR for the FULL-checkpoint requirement (create if absent), and the operations runbook: archive location and retention, refusal reasons, ledger ordering key, version semantics.

## Out of Scope
- Eventbus schema creation/validation redesign (separate issue).
- Recovery from corruption (`scripts/db/recovery*.py`).
- New migration steps.

## Dependencies
- `issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md`: both touch the eventbus migration registry; coordinate the ledger-ordering change with the eventbus migrations.

## Unresolved Questions
- Archive retention and storage policy, production backup location, and permissions: unknown.
- Whether FULL checkpoint is a requirement or intentional conservatism: unknown (no ADR located).
- Workflow schema-version ADR: unknown.

## AI Implementation Instruction
Do not infer retention, location, or permission requirements; record them as open questions. Keep the temporary gate copy and the durable archive as separate concepts in code and docs. Add the failing test for each defect before the fix.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-143443
- **Related target files**: `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/db/migrate_db.py`, `scripts/eventbus/migrations.py`, `tests/db/test_migrations_workflow.py`
