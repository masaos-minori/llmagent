## Goal

Register the recovery-schema rebuild migration in `scripts/db/migrations_workflow.py`, and open workflow migration connections with foreign keys off (`REQ-008`, rebuild with precondition, backfill, and documented rollback).

## Scope

- Modify only `scripts/db/migrations_workflow.py`.
- Plan amendment (user-approved 2026-10-30): this row was appended after the last row once the registry landed.

## Assumptions

- Registry contract (verified in `scripts/shared/db_migrations.py`): `MigrationSpec(migration_id, from_version, to_version, apply, precondition, postcondition)`; `apply` uses `conn.execute` only, never `executescript`, inside the runner's single `BEGIN IMMEDIATE` transaction; the runner writes the version and ledger rows and verifies the fingerprint against `build_workflow_schema_sql()` at `WORKFLOW_SCHEMA_VERSION`.
- Foreign keys (Step 3a finding): `connect_workflow` applies `foreign_keys=ON`. `DROP TABLE tasks` then runs an implicit `DELETE` whose `ON DELETE CASCADE` removes every `attempts` row, and `PRAGMA foreign_keys=OFF` is a no-op inside a transaction. The rebuild therefore needs the connection opened with foreign keys off before the runner begins its transaction: `WORKFLOW_DOMAIN.connect` is changed to open without `foreign_keys=ON` (migrations are its only user), and the postcondition runs `PRAGMA foreign_key_check` and fails on any row.
- Version chain: see the row 10 document; the spec's `from_version` is the last registered `to_version` (or `1.1.0` when none), `to_version` is `WORKFLOW_SCHEMA_VERSION` as set by the row 10 document.
- Depends on the row 10 document: the rebuilt tables must equal its final DDL, including the index name `idx_attempts_task_stage_number`; the runner's fingerprint check enforces it. Names that `tools/stale_detector.py` flags come from that row or are created here.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- One spec `recovery-schema` rebuilds `tasks`, `attempts`, and `processed_events` in dependency order: create `*_new` tables from the new DDL, copy, drop the old tables, rename, create the index. The `tasks` copy uses the intersection of old and new column names read with `PRAGMA table_info`, so it works whether or not the task-key rename has landed.
- Precondition: reject unknown `tasks.status` and `attempts.status` values (raise with the offending value and count). Backfill: `attempt_number = ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)`. Ledger: keep `processed_events` rows only where a completed attempt exists for the task and stage, linking the latest completed attempt; drop the rest.

## Alternatives considered

- Add columns with `ALTER TABLE`: rejected, SQLite cannot add `CHECK` or `NOT NULL` without a default to existing columns (Plan Design).

## Implementation

### Target file

`scripts/db/migrations_workflow.py`

### Procedure

1. Add `_rebuild_recovery_schema` (new)(conn), `_check_statuses` (new)(conn) as the precondition, and `_check_foreign_keys` (new)(conn) as the postcondition; register the spec in `MIGRATIONS`.
2. Change `connect_workflow` so the connection leaves `foreign_keys` off (`apply_connection_pragmas(conn, write_mode=False)`), with a comment stating why.

### Method

- Build the new-table DDL strings inside this module from the same text as `schema_sql.py` is not possible without duplicating it: keep the spec's DDL as literal statements and let the fingerprint check catch drift against the canonical DDL.
- Run the statements one by one with `conn.execute`.

### Details

- Rollback (documented, per the Plan): the runner's verified pre-migration backup is restored by the operator; the failing step itself rolls back automatically.
- `tests/db/test_migrations_workflow.py` opens connections with `connect_workflow`; its tests do not depend on foreign keys being on.

## Compatibility considerations

- Databases at the old version are migrated through the backup gate; a database with unknown statuses is refused before any change.

## Security considerations

- Statements are static; the precondition reads only enumerated values.

## Rollback considerations

- Forward-only; restore the pre-migration backup.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py tests/db/test_migrations_workflow.py -v`
- `uv run ruff format scripts/db/migrations_workflow.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`

## Completion criteria

- `MIGRATIONS` holds the `recovery-schema` spec chained after the current version, the migrated database equals the canonical DDL, `attempts` rows survive the `tasks` rebuild, and the row 22 document's migration tests pass.

## Out of Scope

- The DDL (row 10), the Python write paths, `workflow_schema.py`, tests of other rows, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the recovery-schema spec and the foreign-key-off connection | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 2; with rows 10 and 22 done in batch |
| 2 | Add or update tests per Validation plan | Completed | 20261030-183035 | 20261030-183035 | Covered by the row 22 document done in batch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-183035 | 20261030-183035 | executed in the Plan Phase 2-4 single batch; full suite 10516 passed, 1 unrelated flaky eventbus 503 (passes alone); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/db/migrations_workflow.py