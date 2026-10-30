## Goal

Give the workflow DDL of `scripts/db/schema_sql.py` its status `CHECK` constraints, the persisted `attempt_number` with a unique index, and the ledger link columns on `processed_events`, and bump `WORKFLOW_SCHEMA_VERSION` (`REQ-008`, constrained schema delivered with a migration).

## Scope

- Modify only `scripts/db/schema_sql.py`.

## Assumptions

- Verified (Step 3a, 2026-10-30): `tasks` DDL at `:172-182`, `attempts` at `:184-194`, `processed_events` at `:196-202`, `artifacts` (already has `attempt_number INTEGER`, `:211`) after it; there is no status `CHECK`, no `attempts.attempt_number`, and no `processed_events.attempt_id`; `WORKFLOW_SCHEMA_VERSION = "1.1.0"` at `:25`. `REQUIRED_WORKFLOW_TABLES` in `scripts/agent/services/workflow_schema.py` lists the required columns (row 11 of the Plan, not generated in this pass).
- The dbmig001 registry exists (Plan amendment 2026-10-30): this change ships with the migration of the row 26 document, in one release. Version chain: default after the wftaskapi001 rename, `1.2.0` to `1.3.0`; if that Plan has not landed, `1.1.0` to `1.2.0`. Read `MIGRATIONS` and the current constant, and use the next version; the row 26 spec's `from_version` follows the same rule.
- Design decision for the ledger (Plan Design, chosen option a): `processed_events` becomes a completed-stage ledger. Its new columns are `NOT NULL` (`attempt_id` referencing `attempts`, `attempt_number`), because a ledger row exists only with a completed attempt. Rows of the old started-marker semantics that have no completed attempt are dropped by the migration (row 26 document). Needs confirmation (non-blocking): owner acceptance that started-only markers are discarded; they are inert under the new semantics and were the cause of the skipped-stage defect.
- If the wftaskapi001 rename has landed, the `tasks` column is `task_nonce`; otherwise `idempotency_key`. Keep whichever the file currently has.
- Overlap judgment (Step 2): shared with Frozen Plans toolexec001, ragcorpus001, wftaskapi001, wflease001, dbmig001: separate regions, compatible; wflease001 adds lease columns to `attempts` after this Plan, so keep `attempts` DDL edits minimal.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- Constrain vocabulary in SQL with `CHECK (status IN (...))` equal to `TaskStatus` and `AttemptStatus` in `scripts/agent/workflow/models.py`; a test (row 22 document) asserts the two sets are equal.

## Alternatives considered

- Keep statuses unconstrained and validate only in Python: rejected, raw-SQL writes would stay unchecked (Plan REQ-001, REQ-008).

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. `tasks.status`: add `CHECK (status IN ('pending','running','completed','failed','halted'))`.
2. `attempts`: add `attempt_number INTEGER NOT NULL`, `CHECK (status IN ('running','completed','failed'))`, and `CREATE UNIQUE INDEX IF NOT EXISTS idx_attempts_task_stage_number ON attempts(task_id, stage_id, attempt_number)`.
3. `processed_events`: add `attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE` and `attempt_number INTEGER NOT NULL`.
4. Bump `WORKFLOW_SCHEMA_VERSION` to the next version in the chain and update its comment.

### Method

- Keep the table order (`tasks`, `attempts`, `processed_events`, `artifacts`) so foreign keys read forward.
- The ledger table `schema_migrations` and the version table stay unchanged.

### Details

- The canonical DDL after the migration must equal this DDL exactly, including index names: the runner verifies the fingerprint, so write the migration (row 26 document) from this file's final text.
- `attempts.attempt_number NOT NULL` without a default breaks every `INSERT INTO attempts` that omits it: `attempt_ops.py` and `idempotency_ops.py` (rows 04 and 05 documents) must supply it in the same release; `rg "INSERT INTO attempts" scripts tests` lists the sites.

## Compatibility considerations

- Existing databases are migrated, not recreated; a database at the old version is refused at startup until `scripts/db/migrate_db.py --apply` has run.

## Security considerations

- N/A: DDL only.

## Rollback considerations

- Forward-only: after the migration has run, restore the pre-migration backup the runner took; a code revert alone does not undo the schema.

## Validation plan

- `uv run pytest tests/db/ tests/agent/workflow/ -v`
- `uv run ruff format scripts/db/schema_sql.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- The DDL carries both status `CHECK` sets, `attempts.attempt_number` with the unique index, the `processed_events` link columns, and the bumped version equal to the last registered `to_version`.

## Out of Scope

- The migration (row 26), `workflow_schema.py` required columns (Plan row 11), Python write paths, tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the DDL and bump the version | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 2; with rows 26 and 22 in one release unit done in batch |
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
- **Related target files**: scripts/db/schema_sql.py