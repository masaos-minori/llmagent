<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "scripts/db/migrations_workflow.py", "target_kind": "source", "seq": 26} -->

## Goal

Register the workflow table-rebuild migration in `scripts/db/migrations_workflow.py` (vocabulary preconditions, rebuild with `attempt_number` backfill, postconditions, stamped version) (REQ-008 / AC-10).

## Scope

- Append the rebuild `MigrationSpec` to `REGISTRY` (`migrations_workflow.py:245-262`): `from_version=2`, rebuild of `tasks`, `attempts`, `processed_events` (rename-to-old -> canonical `CREATE` from `schema_sql` -> parent-first copy -> child-first drop).
- Precondition SQL rejects out-of-vocabulary `tasks.status`/`attempts.status` rows and lists the offending rows in the failure message.
- `attempt_number` backfill via `ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)` during the copy.
- Postcondition: table shapes equal the canonical DDL, `PRAGMA foreign_key_check` clean; stamp `workflow_schema_version` row and `PRAGMA user_version`; update `WORKFLOW_VERSION_CODES` (`:42`) and `WORKFLOW_TARGET_VERSION` (`:48`).

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Ledger code landing order: wftaskapi001 row `implementations/20261101-140834_12_*` (Pending) registers `workflow_task_nonce` at code `3` / `1.3.0`. If that lands first this row takes code `4` / `1.4.0`; if this lands first it takes `3` / `1.3.0` and wftaskapi001 renumbers. Whichever lands second must re-verify the registry head (Plan UNK-05). `plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` is open but reserves no code.
- `migration_sql` runs through `executescript` in one all-or-nothing transaction (`scripts/shared/db_migrations.py:404-415`); `PRAGMA foreign_keys` cannot toggle mid-transaction, so the rebuild relies on SQLite 3.25+ rename-follow semantics.

## Design decisions

- Precondition fails closed (Plan UNK-07): existing violating rows — stale `running` attempts, `processed_events` started markers without a completed attempt — are listed, not silently mapped; automatic mapping needs an owner decision before any production run.
- Documented rollback equals the dbmig001 backup gate: restore the pre-migration backup copy of `workflow.sqlite`; there is no down-migration.
- One spec (not three table-specific specs) keeps the rename-copy-drop sequence inside a single transaction.

## Alternatives considered

- ALTER TABLE ADD COLUMN only: rejected — `CHECK` constraints and a unique index require table rebuilds, and `processed_events` gains NOT NULL columns the backfill must populate.

## Implementation
### Target file
`scripts/db/migrations_workflow.py`

### Procedure
1. Add the precondition check function and the `mutation_sql` script (rename, create, copy with backfill, drop).
2. Register the spec in `REGISTRY` and bump `WORKFLOW_VERSION_CODES`/`WORKFLOW_TARGET_VERSION` at landing.
3. Document the rollback procedure in the module docstring (backup-copy restore, dbmig001 gate).

### Method
Direct edit: one appended spec plus registry/version constants.

### Details
- Copy statements order parent-first (`tasks` -> `attempts` -> `processed_events`) and drops child-first to keep FK integrity through the rebuild.

## Compatibility considerations

- `tests/db/test_migrations_workflow.py` head-version expectations change with the bump — owner-visible follow-up (flagged in row 22).

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Precondition listing uses parameter-bound queries; no dynamic SQL over data.

## Rollback considerations

- Restore the backup copy (documented); code revert alone does not un-migrate data.

## Validation plan

- `uv run pytest tests/db/ -v` (row 22 migration tests: valid and invalid databases).
- `uv run python tools/check_db_separation.py`.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- A v2 database migrates to the new head with preserved rows and backfilled numbers; an invalid database is refused with the offending rows listed; the version is stamped (AC-10).

## Out of Scope

- Runner changes (`plans/20261101-133244_dbmigrunner001_*`, open); production execution (Phase 6 deploy).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Registry code `3`/`1.3.0` is also claimed by wftaskapi001 row 12 (Pending); landing order decides the number (Plan UNK-05) | No | — |
| 2 | Plan UNK-07: owner decision on automatic mapping of violating retained rows before any production migration run | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Schema and migration)
- **Requirement ID**: `REQ-008`
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-145309
- **Related target files**: `scripts/db/migrations_workflow.py`, `scripts/db/schema_sql.py`, `scripts/shared/db_migrations.py`, `tests/db/test_create_schema.py`
