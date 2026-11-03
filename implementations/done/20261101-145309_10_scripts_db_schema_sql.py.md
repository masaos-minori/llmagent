<!-- workitem: {"id": "20261101-145309", "generated_at": "2026-11-01T14:53:09Z", "schema_hash": "488513b688446992", "schema_version": 1, "source": "plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md", "target_file": "scripts/db/schema_sql.py", "target_kind": "source", "seq": 10} -->

## Goal

Add the status `CHECK` vocabularies, `attempt_number` with its unique index, and the ledger correlation columns to the canonical DDL in `scripts/db/schema_sql.py`, and bump `WORKFLOW_SCHEMA_VERSION` (REQ-008 / AC-10).

## Scope

- `tasks` (`schema_sql.py:184-194`): `status TEXT NOT NULL CHECK (status IN ('pending','running','completed','failed','halted'))`.
- `attempts` (`:196-206`): `status ... CHECK (status IN ('running','completed','failed'))`, `attempt_number INTEGER NOT NULL`, and `CREATE UNIQUE INDEX idx_attempts_task_stage_number ON attempts(task_id, stage_id, attempt_number)`.
- `processed_events` (`:208-214`): add `attempt_id TEXT NOT NULL`, `attempt_number INTEGER NOT NULL`.
- `WORKFLOW_SCHEMA_VERSION` (`:27`) `1.2.0` -> `1.3.0`.

## Assumptions

- Plan `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` is Frozen; its 26-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` commit `384eb72` on 2026-11-01.
- Canonical semantics come from the Plan REQs (Plan `:41-52`): REQ-001 matrix `pending->{running,halted}`, `running->{completed,failed,halted}`, `failed->{running}`, `completed->failed` transitional, `halted` terminal; exactly three typed errors in `scripts/agent/workflow/errors.py`; `processed_events` as the completed-stage ledger (Plan UNK-02 default); recovery atomically fails the stale attempt and its owning `running` task (Plan UNK-03); claim accepts `pending` or `failed` only (Plan UNK-01).
- Landing-order dependency (Plan UNK-05): the wftaskapi001 procedures (`implementations/20261101-140834_*`, plan `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`) are generated but Pending; the shared migration ledger code is fixed at landing time.
- Version-code landing-order caveat (Plan UNK-05): the Pending wftaskapi001 row `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md` already reserves ledger code `3` / version `1.3.0` for the `task_nonce` rename. If wftaskapi001 lands first, this row's DDL ships as version `1.4.0` / code `4` and the version constant matches that landing; if this Plan lands first, code `3`/`1.3.0` is taken here and wftaskapi001 renumbers to `4`/`1.4.0`. Fix the number at landing time; both orders must end with distinct codes.

## Design decisions

- DDL is the single source (`_WORKFLOW_SCHEMA`, `:178`) used by fresh creation; existing databases change only via the row-26 rebuild migration.
- `artifacts.attempt_number` (`:223`) already exists — the correlation tuple gains its missing members without touching `artifacts`.

## Alternatives considered

- Adding columns without `CHECK`/index: rejected — REQ-008 names the constraints; the unique index is the concurrency backstop the row-18 tests assert.

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Edit the three `CREATE TABLE` statements inside `_WORKFLOW_SCHEMA` (`:178` region).
2. Add the index statement next to the existing workflow index statements.
3. Update the version constant and its guard comments.

### Method
Direct edit of DDL strings.

### Details
- `check_db_separation.py` and the schema-ownership contract keep `schema_sql.py` as the only workflow DDL owner.
- Row 22's `_WORKFLOW_SCHEMA_NO_VEC0` copy must be updated to the same shape in the same commit (it is the migration-fixture source for row 22 tests).

## Compatibility considerations

- Row 11 required-column checks and row 20 fixtures must gain the new columns in the same phase; `tests/db/test_migrations_workflow.py` (existing suite, outside the frozen table) will need its expectations updated — flag it to the owner as a follow-up when the head version bumps.

## Security considerations

- Status/attempt values written to SQL come only from the `models.py` enums, never from caller strings; all state SQL stays parameter-bound.
- Constraints protect the vocabulary invariant at the storage layer; no new surface.

## Rollback considerations

- DDL revert is only safe together with the row-26 migration revert (a migrated database keeps the rebuilt shape until restored from the backup copy).

## Validation plan

- `uv run pytest tests/db/ -v` (row 22 constraint/index tests).
- `uv run python tools/check_db_separation.py`.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- Fresh databases enforce the five/four-status vocabularies, non-null unique attempt numbers per (task, stage), and ledger correlation columns; version constant bumped (AC-10).

## Out of Scope

- Migration steps (row 26); startup column checks (row 11).

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
| — | — | — | — |

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
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_create_schema.py`

## Implementation Result (2026-11-03: superseded by upstream)

This wfrecovery001 procedure implemented an attempt-number-based recovery state
machine. Upstream (`origin/master`) superseded this design with a lease-based
stale-attempt recovery (wflease001, AC-2/AC-4/AC-5/AC-7). The batch was
therefore NOT merged into `origin/master`.

- **Decision (2026-11-03):** full supersession. Every one of the ~32 code files
  the batch touched was rewritten or replaced by upstream (lease columns on
  `attempts`, a `disable_foreign_keys` migration-runner rebuild, fail-closed
  tool audit, schema manifest bumped to workflow version 1.4.0). No substantive
  delta survives.
- **Action:** the 3-way merge (`git merge --no-commit backup-batch` onto branch
  `rederive` from `origin/master`) was aborted (`git merge --abort`), returning
  to a clean `origin/master` at `7d6744fd`.
- **Residual:** `attempt_number` / `CHECK` are entangled with upstream's
  lease/local-retry design and cannot be integrated as a clean, bounded
  addition; reintroducing them would fight the lease architecture.
- **Outcome:** divergent code is not integrated. The batch remains on
  `backup-batch` as a superseded historical record. All 26 procedures were
  executed and marked Completed on `backup-batch`; this note records the
  supersession.

